import os
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

API_BASE = os.environ.get("API_BASE", "http://127.0.0.1:5001")

st.set_page_config(page_title="AI Price Engine", page_icon="⚡", layout="wide")


def fetch_json(path: str, payload: dict[str, Any] | None = None) -> dict[str, Any] | None:
    try:
        if payload is None:
            response = requests.get(f"{API_BASE}{path}", timeout=8)
        else:
            response = requests.post(f"{API_BASE}{path}", json=payload, timeout=8)
        if response.status_code == 200:
            return response.json()
        st.error(response.text)
    except requests.exceptions.ConnectionError:
        st.error("Flask backend is not running. Start it with: python app.py")
    except requests.exceptions.Timeout:
        st.error("Request to backend timed out.")
    return None


def build_chart(points: list[dict[str, Any]]) -> go.Figure:
    df = pd.DataFrame(points)
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["age_years"],
            y=df["price"],
            mode="lines",
            name="Depreciation",
            line=dict(color="#00F5FF", width=3),
            fill="tozeroy",
            fillcolor="rgba(0, 245, 255, 0.08)",
        )
    )
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0A0A0A",
        plot_bgcolor="#0A0A0A",
        font=dict(color="#e8e8e8"),
        title="Depreciation Curve",
        xaxis_title="Age (Years)",
        yaxis_title="Price (₹)",
        margin=dict(l=40, r=20, t=50, b=30),
    )
    return fig


def main() -> None:
    st.title("⚡ AI Price Engine")
    st.caption("Enterprise predictive analytics · price suggestion dashboard")

    metadata = fetch_json("/metadata")
    if not metadata:
        return

    categories = metadata.get("categories", [])
    brand_tiers = metadata.get("brand_tiers", [])
    brands = metadata.get("brands", {})

    category = st.selectbox("Category", categories)
    brand_tier = st.selectbox("Brand Tier", brand_tiers)
    brand_options = brands.get(category, {}).get(brand_tier, [])
    brand = st.selectbox("Brand Name", brand_options)
    condition_score = st.slider("Condition Score", 1, 10, 8)
    age_years = st.slider("Age (Years)", 0.0, 30.0, 2.5, 0.5)

    payload = {
        "category": category,
        "brand_tier": brand_tier,
        "brand": brand,
        "condition_score": condition_score,
        "age_years": age_years,
    }

    result = fetch_json("/predict_price", payload)
    if result:
        st.metric("Suggested Price", f"₹{result['predicted_price']:,.2f}")
        st.caption(f"Confidence: {result['confidence_score']:.1f}%")

    curve = fetch_json("/depreciation_curve", payload)
    if curve and curve.get("points"):
        st.plotly_chart(build_chart(curve["points"]), use_container_width=True)


if __name__ == "__main__":
    main()
#             st.markdown(
#                 f'<div class="label-neon">Model Confidence Rate</div>',
#                 unsafe_allow_html=True,
#             )
#             components.html(render_confidence_gauge(confidence), height=160)
#             st.markdown(
#                 f'<p class="confidence-text">{confidence:.1f}% model confidence</p>',
#                 unsafe_allow_html=True,
#             )
#         else:
#             st.markdown(
#                 '<div class="neon-panel"><div class="label-neon">Optimal Suggested Price</div>'
#                 '<div class="price-display">—</div></div>',
#                 unsafe_allow_html=True,
#             )

#     st.markdown("---")
#     st.markdown("### ◈ Depreciation Curve")

#     curve_points = fetch_depreciation(payload)
#     if curve_points:
#         fig = build_depreciation_chart(curve_points)
#         st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
#     else:
#         st.info("Depreciation chart requires a running backend.")

#     with st.expander("API Request Preview"):
#         st.json(payload)
#         if result:
#             st.json(result)


# if __name__ == "__main__":
#     main()

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