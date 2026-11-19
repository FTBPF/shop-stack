import pytest

from shop_stack import db

def test_db_init_and_drop_schema(engine):
    # Primeira inicialização cria as tabelas
    assert db.init_schema(engine) is True
    # Segunda inicialização não faz nada e devolve False
    assert db.init_schema(engine) is False
    # Drop remove as tabelas e permite voltar a criar
    db.drop_schema(engine)
    assert db.init_schema(engine) is True

def test_db_query_helper(engine):
    db.init_schema(engine)
    rows = db.query(engine, "SELECT :value AS num", value=42)
    assert len(rows) == 1
    assert rows[0]["num"] == 42

