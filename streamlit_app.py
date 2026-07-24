# """
# AI-Powered Price Suggestion Engine — Cyberpunk Streamlit Frontend
# """

# import time
# from typing import Any

# import plotly.graph_objects as go
# import requests
# import streamlit as st
# import streamlit.components.v1 as components

# import os

# API_BASE = os.environ.get("API_BASE", "http://127.0.0.1:5001")

# CYBERPUNK_CSS = """
# <style>
# @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@400;600&display=swap');

# :root {
#   --bg-black: #0A0A0A;
#   --neon-green: #39FF14;
#   --cyber-cyan: #00F5FF;
#   --panel-bg: #111111;
#   --text-dim: #8a8a8a;
# }

# html, body, [class*="css"] {
#   background-color: var(--bg-black) !important;
#   color: #e8e8e8 !important;
#   font-family: 'Rajdhani', sans-serif !important;
# }

# .stApp {
#   background: radial-gradient(ellipse at top, #0f1a0f 0%, var(--bg-black) 55%) !important;
# }

# .block-container {
#   padding-top: 1.5rem !important;
#   max-width: 1200px !important;
# }

# h1, h2, h3 {
#   font-family: 'Orbitron', sans-serif !important;
#   color: var(--neon-green) !important;
#   text-shadow: 0 0 10px rgba(57, 255, 20, 0.6), 0 0 30px rgba(57, 255, 20, 0.25);
# }

# .hero-title {
#   font-family: 'Orbitron', sans-serif;
#   font-size: 2.4rem;
#   font-weight: 900;
#   letter-spacing: 0.12em;
#   text-transform: uppercase;
#   color: var(--neon-green);
#   text-align: center;
#   text-shadow: 0 0 12px rgba(57, 255, 20, 0.8), 0 0 40px rgba(57, 255, 20, 0.35);
#   margin-bottom: 0.25rem;
#   animation: titlePulse 3s ease-in-out infinite;
# }

# .hero-sub {
#   text-align: center;
#   color: var(--cyber-cyan);
#   letter-spacing: 0.25em;
#   font-size: 0.85rem;
#   margin-bottom: 2rem;
#   text-shadow: 0 0 8px rgba(0, 245, 255, 0.5);
# }

# @keyframes titlePulse {
#   0%, 100% { opacity: 1; }
#   50% { opacity: 0.85; }
# }

# .neon-panel {
#   background: linear-gradient(145deg, #121212 0%, #0d0d0d 100%);
#   border: 1px solid rgba(57, 255, 20, 0.35);
#   border-radius: 12px;
#   padding: 1.5rem;
#   box-shadow: 0 0 20px rgba(57, 255, 20, 0.08), inset 0 0 30px rgba(0, 0, 0, 0.5);
#   margin-bottom: 1rem;
# }

# .price-display {
#   font-family: 'Orbitron', sans-serif;
#   font-size: 3.2rem;
#   font-weight: 900;
#   color: var(--neon-green);
#   text-align: center;
#   text-shadow:
#     0 0 10px rgba(57, 255, 20, 1),
#     0 0 25px rgba(57, 255, 20, 0.7),
#     0 0 50px rgba(57, 255, 20, 0.4);
#   animation: priceGlow 2s ease-in-out infinite alternate;
#   margin: 0.5rem 0;
# }

# @keyframes priceGlow {
#   from { text-shadow: 0 0 10px rgba(57, 255, 20, 0.8), 0 0 30px rgba(57, 255, 20, 0.4); }
#   to   { text-shadow: 0 0 20px rgba(57, 255, 20, 1),   0 0 60px rgba(57, 255, 20, 0.6); }
# }

# .label-neon {
#   font-family: 'Orbitron', sans-serif;
#   font-size: 0.75rem;
#   letter-spacing: 0.2em;
#   color: var(--cyber-cyan);
#   text-align: center;
#   text-transform: uppercase;
# }

# .gauge-container {
#   display: flex;
#   justify-content: center;
#   align-items: center;
#   margin: 1rem 0;
# }

# .confidence-text {
#   font-family: 'Orbitron', sans-serif;
#   font-size: 1.4rem;
#   color: var(--cyber-cyan);
#   text-align: center;
#   text-shadow: 0 0 12px rgba(0, 245, 255, 0.7);
# }

# .status-ok { color: var(--neon-green); }
# .status-err { color: #ff3366; }

# div[data-testid="stSlider"] label,
# div[data-testid="stSelectbox"] label {
#   color: var(--cyber-cyan) !important;
#   font-family: 'Orbitron', sans-serif !important;
#   letter-spacing: 0.1em !important;
# }

# /* Slider min/max numbers — keep readable on dark background */
# div[data-testid="stSlider"] [data-testid="stTickBarMin"],
# div[data-testid="stSlider"] [data-testid="stTickBarMax"] {
#   color: #ffffff !important;
#   background: transparent !important;
#   font-family: 'Orbitron', sans-serif !important;
#   font-size: 0.8rem !important;
#   font-weight: 700 !important;
#   text-shadow: none !important;
# }

