# medsales API（医药销售管理系统后端）

基于 **FastAPI + SQLAlchemy 2.0（全异步）** 的医药销售管理系统 API，覆盖进销存、销售、财务、报表、GSP 合规等全部功能模块，所有接口均配 pytest 测试脚本。

## 功能模块

| 模块 | 说明 |
| --- | --- |
| 认证 | 登录（JWT）、当前用户、个人资料、头像与自助改密 |
| 系统管理 | 用户、角色、权限、操作日志 |
| 组织与员工 | 部门、员工档案 |
| 客户管理 | 客户档案 CRUD、信用额度、状态 |
| 商品管理 | 商品、分类、厂家、价格调整历史 |
| 供应商管理 | 供应商档案、账期 |
| 仓库管理 | 仓库档案、冷链属性 |
| 采购管理 | 采购单 CRUD、收货（支持部分收货）、采购入库 |
| 销售管理 | 销售单 CRUD、自动计价、发货出库、取消 |
| 库存管理 | 库存查询（含预警状态）、期初建账、库存流水 |
| 退货管理 | 退货单 CRUD、退货处理入库 |
| 财务收款 | 收款登记、订单核销、应收账龄 |
| 报表分析 | 日/月销售、客户/销售员/商品汇总、订单明细、库存状态、经营看板 |
| GSP 合规 | 首营资质档案（证照审核 + 扫描件归档）、交易准入校验、到期预警中心、批次批号与效期管理 |

## 接口文档

完整的中文接口文档（含通用约定、参数表、请求/响应示例）见：

**《[API接口文档](../docs/API接口文档.md)》**

接口文档由脚本自动生成，接口有变动时重新生成即可：

```bash
.venv/bin/python scripts/gen_api_docs.py
```

同时可访问运行中的 Swagger 在线文档：http://127.0.0.1:8001/docs

## 目录结构

```
api/
├── Dockerfile            # 容器镜像构建
├── docker-compose.yml    # 只起后端（复用根目录 compose 的网络与数据库）
├── .dockerignore
├── app/
│   ├── main.py            # FastAPI 应用入口
│   ├── core/              # 配置、异步数据库、安全（密码哈希/JWT）、权限目录（permissions.py）
│   ├── models/            # SQLAlchemy ORM 模型（现有 18 表 + 系统管理补充表）
│   ├── schemas/           # Pydantic 请求/响应模型
│   └── api/
│       ├── deps.py        # 认证 / 权限校验（require_permission）/ 分页依赖
│       ├── crud.py        # 通用 CRUD 辅助
│       └── routes/        # 各模块路由
├── tests/                 # 每个模块的接口测试
├── scripts/
│   ├── create_admin.py    # 初始化管理员账号
│   └── seed_permissions.py # 同步权限清单（可选创建角色模板）
├── requirements.txt
└── pytest.ini
```

## 快速开始

### 1. 安装依赖

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### 2. 配置环境

```bash
cp .env.example .env
```

默认连接 `postgresql+asyncpg://postgres:pass01!@127.0.0.1:5688/medsalesdb`（本地演示环境的默认值：
根目录 compose 自带的 PostgreSQL 容器 `medsales-db`），按实际修改 `.env`。

> 还没有 `medsalesdb`（或需要重建演示数据）时，用仓库根目录
> [`db/`](../db/README.md) 下的脚本一键建库 + 造数 + 校验：
> `cd ../db && python run_all.py`（约 2 分钟，默认生成四年半数据）。

### 3. 启动服务

```bash
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```

- 接口文档（Swagger）：http://127.0.0.1:8000/docs
- 健康检查：http://127.0.0.1:8000/

启动时会自动补齐新增的系统表（用户/角色/权限/日志/证照/批次），不修改现有 18 张业务表；
存量库上缺失的增量列（如证照的审核字段、附件的版本字段）也会在启动时自动补建。

### GSP 合规相关配置

| 环境变量 | 默认值 | 说明 |
| --- | --- | --- |
| `GSP_ENFORCE_QUALIFICATION` | `true` | 交易准入校验开关。开启后，**已建立资质档案**（录入过证照）的客户/供应商/商品在下单/发货/收货前会被校验；存在过期、待审核或已驳回的证照即拒绝交易 |
| `GSP_STRICT_QUALIFICATION` | `false` | 严格模式。开启后，完全未建档的主体同样禁止交易（存量数据默认不启用，便于逐步推行首营建档） |
| `GSP_EXPIRY_WARNING_DAYS` | `90` | 证照「即将到期」阈值（天），同时用于预警中心的分级窗口 |
| `S3_ENDPOINT_URL` / `S3_ACCESS_KEY` / `S3_SECRET_KEY` / `S3_BUCKET` / `S3_REGION` | 见 `.env.example` | MinIO / S3 兼容对象存储，用于证照扫描件归档 |

### 4. 初始化管理员账号

```bash
.venv/bin/python scripts/create_admin.py --username admin --password admin123
```

### 4.1 权限初始化

所有业务接口都做**权限校验**（无权限返回 403）：账号需经角色继承到对应权限编码。
权限清单由启动时自动幂等补齐，不需要手工建权限：

