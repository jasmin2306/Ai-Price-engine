import os
import pickle
from pathlib import Path
from typing import Any

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
ARTIFACT: dict[str, Any] | None = None

DEFAULT_METADATA = {
    "categories": ["Electronics", "Fashion", "Automobiles", "Furniture"],
    "brand_tiers": ["Premium", "Mid", "Budget"],
    "brands": {
        "Electronics": {
            "Premium": ["Sony", "Apple", "Bose"],
            "Mid": ["Samsung", "LG", "OnePlus"],
            "Budget": ["Xiaomi", "Realme", "Boat"],
        },
        "Fashion": {
            "Premium": ["Gucci", "Louis Vuitton", "Prada"],
            "Mid": ["Zara", "H&M", "Levi's"],
            "Budget": ["Max", "Roadster", "Allen Solly"],
        },
        "Automobiles": {
            "Premium": ["BMW", "Mercedes", "Audi"],
            "Mid": ["Honda", "Toyota", "Hyundai"],
            "Budget": ["Maruti", "Tata", "Mahindra"],
        },
        "Furniture": {
            "Premium": ["Herman Miller", "Steelcase", "Natuzzi"],
            "Mid": ["IKEA", "Godrej", "Urban Ladder"],
            "Budget": ["Nilkamal", "Durian", "Wakefit"],
        },
    },
}


def load_model_artifact() -> dict[str, Any]:
    global ARTIFACT
    if ARTIFACT is not None:
        return ARTIFACT

    if not MODEL_PATH.exists():
        from train_model import train_and_export

        train_and_export(str(MODEL_PATH))

    with open(MODEL_PATH, "rb") as handle:
        ARTIFACT = pickle.load(handle)

    return ARTIFACT


def resolve_original_price(artifact: dict[str, Any], category: str, brand_tier: str, brand: str) -> float:
    key = f"{category}|{brand_tier}|{brand}"
    lookup = artifact.get("brand_price_lookup", {})
    if key in lookup:
        return float(lookup[key])

    base = artifact.get("category_base_price", {}).get(category, 10000)
    mult = artifact.get("tier_multiplier", {}).get(brand_tier, 1.0)
    return round(float(base) * float(mult), 2)


def compute_confidence(artifact: dict[str, Any], feature_df: pd.DataFrame) -> float:
    pipeline = artifact["pipeline"]
    preprocessed = pipeline.named_steps["preprocessor"].transform(feature_df)
    trees = pipeline.named_steps["regressor"].estimators_
    tree_preds = np.array([tree.predict(preprocessed) for tree in trees])
    mean_pred = tree_preds.mean(axis=0)[0]
    std_pred = tree_preds.std(axis=0)[0]
    if mean_pred <= 0:
        return 50.0
    relative_std = std_pred / mean_pred
    confidence = 100.0 - min(100.0, relative_std * 250.0)
    return round(float(np.clip(confidence, 55.0, 98.5)), 1)


def build_feature_frame(payload: dict[str, Any], artifact: dict[str, Any]) -> pd.DataFrame:
    category = payload["category"]
    brand_tier = payload["brand_tier"]
    brand = payload["brand"]
    original_price = resolve_original_price(artifact, category, brand_tier, brand)

    return pd.DataFrame(
        [
            {
                "Category": category,
                "Brand_Tier": brand_tier,
                "Brand": brand,
                "Original_Price": original_price,
                "Age_In_Years": float(payload["age_years"]),
                "Condition_Score": int(payload["condition_score"]),
            }
        ]
    )


def log_prediction(payload: dict[str, Any], predicted_price: float, confidence: float) -> None:
    with SessionLocal() as session:
        session.add(
            ProductPriceModel(
                product_category=ProductCategory(payload["category"]),
                brand_tier=BrandTier(payload["brand_tier"]),
                brand_name=payload["brand"],
                condition_score=int(payload["condition_score"]),
                age_in_years=float(payload["age_years"]),
                predicted_price=round(predicted_price, 2),
                confidence_score=confidence,
            )
        )
        session.commit()


@app.route("/health", methods=["GET"])
def health() -> Any:
    try:
        artifact = load_model_artifact()
        return jsonify({"status": "ok", "model_loaded": bool(artifact)})
    except Exception as exc:  # pragma: no cover - defensive path
        return jsonify({"status": "error", "model_loaded": False, "error": str(exc)}), 500


@app.route("/predict_price", methods=["POST"])
def predict_price() -> Any:
    payload = request.get_json(silent=True) or {}
    required_fields = ["category", "brand_tier", "brand", "condition_score", "age_years"]
    if not payload or any(field not in payload for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        artifact = load_model_artifact()
        feature_df = build_feature_frame(payload, artifact)
        pipeline = artifact["pipeline"]
        predicted = float(pipeline.predict(feature_df)[0])
        predicted = max(500.0, round(predicted, 2))
        confidence = compute_confidence(artifact, feature_df)

        log_prediction(payload, predicted, confidence)

        return jsonify({"predicted_price": predicted, "confidence_score": confidence})
    except Exception as exc:  # pragma: no cover - defensive path
        return jsonify({"error": str(exc)}), 500


@app.route("/depreciation_curve", methods=["POST"])
def depreciation_curve() -> Any:
    payload = request.get_json(silent=True) or {}
    if not payload or any(field not in payload for field in ["category", "brand_tier", "brand", "condition_score", "age_years"]):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        artifact = load_model_artifact()
        feature_df = build_feature_frame(payload, artifact)
        pipeline = artifact["pipeline"]
        points = []

        for age in np.linspace(0, 30, 31):
            row = feature_df.iloc[0].copy()
            row["Age_In_Years"] = float(age)
            point_df = pd.DataFrame([row])
            predicted = float(pipeline.predict(point_df)[0])
            points.append({"age_years": round(float(age), 1), "price": round(max(500.0, predicted), 2)})

        return jsonify({"points": points})
    except Exception as exc:  # pragma: no cover - defensive path
        return jsonify({"error": str(exc)}), 500


@app.route("/metadata", methods=["GET"])
def metadata() -> Any:
    try:
        artifact = load_model_artifact()
        return jsonify(
            {
                "categories": artifact.get("categories", DEFAULT_METADATA["categories"]),
                "brand_tiers": artifact.get("brand_tiers", DEFAULT_METADATA["brand_tiers"]),
                "brands": artifact.get("brands", DEFAULT_METADATA["brands"]),
            }
        )
    except Exception as exc:  # pragma: no cover - defensive path
        return jsonify({"categories": DEFAULT_METADATA["categories"], "brand_tiers": DEFAULT_METADATA["brand_tiers"], "brands": DEFAULT_METADATA["brands"], "error": str(exc)})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("FLASK_PORT", "5001")), debug=True)