# /* Slider thumb */
# div[data-testid="stSlider"] [data-baseweb="slider"] [role="slider"] {
#   background-color: var(--cyber-cyan) !important;
#   border: 2px solid var(--neon-green) !important;
#   box-shadow: 0 0 10px rgba(0, 245, 255, 0.7) !important;
# }

# .slider-value {
#   font-family: 'Orbitron', sans-serif;
#   font-size: 0.95rem;
#   color: #cccccc;
#   margin: -0.4rem 0 1.2rem 0;
#   padding: 0.35rem 0.75rem;
#   background: rgba(0, 245, 255, 0.06);
#   border-left: 3px solid var(--cyber-cyan);
#   border-radius: 0 6px 6px 0;
# }

# .slider-value span {
#   color: var(--neon-green);
#   font-size: 1.15rem;
#   font-weight: 700;
#   text-shadow: 0 0 8px rgba(57, 255, 20, 0.5);
# }

# hr {
#   border-color: rgba(0, 245, 255, 0.2) !important;
# }

# #MainMenu, footer, header { visibility: hidden; }
# </style>
# """


# def render_confidence_gauge(confidence: float) -> str:
#     pct = min(100, max(0, confidence))
#     circumference = 2 * 3.14159 * 54
#     offset = circumference * (1 - pct / 100)
#     color = "#39FF14" if pct >= 75 else "#00F5FF" if pct >= 60 else "#ff3366"
#     return f"""
#     <div class="gauge-container">
#       <svg width="140" height="140" viewBox="0 0 140 140">
#         <circle cx="70" cy="70" r="54" fill="none" stroke="#1a1a1a" stroke-width="10"/>
#         <circle cx="70" cy="70" r="54" fill="none" stroke="{color}" stroke-width="10"
#           stroke-dasharray="{circumference}" stroke-dashoffset="{offset}"
#           stroke-linecap="round" transform="rotate(-90 70 70)"
#           style="filter: drop-shadow(0 0 8px {color}); transition: stroke-dashoffset 0.8s ease;"/>
#         <text x="70" y="65" text-anchor="middle" fill="{color}" font-family="Orbitron" font-size="22" font-weight="bold">{pct:.0f}%</text>
#         <text x="70" y="88" text-anchor="middle" fill="#8a8a8a" font-family="Rajdhani" font-size="11">CONFIDENCE</text>
#       </svg>
#     </div>
#     """


# def animated_price_html(target: float, duration_ms: int = 1200) -> str:
#     return f"""
#     <div class="neon-panel">
#       <div class="label-neon">Optimal Suggested Price</div>
#       <div class="price-display" id="price-counter">₹0</div>
#     </div>
#     <script>
#     (function() {{
#       const target = {target};
#       const el = document.getElementById('price-counter');
#       const duration = {duration_ms};
#       const start = performance.now();
#       function tick(now) {{
#         const t = Math.min(1, (now - start) / duration);
#         const eased = 1 - Math.pow(1 - t, 3);
#         const val = Math.round(target * eased);
#         el.textContent = '₹' + val.toLocaleString('en-IN');
#         if (t < 1) requestAnimationFrame(tick);
#       }}
#       requestAnimationFrame(tick);
#     }})();
#     </script>
#     """


# def fetch_prediction(payload: dict[str, Any]) -> dict[str, Any] | None:
#     try:
#         resp = requests.post(f"{API_BASE}/predict_price", json=payload, timeout=8)
#         if resp.status_code == 200:
#             return resp.json()
#         st.error(f"API error: {resp.json().get('error', resp.text)}")
#     except requests.exceptions.ConnectionError:
#         st.error("Cannot reach Flask API. Start backend: `python app.py`")
#     except requests.exceptions.Timeout:
#         st.error("API request timed out.")
#     return None


# def fetch_depreciation(payload: dict[str, Any]) -> list[dict] | None:
#     try:
#         resp = requests.post(f"{API_BASE}/depreciation_curve", json=payload, timeout=10)
#         if resp.status_code == 200:
#             return resp.json().get("points", [])
#     except requests.exceptions.RequestException:
#         pass
#     return None


# def build_depreciation_chart(points: list[dict]) -> go.Figure:
#     ages = [p["age_years"] for p in points]
#     prices = [p["price"] for p in points]

