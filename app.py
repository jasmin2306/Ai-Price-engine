import pickle
from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st

# Path configuration
APP_ROOT = Path(__file__).resolve().parent
MODEL_PATH = APP_ROOT / "model.pkl"

st.set_page_config(
    page_title="AI Price Engine",
    page_icon="⚡",
    layout="wide"
)

# 1. Model Loading with Caching
@st.cache_resource
def load_model():
    if not MODEL_PATH.exists():
        st.error(f"model.pkl not found at {MODEL_PATH}. Please upload model.pkl to repository.")
        st.stop()
    with open(MODEL_PATH, "rb") as f:
        artifact = pickle.load(f)
    return artifact

# 2. Helper Logic Functions
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

# 3. App Main Execution
artifact = load_model()

st.title("⚡ AI PRICE ENGINE")
st.caption("ENTERPRISE PREDICTIVE ANALYTICS · NEURAL PRICING CORE")

st.divider()

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("❖ Product Parameters")
    
    category = st.selectbox("Category", options=artifact["categories"])
    
    brand_tiers_opts = artifact["brand_tiers"]
    brand_tier = st.selectbox("Brand Tier", options=brand_tiers_opts)
    
    available_brands = artifact["brands"].get(category, {}).get(brand_tier, [])
    if not available_brands:
        st.warning("No brands available for this selection.")
        brand = None
    else:
        brand = st.selectbox("Brand Name", options=available_brands)
        
    condition_score = st.slider("Condition Score", min_value=1, max_value=10, value=4)
    age_years = st.slider("Age (Years)", min_value=0.0, max_value=30.0, value=2.5, step=0.5)

with col2:
    st.subheader("❖ Live Prediction")
    
    if brand:
        original_price = resolve_original_price(artifact, category, brand_tier, brand)
        
        feature_df = pd.DataFrame([{
            "Category": category,
            "Brand_Tier": brand_tier,
            "Brand": brand,
            "Original_Price": original_price,
            "Age_In_Years": float(age_years),
            "Condition_Score": int(condition_score),
        }])
        
        pipeline = artifact["pipeline"]
        predicted = float(pipeline.predict(feature_df)[0])
        predicted = max(500.0, round(predicted, 2))
        confidence = compute_confidence(artifact, feature_df)
        
        st.metric(label="OPTIMAL SUGGESTED PRICE", value=f"₹{predicted:,.2f}")
        st.caption(f"Model Confidence Score: **{confidence}%**")
        st.caption(f"Estimated Original Base Price: ₹{original_price:,.2f}")
        
        # Depreciation Curve Chart
        st.markdown("---")
        st.write("##### Price Depreciation Forecast")
        ages = np.linspace(0, 30, 31)
        curve_points = []
        for a in ages:
            df = pd.DataFrame([{
                "Category": category,
                "Brand_Tier": brand_tier,
                "Brand": brand,
                "Original_Price": original_price,
                "Age_In_Years": float(a),
                "Condition_Score": int(condition_score),
            }])
            p = float(pipeline.predict(df)[0])
            curve_points.append({"Age": round(float(a), 1), "Price": round(max(500, p), 2)})
            
        curve_df = pd.DataFrame(curve_points)
        st.line_chart(curve_df.set_index("Age"))
