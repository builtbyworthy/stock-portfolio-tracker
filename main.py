#!/bin/python3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from temp_db import stocks, Stock
from starlette.responses import RedirectResponse
from mysql import connector as mysql_connector
from contextlib import contextmanager
import random
import requests

app = FastAPI()

# Database Configuration


def get_db_connection():
    """
    Returns the DB Connection.
    """
    return mysql_connector.connect(
        host="*",
        user="*",
        password="*",
        database="*"
    )


@contextmanager
def db_cursor():
    """
    Yields the DB cursor, to use for querying.
    """
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        yield cursor
    finally:
        cursor.close()
        db.close()


def convert_to_stock(data: List[dict]):
    try:
        return [Stock(**row) for row in data]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Data formatting error: {str(e)}")


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
def view_stocks(symbol: Optional[str] = None, stock_id: Optional[int] = None):
    with db_cursor() as cursor:
        if symbol is not None:
            cursor.execute(
                "SELECT * FROM stocks WHERE symbol = %s", (symbol.upper(),))
        elif stock_id is not None:
            cursor.execute(
                "SELECT * FROM stocks WHERE stock_id = %s", (stock_id,))
        else:
            cursor.execute("SELECT * FROM stocks")

        data = cursor.fetchall()

        # Converting to Stock data type.
        return convert_to_stock(data)


@app.get("/stocks/{symbol}", response_model=Stock)
def view_stock(symbol: str):
    with db_cursor() as cursor:
        cursor.execute("SELECT * FROM stocks WHERE symbol = %s",
                       (symbol.upper(),))
        data = cursor.fetchall()

        # Converting to Stock data type.
        stocks = convert_to_stock(data)

        if not stocks:
            raise HTTPException(status_code=404, detail="Stock not found")

        return stocks[0]


@app.post("/stocks", response_model=Stock)
def add_stock(stock: StockCreate):
    with db_cursor() as cursor:
        cursor.execute("SELECT * FROM stocks WHERE symbol = %s",
                       (stock.symbol.upper(),))
        exists = cursor.fetchall()

        if exists:
            raise HTTPException(
                status_code=400, detail="Stock already exists.")

        # Add the new stock.
        sql = "INSERT INTO stocks (symbol, quantity) VALUES (%s, %s)"
        val = (stock.symbol.upper(), stock.quantity)
        cursor.execute(sql, val)

        # Commit the transaction.
        cursor._connection.commit()

        # Get the last inserted ID.
        stock_id = cursor.lastrowid
        return Stock(stock_id=stock_id, symbol=stock.symbol.upper(), quantity=stock.quantity)


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
