  # Shop Stack

  Shop Stack is a Python-based ETL project that extracts data from CSV and Parquet files, processes it using DuckDB, and loads it into a PostgreSQL database using SQLAlchemy.

  The project provides a command-line interface (CLI) to manage the database schema and load data into the database.

  For a detailed explanation of the project's technical decisions and implementation choices, see `project/DECISIONS.md`.

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

  These variables are used by Shop Stack to determine where to connect and which credentials to use.

  For a complete list of available PostgreSQL environment variables and their descriptions, refer to the [PostgreSQL documentation - Environment Variables](https://www.postgresql.org/docs/current/libpq-envars.html).

  ## CLI Commands

  All commands can be executed using `uv run shop`, which runs the CLI within the project's virtual environment.
  It is also possible to setup first the virtual environment using `source .venv/bin/activate`, and then running the commands with `shop`.

  ### `shop db init`

  Creates the PostgreSQL database schema required by Shop Stack.

  ```bash
  uv run shop db init
  ```

  This command initializes the database tables and their constraints. It is intended to be used when setting up the database for the first time.

  ### `shop db drop`

  Drops the PostgreSQL database schema created by Shop Stack.

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

  The loader identifies which database table each file belongs to through its filename prefix. For each target table, it searches for files following the naming convention `{table_name}*.csv` or `{table_name}*.parquet`.

  For example:

  - `users.csv` or `users.parquet` → loaded into the `users` table.
  - `products.csv` or `products.parquet` → loaded into the `products` table.
  - `orders.csv` or `orders.parquet` → loaded into the `orders` table.
  - `order_items.csv` or `order_items.parquet` → loaded into the `order_items` table.
  - `events.csv` or `events.parquet` → loaded into the `events` table.

  The `*` wildcard allows additional text in the filename, such as `users-2026-10-01.csv` or `users_part1.parquet`.

  The loader supports both CSV and Parquet formats. Files that do not match one of the expected table prefixes are ignored.

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
  │       ├── reports.py
  │       ├── warehouse.py
  │       └── __init__.py
  ├── tests/
  ├── project/
  │   └── DECISIONS.md
  ├── fixtures/
  ├── pyproject.toml
  └── README.md
  ```

  - `sql/` – SQL scripts used for database operations and data merging.
  - `db.py` – Database connection and schema management.
  - `loading.py` – Data loading and ETL logic.
  - `warehouse.py` – Builds the DuckDB data warehouse by extracting and transforming data from PostgreSQL into a star schema.
  - `reports.py` – Executes analytical SQL reports against the DuckDB warehouse and returns the results.
  - `tests/` – Automated tests.
  - `project/DECISIONS.md` – Documents the technical decisions and implementation choices made throughout the project.
  - `fixtures/` – Sample data files used for testing.
