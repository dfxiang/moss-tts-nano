# 医药销售管理系统前端

面向**药品、疫苗、医疗器械销售公司**的业务管理系统前端，与仓库内 [api](../api/README.md)（FastAPI 全异步后端）配套使用，覆盖客户、商品、采购、销售、库存、退货、财务、报表、GSP 合规等全部业务模块。

> 当前状态：全部业务页面、权限控制与 GSP 流程均已实现。

---

## 1. 技术栈

| 类别 | 选型 | 说明 |
| --- | --- | --- |
| 框架 | Vue 3 + TypeScript | 组合式 API，严格类型 |
| 构建 | Vite | 开发/构建一体化 |
| UI 组件库 | Element Plus | 中后台管理系统常用组件齐全 |
| 状态管理 | Pinia | 用户信息、权限、全局配置 |
| 路由 | Vue Router 4 | 动态路由 + 路由守卫 |
| HTTP | Axios | 统一封装请求/拦截器 |
| 图表 | ECharts | 销售趋势、品类占比等报表可视化 |
| 类型检查 | vue-tsc | `npx vue-tsc --noEmit` 独立执行类型检查 |
| 包管理 | npm | Node 自带，使用简单 |

---

## 2. 功能模块与页面

| 模块 | 页面 | 说明 |
| --- | --- | --- |
| 认证 | 登录 | 用户名密码登录；预留系统对接（API Key）说明页 |
| 工作台 | 经营看板 | 今日/本月销售额、毛利、库存预警、待办（对应后端 /reports/dashboard） |
| 系统管理 | 用户管理 | 用户增删改查、分配角色 |
| 系统管理 | 角色权限 | 角色维护、权限分配 |
| 系统管理 | 操作日志 | 审计日志查询 |
| 组织员工 | 部门管理 | 部门档案维护 |
| 组织员工 | 员工管理 | 员工档案、部门归属、在职状态 |
| 客户管理 | 客户档案 | 客户增删改查、类型/等级/状态、信用额度 |
| 商品管理 | 商品档案 | SKU、分类、厂家、供应商、成本与售价 |
| 商品管理 | 商品分类 | 一级分类维护 |
| 商品管理 | 厂家管理 | 生产厂家档案 |
| 商品管理 | 价格调整 | 调价单与价格历史 |
| 供应商管理 | 供应商档案 | 供应商增删改查、账期、合作状态 |
| 仓库管理 | 仓库档案 | 仓库维护、冷链属性 |
| 采购管理 | 采购订单 | 采购单创建/查询/编辑/删除 |
| 采购管理 | 采购收货 | 到货登记、部分收货、入库 |
| 销售管理 | 销售订单 | 下单（自动计价）、明细、取消 |
| 销售管理 | 发货出库 | 库存校验、发货登记 |
| 库存管理 | 库存查询 | 各仓库存、安全库存、预警状态、库存价值 |
| 库存管理 | 库存流水 | 流水追溯（穿透到来源单据） |
| 库存管理 | 期初建账 | 期初库存录入 |
| 退货管理 | 退货单 | 退货单创建/查询/处理入库 |
| 财务收款 | 收款记录 | 收款登记、订单核销 |
| 财务收款 | 应收账龄 | 应收余额与逾期分析 |
| 报表分析 | 销售报表 | 日/月销售汇总（含环比） |
| 报表分析 | 客户汇总 | 客户订单数、销售额、毛利 |
| 报表分析 | 销售员业绩 | 按部门/销售员统计 |
| 报表分析 | 商品汇总 | 销量、销售额、毛利排名 |
| 报表分析 | 订单明细 | 明细导出（支持条件筛选） |
| GSP 合规 | 证照管理 | 证照台账：首营资料审核（通过/驳回）、扫描件归档 |
| GSP 合规 | 资质档案 | 一户一档：合规结论、阻断/预警清单、建档与换证 |
| GSP 合规 | 预警中心 | 证照/批次到期分级预警（已过期 / 30 / 60 / 90 天 / 待审核） |
| GSP 合规 | 批次效期 | 批次批号、近效期提醒 |

---

## 3. 路由规划

```
/login                         登录页（免认证）
/                              布局框架（需认证）
├── /dashboard                 经营看板
├── /system/users              用户管理
├── /system/roles              角色权限
├── /system/logs               操作日志
├── /org/departments           部门管理
├── /org/employees             员工管理
├── /customers                 客户档案
├── /products                  商品档案
├── /products/categories       商品分类
├── /products/manufacturers    厂家管理
├── /products/prices           价格调整
├── /suppliers                 供应商档案
├── /warehouses                仓库档案
├── /purchase/orders           采购订单
├── /purchase/receive          采购收货
├── /sales/orders              销售订单
├── /sales/ship                发货出库
├── /inventory/stock           库存查询
├── /inventory/movements       库存流水
├── /inventory/opening         期初建账
├── /returns                   退货管理
├── /finance/payments          收款记录
├── /finance/receivables       应收账龄
├── /reports/sales             销售报表
├── /reports/customers         客户汇总
├── /reports/employees         销售员业绩
├── /reports/products          商品汇总
├── /reports/orders            订单明细
├── /gsp/certificates          证照管理
├── /gsp/qualification         资质档案（一户一档）
├── /gsp/alerts                预警中心
└── /gsp/batches               批次效期
```

---

## 4. 目录结构

