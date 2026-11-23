# Shop Stack

Build a small but complete data stack for an online clothing retailer:
extract from a cloud warehouse, load a transactional database, build an
analytical star schema, and answer the business's questions on top of it,
all driven by one command line tool.

This is the capstone of the SQL stage: every session shows up somewhere.
Build it with the same rigor as `footy-table` and `footy-sql`. It's also
the project you'll show in job interviews: write its README for a hiring
manager.


## Learning Objectives

* Extracting data from BigQuery with Python: parameterized queries, cost
  estimates before running, Parquet output (Session 6).
* Designing and loading a normalized OLTP schema in PostgreSQL, with
  constraints, in transactions, and reconciling counts with the source
  (Sessions 4 and 5).
* Designing a star schema with a stated grain, and building it in DuckDB
  from the OLTP data (Sessions 4 and 6).
* Analytical SQL for real business metrics: cohort retention, funnels,
  return rates, margins (Sessions 2, 3 and 6).
* Comparing engines on the same queries, with numbers (Sessions 5 and 6).
* A tested, reproducible pipeline: one command rebuilds everything.


## Concepts

* **Source** — BigQuery's public `bigquery-public-data.thelook_ecommerce`
  dataset: users, products, orders, order items and web events of a
  fictional clothing shop.
* **Extract** — a slice of the source (a date range), saved locally as
  Parquet files, one per table. Raw: exactly as BigQuery returned it.
* **OLTP** — your PostgreSQL schema: normalized, constrained, loaded from
  the extract.
* **Warehouse** — your DuckDB file: a star schema built from the OLTP
  database.

The data flows one way, each step reading only from the one before:

```
BigQuery ──extract──▶ Parquet ──load──▶ PostgreSQL ──build──▶ DuckDB ──report──▶ results
(source)              (extract)         (OLTP)                (warehouse)
```

**Metrics**, defined precisely so that everyone gets the same numbers:

* **Revenue** — the sum of `sale_price` of order items whose status is
  neither `Cancelled` nor `Returned`, by the item's `created_at`.
* **Gross margin** — revenue minus the products' `cost`, over the same
  items.
* **Active order** — an order whose status isn't `Cancelled` (returned
  orders count: the customer did come back).
* **Cohort** — a group of customers who share a starting point; here,
  the month of their first active order. Everyone who first ordered in
  January 2025 is the January 2025 cohort.
* **Retention** — for each cohort, the share of its customers who placed
  an active order again *k* months later (written **M+k**). "January's
  retention at M+2 is 100%" means every customer in the January cohort
  ordered again in March.

  Cohorts are how a shop tells whether customers come back, without new
  customers hiding old ones leaving: each row follows one group over
  time. On the fixtures (see Acceptance) the result looks like this:

  | Cohort  | Customers | M+1  | M+2  |
  |---------|-----------|------|------|
  | 2025-01 | 2         | 50%  | 100% |
  | 2025-02 | 1         | 100% |      |
  | 2025-03 | 1         |      |      |

  Read it row by row: of January's 2 customers, 1 ordered in February
  (M+1) and both ordered in March (M+2). Empty cells are months that
  haven't happened yet in the data.
* **Funnel** — over web sessions: the number of distinct sessions with
  at least one `product` event, one `cart` event, and one `purchase`
  event; each stage's conversion relative to the previous one.
* **Return rate** — per product category, returned items over all items
  that weren't cancelled.


## Data Source

`thelook_ecommerce` in BigQuery's public datasets, through your sandbox
project from Session 6. The tables you need, and the columns to start with
(check the real schemas in the console: they're the authority):

| Table         | Columns                                                                 |
|---------------|-------------------------------------------------------------------------|
| `users`       | `id`, `first_name`, `country`, `traffic_source`, `created_at`           |
| `products`    | `id`, `name`, `category`, `brand`, `department`, `cost`, `retail_price` |
| `orders`      | `order_id`, `user_id`, `status`, `created_at`, `num_of_item`            |
| `order_items` | `id`, `order_id`, `user_id`, `product_id`, `status`, `created_at`, `sale_price` |
| `events`      | `id`, `user_id`, `session_id`, `sequence_number`, `created_at`, `event_type` |

The data is synthetic and regenerated regularly, so totals change over
time: your extract is a snapshot, and that's fine. Keep slices small enough
to stay well inside the sandbox's free limits (one year of orders is a good
start; events are by far the biggest table).

