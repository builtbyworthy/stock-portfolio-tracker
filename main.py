#!/bin/python3
from fastapi import FastAPI, HTTPException
from temp_db import stocks
from starlette.responses import RedirectResponse
import random

app = FastAPI()

# TODO: Write logic that checks whether a stock is already
# in the db before adding.


@app.get("/")
def index():
    return RedirectResponse(url="/stocks")


@app.get("/stocks")
def view_stocks(symbol: str = None, stock_id: int = None):
    if symbol is not None:
        return list(filter(lambda x: x["symbol"].lower() == symbol.lower(), stocks))
    elif stock_id is not None:
        return list(filter(lambda x: x["stock_id"] == stock_id, stocks))
    return stocks


@app.get("/stocks/{symbol}")
def view_stock(symbol: str):
    return list(filter(lambda x: x["symbol"].lower() == symbol.lower(), stocks))


@app.post("/stocks")
def add_stock(stock: dict):
    for current_stock in stocks:
        if current_stock["symbol"].lower() == stock["symbol"].lower():
            return {"message": "Stock already added!"}

    new_stock = {
        "stock_id": max(x["stock_id"] for x in stocks) + 1,
        "symbol": stock["symbol"].upper(),
        "quantity": stock["quantity"]
    }
    stocks.append(new_stock)
    return new_stock


@app.put("/stocks/{symbol}")
def update_stock(symbol: str, updated_stock: dict):

    stock = list(
        filter(lambda x: x["symbol"].lower() == symbol.lower(), stocks))

    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    if "symbol" in updated_stock.keys():
        stock[0]["symbol"] = updated_stock["symbol"]
    if "quantity" in updated_stock.keys():
        stock[0]["quantity"] = updated_stock["quantity"]

    return stock


@app.delete("/stocks/{symbol}")
def delete_stock(symbol: str):
    for i, stock in enumerate(stocks):
        if stock["symbol"].lower() == symbol.lower():
            return stocks.pop(i)

    raise HTTPException(status_code=404, detail="Stock not found")


@app.get("/view_portfolio")
def view_portfolio():
    portfolio = []

    for stock in stocks:
        portfolio.append(
            {
                "symbol": stock["symbol"],
                "quantity": stock["quantity"],
                "price": f"{random.randint(10, 500):0.2f}"
            }
        )

    return portfolio


@app.get("/historical_prices")
def view_historical_prices():
    return {"message": "Work in progress."}
