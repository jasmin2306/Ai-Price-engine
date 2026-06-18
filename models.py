"""SQLAlchemy schema for price prediction audit log."""

from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, Enum, Float, Integer, Numeric, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class ProductCategory(PyEnum):
    ELECTRONICS = "Electronics"
    FASHION = "Fashion"
    AUTOMOBILES = "Automobiles"
    FURNITURE = "Furniture"


class BrandTier(PyEnum):
    PREMIUM = "Premium"
    MID = "Mid"
    BUDGET = "Budget"


class ProductPriceModel(Base):
    __tablename__ = "product_price_predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_category = Column(
        Enum(ProductCategory, name="product_category_enum"),
        nullable=False,
    )
    brand_tier = Column(Enum(BrandTier, name="brand_tier_enum"), nullable=False)
    brand_name = Column(String(100), nullable=False)
    condition_score = Column(Integer, nullable=False)
    age_in_years = Column(Float, nullable=False)
    predicted_price = Column(Numeric(12, 2), nullable=False)
    confidence_score = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


def get_engine(db_url: str = "sqlite:///price_predictions.db"):
    return create_engine(db_url, echo=False)


def init_db(db_url: str = "sqlite:///price_predictions.db"):
    engine = get_engine(db_url)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)
