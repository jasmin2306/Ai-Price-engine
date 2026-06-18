# AI-Powered Price Suggestion Engine

Enterprise predictive analytics platform that suggests optimal resale prices using a Random Forest model trained on product category, brand tier, condition, and age.

## Architecture

```
streamlit_app.py  →  Flask app.py (/predict_price)  →  model.pkl
                              ↓
                    SQLite (price_predictions.db)
```

| Component | File |
|-----------|------|
| Training notebook | `price_prediction_pipeline.ipynb` |
| Training script (CLI) | `train_model.py` |
| Trained model | `model.pkl` |
| REST API | `app.py` |
| Database schema | `models.py` |
| Frontend | `streamlit_app.py` |

## Quick Start

### 1. Create virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Train the model

**Option A — Jupyter notebook**

```bash
jupyter notebook price_prediction_pipeline.ipynb
```

Run all cells. The final cell saves `model.pkl`.

**Option B — Command line**

```bash
python train_model.py
```

### 4. Start the Flask backend

```bash
python app.py
```

Server runs at `http://127.0.0.1:5001` (port 5000 is reserved on many Windows machines).

### 5. Start the Streamlit frontend

In a second terminal:

```bash
streamlit run streamlit_app.py
```

Open the URL shown in the terminal (default `http://localhost:8501`).

## API Documentation

### `GET /health`

Health check.

**Response:**
```json
{ "status": "ok", "model_loaded": true }
```

### `POST /predict_price`

Predict optimal price for a product.

**Request body:**
```json
{
  "category": "Electronics",
  "brand_tier": "Premium",
  "brand": "Sony",
  "condition_score": 8,
  "age_years": 2.5
}
```

| Field | Type | Constraints |
|-------|------|-------------|
| `category` | string | `Electronics`, `Fashion`, `Automobiles`, `Furniture` |
| `brand_tier` | string | `Premium`, `Mid`, `Budget` |
| `brand` | string | Must match tier for category |
| `condition_score` | int | 1–10 |
| `age_years` | float | 0–30 |

**Response:**
```json
{
  "predicted_price": 45230.00,
  "confidence_score": 87.3
}
```

Confidence is derived from prediction variance across Random Forest trees (lower variance → higher confidence).

### `POST /depreciation_curve`

Returns 31 price points (age 0–30) for charting.

Same request body as `/predict_price`.

### `GET /metadata`

Returns categories, brand tiers, and brand lists for UI dropdowns.

## Model Training Guide

The notebook (`price_prediction_pipeline.ipynb`) covers:

1. **Synthetic data generation** — 8,000 samples with realistic depreciation by category
2. **Feature engineering** — Category, Brand Tier, Brand, Original Price, Age, Condition
3. **Preprocessing** — One-hot encoding + standard scaling
4. **Training** — `RandomForestRegressor` (200 trees)
5. **Evaluation** — R², MAE, residual plots
6. **Confidence** — Tree-level prediction std → 0–100% score
7. **Export** — `model.pkl` artifact with pipeline + brand price lookup

### Features

| Feature | Description |
|---------|-------------|
| Category | Product vertical |
| Brand_Tier | Premium / Mid / Budget |
| Brand | Brand name (maps to original price) |
| Original_Price | MSRP proxy |
| Age_In_Years | Product age |
| Condition_Score | 1 (poor) – 10 (excellent) |

## Database

Predictions are logged to `price_predictions.db` (SQLite) via SQLAlchemy model `ProductPriceModel` in `models.py`.

## UI Theme

Cyberpunk dark theme with CSS variables:

- Background: `#0A0A0A`
- Neon green: `#39FF14`
- Cyber cyan: `#00F5FF`

Features: animated price counter, circular confidence gauge, Plotly depreciation chart, real-time API calls on input change.

## Project Structure

```
.
├── app.py
├── models.py
├── train_model.py
├── streamlit_app.py
├── price_prediction_pipeline.ipynb
├── model.pkl
├── requirements.txt
├── README.md
└── price_predictions.db   # created at runtime
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `model.pkl not found` | Run `python train_model.py` or the notebook |
| Streamlit cannot connect | Ensure Flask is running on port 5001 |
| Port permission error on Windows | Port 5000 is system-reserved; this project uses **5001** by default |
| Port in use | Set `FLASK_PORT=8080` and `API_BASE=http://127.0.0.1:8080` |

## License

MIT