#     fig = go.Figure()
#     fig.add_trace(
#         go.Scatter(
#             x=ages,
#             y=prices,
#             mode="lines",
#             name="Depreciation",
#             line=dict(color="#00F5FF", width=3),
#             fill="tozeroy",
#             fillcolor="rgba(0, 245, 255, 0.08)",
#         )
#     )
#     fig.update_layout(
#         template="plotly_dark",
#         paper_bgcolor="#0A0A0A",
#         plot_bgcolor="#0A0A0A",
#         font=dict(family="Rajdhani", color="#e8e8e8"),
#         title=dict(
#             text="DEPRECIATION CURVE",
#             font=dict(family="Orbitron", color="#39FF14", size=16),
#             x=0.5,
#         ),
#         xaxis=dict(
#             title="Age (Years)",
#             gridcolor="rgba(0, 245, 255, 0.12)",
#             zerolinecolor="rgba(57, 255, 20, 0.2)",
#         ),
#         yaxis=dict(
#             title="Price (₹)",
#             gridcolor="rgba(0, 245, 255, 0.12)",
#             zerolinecolor="rgba(57, 255, 20, 0.2)",
#             tickformat=",.0f",
#         ),
#         margin=dict(l=60, r=20, t=60, b=50),
#         height=380,
#     )
#     return fig


# def fetch_metadata() -> dict | None:
#     try:
#         resp = requests.get(f"{API_BASE}/metadata", timeout=5)
#         if resp.status_code == 200:
#             return resp.json()
#     except requests.exceptions.RequestException:
#         pass
#     return None


# def main():
#     st.set_page_config(
#         page_title="AI Price Engine",
#         page_icon="⚡",
#         layout="wide",
#         initial_sidebar_state="collapsed",
#     )
#     st.markdown(CYBERPUNK_CSS, unsafe_allow_html=True)
#     st.markdown('<div class="hero-title">⚡ AI Price Engine</div>', unsafe_allow_html=True)
#     st.markdown(
#         '<div class="hero-sub">ENTERPRISE PREDICTIVE ANALYTICS · NEURAL PRICING CORE</div>',
#         unsafe_allow_html=True,
#     )

#     meta = fetch_metadata()
#     if not meta:
#         st.warning("Backend offline — using default catalog. Run `python app.py` first.")
#         meta = {
#             "categories": ["Electronics", "Fashion", "Automobiles", "Furniture"],
#             "brand_tiers": ["Premium", "Mid", "Budget"],
#             "brands": {
#                 "Electronics": {
#                     "Premium": ["Sony", "Apple", "Bose"],
#                     "Mid": ["Samsung", "LG", "OnePlus"],
#                     "Budget": ["Xiaomi", "Realme", "Boat"],
#                 },
#                 "Fashion": {
#                     "Premium": ["Gucci", "Louis Vuitton", "Prada"],
#                     "Mid": ["Zara", "H&M", "Levi's"],
#                     "Budget": ["Max", "Roadster", "Allen Solly"],
#                 },
#                 "Automobiles": {
#                     "Premium": ["BMW", "Mercedes", "Audi"],
#                     "Mid": ["Honda", "Toyota", "Hyundai"],
#                     "Budget": ["Maruti", "Tata", "Mahindra"],
#                 },
#                 "Furniture": {
#                     "Premium": ["Herman Miller", "Steelcase", "Natuzzi"],
#                     "Mid": ["IKEA", "Godrej", "Urban Ladder"],
#                     "Budget": ["Nilkamal", "Durian", "Wakefit"],
#                 },
#             },
#         }

#     col_inputs, col_results = st.columns([1, 1.2], gap="large")

#     with col_inputs:
#         st.markdown("### ◈ Product Parameters")
#         category = st.selectbox("Category", meta["categories"], key="category")
#         brand_tier = st.selectbox("Brand Tier", meta["brand_tiers"], key="brand_tier")
#         brand_options = meta["brands"][category][brand_tier]
#         brand = st.selectbox("Brand Name", brand_options, key="brand")
#         condition_score = st.slider(
#             "Condition Score",
#             min_value=1,
#             max_value=10,
#             value=8,
#             step=1,
#             key="condition",
#             help="1 = Poor condition, 10 = Excellent condition",
#         )
#         st.markdown(
#             f'<div class="slider-value">Selected: <span>{condition_score}</span> / 10</div>',
#             unsafe_allow_html=True,
#         )
#         age_years = st.slider(
#             "Age (Years)",
#             min_value=0.0,
#             max_value=30.0,
#             value=2.5,
#             step=0.5,
#             key="age",
#             help="Product age from 0 to 30 years",
#         )
#         st.markdown(
#             f'<div class="slider-value">Selected: <span>{age_years:.1f}</span> years</div>',
#             unsafe_allow_html=True,
#         )

#     payload = {
#         "category": category,
#         "brand_tier": brand_tier,
#         "brand": brand,
#         "condition_score": condition_score,
#         "age_years": age_years,
#     }

#     with col_results:
#         st.markdown("### ◈ Live Prediction")
#         result = fetch_prediction(payload)

#         if result:
#             price = result["predicted_price"]
#             confidence = result["confidence_score"]

#             components.html(animated_price_html(price), height=160)
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