`fixtures/` holds a tiny hand-made dataset with the same columns, as CSV,
for the tests: 5 users, 4 products, 9 orders, 11 order items and 7 web
sessions. Every expected number under Acceptance can be checked by hand
from those files.

Two databases on the lab VM are yours, already created and empty:

* `ff.shop-stack`, for development: what `shop` uses day to day.
* `ff.shop-stack-test`, for the tests (see Guidance). Tests never touch the
  development database.

Connect as in the sessions, with the libpq environment variables
(`PGHOST`, `PGUSER`, `PGPASSWORD`, ...), and point `PGDATABASE` at the
development database:

```
export PGDATABASE=ff.shop-stack
```

With those set, `psql` needs no connection options, and neither do `shop`
and DuckDB (see below).


## Usage and Behaviour

`shop` connects to PostgreSQL through the `SHOP_DB_URL` environment
variable, a SQLAlchemy URL. When that's not set, it uses
`postgresql+psycopg://`: an otherwise empty URL, which libpq fills in from
the `PG*` variables, as it does for `psql`. Day to day,
`PGDATABASE=ff.shop-stack` is all you need; `SHOP_DB_URL` is for pointing
`shop` somewhere else (the tests do). BigQuery is reached through your
sandbox project, in `SHOP_BQ_PROJECT`.


### Extract

```
shop extract --from {YYYY-MM-DD} --to {YYYY-MM-DD} [--dry-run] [--max-gb {N}]
```

* Runs one parameterized query per table (dates as query parameters, never
  formatted into the SQL) and writes `extract/{table}.parquet`.
* `orders` and `events` are filtered by their `created_at`; `order_items`
  through their order, so every item's order is in the extract. `users`
  and `products` are small: take them all, so that every order and event
  finds its user and product.
* Always does a dry run first, prints the estimated bytes for each query,
  and refuses to run if the total exceeds `--max-gb` (default: 5).
  `--dry-run` stops after printing the estimates.
* Only the five tables and the listed columns: no `SELECT *`.


### Load

```
shop load [--source {dir}]
```

* Loads `extract/` (or `--source`, which may hold CSV or Parquet files:
  the tests use `fixtures/`) into the PostgreSQL schema in `SHOP_DB_URL`,
  creating it if needed, in one transaction.
* Your schema: normalized, typed (money is `NUMERIC`), with primary keys,
  foreign keys, `NOT NULL`s and `CHECK`s where they make sense. Anonymous
  web events (no `user_id`) must load. See **Designing the OLTP Schema**,
  below.
* Reconciles: after loading, compares each table's row count with the
  source files and fails loudly on any difference.
* Re-running replaces the data; it never duplicates it.


### Build

```
shop build [--warehouse {file.duckdb}]
```

* Builds the star schema in DuckDB (default: `warehouse.duckdb`), reading
  from PostgreSQL, never from the extract files: PostgreSQL is the
  checked, constrained source of truth.
* DuckDB reads PostgreSQL directly, with its `postgres` extension (see
  Guidance): the whole build is one `warehouse.sql` file, in DuckDB's SQL,
  that you can also run by hand in the DuckDB CLI.
* At least: `fact_order_items` (grain: one row per order item, with
  revenue, cost and status), `fact_events` (one row per event),
  `dim_customer`, `dim_product` and `dim_date`. Document each table's grain
  and keys in the README. See **Designing the Star Schema**, below.
* Rebuilds from scratch every time.


### Report

```
shop report {metric} [--warehouse {file.duckdb}] [--csv]
```

