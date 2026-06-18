"""Flask REST API for AI-powered price suggestions."""

import pickle
from decimal import Decimal
from pathlib import Path

import numpy as np
import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS

from models import BrandTier, ProductCategory, ProductPriceModel, init_db

APP_ROOT = Path(__file__).resolve().parent
MODEL_PATH = APP_ROOT / "model.pkl"

app = Flask(__name__)
CORS(app)
SessionLocal = init_db()

_model_artifact = None


def load_model():
    global _model_artifact
    if _model_artifact is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"model.pkl not found at {MODEL_PATH}. Run train_model.py or the notebook first."
            )
        with open(MODEL_PATH, "rb") as f:
            _model_artifact = pickle.load(f)
    return _model_artifact


def resolve_original_price(artifact: dict, category: str, brand_tier: str, brand: str) -> float:
    key = f"{category}|{brand_tier}|{brand}"
    lookup = artifact["brand_price_lookup"]
    if key in lookup:
        return lookup[key]
    base = artifact["category_base_price"][category]
    mult = artifact["tier_multiplier"][brand_tier]
    return round(base * mult, 2)


def compute_confidence(artifact: dict, feature_df: pd.DataFrame) -> float:
    pipeline = artifact["pipeline"]
    preprocessed = pipeline.named_steps["preprocessor"].transform(feature_df)
    trees = pipeline.named_steps["regressor"].estimators_
    tree_preds = np.array([t.predict(preprocessed) for t in trees])
    mean_pred = tree_preds.mean(axis=0)[0]
    std_pred = tree_preds.std(axis=0)[0]
    if mean_pred <= 0:
        return 50.0
    relative_std = std_pred / mean_pred
    confidence = 100.0 - min(100.0, relative_std * 250.0)
    return round(float(np.clip(confidence, 55.0, 98.5)), 1)


def validate_payload(data: dict) -> tuple[dict | None, str | None]:
    required = ["category", "brand_tier", "brand", "condition_score", "age_years"]
    missing = [k for k in required if k not in data]
    if missing:
        return None, f"Missing fields: {', '.join(missing)}"

    artifact = load_model()
    category = str(data["category"])
    brand_tier = str(data["brand_tier"])
    brand = str(data["brand"])

    if category not in artifact["categories"]:
        return None, f"Invalid category. Allowed: {artifact['categories']}"
    if brand_tier not in artifact["brand_tiers"]:
        return None, f"Invalid brand_tier. Allowed: {artifact['brand_tiers']}"
    if brand not in artifact["brands"][category][brand_tier]:
        return None, f"Invalid brand for {category}/{brand_tier}"

    try:
        condition_score = int(data["condition_score"])
        age_years = float(data["age_years"])
    except (TypeError, ValueError):
        return None, "condition_score must be int and age_years must be float"

    if not 1 <= condition_score <= 10:
        return None, "condition_score must be between 1 and 10"
    if not 0 <= age_years <= 30:
        return None, "age_years must be between 0 and 30"

    return {
        "category": category,
        "brand_tier": brand_tier,
        "brand": brand,
        "condition_score": condition_score,
        "age_years": age_years,
    }, None


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "model_loaded": MODEL_PATH.exists()})


@app.route("/predict_price", methods=["POST"])
def predict_price():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    validated, error = validate_payload(data)
    if error:
        return jsonify({"error": error}), 400

    try:
        artifact = load_model()
        original_price = resolve_original_price(
            artifact,
            validated["category"],
            validated["brand_tier"],
            validated["brand"],
        )

        feature_df = pd.DataFrame(
            [
                {
                    "Category": validated["category"],
                    "Brand_Tier": validated["brand_tier"],
                    "Brand": validated["brand"],
                    "Original_Price": original_price,
                    "Age_In_Years": validated["age_years"],
                    "Condition_Score": validated["condition_score"],
                }
            ]
        )

        pipeline = artifact["pipeline"]
        predicted = float(pipeline.predict(feature_df)[0])
        predicted = max(500.0, round(predicted, 2))
        confidence = compute_confidence(artifact, feature_df)

        session = SessionLocal()
        try:
            record = ProductPriceModel(
                product_category=ProductCategory(validated["category"]),
                brand_tier=BrandTier(validated["brand_tier"]),
                brand_name=validated["brand"],
                condition_score=validated["condition_score"],
                age_in_years=validated["age_years"],
                predicted_price=Decimal(str(predicted)),
                confidence_score=confidence,
            )
            session.add(record)
            session.commit()
        finally:
            session.close()

        return jsonify(
            {
                "predicted_price": predicted,
                "confidence_score": confidence,
            }
        )
    except FileNotFoundError as exc:
        return jsonify({"error": str(exc)}), 503
    except Exception as exc:
        return jsonify({"error": f"Prediction failed: {exc}"}), 500


@app.route("/metadata", methods=["GET"])
def metadata():
    """Return dropdown options and depreciation parameters for the frontend."""
    artifact = load_model()
    return jsonify(
        {
            "categories": artifact["categories"],
            "brand_tiers": artifact["brand_tiers"],
            "brands": artifact["brands"],
        }
    )


@app.route("/depreciation_curve", methods=["POST"])
def depreciation_curve():
    """Return price vs age points for charting."""
    data = request.get_json(silent=True) or {}
    validated, error = validate_payload(
        {
            **data,
            "condition_score": data.get("condition_score", 8),
            "age_years": data.get("age_years", 0),
        }
    )
    if error:
        return jsonify({"error": error}), 400

    artifact = load_model()
    original_price = resolve_original_price(
        artifact,
        validated["category"],
        validated["brand_tier"],
        validated["brand"],
    )

    ages = np.linspace(0, 30, 31)
    points = []
    pipeline = artifact["pipeline"]

    for age in ages:
        feature_df = pd.DataFrame(
            [
                {
                    "Category": validated["category"],
                    "Brand_Tier": validated["brand_tier"],
                    "Brand": validated["brand"],
                    "Original_Price": original_price,
                    "Age_In_Years": float(age),
                    "Condition_Score": validated["condition_score"],
                }
            ]
        )
        price = float(pipeline.predict(feature_df)[0])
        points.append({"age_years": round(float(age), 1), "price": round(max(500, price), 2)})

    return jsonify({"points": points, "original_price": original_price})


if __name__ == "__main__":
    import os

    # Port 5000 is reserved by Windows (Hyper-V/WSL); use 5001 by default.
    port = int(os.environ.get("FLASK_PORT", 5001))
    app.run(host="127.0.0.1", port=port, debug=True)