```bash
# 同步内置权限清单；--with-roles 顺带创建角色模板（销售员/采购员/仓管员/财务/质量管理）
.venv/bin/python scripts/seed_permissions.py --with-roles

# 容器内
docker compose exec medsales-api python scripts/seed_permissions.py --with-roles
```

编码约定、内置约束（`all` 通配、最后一个管理员保护等）与前端联动方式见
**《[权限控制说明](../docs/权限控制说明.md)》**。接口清单中的「所需权限」列由
`scripts/gen_api_docs.py` 从路由依赖自动生成。

登录获取令牌：

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

调用其他接口时携带请求头 `Authorization: Bearer <token>`。

### 系统对接：通过 API Key 获取令牌（get token）

供系统间集成使用：配置好 API Key 后，用 **API Key + 用户 ID** 即可换取和登录完全相同的 JWT，无需用户名密码。

**1. 配置 API Key（环境变量）**

在启动/构建容器时通过环境变量 `SYS_API_KEYS` 指定，例如：

```bash
SYS_API_KEYS=mk-your-secret-key-here docker compose up -d
```

支持逗号分隔配置多个 key（轮换期间新旧 key 可并存）：

```bash
SYS_API_KEYS=old-key,new-key
```

未配置时调用该接口会返回 401（提示未配置）。

**2. 调用 get token 接口**

```bash
curl -X POST http://127.0.0.1:8001/api/auth/token \
  -H "Content-Type: application/json" \
  -d '{"api_key":"mk-your-secret-key-here","user_id":1}'
```

返回 `{"access_token":"...","token_type":"bearer"}`，后续请求同样携带 `Authorization: Bearer <token>` 即可。

**3. 轮换流程**：先同时配置新旧两个 key → 下游系统切换到新 key → 移除旧 key 重新启动容器。

## 容器化部署（Docker）

镜像已封装好（python:3.12-slim + uvicorn，非 root 运行，带健康检查），可直接构建并运行：

### 方式一：Docker Compose（推荐）

```bash
docker compose up -d --build
```

`docker-compose.yml` 复用仓库根目录 compose 创建的网络 `medsales` 与数据库容器 `medsales-db`
（因此需要先在根目录执行过一次 `docker compose up -d`），数据库地址直接使用容器名
`medsales-db:5432`，无需端口映射。启动后：

- 接口文档：http://127.0.0.1:8001/docs
- 健康检查：http://127.0.0.1:8001/

> 容器映射为宿主机 8001（容器内仍是 8000），端口冲突时可自行修改映射。

> 该编排只包含后端服务，**不含对象存储**：GSP 证照扫描件与头像需要额外的 S3/MinIO
> （根目录的 `docker-compose.yml` 已自带一套专用 MinIO，或用 `S3_*` 环境变量指向你自己的实例）。

查看日志 / 停止：

```bash
docker compose logs -f medsales-api
docker compose down
```

### 方式二：单独构建并运行

```bash
docker build -t medsales-api:latest .
docker run -d --name medsales-api \
  --network medsales \
  -p 8001:8000 \
  -e DATABASE_URL=postgresql+asyncpg://postgres:pass01!@medsales-db:5432/medsalesdb \
  medsales-api:latest
```

> `medsales` 与 `medsales-db` 分别是根 compose 创建的网络与数据库容器名，按实际替换。

### 在容器内初始化管理员账号

```bash
docker compose exec medsales-api python scripts/create_admin.py --username admin --password admin123
```

### 在容器内运行测试

镜像不包含测试目录，如需在容器内跑测试，可挂载源码：

```bash
docker run --rm -v "$PWD":/opt/medsales -w /opt/medsales medsales-api:latest \
  sh -c "pip install -r requirements.txt && python -m pytest -q"
```

> 说明：容器与宿主机测试都无需真实数据库——pytest 使用内存 SQLite；只有运行服务时才连接 `medsalesdb`。

## 运行测试

所有接口均有对应测试脚本（tests/ 目录，按模块划分），测试使用内存 SQLite，无需真实数据库：

```bash
.venv/bin/python -m pytest -q
```

测试覆盖全部接口的成功路径与关键异常路径，其中 GSP 用例覆盖「建档 → 审核 → 资质档案 →
交易拦截 → 换证复审 → 附件版本化 → 到期预警」完整闭环。

## 主要设计说明

- **全异步**：SQLAlchemy 2.0 async + asyncpg（生产）/ aiosqlite（测试），所有接口为 `async def`。
- **自动计价**：创建销售单时按商品当日挂网价与行折扣自动计算小计、优惠、应收、成本。
- **库存闭环**：采购收货 → 采购入库流水；销售发货 → 销售出库流水；退货处理 → 退货入库流水；期初建账 → 期初入库流水。
- **状态机**：销售单 待付款 → 已发货 → 已完成 / 已取消；采购单 待收货 → 部分收货 → 已完成；退货单 待处理 → 已完成。
- **安全**：PBKDF2-SHA256 密码哈希（标准库实现），JWT 令牌认证。
- **兼容性**：新增表使用 BIGINT（PostgreSQL）/ INTEGER（SQLite）方言变体，保证生产与测试环境一致。
