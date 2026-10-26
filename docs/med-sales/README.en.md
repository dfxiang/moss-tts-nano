# med-sales — Pharmaceutical Sales Management System

## 📱 Mobile Demo

[![Med-sales mobile demo](https://i0.hdslb.com/bfs/archive/016f6b1605ed0a0f41d2d0ef63496fee8cb18bef.jpg)](https://www.bilibili.com/video/BV1WtnQ6BE7F/)

[![Watch the mobile demo](https://img.shields.io/badge/Bilibili-Watch_the_mobile_demo-00A1D6?logo=bilibili&logoColor=white)](https://www.bilibili.com/video/BV1WtnQ6BE7F/)
[![Download the Android APK](https://img.shields.io/badge/GitHub_Releases-Download_Android_APK-2ea44f?logo=android&logoColor=white)](https://github.com/dfxiang/med-sales/releases/download/26.10.1/medsales-release-unsigned-26.10.26.1.apk)

The mobile sales workspace is available on Android. It includes the operations dashboard, sales orders,
inventory lookup, GSP expiry alerts and profile settings. The demo is 41 seconds long; the APK supports
Android 8.0 (API 26) and later, with a configurable API server address.

> Download: `medsales-release-unsigned-26.10.26.1.apk`
> ([Release 26.10.1](https://github.com/dfxiang/med-sales/releases/tag/26.10.1)). This release is
> unsigned, so Android requires permission to install apps from an unknown source. Sign it with your own
> certificate for production distribution. See [Android client](android/README.md) for build and security notes.

A sales management system for **pharmaceutical, vaccine and medical-device distributors**, covering
the whole business chain: customers, products, purchasing, sales, inventory, returns, receivables,
reporting and China GSP compliance.

Backend: FastAPI (fully async) on PostgreSQL 17. Frontend: Vue 3 + Element Plus. The repository ships
a deterministic mock-data generator that produces four and a half years of business data, plus a
Docker Compose setup for the complete stack.

[![License](https://img.shields.io/badge/License-Apache--2.0%20%2B%20Commons%20Clause-3b6ea5.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-async-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Vue](https://img.shields.io/badge/Vue-3-42b883.svg?logo=vuedotjs&logoColor=white)](https://vuejs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-4169E1.svg?logo=postgresql&logoColor=white)](https://www.postgresql.org/)

> 中文文档见 [README.md](README.md)。

## Screenshots

![Sales report](docs/images/sales-report.png)

![Sales orders](docs/images/sales-orders.png)

![Inventory](docs/images/inventory-stock.png)

## Features

| Module | Description |
| --- | --- |
| Authentication | JWT login, API-key token exchange for system integration, self-service profile / avatar / password |
| System admin | Users (display name, phone, email, avatar), roles, permissions, audit log, admin password reset |
| Organization | Departments, employee records |
| Customers | Customer master data, type/level, credit limit, status |
| Products | Products, categories, manufacturers, price-adjustment history |
| Suppliers | Supplier master data, payment terms, cooperation status |
| Warehouses | Nationwide warehouse records, cold-chain capability |
| Purchasing | Purchase orders, goods receipt (partial receipt supported), stock-in |
| Sales | Sales orders, automatic pricing, stock validation, shipment, cancellation |
| Inventory | Stock query with alert status, opening balances, full movement traceability |
| Returns | Return orders, return reasons, stock-in handling |
| Receivables | Payment registration, order reconciliation, aging analysis |
| Reporting | Daily/monthly sales, customer/salesperson/product summaries, order details, dashboard |
| GSP compliance | First-supply qualification files (certificate review + scanned attachments), transaction gating, expiry alert center, batch/expiry tracking |
| Mobile | Android 8.0+ WebView client with dashboard, sales orders, inventory, GSP alerts and profile |

## Tech stack

| Layer | Choice |
| --- | --- |
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Pydantic v2, JWT (PBKDF2-SHA256 password hashing) |
| Frontend | Vue 3, TypeScript, Vite, Element Plus, Pinia, Vue Router 4, Axios, ECharts |
| Database | PostgreSQL 17 (asyncpg); in-memory SQLite (aiosqlite) for unit tests |
| Object storage | MinIO (S3-compatible) for GSP certificates and avatars |
| Testing | pytest + httpx (API), Playwright (E2E and live-environment regression) |
| Deployment | Docker / Docker Compose, nginx (static assets + same-origin `/api` proxy) |

## Repository layout

```
med-sales/
├── docs/                       # API, database, permissions, GSP, reporting and user-profile docs
│   └── images/                 # screenshots used by the READMEs
├── api/                        # backend (FastAPI, fully async)
│   ├── app/                    # application code (core / models / schemas / api/routes / services)
│   ├── tests/                  # Backend API tests
│   ├── scripts/                # admin bootstrap, permission catalog, API docs, report rollup
│   ├── Dockerfile              # backend image (python:3.12-slim, non-root)
│   └── docker-compose.yml      # backend-only compose (reuses the root stack's network + database)
├── frontend/                   # frontend (Vue 3 + TypeScript)
│   ├── src/                    # pages, components, router, stores, request layer
│   ├── tests/e2e/              # isolated Playwright suite (own backend + seed data)
│   ├── tests/live/             # regression suite for a running deployment
│   ├── Dockerfile              # multi-stage build: Node build → nginx
│   └── nginx.conf              # static assets + /api reverse proxy
├── android/                    # Android mobile workspace (WebView + native network bridge)
├── db/                         # database initialization and mock-data generation
│   ├── schema.sql              # DDL for 18 business tables + 7 views (Chinese comments)
│   ├── mock_params.py          # data volume / date range / yearly targets
│   ├── generate_mock_data.py   # generates four and a half years of demo data
│   └── run_all.py              # create → generate → verify
├── docker-compose.yml          # database + object storage + backend + frontend
├── .env.example                # deployment template (ports / passwords / time zone)
├── .github/                    # issue forms and PR template
├── AGENTS.md                   # in-repo development conventions (pagination, tables, shared selects…)
└── LICENSE
```

## Quick start

```bash
git clone https://github.com/dfxiang/med-sales.git
cd med-sales
```

### Prerequisites

- Docker and Docker Compose v2;
- Python 3.12+ only if you want to generate the demo data.

PostgreSQL 17 and MinIO are bundled in `docker-compose.yml`. The database must use **UTF-8 with the
ICU `zh-u-co-pinyin` collation** (Chinese sorted by pinyin) — see
[docs/数据库部署与配置.md](docs/数据库部署与配置.md) (Chinese) for containerized and native installs.

### Initial startup

```bash
# 1. Start the database first (the rest of the stack comes later)
docker compose up -d medsales-db

# 2. Create the schema, generate 4.5 years of demo data and verify it (~2 minutes)
cd db
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python run_all.py
cd ..

# 3. Start backend + frontend + object storage
docker compose up -d --build

# 4. Create the initial admin account (once, after the first start)
docker compose exec medsales-api python scripts/create_admin.py --username admin --password YOUR_PASSWORD

# 5. Backfill the report rollup tables (otherwise reports show 0)
docker compose exec medsales-api python scripts/rebuild_sales_rollup.py
```

Ports, passwords and the time zone are configurable through a `.env` file in the repository root
(`cp .env.example .env`). If host port 5688 is taken, change `MEDSALES_DB_PORT` and point the data
scripts at the same port with `MEDSALESDB_PORT=<port>`.

| Entry point | URL |
| --- | --- |
| Web UI | http://127.0.0.1:8088 |
| API | http://127.0.0.1:8001 |
| Swagger | http://127.0.0.1:8001/docs |
| MinIO console | http://127.0.0.1:9021 |

### Local development (without Docker)

```bash
# Backend
cd api
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env                                          # adjust the database connection
.venv/bin/python scripts/create_admin.py --username admin --password YOUR_PASSWORD
.venv/bin/python scripts/seed_permissions.py --with-roles     # optional: built-in role templates
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm install
npm run dev                                                   # http://127.0.0.1:5273
```

The dev server calls `http://127.0.0.1:8001/api` (see `frontend/.env.development`); in containers it
uses the same-origin `/api` proxied by nginx.

### Configuration

Backend settings come from environment variables or `api/.env` (see `api/.env.example`); in
containers they are injected by `docker-compose.yml`. The most important ones:

| Variable | Default | Description |
| --- | --- | --- |
| `DATABASE_URL` | `postgresql+asyncpg://postgres:pass01!@medsales-db:5432/medsalesdb` | Database connection string (change for external databases) |
| `TZ` | `Asia/Shanghai` | Container time zone; "today" metrics, receivables aging and certificate expiry are computed in it |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | `postgres` / `pass01!` / `medsalesdb` | Bundled database credentials (**change in production**) |
| `POSTGRES_INITDB_ARGS` | ICU `zh-u-co-pinyin` + UTF8 | Applied only when the data volume is empty |
| `MEDSALES_DB_PORT` / `MEDSALES_API_PORT` / `MEDSALES_WEB_PORT` | `5688` / `8001` / `8088` | Host port mappings |
| `JWT_SECRET` | `medsales-change-me-…` | **Must be changed in production** |
| `SYS_API_KEYS` | empty | API keys for system integration (comma separated, supports rotation) |
| `CORS_ORIGINS` | `*` | Allowed origins; tighten in production |
| `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` | `medsales` / `medsales-minio-secret` | Object storage credentials (**change in production**) |
| `GSP_ENFORCE_QUALIFICATION` | `true` | Block transactions when a registered entity has expired/pending/rejected certificates |
| `GSP_STRICT_QUALIFICATION` | `false` | Strict mode: also block entities without any qualification file |
| `GSP_EXPIRY_WARNING_DAYS` | `90` | Certificate expiry warning threshold (days) |

> Deployment security checklist: [SECURITY.md](SECURITY.md) (Chinese).

## Database and demo data

Requirements: **PostgreSQL 17**, encoding `UTF8`, collation ICU `zh-u-co-pinyin` — see
[docs/数据库部署与配置.md](docs/数据库部署与配置.md) (Chinese) for containerized and native
installation, collation and time zone configuration, connecting an existing database, and
backup/restore.

The original database holds 18 business tables and 7 reporting views; the project adds system tables
for users/permissions, batches and certificates (created automatically on API startup, existing
tables untouched).

```bash
cd db
.venv/bin/python run_all.py            # create the database and initialize it if missing
.venv/bin/python run_all.py --reset    # drop and rebuild
```

Reports read pre-aggregated rollup tables, so after generating data you must backfill them once:
`docker compose exec medsales-api python scripts/rebuild_sales_rollup.py`.

## Tests

```bash
# Backend (in-memory SQLite, no real database needed)
cd api && .venv/bin/python -m pytest -q

# Frontend build
cd frontend && npm run build

# Frontend E2E (starts an isolated backend on 8002 and a dev server on 5273)
cd frontend && npx playwright test

# Regression against a running deployment (requires 8088/8001 to be up)
cd frontend && npx playwright test --config playwright.live.config.ts
```

## Documentation

All documents are currently written in Chinese:

| Document | Content |
| --- | --- |
| [docs/API接口文档.md](docs/API接口文档.md) | Generated Chinese API reference with parameters and examples |
| [docs/数据库部署与配置.md](docs/数据库部署与配置.md) | PostgreSQL 17 deployment, UTF-8 + Chinese pinyin collation, time zone, backup/restore |
| [docs/GSP合规闭环.md](docs/GSP合规闭环.md) | GSP workflow: qualification review, transaction gating, expiry alerts, renewal archiving |
| [docs/权限控制说明.md](docs/权限控制说明.md) | Permission model, code conventions, extension guide |
| [docs/销售报表汇总表.md](docs/销售报表汇总表.md) | Rollup tables, maintenance sequence, backfill and reconciliation |
| [docs/用户资料扩展设计.md](docs/用户资料扩展设计.md) | Profile fields, password self-service, admin reset and avatar security |
| [docs/许可与商用说明.md](docs/许可与商用说明.md) | What is allowed and what needs a commercial license (Chinese) |
| [db/README.md](db/README.md) | Demo database scripts, connection parameters, data volume |
| [api/README.md](api/README.md) · [frontend/README.md](frontend/README.md) | Per-side technical details |

## Contributing

Issues and pull requests are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) (Chinese) for the
environment, workflow and code conventions. Please report security issues privately as described in
[SECURITY.md](SECURITY.md).

## License and commercial use

Licensed under the **Apache License 2.0 with the Commons Clause condition v1.0** — full text in
[LICENSE](LICENSE).

| You may | You may not |
| --- | --- |
| Use it commercially (run it for your own business), modify it and build on top of it (your changes may stay closed) | Package the software (or substantially its functionality) into a product or service and charge third parties for it |
| Copy and redistribute it free of charge (keeping copyright and license notices) | Offer it as a paid hosted service (SaaS), paid consulting or paid support |
| Study and teach with it | Remove or alter the copyright and license notices |

> Note: because of the "no selling" condition this project is **source-available, not OSI open
> source** (GitHub reports the license as "Other") — full explanation in
> [docs/许可与商用说明.md](docs/许可与商用说明.md).

Commercial licensing, custom development and support (the copyright holder may grant separate terms):
`4198166@qq.com` · WeChat `4198166` · phone `+86 185 7281 7101`.

## Disclaimer

- All companies and business data in this repository (including the fictional 华康医药销售有限公司,
  its customers, prices and documents) are **generated by scripts** and unrelated to any real
  organization. Do not use them for any real business decision.
- This is general-purpose sales management software: it is not a medical device, and it provides no
  medical or prescribing advice.
- The GSP features are auxiliary tooling that helps structure a compliance process; they are **not a
  guarantee of compliance**. Real operations must follow local regulations and be reviewed by the
  responsible quality staff.
- The software is provided "as is", without warranties of any kind. Run your own security review and
  keep backups before using it in production.