* `metric` is one of `revenue` (per month), `margin` (per month),
  `retention` (per cohort), `funnel`, `returns` (per category) and
  `sources` (revenue per traffic source). All computed in SQL, in DuckDB,
  from the star schema.
* Prints a readable table. `--csv` writes it to standard output as CSV
  instead.


### Bench

```
shop bench
```

* Runs three of the reports on PostgreSQL (against the normalized schema)
  and on DuckDB (against the star schema), several times each, and prints
  the median times side by side.
* The same question needs two queries here: the DuckDB one you already
  have, and a PostgreSQL one written against your OLTP tables. Their
  results must match; that's part of the test.


### All

```
shop all --from {YYYY-MM-DD} --to {YYYY-MM-DD}
```

* `extract`, `load`, `build`, then every report: the whole stack from one
  command.


### Designing the OLTP Schema

Same principles as `footy-sql`'s **Designing the Schema**. Here the
entities are given, one per source table, but their source shapes aren't
all normalized. Questions to answer on paper before writing DDL:

* Which source columns are the keys? (They're stable ids: keep them as
  natural keys, rather than adding surrogates.)
* `order_items` has a `user_id`, and so does its order. Is that the same
  fact stored twice? What should your schema keep?
* `orders` has `num_of_item`: can it be computed from `order_items`? Keep
  it, check it, or drop it?
* `status` and `event_type` hold a few known values: which constraint
  makes sure no others get in?
* `events.user_id` can be empty. What does that mean for its foreign key?

Self-check: every reference is a foreign key, no fact is stored twice, and
the fixtures' negative-price and unknown-product cases (see Acceptance)
would each break a named constraint.


### Designing the Star Schema

A reminder of Session 4's OLTP vs. OLAP modelling:

* **Grain first.** The grain of a fact table is what one of its rows is:
  "one order item", "one web event". Decide it first, write it down in
  one sentence; everything else follows from it.
* **Facts** hold the measurements (sale price, cost) and the keys of the
  dimensions. **Dimensions** hold what you group and filter by (category,
  brand, country, traffic source), one wide table each, with no further
  joins: where OLTP normalizes, the warehouse deliberately repeats.
* **`dim_date`** has one row per day, with its year, month, first day of
  the month, weekday, and so on. Reports group by its columns instead of
  calling date functions everywhere. Build it with DuckDB's `range` (or
  `generate_series`) over the days the data covers.

Self-check: you can state each table's grain in one sentence, and every
report under **Report** is one fact table joined to some of its
dimensions, then grouped.


## Guidance

* Initialize with `uv init --app --package shop-stack` (the command is
  `shop`), and add every dependency up front:

  ```
  uv add click sqlalchemy "psycopg[binary]" duckdb google-cloud-bigquery pyarrow pandas
  uv add --dev pytest
  ```

  `pandas` is for pretty-printing and for trying out hard metrics (see
  retention, below): every computation that `shop` runs is SQL.
* Suggested module layout, with each SQL file named after the engine it
  runs on:
  * `__init__.py` — CLI entry point; calls into other modules, nothing else.
  * `extract.py` — BigQuery queries (BigQuery SQL), dry runs, Parquet
    writing.
  * `oltp.py` + `oltp.sql` — the PostgreSQL schema (PostgreSQL DDL),
    loading, reconciling.
  * `warehouse.py` + `warehouse.sql` — the star schema build (DuckDB SQL,
    reading PostgreSQL through `ATTACH`).
  * `reports.py` + `reports/{metric}.sql` — one DuckDB query per metric,
    against the star schema.
  * `bench.py` + `bench/{metric}.sql` — the PostgreSQL versions of the
    three benchmarked reports, against the OLTP schema.
* Keep SQL in `.sql` files, loaded by name: easier to read, test and run
  by hand in `psql`, DBeaver or the DuckDB CLI. As in `footy-sql`, develop
  every query by hand first.
