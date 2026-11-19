import click
from pathlib import Path
from sqlalchemy.exc import OperationalError, IntegrityError

from . import db, loading


@click.group()
def main():
    """Shop Stack: BigQuery -> Parquet -> PostgreSQL -> DuckDB -> reports."""
    pass

@main.group("db")
def db_group():
    """Manage the database schema."""
    pass


@db_group.command()
def init():
    """Create the schema (does nothing if it already exists)."""
    engine = db.get_engine()
    with engine.begin() as conn:
        try:
            db.init_schema(conn)
            click.echo("Created Schema.")
        except OperationalError as e:
            raise click.ClickException(f"Failed to init the database: {e}")


@db_group.command()
def drop():
    """Drops the schema (does nothing if it doesn't exist)."""
    engine = db.get_engine()
    with engine.begin() as conn:
        try:
            click.confirm(
                "This deletes all shop-stack tables and their data. Continue?",
                abort=True,
            )
            db.drop_schema(conn)
            click.echo("Dropped existing schema.")
        except OperationalError as e:
                    raise click.ClickException(f"Failed to drop the database: {e}")


@main.command()
@click.option(
    "--source",
    type=click.Path(path_type=Path),
    default=Path("extract"),
    show_default=True,
    help="Directory containing source Parquet or CSV files.",
)
def load(source):
    """Load extracted files into the PostgreSQL OLTP database."""
    engine = db.get_engine()
    try:
        counts = loading.load_all(engine, source)
    except OperationalError as e:
        raise click.ClickException(f"Database connection failed: {e.orig}")
    except IntegrityError as e:
        raise click.ClickException(f"Data validation failed: {e.orig}")
    except (FileNotFoundError, RuntimeError, ValueError) as e:
        raise click.ClickException(str(e))

    for table, count in counts.items():
        click.echo(f"Loaded {count} rows into {table}.")