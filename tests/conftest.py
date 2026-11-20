import os
from pathlib import Path
import pytest
import sqlalchemy as sa

from shop_stack import db

TEST_FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def test_db_url():
    url = os.environ.get("SHOP_TEST_DB_URL")
    if not url:
        pytest.skip("SHOP_TEST_DB_URL is not set; skipping database tests.")
    return url


@pytest.fixture
def db_engine(test_db_url):
    # Garante que qualquer chamada interna (como o CLI) usa a base de dados de testes
    yield sa.create_engine(test_db_url)
    
@pytest.fixture
def db_connection(db_engine):
    with db_engine.begin() as conn:
        db.init_schema(conn)
        yield conn
        db.drop_schema(conn)


@pytest.fixture
def fixtures_dir():
    return TEST_FIXTURES_DIR
