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
def engine(test_db_url):
    # Garante que qualquer chamada interna (como o CLI) usa a base de dados de testes
    engine = sa.create_engine(test_db_url)
    db.drop_schema(engine)
    yield engine


@pytest.fixture
def fixtures_dir():
    return TEST_FIXTURES_DIR
