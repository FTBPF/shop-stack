  # Shop Stack

  Shop Stack is a Python-based ETL project that extracts data from CSV and Parquet files, processes it using DuckDB, and loads it into a PostgreSQL database using SQLAlchemy.

  The project provides a command-line interface (CLI) to manage the database schema and load data into the database.

  ## Requirements

  - Python 3.14+
  - [PostgreSQL](https://www.postgresql.org/)
  - [uv](https://docs.astral.sh/uv/)

  ## Installation

  Clone the repository:

  ```bash
  git clone git@github.com:FTBPF/shop-stack.git
  cd shop-stack
  ```

  Install the project and its dependencies:

  ```bash
  uv sync
  ```

  ## Database Configuration

  Shop Stack uses PostgreSQL for data storage. The connection is configured through PostgreSQL environment variables.

  Configure the following variables according to your PostgreSQL setup:

  ```bash
  export PGHOST=
  export PGPORT=
  export PGUSER=
  export PGPASSWORD=
  export PGDATABASE=
  ```

  These variables are used by the database connection to determine where to connect and which credentials to use.

  ## CLI Commands

  All commands can be executed using `uv run shop`, which runs the CLI within the project's virtual environment.
  It is also possible to setup first the virtual environment using `source .venv/bin/activate`, and then running the commands with `shop`.

  ### `shop db init`

  Creates the database schema required by Shop Stack.

  ```bash
  uv run shop db init
  ```

  This command initializes the database tables and their constraints. It is intended to be used when setting up the database for the first time.

  ### `shop db drop`

  Drops the database schema created by Shop Stack.

  ```bash
  uv run shop db drop
  ```

  This command removes the project tables from the database. Existing data stored in those tables will be lost.


  ### `shop load`

  Loads the source data into the PostgreSQL database.

  ```bash
  uv run shop load --source <source-directory>
  ```

  By default, the command reads the source files from the `extract/` directory, which contains the Parquet files generated during the BigQuery extraction process.

  #### Options

  | Option | Required | Description |
  |---|---|---|
  | `--source` | No | Path to the directory containing the source files to be loaded. |

  #### Example

  Load data from the default `extract/` directory:

  ```bash
  uv run shop load 
  ```

  Load data from a different directory:

  ```bash
  uv run shop load --source fixtures/
  ```

  The loading process:

  1. Creates a load batch to track the execution.
  2. Reads matching CSV and Parquet files from the source directory using DuckDB.
  3. Loads the data into PostgreSQL using SQL MERGE statements.
  4. Inserts new records and updates existing ones.
  5. Reports the number of records read, inserted and updated for each table.
  6. Marks the load batch as successful when the process completes.

  The loading process supports the following tables:

  - `users`
  - `products`
  - `orders`
  - `order_items`
  - `events`

  The loader uses a single database transaction so that changes can be rolled back if the loading process fails.

  ## Testing
  Database integration tests require a dedicated test database configured via `SHOP_TEST_DB_URL` (tables in this database will be dropped and recreated during test runs)
  
  Run the tests using pytest:

  ```bash
  export SHOP_TEST_DB_URL="postgresql+psycopg://user:password@localhost:5432/shop_stack_test"
  uv run pytest
  ```

  Tests cover the database operations, data loading, database constraints and expected failure scenarios.

  ## Project Structure

  ```text
  shop-stack/
  ├── src/
  │   └── shop_stack/
  │       ├── sql/
  │       ├── db.py
  │       ├── loading.py
  │       └── __init__.py
  ├── tests/
  ├── fixtures/
  ├── pyproject.toml
  └── README.md
  ```

  - `sql/` – SQL scripts used for database operations and data merging.
  - `db.py` – Database connection and schema management.
  - `loading.py` – Data loading and ETL logic.
  - `tests/` – Automated tests.
  - `fixtures/` – Sample data files used for testing.
