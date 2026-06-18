"""Train Random Forest price model and export model.pkl (run from notebook or CLI)."""

import pickle
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)

CATEGORIES = ["Electronics", "Fashion", "Automobiles", "Furniture"]
BRAND_TIERS = ["Premium", "Mid", "Budget"]

BRANDS = {
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
}

CATEGORY_BASE_PRICE = {
    "Electronics": 45000,
    "Fashion": 8000,
    "Automobiles": 850000,
    "Furniture": 35000,
}

TIER_MULTIPLIER = {"Premium": 1.8, "Mid": 1.0, "Budget": 0.55}


def brand_original_price(category: str, brand_tier: str, brand: str) -> float:
    base = CATEGORY_BASE_PRICE[category]
    mult = TIER_MULTIPLIER[brand_tier]
    brand_idx = BRANDS[category][brand_tier].index(brand)
    brand_factor = 0.85 + 0.1 * brand_idx
    jitter = 1.0 + (hash(brand) % 20 - 10) / 100.0
    return round(base * mult * brand_factor * jitter, 2)


def generate_synthetic_data(n_samples: int = 8000) -> pd.DataFrame:
    rows = []
    for _ in range(n_samples):
        category = np.random.choice(CATEGORIES)
        brand_tier = np.random.choice(BRAND_TIERS)
        brand = np.random.choice(BRANDS[category][brand_tier])
        age = np.random.uniform(0, 30)
        condition = np.random.randint(1, 11)
        original = brand_original_price(category, brand_tier, brand)

        category_decay = {
            "Electronics": 0.12,
            "Fashion": 0.18,
            "Automobiles": 0.08,
            "Furniture": 0.06,
        }[category]
        condition_factor = 0.55 + (condition / 10) * 0.45
        wear = 1.0 - (10 - condition) * 0.03
        depreciated = original * (1 - category_decay) ** age * condition_factor * wear
        noise = np.random.normal(0, original * 0.04)
        predicted_price = max(500, depreciated + noise)

        rows.append(
            {
                "Category": category,
                "Brand_Tier": brand_tier,
                "Brand": brand,
                "Original_Price": original,
                "Age_In_Years": round(age, 2),
                "Condition_Score": condition,
                "Predicted_Price": round(predicted_price, 2),
            }
        )
    return pd.DataFrame(rows)


def build_pipeline() -> Pipeline:
    categorical = ["Category", "Brand_Tier", "Brand"]
    numeric = ["Original_Price", "Age_In_Years", "Condition_Score"]

    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical),
            ("num", StandardScaler(), numeric),
        ]
    )

    regressor = RandomForestRegressor(
        n_estimators=200,
        max_depth=18,
        min_samples_leaf=3,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )

    return Pipeline([("preprocessor", preprocessor), ("regressor", regressor)])


def confidence_from_forest(pipeline: Pipeline, X: pd.DataFrame) -> float:
    """Confidence from inverse relative std across trees (0-100)."""
    preprocessed = pipeline.named_steps["preprocessor"].transform(X)
    trees = pipeline.named_steps["regressor"].estimators_
    tree_preds = np.array([t.predict(preprocessed) for t in trees])
    mean_pred = tree_preds.mean(axis=0)[0]
    std_pred = tree_preds.std(axis=0)[0]
    if mean_pred <= 0:
        return 50.0
    relative_std = std_pred / mean_pred
    confidence = 100.0 - min(100.0, relative_std * 250.0)
    return round(float(np.clip(confidence, 55.0, 98.5)), 1)


def train_and_export(output_path: str = "model.pkl") -> dict:
    df = generate_synthetic_data(8000)
    feature_cols = [
        "Category",
        "Brand_Tier",
        "Brand",
        "Original_Price",
        "Age_In_Years",
        "Condition_Score",
    ]
    X = df[feature_cols]
    y = df["Predicted_Price"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE
    )

    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)

    test_score = pipeline.score(X_test, y_test)

    brand_price_lookup = {}
    for category in CATEGORIES:
        for tier in BRAND_TIERS:
            for brand in BRANDS[category][tier]:
                brand_price_lookup[f"{category}|{tier}|{brand}"] = brand_original_price(
                    category, tier, brand
                )

    artifact = {
        "pipeline": pipeline,
        "brand_price_lookup": brand_price_lookup,
        "brands": BRANDS,
        "categories": CATEGORIES,
        "brand_tiers": BRAND_TIERS,
        "category_base_price": CATEGORY_BASE_PRICE,
        "tier_multiplier": TIER_MULTIPLIER,
        "feature_columns": feature_cols,
        "metrics": {"r2_test": round(test_score, 4)},
    }

    with open(output_path, "wb") as f:
        pickle.dump(artifact, f)

    print(f"Model saved to {output_path} | Test R²: {test_score:.4f}")
    return artifact


if __name__ == "__main__":
    train_and_export()
