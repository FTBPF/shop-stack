from pathlib import Path
import duckdb

THIS_DIR = Path(__file__).parent
REPORTS_DIR = THIS_DIR / "sql" / "reports"


def run_duck_query(conn, report_name):
    sql_path = REPORTS_DIR / f"{report_name}.sql"
    sql = sql_path.read_text()

    return conn.execute(sql).df()


def get_revenue(conn):
    """Returns the revenue report."""
    return run_duck_query(conn, "revenue")


def get_margin(conn):
    """Returns the gross margin report."""
    return run_duck_query(conn, "margin")


def get_returns(conn):
    """Returns the returns report."""
    return run_duck_query(conn, "returns")


def get_sources(conn):
    """Returns the revenue by traffic source report."""
    return run_duck_query(conn, "sources")


def get_funnel(conn):
    return run_duck_query(conn, "funnel")


def get_retention(conn):
    return run_duck_query(conn, "retention")


def run_report(warehouse_path, metric):
    """Runs one report against the DuckDB warehouse."""

    report_functions = {
        "revenue": get_revenue,
        "margin": get_margin,
        "returns": get_returns,
        "sources": get_sources,
        "funnel": get_funnel,
        "retention": get_retention,
    }

    with duckdb.connect(str(warehouse_path), read_only=True) as conn:
        return report_functions[metric](conn)
