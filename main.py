#!/bin/python3
from fastapi import FastAPI
from temp_db import stocks
from starlette.responses import RedirectResponse
import random

app = FastAPI()


@app.get("/")
def index():
    return RedirectResponse(url="/stocks")


@app.get("/stocks")
def view_stocks(symbol: str = None, stock_id: int = None):
    if symbol is not None:
        return list(filter(lambda x: symbol in [x["symbol"].lower(), x["symbol"]], stocks))
    elif stock_id is not None:
        return list(filter(lambda x: x["stock_id"] == stock_id, stocks))
    return stocks


@app.get("/stocks/{symbol}")
def view_stock(symbol: str):
    return list(filter(lambda x: symbol in [x["symbol"].lower(), x["symbol"]], stocks))


@app.post("/stocks")
def add_stock(stock: dict):
    new_stock = {
        "stock_id": max(x["stock_id"] for x in stocks) + 1,
        "symbol": stock["symbol"].upper(),
        "quantity": stock["quantity"]
    }
    stocks.append(new_stock)
    print(stocks)
    return stocks


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