* **BigQuery from Python.** You've used BigQuery in the web console; from
  Python, it takes a one-off setup, then a client.
  1. Install the Google Cloud CLI, `gcloud`
     ([instructions](https://cloud.google.com/sdk/docs/install)).
  2. Log in, once, for code running on your laptop:
     `gcloud auth application-default login`. It opens a browser; use the
     same Google account as your sandbox.
  3. Find your sandbox's project id: in the console, the project picker at
     the top shows it (something like `my-sandbox-123456`). Put it in
     `SHOP_BQ_PROJECT`.

  Then, a dry run (the cost estimate) and a real run, both with
  parameters:

  ```python
  import datetime as dt
  import os

  import pyarrow.parquet as pq
  from google.cloud import bigquery

  client = bigquery.Client(project=os.environ['SHOP_BQ_PROJECT'])

  sql = '''
      SELECT order_id, user_id, status, created_at, num_of_item
      FROM `bigquery-public-data.thelook_ecommerce.orders`
      WHERE created_at >= @start AND created_at < @end
  '''
  params = [
      bigquery.ScalarQueryParameter('start', 'TIMESTAMP', dt.datetime(2025, 1, 1)),
      bigquery.ScalarQueryParameter('end', 'TIMESTAMP', dt.datetime(2026, 1, 1)),
  ]

  # Dry run: nothing is read or billed, BigQuery only estimates.
  config = bigquery.QueryJobConfig(
      query_parameters=params, dry_run=True, use_query_cache=False,
  )
  job = client.query(sql, job_config=config)
  print(f'{job.total_bytes_processed / 1e9:.3f} GB')

  # Real run: results as an Arrow table, written straight to Parquet.
  config = bigquery.QueryJobConfig(query_parameters=params)
  table = client.query(sql, job_config=config).to_arrow()
  pq.write_table(table, 'extract/orders.parquet')
  ```

  `--to` is inclusive for the user, so `end` is the day after it.
  `users` and `products` need no parameters at all.
* **Loading from Python.** Same transaction pattern as `footy-sql` (one
  `engine.begin()` block for the whole load, `conn.execute(insert,
  list_of_dicts)` per table). To read CSV and Parquet files alike, DuckDB
  is handy: it returns plain Python values, with `None` for empty cells
  (the anonymous events' `user_id`).

  ```python
  import duckdb

  READERS = {
      '.csv': 'SELECT * FROM read_csv(?)',
      '.parquet': 'SELECT * FROM read_parquet(?)',
  }

  def read_rows(path):
      """Rows of a CSV or Parquet file, as a list of dicts."""
      result = duckdb.execute(READERS[path.suffix], [str(path)])
      columns = [d[0] for d in result.description]
      return [dict(zip(columns, row)) for row in result.fetchall()]
  ```

  Insert parents before children (users and products, then orders, then
  order items), and delete in the opposite order when re-loading.
* **DuckDB reading PostgreSQL.** First, attach PostgreSQL as a read-only
  database named `oltp` (by hand in the DuckDB CLI, or from
  `warehouse.py`):

  ```sql
  INSTALL postgres;
  LOAD postgres;
  ATTACH '' AS oltp (TYPE postgres, READ_ONLY);
  ```

  The empty string is a libpq connection string with nothing in it, so,
  like `psql`, DuckDB takes everything from the `PG*` variables.

  Then `warehouse.sql` reads its tables as `oltp.public.<table>`:

  ```sql
  CREATE OR REPLACE TABLE dim_product AS
  SELECT ... FROM oltp.public.product;
  ```

  From `warehouse.py`, attach whatever `SHOP_DB_URL` points at (in tests,
  `ff.shop-stack-test`). `ATTACH` also takes a plain `postgresql://` URL,
  without SQLAlchemy's `+psycopg`:
  `sa.make_url(url).set(drivername='postgresql').render_as_string(hide_password=False)`
  converts `postgresql+psycopg:///ff.shop-stack-test` into
  `postgresql:///ff.shop-stack-test`, and the default
  `postgresql+psycopg://` into `postgresql://`, which, like `''`, takes
  everything from the `PG*` variables. `ATTACH` can't take a query
  parameter, so `warehouse.py` builds that statement from the URL, runs
  it, then runs `warehouse.sql`. It's the one place where a value is
  formatted into SQL: it comes from your own environment, never from a
  user.
* Tests:
  * `extract.py`: test the query building and the cost guard with a fake
    client; never call BigQuery from tests.
  * Everything else: run the pipeline on `fixtures/`, against
    `ff.shop-stack-test` (in `SHOP_TEST_DB_URL`, e.g.
    `postgresql+psycopg:///ff.shop-stack-test`: the same `PG*` variables,
    another database) and a DuckDB file in `tmp_path`, and check the
    Acceptance numbers. Same `pytest` fixture pattern as `footy-sql`, and
    the same rule: no `SHOP_TEST_DB_URL`, no tests.
  * GitHub Actions: the same throwaway PostgreSQL `services:` container as
    `footy-sql`.
* Cohort retention is the hardest query here. If you're stuck, build it in
  pandas on the fixtures first, then translate it step by step into CTEs:
  your Rosetta Stone was made for this. The steps: each customer's cohort
  month; each customer's active order months; the difference in months
  between the two; then, per cohort and difference, distinct customers
  over the cohort's size.

### Possible course

1. The OLTP schema and `shop load`, on the fixtures, reconciling.
2. The star schema and `shop build`, on the fixtures.
3. `revenue`, `margin`, `returns`, `sources`; then `funnel`; then
   `retention`.
4. `shop extract`, with the cost guard, then the real data through every step.
5. `shop bench`, `shop all`, the README.


## Suggested Pace

Two working weeks, at 4-6h a day. Every row is one or more branches, PRs
with green GitHub Actions, and merges. Days 5 and 10 are deliberate slack.
Check-ins happen about twice a week, on days that vary: whenever one comes,
show where you are, and never wait for one to carry on.

**Week one — from fixtures to a star schema.**

| Day | Focus | End of day |
|-----|-------|------------|
| 1 | **Skeleton and OLTP design.** `uv init`, `click` group, `pytest`, GitHub Actions with the PostgreSQL service. ER diagram of the OLTP schema on paper, through **Designing the OLTP Schema**'s questions and self-check; photo sent to your mentor. | CI green; schema designed and self-checked. |
| 2 | **Load.** `oltp.sql`, run by hand first, then `shop load --source fixtures/` in one transaction, reconciliation, re-runs without duplicates. Tests on row counts and on constraints (a negative price, an order item with an unknown product). | The fixtures load and reconcile. |
| 3 | **Star schema design and build.** Grain and keys of each table on paper, through **Designing the Star Schema**'s self-check; photo sent to your mentor. Then `warehouse.sql`, by hand in the DuckDB CLI, then `shop build` on the fixtures. | `fact_order_items` has 11 rows; the dimensions hold 5 customers and 4 products. |
| 4 | **First reports.** `revenue`, `margin`, `returns` and `sources`, each a `.sql` file with a test against Acceptance. | Four reports match Acceptance. |
| 5 | **Slack.** Catch up. Review the week; refactor what hurts. | Week one wrapped up. |

**Week two — real data and the hard metrics.**

| Day | Focus | End of day |
|-----|-------|------------|
| 6 | **Funnel and retention.** The funnel first (distinct sessions per stage), then cohort retention, in pandas first if needed, then in SQL. Tested against Acceptance. | Every report matches Acceptance. |
| 7 | **Extract.** BigQuery setup (`gcloud`, login, project id), then `shop extract` with dry-run estimates, the `--max-gb` guard and parameters, tested with a fake client. Then a real extract of one year. | Real Parquet files under `extract/`; their sizes and estimated bytes noted. |
| 8 | **Real data, end to end.** Load, reconcile, build and report on the real extract. Fix what the real data reveals (anonymous events, statuses, time zones). `shop all`. | `shop all` runs end to end on real data. |
| 9 | **Bench and README.** The PostgreSQL versions of three reports, then `shop bench`, results in the README with your interpretation (Session 6's head to head, on your own data). README for a hiring manager: the problem, the architecture (a diagram), the grain of each table, findings, how to run it. | Every Acceptance item covered by a test; CI green on `main`. |
| 10 | **Slack and stretch.** Anything that slipped, then stretch goals. Prepare a 20-minute presentation for the next check-in. | Ready for the final review and presentation. |


## Acceptance

All numbers for the `fixtures/` dataset, after `shop load --source
fixtures/` and `shop build`. They're small enough to verify by hand: do
it once, before writing the queries.

* **Row counts:** 5 users, 4 products, 9 orders, 11 order items and 19
  events in both PostgreSQL and `fact_*`/`dim_*` tables (one
  `fact_order_items` row per order item, including the cancelled and
  returned ones).
* **Revenue** per month: January 2025 **88.00**, February **80.00**, March
  **208.00**; total **376.00**. (Item 1003 is returned and item 1006 is
  cancelled: neither counts.)
* **Gross margin:** **223.00** in total.
* **Returns** per category: Outerwear & Coats **50%** (1 of 2: the
  cancelled jacket doesn't count); Jeans, Socks and Tops & Tees **0%**.
* **Sources:** Search **176.00**, Organic **140.00**, Email **60.00**;
  Facebook has no revenue (its only order was cancelled).
* **Retention**, per cohort:
  * January 2025: 2 customers (Ana, Bruno); M+1 **50%** (only Ana's
    returned February order), M+2 **100%**.
  * February 2025: 1 customer (Carla); M+1 **100%**.
  * March 2025: 1 customer (Eva); no later months yet.
  * Diogo has no cohort: his only order was cancelled.
* **Funnel:** 7 sessions; **5** with a product view, **4** with a cart, **3**
  with a purchase. Conversion: product → cart **80%**, cart → purchase
  **75%**; sessions → purchase **42.9%**. Session 7 is anonymous and must
  still count.
* **Bench:** each benchmarked report gives the same result on PostgreSQL
  and DuckDB.

Also test:

* `shop load` twice: still 11 order items.
* A fixture copy with a negative `sale_price` loads nothing, with a clear
  message.
* `shop extract --max-gb 0.000001` refuses to run, printing the estimates.
* Any command with a missing or unreachable database fails with a clear
  message, not a traceback.


## Stretch Goals

* RFM segmentation, a classic in marketing analytics. Score every customer
  on three questions:
  * **Recency** — how long since their last order? (Recent is better.)
  * **Frequency** — how many orders have they placed?
  * **Monetary** — how much have they spent in total?

  `NTILE(5) OVER (ORDER BY ...)` splits customers into five equal-sized
  groups for each one, scored 1 (worst) to 5 (best); mind the direction
  for recency, where fewer days is better. A customer scored 5-5-5 is one
  of your best; 1-1-1, probably lost; 1-5-5, a big spender who stopped
  coming, worth an email. Name a handful of segments from the scores
  ("champions", "at risk", "lost", ...), and report how many customers
  and how much revenue each holds.
* Incremental extracts: `shop extract --since-last` fetches only what's new
  since the last extract, and `shop load` appends.
* Partition the extract by month (Hive-style directories, Session 6) and
  show the effect of partition pruning on a report.
* A Marimo notebook report on top of the warehouse, with charts: the
  `record-store` standard, on your own stack.


## Parting Principles

* Same Git and GitHub workflow as always: a branch per "thing", a PR, green
  Actions, merge, clean up.
* Define metrics before computing them, in words, in the README. Most
  "wrong numbers" in real jobs are disagreements about definitions.
* Reconcile at every step. If a count changes between two steps, you want
  to find out from your tool, not from your boss.
* Mind the bill: dry-run before you run, select only the columns you need.
