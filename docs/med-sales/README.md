# 医药销售管理系统（med-sales）

## 📱 移动端 Demo

[![医药销售系统移动端演示视频](https://i0.hdslb.com/bfs/archive/016f6b1605ed0a0f41d2d0ef63496fee8cb18bef.jpg)](https://www.bilibili.com/video/BV1WtnQ6BE7F/)

[![观看移动端演示视频](https://img.shields.io/badge/Bilibili-观看移动端演示视频-00A1D6?logo=bilibili&logoColor=white)](https://www.bilibili.com/video/BV1WtnQ6BE7F/)
[![下载 Android APK](https://img.shields.io/badge/GitHub_Releases-下载_Android_APK-2ea44f?logo=android&logoColor=white)](https://github.com/dfxiang/med-sales/releases/download/26.10.1/medsales-release-unsigned-26.10.26.1.apk)

移动销售工作台现已在 Android 上可用，覆盖经营首页、销售订单、库存查询、GSP 到期预警和个人资料。
演示视频时长 41 秒；APK 支持 Android 8.0（API 26）及以上，服务器地址可在登录页或“我的”中切换。

> 下载文件：`medsales-release-unsigned-26.10.26.1.apk`（[Release 26.10.1](https://github.com/dfxiang/med-sales/releases/tag/26.10.1)）。
> 当前 Release 包未签名，安装时需允许应用安装未知来源；正式分发请使用自己的证书签名。
> 构建与安全说明见 [Android 客户端](android/README.md)。

> 文档镜像同步自 [dfxiang/med-sales@b67336c](https://github.com/dfxiang/med-sales/commit/b67336c)；
> 本目录保留原项目的文档层级，源码与最新版本仍以源仓库为准。

面向**药品、疫苗、医疗器械销售公司**的销售业务管理系统，覆盖客户、商品、采购、销售、库存、退货、
财务收款、报表分析与 GSP 合规的完整业务链路。

后端是 FastAPI（全异步）+ PostgreSQL 17，前端是 Vue 3 + Element Plus；仓库内自带一套可复现的
四年半演示数据生成脚本，并通过 Docker Compose 启动整套服务。

[![License](https://img.shields.io/badge/License-Apache--2.0%20%2B%20Commons%20Clause-3b6ea5.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-async-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Vue](https://img.shields.io/badge/Vue-3-42b883.svg?logo=vuedotjs&logoColor=white)](https://vuejs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-4169E1.svg?logo=postgresql&logoColor=white)](https://www.postgresql.org/)

> **English** — med-sales is a full-stack sales management system for pharmaceutical, vaccine and
> medical-device distributors. The backend is FastAPI (fully async) on PostgreSQL 17, the frontend is
> Vue 3 + Element Plus, and the repository ships a deterministic mock-data generator that produces
> four and a half years of business data. It covers customers, products, purchasing, sales,
> inventory, returns, receivables, reporting and China GSP compliance (first-supply qualification
> review, transaction gating, expiry alerts, batch/expiry tracking).
> Licensed under **Apache-2.0 + Commons Clause**: free to use commercially, but reselling the
> software itself is not allowed — see [LICENSE](LICENSE) and [docs/许可与商用说明.md](docs/许可与商用说明.md).
>
> 📖 [English README](README.en.md)

## 界面

![销售报表](docs/images/sales-report.png)

![销售订单](docs/images/sales-orders.png)

![库存查询](docs/images/inventory-stock.png)

## 功能模块

| 模块 | 说明 |
| --- | --- |
| 认证 | 用户登录（JWT）、系统对接（API Key 换取令牌）、个人资料 / 头像 / 自助改密 |
| 系统管理 | 用户（显示名称 / 电话 / 邮箱 / 头像）、角色、权限、操作日志、管理员重置密码 |
| 组织与员工 | 部门、员工档案 |
| 客户管理 | 客户档案、类型/等级、信用额度、状态 |
| 商品管理 | 商品、分类、生产厂家、价格调整历史 |
| 供应商管理 | 供应商档案、结算账期、合作状态 |
| 仓库管理 | 全国仓库档案、冷链能力 |
| 采购管理 | 采购订单、到货登记（支持部分收货）、采购入库 |
| 销售管理 | 销售订单、自动计价、库存校验、发货出库、取消 |
| 库存管理 | 库存查询（预警状态）、期初建账、全量流水追溯 |
| 退货管理 | 退货单、退货原因、处理入库 |
| 财务收款 | 收款登记、订单核销、应收账龄分析 |
| 报表分析 | 日/月销售、客户/销售员/商品汇总、订单明细、经营看板 |
| GSP 合规 | 首营资质档案（证照审核 + 扫描件归档）、交易准入校验、到期预警中心、批次批号与效期管理 |
| 移动端 | Android 8.0+ WebView 客户端，支持经营首页、销售订单、库存、GSP 预警和个人资料 |

## 技术栈

| 层次 | 选型 |
| --- | --- |
| 后端 | Python 3.12、FastAPI、SQLAlchemy 2.0（全异步）、Pydantic v2、JWT（PBKDF2-SHA256 密码哈希） |
| 前端 | Vue 3、TypeScript、Vite、Element Plus、Pinia、Vue Router 4、Axios、ECharts |
| 数据库 | PostgreSQL 17（asyncpg）；单元测试用内存 SQLite（aiosqlite） |
| 对象存储 | MinIO（S3 兼容），存放 GSP 证照扫描件与头像 |
| 测试 | pytest + httpx（接口）、Playwright（前端 E2E 与运行环境回归） |
| 部署 | Docker / Docker Compose、nginx（静态资源 + `/api` 同源反代） |

## 仓库结构

```
med-sales/
├── docs/                       # 项目文档（接口、数据库、权限、GSP、报表、用户资料…）
│   └── images/                 # README 截图
├── api/                        # 后端（FastAPI，全异步）
│   ├── app/                    # 应用源码（core / models / schemas / api/routes / services）
│   ├── tests/                  # 后端接口测试
│   ├── scripts/                # 初始化管理员、权限清单、接口文档、报表回填脚本
│   ├── Dockerfile              # 后端镜像（python:3.12-slim，非 root）
│   └── docker-compose.yml      # 只起后端的编排
├── frontend/                   # 前端（Vue 3 + TypeScript）
│   ├── src/                    # 页面、组件、路由、状态、请求封装
│   ├── tests/e2e/              # 隔离环境 Playwright 用例（自带后端与种子数据）
│   ├── tests/live/             # 针对运行中部署的界面回归用例
│   ├── Dockerfile              # 多阶段构建：Node 构建 → nginx 托管
│   └── nginx.conf              # 静态资源 + /api 反向代理
├── android/                    # Android 移动销售工作台（WebView + 原生网络桥）
├── db/                         # 演示数据库 medsalesdb 的建库与造数脚本
│   ├── schema.sql              # 18 张业务表 + 7 个视图的 DDL（含中文注释）
│   ├── mock_params.py          # 数据规模 / 区间 / 年度目标等生成参数
│   ├── generate_mock_data.py   # 生成四年半演示数据
│   └── run_all.py              # 建库 → 造数 → 校验 一键执行
├── docker-compose.yml          # 数据库 + 对象存储 + 前后端一体化编排
├── .env.example                # 部署参数模板（端口 / 口令 / 时区），复制为 .env 生效
├── .github/                    # Issue 与 PR 模板
├── AGENTS.md                   # 仓库内部的开发约定（分页、表格、统一选择控件等）
└── LICENSE
```

## 快速开始

```bash
git clone https://github.com/dfxiang/med-sales.git
cd med-sales
```

### 前置要求

- Docker 与 Docker Compose v2；
- 演示数据脚本需要 Python 3.12+（只在造数时用到）。

数据库（PostgreSQL 17）、对象存储（MinIO）都由 compose 自带，不用另外准备；
要求数据库为 **UTF-8 + 中文拼音排序（ICU `zh-u-co-pinyin`）**，详见
[数据库部署与配置](docs/数据库部署与配置.md)。

### 首次启动（Docker Compose）

```bash
# ① 先起数据库（其余服务随后，让数据库就绪后再灌数据）
docker compose up -d medsales-db

# ② 建库 + 生成四年半演示数据 + 校验（约 2 分钟，参数见 db/README.md）
cd db
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python run_all.py
cd ..

# ③ 启动后端 + 前端 + 对象存储（MinIO）
docker compose up -d --build

# ④ 初始化管理员账号（首次启动后执行一次）
docker compose exec medsales-api python scripts/create_admin.py --username admin --password 你的密码

# ⑤ 回填报表预聚合表（造数后必须执行一次，否则报表页全为 0）
docker compose exec medsales-api python scripts/rebuild_sales_rollup.py
```

> 端口、口令、时区都可以用仓库根目录的 `.env` 覆盖（模板见 `.env.example`）：`cp .env.example .env`。
> 例如本机 5688 已被占用时，把 `MEDSALES_DB_PORT` 改成别的端口，造数脚本再用
> `MEDSALESDB_PORT=<同一端口>` 指向它。

启动后：

| 入口 | 地址 |
| --- | --- |
| 前端 Web | http://127.0.0.1:8088 |
| 后端 API | http://127.0.0.1:8001 |
| Swagger 文档 | http://127.0.0.1:8001/docs |
| MinIO 控制台 | http://127.0.0.1:9021 |

### 本地开发（不用容器）

```bash
# 后端
cd api
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env                                          # 按实际数据库连接修改
.venv/bin/python scripts/create_admin.py --username admin --password 你的密码
.venv/bin/python scripts/seed_permissions.py --with-roles      # 可选：内置角色模板
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000

# 前端
cd frontend
npm install
npm run dev                                                   # http://127.0.0.1:5273
```

前端开发环境默认请求 `http://127.0.0.1:8001/api`（见 `frontend/.env.development`）；
容器部署时改为同源 `/api`，由 nginx 反代。

### 配置项

后端配置支持环境变量或 `api/.env`（见 `api/.env.example`），容器部署时由 `docker-compose.yml` 注入。

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `DATABASE_URL` | `postgresql+asyncpg://postgres:pass01!@medsales-db:5432/medsalesdb` | 数据库连接串（接外部库时改这里） |
| `TZ` | `Asia/Shanghai` | 容器时区；经营看板「今日」、应收账龄、证照到期天数都按它计算 |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | `postgres` / `pass01!` / `medsalesdb` | 自带数据库的账号与库名，**生产必须改口令** |
| `POSTGRES_INITDB_ARGS` | `--locale-provider=icu --icu-locale=zh-u-co-pinyin --encoding=UTF8` | 初始化参数，只在数据卷为空时生效，见[数据库部署与配置](docs/数据库部署与配置.md) |
| `MEDSALES_DB_PORT` / `MEDSALES_API_PORT` / `MEDSALES_WEB_PORT` | `5688` / `8001` / `8088` | 宿主机端口映射 |
| `MEDSALES_MINIO_API_PORT` / `MEDSALES_MINIO_CONSOLE_PORT` | `9020` / `9021` | MinIO 的 S3 端口与控制台端口 |
| `JWT_SECRET` | `medsales-change-me-…` | **生产必须修改**，令牌签名密钥 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | 令牌有效期（分钟） |
| `SYS_API_KEYS` | 空 | 系统对接 API Key，逗号分隔，支持新旧并存轮换 |
| `CORS_ORIGINS` | `*` | 允许的跨域来源，生产建议收紧 |
| `DEBUG` | `false` | 调试模式 |
| `S3_ENDPOINT_URL` / `S3_ACCESS_KEY` / `S3_SECRET_KEY` / `S3_BUCKET` / `S3_REGION` | 指向自带 MinIO | 证照扫描件与头像存储 |
| `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` | `medsales` / `medsales-minio-secret` | 对象存储凭据，**生产必须修改** |
| `GSP_ENFORCE_QUALIFICATION` | `true` | 已建档主体的证照过期/待审核/驳回时禁止交易 |
| `GSP_STRICT_QUALIFICATION` | `false` | 严格模式：未建档主体同样禁止交易 |
| `GSP_EXPIRY_WARNING_DAYS` | `90` | 证照到期预警阈值（天） |

> 安全清单（改默认凭据、收紧 CORS、HTTPS、备份）见 [SECURITY.md](SECURITY.md)。

## 数据库与演示数据

数据库要求 **PostgreSQL 17**、字符集 `UTF8`、排序规则用 ICU 的 `zh-u-co-pinyin`（中文按拼音排序）。
容器化 / 本机安装、字符集与中文排序规则配置、接入已有实例、备份与常见问题，见
[数据库部署与配置](docs/数据库部署与配置.md)。

数据库中原有 18 张业务表与 7 个报表视图，项目在保留原表结构的基础上补齐了用户权限、批次效期、
证照管理等系统表（API 启动时自动补齐，不改动存量表）。

- 18 张业务表：客户、商品、供应商、仓库、采购、销售、库存、退货、收款等；
- 7 个报表视图：日/月销售、客户/销售员/商品汇总、订单明细、库存状态；
- 演示数据：4 年半（2022-01-01 ~ 2026-07-31）经营数据，单据流水约 490 万条，
  由 [db/](db/README.md) 下的脚本按固定随机种子生成，可复现、可调参。

```bash
cd db
.venv/bin/python run_all.py            # 数据库不存在时创建并初始化
.venv/bin/python run_all.py --reset    # 删除已有 medsalesdb 后重建
```

报表走预聚合汇总表（见 [docs/销售报表汇总表.md](docs/销售报表汇总表.md)），造数脚本直接写明细表，
因此生成数据后要回填一次汇总表：
`docker compose exec medsales-api python scripts/rebuild_sales_rollup.py`。

## 测试

```bash
# 后端接口测试（使用内存 SQLite，无需真实数据库）
cd api && .venv/bin/python -m pytest -q

# 前端构建
cd frontend && npm run build

# 前端 E2E（自动拉起隔离的后端 8002 与前端 5273）
cd frontend && npx playwright test

# 针对运行中部署的界面回归（需要 8088 / 8001 已在运行）
cd frontend && npx playwright test --config playwright.live.config.ts
```

## 文档

| 文档 | 说明 |
| --- | --- |
| [API接口文档](docs/API接口文档.md) | 由 OpenAPI 自动生成的中文接口规范，含参数与示例 |
| [数据库部署与配置](docs/数据库部署与配置.md) | PostgreSQL 17 的容器化/本机安装、UTF-8 与中文拼音排序、时区、备份恢复 |
| [GSP 合规闭环](docs/GSP合规闭环.md) | 首营资质建档/审核、交易准入、到期预警、换证归档 |
| [权限控制说明](docs/权限控制说明.md) | 权限模型、编码约定、内置约束与扩展方式 |
| [销售报表汇总表](docs/销售报表汇总表.md) | 报表预聚合表结构、维护时序、回填与对账 |
| [用户资料与头像](docs/用户资料扩展设计.md) | 显示名称、联系方式、自助改密、管理员重置密码与头像安全边界 |
| [许可与商用说明](docs/许可与商用说明.md) | 干什么可以、干什么需要授权（中文解释） |
| [Android 客户端](android/README.md) | APK 下载、移动端功能、构建、服务器地址与安全边界 |
| [演示数据库初始化](db/README.md) | 建库/造数脚本、连接参数、数据规模 |
| [后端说明](api/README.md) | 后端部署、配置、测试、容器化 |
| [前端说明](frontend/README.md) | 前端技术栈、页面实现、测试与部署方式 |

## 参与贡献

欢迎提 Issue 与 PR，环境要求、改动流程与代码约定见 [CONTRIBUTING.md](CONTRIBUTING.md)；
安全问题请走 [SECURITY.md](SECURITY.md) 中的私下渠道。

## 许可证与商用

本项目采用 **Apache License 2.0 + Commons Clause 条件 v1.0**（完整条款见 [LICENSE](LICENSE)）。

| 你可以 | 你不可以 |
| --- | --- |
| 商用：部署到自己的业务中、按需修改与二次开发（改动可闭源） | 把本软件（或其实质功能）打包成产品/服务向第三方收费 |
| 复制、免费再分发（需保留版权与许可声明） | 用它对外提供收费托管（SaaS）、收费咨询与技术支持 |
| 学习研究、内部教学 | 移除或篡改版权与许可声明 |

> 说明：由于带有「禁止售卖」条件，本项目属于 **source-available（源码可见）**，不是 OSI 认证的
> 开源许可（GitHub 会显示为 Other）；完整解释见 [docs/许可与商用说明.md](docs/许可与商用说明.md)。

商业授权、定制开发与技术支持（版权所有者可另行授权）：`4198166@qq.com` · 微信 `4198166` · 电话 `+86 185 7281 7101`。

## 免责声明

- 仓库中的企业与业务数据（含「华康医药销售有限公司」等主体、客户、价格、单据）**全部为脚本
  生成的虚构数据**，与任何真实企业无关，请勿用于任何实际业务判断。
- 本项目是通用的销售业务管理软件，不是药品/医疗器械本身，也不提供任何医疗或用药建议。
- GSP 相关功能只是帮助梳理合规流程的辅助工具，**不构成合规承诺**；实际经营须遵守当地法规，
  并由质量负责人与专业人员把关。
- 软件按「原样」提供，不附带任何明示或默示担保；生产环境上线前请自行完成安全评估与数据备份。

## 交个朋友 / 支持项目

如果这个项目对你有帮助，欢迎请我喝杯咖啡；也欢迎加微信交个朋友，聊聊业务、产品和技术。
支持完全自愿，不影响任何使用权益。

<table>
  <tr>
    <td align="center">
      <img src="weixin.jpg" alt="作者个人微信二维码" width="260"><br>
      <sub>扫码加微信，交个朋友</sub>
    </td>
    <td align="center">
      <img src="donation.jpg" alt="项目捐赠二维码" width="260"><br>
      <sub>请我喝杯咖啡，支持项目持续维护</sub>
    </td>
  </tr>
</table>
