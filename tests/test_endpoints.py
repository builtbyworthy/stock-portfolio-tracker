#!...
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def assert_endpoint(url: str, type: str = "GET", status_code: int = 200):
    if type == "GET":
        response = client.get(url)
    elif type == "POST":
        response = client.post(url)
    elif type == "PUT":
        response = client.put(url)
    elif type == "DELETE":
        response = client.delete(url)

    assert response.status_code == status_code


def test_index():
    assert_endpoint("/")


# @app.get("/stocks", response_model=List[Stock])
def test_view_stocks():
    assert_endpoint("/stocks")


# @app.get("/stocks/{symbol}", response_model=Stock)
def test_view_stock():
    assert_endpoint("/stocks/{symbol}")


# @app.post("/stocks", response_model=Stock)
def test_add_stock():
    assert_endpoint("/stocks", "POST")


# @app.put("/stocks/{symbol}", response_model=Stock)
def test_update_stock():
    assert_endpoint("/stocks/{symbol}", "DELETE")


# @app.delete("/stocks/{symbol}", response_model=Stock)
def test_delete_stock():
    assert_endpoint("/stocks/{symbol}", "DELETE")


# @app.get("/view_portfolio", response_model=List[PortfolioStock])
def test_view_portfolio():
    assert_endpoint("/view_portfolio")


def test_view_historical_prices():
    assert_endpoint("/historical_prices")
