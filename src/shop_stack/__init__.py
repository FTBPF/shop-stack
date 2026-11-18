import click
from sqlalchemy.exc import OperationalError

from . import db


@click.group()
def main():
    """Shop Stack: BigQuery -> Parquet -> PostgreSQL -> DuckDB -> reports."""
    pass

@main.group("db")
def db_group():
    """Manage the database schema."""
    pass


@db_group.command()
@click.option(
    "--drop",
    is_flag=True,
    help="Drop existing schema before initializing."
)
def init(drop):
    """Create the schema (does nothing if it already exists)."""
    engine = db.get_engine()
    try:
        if drop:
            click.confirm(
                "This deletes all shop-stack tables and their data. Continue?",
                abort=True,
            )
            db.drop_schema(engine)
            click.echo("Dropped existing schema.")
        created = db.init_schema(engine)
    except OperationalError as e:
        raise click.ClickException(f"Failed to init the database: {e}")
    if created:
        click.echo("Schema created.")
    else:
        click.echo("Schema already exists.")

