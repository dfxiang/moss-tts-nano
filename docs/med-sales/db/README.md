# medsalesdb 演示数据库初始化

本目录用于初始化本项目使用的演示数据库 `medsalesdb`：在 PostgreSQL 容器
`medsales-db`（宿主机端口 5688）中建库，执行 `schema.sql` 建表/建视图/写注释，
再灌入 2022-01-01 ~ 2026-07-31（约四年半）符合业务逻辑的 mock 数据，
最后做一次结构与指标校验。

后端（`api/`）与前端（`frontend/`）直接使用这套数据；数据库里除 `schema.sql`
定义的 18 张业务表和 7 个报表视图外，用户/角色/权限/批次/证照等系统表由 API
服务启动时自动补齐。

## 公司背景（模拟对象）

- 公司：华康医药销售有限公司（大型医药流通企业，经营疫苗、药品、医疗器械）
- 规模：约 500 名员工（九大区域销售部 + 总部职能）
- 业绩：完整年度销售额约 **500 亿元/年**，销售毛利约 **80 亿元/年**
- 客户：三级/二级医院、疾控中心、连锁药房、诊所、经销商等约 1650 家机构

## 数据库容器

推荐直接用仓库根目录 compose 自带的数据库（UTF-8 与中文拼音排序都已配好）：

```bash
docker compose up -d medsales-db        # 在仓库根目录执行
```

它监听宿主机 `5688`（可用根目录 `.env` 里的 `MEDSALES_DB_PORT` 改），账号口令见下方「连接信息」。
不想用容器时，按下表或 [数据库部署与配置](../docs/数据库部署与配置.md) 自己装一个 PostgreSQL 17
（要求 UTF-8 + 中文拼音排序），再用 `MEDSALESDB_*` 或 `DATABASE_URL` 把脚本指过去。

> 若 5688 已被别的实例占用，把 `MEDSALES_DB_PORT` 改成其它端口，并让脚本指向同一端口：
> `MEDSALESDB_PORT=5699 .venv/bin/python run_all.py`。

## 连接信息

| 项目 | 值 |
| --- | --- |
| 主机 | 127.0.0.1 |
| 端口 | 5688 |
| 用户 | postgres |
| 密码 | pass01! |
| 数据库 | medsalesdb |

参数解析优先级（详见 `db_config.py`）：

1. `MEDSALESDB_HOST` / `MEDSALESDB_PORT` / `MEDSALESDB_USER` /
   `MEDSALESDB_PASSWORD` / `MEDSALESDB_NAME`（另有 `MEDSALESDB_ADMIN_DB`）；
2. 项目统一变量 `DATABASE_URL`，与 `api/.env`、根目录 `docker-compose.yml` 同一套值，
   例如 `postgresql+asyncpg://postgres:pass01!@127.0.0.1:5688/medsalesdb`；
3. 内置默认值（即上表）。

在 Docker 网络内（如容器里）执行时，把主机换成容器名即可：

```bash
MEDSALESDB_HOST=medsales-db MEDSALESDB_PORT=5432 python run_all.py
```

## 运行方式

