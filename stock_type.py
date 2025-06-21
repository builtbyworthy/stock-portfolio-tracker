#!/bin/python3
from typing import Optional

from pydantic import BaseModel, Field, field_serializer


class StockBase(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=10,
                        description="Stock symbol")
    quantity: int = Field(..., ge=0,
                          description="Stock quantity (Quantity must be non-negative)")


class Stock(StockBase):
    stock_id: int = Field(..., description="Unique identifier of the stock")


class StockCreate(StockBase):
    pass


class StockUpdate(BaseModel):
    symbol: Optional[str] = Field(None, min_length=1, max_length=10,
                                  description="Stock symbol")
    quantity: Optional[int] = Field(None, ge=0,
                                    description="Stock quantity (Quantity must be non-negative)")


class PortfolioStock(StockCreate):
    price: float = Field(..., description="Stock price")

    @field_serializer("price")
    def format_price(self, value: float):
        return f"{value:.2f}"