```
frontend/
├── public/
├── src/
│   ├── api/                 # 各模块接口封装（按模块拆分）
│   │   ├── auth.ts
│   │   ├── customer.ts
│   │   ├── product.ts
│   │   ├── sales.ts
│   │   ├── purchase.ts
│   │   ├── inventory.ts
│   │   └── ...
│   ├── assets/              # 静态资源
│   ├── components/          # 通用组件
│   ├── layout/              # 布局（侧边栏、顶栏、面包屑）
│   ├── router/              # 路由与守卫
│   ├── stores/              # Pinia（user.ts：登录态、角色与权限编码）
│   ├── directives/          # v-permission 指令（按钮级权限显隐）
│   ├── utils/               # request.ts、格式化、权限编码辅助（permission.ts）
│   ├── views/               # 页面（按模块目录组织）
│   │   ├── dashboard/
│   │   ├── system/
│   │   ├── sales/
│   │   └── ...
│   ├── App.vue
│   └── main.ts
├── .env.development          # 开发环境变量
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

---

## 5. 与后端对接约定

### 5.1 环境变量

```bash
# frontend/.env.development
VITE_API_BASE_URL=http://127.0.0.1:8001/api
```

> 容器部署时通过构建参数 `VITE_API_BASE_URL=/api` 使用同源地址（见 6.1）。

### 5.2 请求封装（utils/request.ts）

- 基于 Axios 统一创建实例，`baseURL` 取 `VITE_API_BASE_URL`；
- 请求拦截器：从 Pinia/localStorage 读取 `access_token`，自动附加请求头 `Authorization: Bearer <token>`；
- 响应拦截器：统一处理分页结构与错误；
- `401`：清除本地登录态，跳转 `/login`；
- 业务错误：弹出 `ElMessage.error(detail)`。

### 5.3 认证流程

1. 登录页调用 `POST /api/auth/login` 获取 `access_token`，存入 Pinia + localStorage；
2. 登录成功后调用 `GET /api/auth/me` 拉取角色与**权限编码**（`permissions` / `is_superuser`），存入 Pinia；
3. 路由守卫：无 token → 跳转 `/login`；有 token 但未加载权限 → 先补拉；缺少路由所需权限 → 跳转 `/403`；
4. 系统间对接场景：后端 `POST /api/auth/token`（API Key + 用户 ID）获取令牌，供服务端脚本调用，不在前端页面上使用。

### 5.3.1 权限控制（前端侧）

权限编码与后端共用（`模块:动作`，`all` 为通配），前端做四件事：

| 位置 | 做法 |
| --- | --- |
| 路由 | `meta: { permission: 'sales:view' }`，守卫拦截无权访问 |
| 菜单 | `MainLayout.vue` 的 `menuGroups` 按 `permission` 过滤，空分组自动隐藏 |
| 按钮 | 指令 `v-permission="'sales:manage'"`，或 `CrudPage` 的 `managePermission` 配置 |
| 取数 | 无权限的模块直接不发请求（如经营看板按权限决定是否加载报表/预警） |

注意：前端显隐只是交互收敛，真正的拦截在后端 `require_permission`。
完整设计见 [权限控制说明](../docs/权限控制说明.md)。

### 5.4 分页与响应结构

- 列表请求统一携带 `page`、`size` 查询参数；
- 列表响应：`{ "items": [...], "total": 0, "page": 1, "size": 20 }`；
- 错误响应：`{ "detail": "错误描述" }`，按 HTTP 状态码区分 400/401/404/422。

### 5.5 接口文档

全部接口定义见 [API接口文档](../docs/API接口文档.md)，前端各 `src/api/*.ts` 封装与其一一对应。

---

## 6. 快速开始

```bash
cd frontend
npm install
npm run dev        # 开发环境，默认 http://127.0.0.1:5273，接口默认取 http://127.0.0.1:8001/api
npm run build      # 生产构建
npm run test:e2e   # Playwright E2E
```

> E2E 用例要求本机同时具备：项目自带的数据库容器（默认 `medsales-db`，先执行
> `docker compose up -d medsales-db`；`api/scripts/e2e_backend.sh` 会在其中创建独立的
> `medsales_e2e` 库并在每次运行前重置）与已装好依赖的 `api/.venv`。

## 6.1 容器化运行

```bash
# 在仓库根目录一键启动前后端
docker compose up -d --build
```

- 前端：http://127.0.0.1:8088
- 后端：http://127.0.0.1:8001，Swagger：http://127.0.0.1:8001/docs

前端镜像为多阶段构建：Node 构建产物 → nginx 托管，`/api` 由 nginx 同源反代到后端容器，浏览器无需关心后端地址。

---

## 7. 测试

### 隔离环境 E2E

```bash
npm run test:e2e
```

测试会自动启动独立的 E2E 后端（端口 8002，使用独立的 `medsales_e2e` 数据库，每次运行自动重置）和前端开发服务器（端口 5273），验收标准为全部用例通过。

### 针对已部署环境的回归测试

上面的 `npm run test:e2e` 针对的是自带种子数据的隔离环境。若要验证**正在运行的部署**（默认 `http://127.0.0.1:8088`，数据量为演示库规模）的界面行为，使用独立的 live 配置：

```bash
# 验证分页控件是否存在、每页条数可否调整、翻页/跳页/查询归位是否正常
npx playwright test --config playwright.live.config.ts

# 或指定其他地址
LIVE_BASE_URL=http://your-host:8088 npx playwright test --config playwright.live.config.ts
```

- 覆盖分页、列表布局与列宽、筛选（单据号/客户/员工/部门/收款应收）、GSP 资质档案、
  权限目录与权限分配、个人资料与头像等。
- live 配置不会启动自带后端，直接访问运行中的部署；断言基于页面实时数据，可重复运行。
