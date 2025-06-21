#!/bin/python3
import os
from typing import List
from contextlib import contextmanager

from dotenv import load_dotenv
from mysql import connector as mysql_connector
from fastapi import HTTPException
import requests

from stock_type import Stock


load_dotenv()  # loads from .env in the current directory


def get_db_connection():  # Database Configuration
    """
    Returns the DB Connection.
    """
    return mysql_connector.connect(
        host=os.getenv("SPT_DB_HOST"),
        user=os.getenv("SPT_DB_USER"),
        password=os.getenv("SPT_DB_PASSWORD"),
        database=os.getenv("SPT_DB_NAME")
    )


def get_api_key():
    return os.getenv("SPT_ALPHA_VANTAGE_KEY")


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


def get_api_data(url: str):
    req = requests.get(url)
    data = req.json()
    return data
