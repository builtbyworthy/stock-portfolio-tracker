#!/bin/python3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from temp_db import stocks, Stock
from starlette.responses import RedirectResponse
from mysql import connector as mysql_connector
import random
import requests

app = FastAPI()

# Database Configuration
db = mysql_connector.connect()


class StockCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=10,
                        description="Stock symbol")
    quantity: int = Field(..., description="Stock quantity")


class StockUpdate(BaseModel):
    symbol: Optional[str] = Field(None, min_length=1, max_length=10,
                                  description="Stock symbol")
    quantity: Optional[int] = Field(None, description="Stock quantity")


class PortfolioStock(StockCreate):
    price: float = Field(..., description="Stock price")


@app.get("/")
def index():
    return RedirectResponse(url="/stocks")


@app.get("/stocks", response_model=List[Stock])
def view_stocks(symbol: str = None, stock_id: int = None):
    if symbol is not None:
        return list(filter(lambda x: x.symbol.lower() == symbol.lower(), stocks))
    elif stock_id is not None:
        return list(filter(lambda x: x.stock_id == stock_id, stocks))
    return stocks


@app.get("/stocks/{symbol}", response_model=Stock)
def view_stock(symbol: str):
    return list(filter(lambda x: x.symbol.lower() == symbol.lower(), stocks))


@app.post("/stocks", response_model=Stock)
def add_stock(stock: StockCreate):
    for current_stock in stocks:
        if current_stock.symbol.lower() == stock.symbol.lower():
            return {"message": "Stock already added!"}

    new_stock = Stock(
        stock_id=max(x.stock_id for x in stocks) + 1,
        symbol=stock.symbol.upper(),
        quantity=stock.quantity
    )

    stocks.append(new_stock)
    return new_stock


@app.put("/stocks/{symbol}", response_model=Stock)
def update_stock(symbol: str, updated_stock: StockUpdate):
    matching = [s for s in stocks if s.symbol.lower() == symbol.lower()]

    if not matching:
        raise HTTPException(status_code=404, detail="Stock not found")

    stock = matching[0]

    if updated_stock.symbol is not None:
        stock.symbol = updated_stock.symbol.upper()
    if updated_stock.quantity is not None:
        stock.quantity = updated_stock.quantity

    return stock


@app.delete("/stocks/{symbol}", response_model=Stock)
def delete_stock(symbol: str):
    for i, stock in enumerate(stocks):
        if stock.symbol.lower() == symbol.lower():
            return stocks.pop(i)

    raise HTTPException(status_code=404, detail="Stock not found")


@app.get("/view_portfolio", response_model=List[PortfolioStock])
def view_portfolio():
    portfolio = []

    for stock in stocks:
        portfolio.append(
            PortfolioStock(
                symbol=stock.symbol,
                quantity=stock.quantity,
                price=f"{random.randint(10, 500):0.2f}"
            )
        )
    return portfolio


@app.get("/historical_prices")
async def view_historical_prices():
    url = "https://www.alphavantage.co/query?function=HISTORICAL_OPTIONS&symbol=IBM&apikey=demo"
    req = requests.get(url)
    data = req.json()["data"]

    return data
