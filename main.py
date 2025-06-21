#!/bin/python3
import random
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from starlette.responses import RedirectResponse

from helper_functions import db_cursor, convert_to_stock, get_api_data, get_api_key
from stock_type import Stock, StockCreate, StockUpdate, PortfolioStock
from prometheus_metrics import REQUEST_LATENCY, REQUEST_COUNT, mount_prometheus_endpoint


app = FastAPI()


@app.get("/")
def index():
    return RedirectResponse(url="/stocks")


@app.get("/stocks", response_model=List[Stock])
async def view_stocks(symbol: Optional[str] = None, stock_id: Optional[int] = None):
    with REQUEST_LATENCY.labels("get", "/stocks").time():
        REQUEST_COUNT.labels("get", "/stocks").inc()

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
async def view_stock(symbol: str):
    with REQUEST_LATENCY.labels("get", "/stocks/{symbol}").time():
        REQUEST_COUNT.labels("get", "/stocks/{symbol}").inc()

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
async def add_stock(stock: StockCreate):
    with REQUEST_LATENCY.labels("post", "/stocks").time():
        REQUEST_COUNT.labels("post", "/stocks").inc()

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
async def update_stock(symbol: str, updated_stock: StockUpdate):
    with REQUEST_LATENCY.labels("put", "/stocks/{symbol}").time():
        REQUEST_COUNT.labels("put", "/stocks/{symbol}").inc()

        with db_cursor() as cursor:
            cursor.execute("SELECT * FROM stocks WHERE symbol = %s",
                           (symbol.upper(),))
            exists = cursor.fetchall()

            if not exists:
                raise HTTPException(status_code=404, detail="Stock not found")

            stock = exists[0]

            # Update fields.
            new_symbol = updated_stock.symbol.upper(
            ) if updated_stock.symbol else stock["symbol"]
            new_quantity = updated_stock.quantity if updated_stock.quantity is not None else stock[
                "quantity"]

            # Check that the values are unique (only if symbol is changing).
            if updated_stock.symbol and new_symbol != stock["symbol"]:
                cursor.execute(
                    "SELECT * FROM stocks WHERE symbol = %s", (new_symbol,))
                symbol_conflict = cursor.fetchall()
                if symbol_conflict:
                    raise HTTPException(
                        status_code=400, detail=f"Stock symbol '{new_symbol}' already exists.")

            # Update table.
            cursor.execute(
                "UPDATE stocks SET symbol = %s, quantity = %s WHERE symbol = %s",
                (new_symbol, new_quantity, symbol.upper())
            )

            # Commit the transaction.
            cursor._connection.commit()

            return Stock(stock_id=stock["stock_id"], symbol=new_symbol, quantity=new_quantity)


@app.delete("/stocks/{symbol}", response_model=Stock)
async def delete_stock(symbol: str):
    with REQUEST_LATENCY.labels("delete", "/stocks/{symbol}").time():
        REQUEST_COUNT.labels("delete", "/stocks/{symbol}").inc()

        with db_cursor() as cursor:
            cursor.execute("SELECT * FROM stocks WHERE symbol = %s",
                           (symbol.upper(),))
            exists = cursor.fetchall()

            if not exists:
                raise HTTPException(status_code=404, detail="Stock not found")

            stock = exists[0]

            # Removing from table.
            cursor.execute("DELETE FROM stocks WHERE symbol = %s",
                           (symbol.upper(),))

            # Commit the transaction.
            cursor._connection.commit()

            return Stock(stock_id=stock["stock_id"], symbol=stock["symbol"], quantity=stock["quantity"])


@app.get("/view_portfolio", response_model=List[PortfolioStock])
async def view_portfolio():
    with REQUEST_LATENCY.labels("get", "/view_portfolio").time():
        REQUEST_COUNT.labels("get", "/view_portfolio").inc()

        with db_cursor() as cursor:
            # Getting the latest 10 stocks - due to API limits!
            cursor.execute(
                "SELECT * FROM stocks ORDER BY created_at DESC, stock_id DESC LIMIT 10")
            stocks = cursor.fetchall()
            portfolio = []

            for stock in stocks:
                url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={stock["symbol"]}&apikey={get_api_key()}"
                data = get_api_data(url)

                portfolio.append(
                    PortfolioStock(
                        symbol=stock["symbol"],
                        quantity=stock["quantity"],
                        price=data["Global Quote"]["05. price"]
                    )
                )
            return portfolio


@app.get("/historical_prices")
async def view_historical_prices():
    with REQUEST_LATENCY.labels("get", "/historical_prices").time():
        REQUEST_COUNT.labels("get", "/historical_prices").inc()

        url = "https://www.alphavantage.co/query?function=HISTORICAL_OPTIONS&symbol=IBM&apikey=demo"
        data = get_api_data(url)["data"]
        return data


# Mounting the Prometheus metrics endpoint.
mount_prometheus_endpoint(app)