依赖只有 `psycopg`，可复用任意已装好该依赖的 Python 环境，也可以单独建虚拟环境：

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python run_all.py
```

```bash
.venv/bin/python run_all.py            # 数据库不存在时创建并初始化
.venv/bin/python run_all.py --reset    # 删除后重建（会清空演示数据）
```

也可分步执行：

```bash
.venv/bin/python create_database.py     # 创建 medsalesdb + 执行 schema.sql
.venv/bin/python generate_mock_data.py  # 生成四年半 mock 数据
.venv/bin/python verify_database.py     # 校验结构与指标
```

> `--reset` 会先 `DROP DATABASE medsalesdb`。重建后 APIs 新增的系统表会在
> `docker compose up -d --build medsales-api` 启动时自动补建，管理员账号需重新执行
> `api/scripts/create_admin.py --username admin --password admin123`（或容器内对应命令）。

## 脚本与文件说明

| 文件 | 说明 |
| --- | --- |
| `db_config.py` | 连接配置（环境变量 / `DATABASE_URL` 可覆盖） |
| `mock_params.py` | 生成参数：种子、数据区间、年度销售目标、分类占比与毛利率、季节系数等 |
| `schema.sql` | 数据库 DDL：18 张表、7 个视图、索引、表/视图/列中文注释 |
| `create_database.py` | 创建 medsalesdb 数据库并执行 schema.sql |
| `generate_mock_data.py` | 按 `mock_params.py` 生成指定区间的 mock 数据并写入 |
| `verify_database.py` | 校验对象、数据规模、年度销售/毛利指标与库存一致性 |
| `run_all.py` | 一键顺序执行以上三步 |
| `requirements.txt` | 运行依赖（`psycopg[binary]`） |

## 可调参数

集中放在 `mock_params.py`（生成与校验共用，改一处即两边一致）：

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `SEED` | `20260829` | 随机种子，固定种子可复现 |
| `START_DATE` / `END_DATE` | `2022-01-01` / `2026-07-31` | 数据区间 |
| `YEAR_TARGET` | 490 / 500 / 506 / 512 / 527 亿 | **年化**销售目标（元/年），实际区间按覆盖天数折算 |
| `CATEGORY_SHARE` | 见文件 | 7 大类销售占比（合计 1.0） |
| `CATEGORY_MARGIN` | 见文件 | 7 大类毛利率，综合约 17% |
| `MONTH_WEIGHT` / `DOW_WEIGHT` | 见文件 | 月度季节系数、星期系数 |
| `MAX_LINES` | `18` | 单张销售订单最多明细行数 |
| `EMPLOYEE_COUNT` / `CUSTOMER_COUNT` | `500` / `1650` | 规模目标，生成时会与部门/客户计划表核对 |

也可以不改文件，用命令行覆盖（`run_all.py` 会把参数透传给各步骤）：

```bash
python run_all.py --reset --seed 20260101
python run_all.py --reset --start-date 2023-01-01 --end-date 2025-12-31
python verify_database.py --start-date 2023-01-01 --end-date 2025-12-31
```

## 数据模型概览

**基础档案（9 张）**：商品分类、生产厂家、供应商、仓库（含冷链属性）、
部门、员工、客户、商品（含批准文号/储存条件/效期）、价格调整历史。

**业务单据（7 张）**：销售订单（含开票/结算/配送方式）、销售订单明细、
付款记录、销售退货、销售退货明细、采购订单（含冷链运输）、采购订单明细。

**库存（2 张）**：库存表、库存流水表。合计 18 张表。

**视图（7 个）**：

| 视图 | 用途 |
| --- | --- |
| `v_order_detail` | 订单 + 客户 + 销售员 + 仓库 + 商品全维度明细 |
| `v_sales_daily` | 每日销售汇总（订单数、销量、销售额、毛利） |
| `v_sales_monthly` | 月度销售汇总（含环比增速） |
| `v_product_sales_summary` | 商品销量、销售额、毛利排行 |
| `v_customer_sales_summary` | 客户订单数、销售额、最近下单 |
| `v_employee_sales_summary` | 销售员业绩统计 |
| `v_inventory_status` | 库存与安全库存、库存状态、库存价值 |

全部表、视图、索引均带中文注释；索引覆盖订单日期/客户/销售员/状态、
明细关联键、付款、退货、采购、库存流水等常用查询路径。

## 业务与 mock 数据逻辑

- **商品结构**：365 个商品，覆盖 7 大类——疫苗（24）、化学药品（130）、
  生物制品（18）、中成药（34）、高值耗材（73）、低值耗材（54）、
  医疗设备（32），单价从 0.35 元（注射器）到 1280 万元（磁共振）；
  疫苗、生物制品、胰岛素等标记 2~8℃ 冷链并自动冷链配送。
- **销售目标**：完整年度销售额 490~512 亿元（约 500 亿元/年），
  按年度、分类双重缩放对齐目标；综合毛利率约 17%，对应毛利约 80 亿元/年。
- **客户行为**：1650 家机构按类型差异化下单（医院采购高值耗材与设备、
  CDC 采购疫苗、连锁药房采购药品与中成药、经销商综合采购），
  并按客户规模/合作等级决定订单频次与金额。
- **季节波动**：流感季（9~12 月）疫苗与抗病毒药放量、春节低谷、
  周末订单减少、月末医院集中采购。
- **价格与回款**：药品/耗材挂网价随集采逐年小幅下调，成本同步联动，
  保证毛利稳定；医院/CDC/经销商按账期回款（月结 30~90 天），
  期末保留应收账款；药房/诊所现款结算。
- **采购与库存**：按“库存不低于安全库存”模拟补货，收货量、期初库存与
  期末库存经库存流水闭环校验；冷链商品走冷链采购与配送。
- **退货**：约 2.5% 订单发生质量/效期/滞销退货，已完成退货回补库存。

## 数据规模

| 指标 | 数量 |
| --- | --- |
| 员工 | 500 |
| 客户 | 1,650 |
| 商品 | 365 |
| 销售订单 | 212,585（有效 201,885） |
| 订单明细 | 1,621,651 |
| 付款记录 | 196,687 |
| 销售退货 | 5,040 |
| 采购订单/明细 | 217,525 / 317,832 |
| 库存记录/流水 | 3,204 / 1,860,461 |

（以上为默认种子 `20260829`、默认区间一次生成的实际结果；`verify_database.py`
会输出当前库的真实行数。运行中的演示库会被接口测试/E2E 用例改动，行数略有出入属正常。）
