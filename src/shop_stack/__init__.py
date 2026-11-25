import click
import duckdb
import pandas as pd
from pathlib import Path
from sqlalchemy.exc import OperationalError, ProgrammingError

from . import db, loading, reports, warehouse as wh


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
    with engine.begin() as conn:
        try:
            summaries = loading.load_all(conn, source)
        except ProgrammingError as e:
            raise click.ClickException(f"Database schema not found. Run `shop db init` first.")
        except Exception as e:
            raise click.ClickException(f"Failed to load the files: {e}")
    load_df = pd.DataFrame(summaries).set_index("table")
    click.echo(load_df)


@main.command()
@click.option(
    "--warehouse",
    default="warehouse.duckdb",
    show_default=True,
    help="Path to the DuckDB warehouse.",
)
def build(warehouse):
    """Build the analytical warehouse."""
    try:
        wh.build_warehouse(warehouse)
    except duckdb.CatalogException:
        raise click.ClickException("Missing tables in PostgreSQL, run `shop db init` first.")
    except Exception as e:
        raise click.ClickException(f"Failed to build the warehouse: {e}")
    click.echo("Warehouse built successfully.")


@main.command()
@click.argument(
    "metric",
    type=click.Choice(["revenue", "margin", "returns", "sources"]),
)
@click.option(
    "--warehouse",
    default="warehouse.duckdb",
    show_default=True,
    help="Path to the DuckDB warehouse.",
)
def report(metric, warehouse):
    """Run one report against the DuckDB warehouse."""
    if not Path(warehouse).exists():
        raise click.ClickException(f"Warehouse not found: {warehouse}. Run `shop build` first.")
    try:
        report_df = reports.run_report(warehouse, metric)
    except Exception as e:
        raise click.ClickException(f"Failed to run the report: {e}")
    click.echo(report_df)
