# 统一业务对象选择控件 TODO（客户 / 商品 / 分类 / 厂家 / 供应商 / 仓库）

> 补充（第八轮）：对象已扩到 **八个** —— 新增**员工（销售员）**与**部门**两个控件
> （`EmployeeSelect.vue` / `DepartmentSelect.vue`，候选同样「编码 - 名称」，员工显示「工号 - 姓名」）。
> 已用在「销售员业绩」页：`/reports/employee-summary` 增加 `employee_id`（原有 `department_id`）。
> 该页**职位只有展示列，不做筛选**（按需求明确不加控件）。

> 目标：把这六个业务对象的选择做成统一控件——**显示「编码 + 名称」**、**既能按编码搜也能按名称搜**，
> 新增/编辑表单与查询筛选栏共用同一套实现（同一份候选数据、同一套失效规则）。
>
> 排查方式：静态阅读前端源码（`frontend/src`）+ 对**本机运行环境**（`http://127.0.0.1:8001/api`，admin/admin123）
> 逐个对象实测计数与 keyword 搜索行为。本文只记录问题与改造计划，不改代码。

## 一、结论速览

1. 六个对象里**只有「客户」有统一控件**（`frontend/src/components/CustomerSelect.vue`），其余五个（商品、分类、厂家、供应商、仓库）都没有。
2. 唯一的这个控件**也不满足「编码 + 名称」**：候选只显示名称（`CustomerSelect.vue:54`），只能按名称匹配。
3. 有 **7 个页面 + 明细行组件**自建 `el-select` 并各自 `fetchAllOptions()` 全量拉候选；另有 **5 个字段走 `CrudPage` 的 `optionsApi`**（商品管理 4 个 + 批次管理 1 个，只显示名称、默认不可输入搜索）。
4. 后端**基本不用改**：六个列表接口都已支持 `keyword` 同时匹配编码与名称（实测见下表），缺的只是前端的统一封装。
5. **商品的「编码」就是 SKU**：`product` 表没有 `code` 字段，`sku` 即唯一业务编码；界面上任何地方都不应出现商品主键。目前唯一的违规在批次管理——列表列显示裸主键（4.5），查询栏是「商品 ID」文本框（4.3）。
6. **筛选栏普遍缺实体过滤**：库存查询只有「仓库 + 状态」，缺按商品过滤（后端 `product_id` 其实早就支持）；同类的还有库存状态、库存流水、批次、商品管理、采购/销售订单、商品汇总、订单明细等，逐页结果见 4.3。

## 二、六个对象现状（运行环境实测）

权限前提：需要在运行环境登录 `admin/admin123`。计数取自 `GET /api/<对象>?page=1&size=1` 的 `total`。

| 对象 | 编码字段 | 后端 keyword 覆盖字段 | 现有统一控件 | 运行环境数据量 |
| --- | --- | --- | --- | --- |
| 客户 customer | `code`（如 `C00001`） | name / code | ✅ `CustomerSelect.vue`（仅名称、无编码） | 1650 |
| 商品 product | `sku`（如 `SKU-VAC-002`） | name / sku / approval_no | ❌ 无（仅 `ItemsEditor.vue` 内部内联下拉） | 365 |
| 分类 category | `code`（如 `CAT-VAC`） | name / code | ❌ 无 | 7 |
| 厂家 manufacturer | **无编码字段** | name | ❌ 无 | 148 |
| 供应商 supplier | `code`（如 `SUP001`） | name / code | ❌ 无 | 37 |
| 仓库 warehouse | `code`（如 `WH-SCT`） | name / code | ❌ 无 | 9 |

关于商品的编码口径：

- `product` 表**没有 `code` 字段**，唯一业务编码就是 `sku`（`api/app/models/master.py:95`，`sku` 为 `unique`）。所以统一控件的 label 用 `SKU - 名称`，搜索走 `keyword`（后端已同时匹配 `name` / `sku` / `approval_no`）。
- **商品主键（`product_id`）只用于接口传参，不出现在界面上**：列表列、下拉候选、回显文本一律用「SKU + 名称」。目前唯一的违规是批次管理的列表列与查询栏（`Batches.vue:14,20`），其它页面（库存、库存状态、商品汇总、订单明细、库存流水）都已经是 SKU / 名称。

实测（按编码搜，均能命中）：

```
GET /api/suppliers?keyword=SUP001      -> 1 条  SUP001 北京科兴生物制品有限公司
GET /api/warehouses?keyword=WH-SCT     -> 1 条  WH-SCT 广州中心仓
GET /api/categories?keyword=CAT-VAC    -> 1 条  CAT-VAC 疫苗
GET /api/customers?keyword=C00001      -> 1 条  C00001 长沙市第一中心医院
GET /api/products?keyword=SKU-VAC-002  -> 1 条  SKU-VAC-002 三价流感病毒裂解疫苗
GET /api/manufacturers?keyword=华兰     -> 1 条  （无 code）华兰生物
```

## 三、现在已经封装了什么

| 位置 | 作用 | 局限 |
| --- | --- | --- |
| `frontend/src/components/CustomerSelect.vue` | 客户选择控件（`v-model` 绑定客户 ID） | 只显示名称；`filterable` 只能按名称匹配 |
| `frontend/src/utils/customerOptions.ts` | 客户候选全站缓存（只拉一次）+ `refreshCustomerOptions()` | 只服务客户 |
| `frontend/src/utils/gsp.ts` → `searchEntityOptions()` / `getEntityOption()` | 客户/供应商/商品/厂家的**远程 keyword 搜索**，label 已是「编码 + 名称」 | 只被 GSP 两个页面使用，和上面的控件是两套实现 |

也就是说：`utils/gsp.ts` 里的那套逻辑，才是本次要推广的形态，但目前只有证照/首营资质页在用。

## 四、未使用统一控件的位置清单

### 4.1 新增 / 编辑表单

| 页面 | 位置 | 对象 | 当前实现 | 问题 |
| --- | --- | --- | --- | --- |
| 商品管理 `Products.vue:45,49,53` | 分类 / 生产厂家 / 主要供应商 | 分类·厂家·供应商 | `CrudPage` `formFields` `type=select` + `optionsApi` | 只显示名称、**无编码**、默认不可输入搜索（`CrudPage.vue:415` 只在 `allowCreate` 时开 `filterable`） |
| 批次管理 `Batches.vue:23` | 商品 | 商品 | 同上 | 只显示名称、看不到 SKU、不可搜索 |
| 采购订单 `PurchaseOrders.vue:218,225` | 供应商 / 收货仓库 | 供应商·仓库 | 自建 `el-select` + `fetchAllOptions()` | 只显示名称、无编码 |
| 销售订单 `SalesOrders.vue:241` | 发货仓库 | 仓库 | 自建 `el-select` + `fetchAllOptions()` | 只显示名称、无编码 |
| 期初入库 `OpenStock.vue:57` | 仓库 | 仓库 | 自建 `el-select` + `fetchAllOptions()` | 只显示名称、无编码 |
| 退货管理 `Returns.vue:180` | 原订单 | 订单 | 自建 `el-select` + `fetchAllOptions('/sales-orders')` | 属订单对象，同样是全量拉取 |
| 所有明细行 `ItemsEditor.vue:68` | 明细「商品」列 | 商品 | 组件内 `el-select`，候选由父页面 `:product-options` 传入 | 3 个父页面（采购/销售/退货/期初）各自 `fetchAllOptions('/products')`，label 格式与其它页面不一致 |

### 4.2 查询 / 筛选栏

| 页面 | 位置 | 对象 | 当前实现 | 问题 |
| --- | --- | --- | --- | --- |
| 商品管理 `Products.vue:37` | 分类 | 分类 | `searchFields` `type=select` + `optionsApi` | 只显示名称、不可输入搜索、无编码 |
| 采购订单 `PurchaseOrders.vue:174` | 供应商 | 供应商 | 自建 `el-select` | 只显示名称、无编码；后端还支持 `warehouse_id` 但页面没有仓库筛选入口 |
| 库存查询 `Inventory.vue:57` | 仓库 | 仓库 | 自建 `el-select` | 只显示名称、不可输入搜索 |
| 库存流水 `Movements.vue:75` | 商品 | 商品 | 自建 `el-select`，label 自拼成「名称（编码）」 | 显示格式与其它页面不一致；全量拉 365 商品；后端还支持 `warehouse_id` 未用 |
| 价格调整 `PriceHistory.vue:76` | 商品 | 商品 | 自建 `el-select`，label 为「SKU - 名称」 | 已是编码+名称，但全量拉取、不与其它页面共用 |

### 4.3 筛选栏缺的实体过滤（逐页核对）

「后端支持」一列是逐个接口核对出来的（`api/app/api/routes/*.py`）；标 ⚠️ 的需要顺带改后端。

| 页面 | 现有筛选 | 缺的对象过滤 | 后端支持情况 | 备注 |
| --- | --- | --- | --- | --- |
| 库存查询 `Inventory.vue` | 仓库、库存状态 | **商品** | ✅ `/inventory` 已支持 `product_id`（`inventory.py:48`） | 只能靠 `product_id`，接口没有商品关键词参数 |
| 库存状态报表 `InventoryStatus.vue` | 无 | **仓库**、商品 | ⚠️ `/reports/inventory-status` 只透传了 `warehouse_id`（`reports.py:528`），没透 `product_id` | 补商品筛选要顺手把 `product_id` 透给 `list_inventory` |
| 库存流水 `Movements.vue` | 类型、商品 | **仓库**；变动日期区间 | ✅ `/inventory/movements` 支持 `warehouse_id`、`start_date`、`end_date`（`inventory.py:95`） | 页面只用到了 `movement_type` + `product_id` |
| 批次管理 `Batches.vue` | 商品（当前是 ID 文本框） | **状态**、批号关键词 | ⚠️ `/gsp/batches` 支持 `status`、`keyword`（`gsp.py:640`），但 `keyword` **只匹配批号**（`gsp.py:648`），搜不到商品 | 商品筛选必须走控件传 `product_id`；该接口在演示数据下为 0 条 |
| 商品管理 `Products.vue` | 关键词、分类 | **生产厂家**、在售状态 | ✅ `/products` 支持 `manufacturer_id`、`is_active`（`products.py:158`） | 后端不支持按供应商筛选商品 |
| 采购订单 `PurchaseOrders.vue` | 状态、供应商 | **收货仓库**；下单日期区间 | ✅ `/purchase-orders` 支持 `warehouse_id`、`start_date`、`end_date`（`purchase.py:53`） | 日期区间与实体筛选一起补 |
| 销售订单 `SalesOrders.vue` | 状态、客户 | 发货仓库、销售员、日期区间 | ⚠️ 支持 `employee_id`、`start_date`、`end_date`；**不支持** `warehouse_id`（`sales.py:66`） | 仓库筛选需要后端加参数；销售员/部门不在本次六个对象内 |
| 退货管理 `Returns.vue` | 客户、状态 | 退货日期区间 | ✅ 支持 `start_date` / `end_date`（`returns.py:75`） | 非实体筛选，可一并补 |
| 商品销售汇总 `ProductSummary.vue` | 无 | **分类**、商品、厂家 | ⚠️ 只支持 `category_id`（`reports.py:420`）；商品/厂家筛选要改后端聚合 | 分类可直接接控件 |
| 订单明细报表 `OrderDetail.vue` | 客户、状态、日期区间 | **商品**、仓库 | ⚠️ 只支持 `order_id` / `customer_id` / `status` / 日期（`reports.py:436`） | 加商品/仓库筛选需要后端加 `product_id`、`warehouse_id` |
| 客户销售汇总 `CustomerSummary.vue` | 客户 | — | ✅ 另支持 `keyword`（名称/编码模糊，`reports.py:223`） | 客户控件升级为「编码+名称 + 远程搜索」后天然覆盖 |
| 销售员业绩汇总 `EmployeeSummary.vue` | 无 | 部门 | ✅ 支持 `department_id`（`reports.py:287`） | 部门不在本次六个对象内，先记着 |
| 每日/月度销售汇总 `SalesReports.vue` | 无 | 日期/月份区间 | ⚠️ `sales-daily` 支持 `start_date`/`end_date`；`sales-monthly` 的参数是 `start_month`/`end_month` 但实现里是按全量再内存过滤（`reports.py:154`） | 加筛选时注意月度接口目前不做 database 侧过滤 |
| 证照管理 `Certificates.vue` | 关键词、对象类型、审核状态 | 证照状态 | ✅ 支持 `status`、`entity_id`（`gsp.py:188`） | 优先级低 |
| 收款记录 `Payments.vue` / 应收账龄 `Receivables.vue` | 客户、单号/日期、结算方式等 | — | ✅ 齐全 | 无需改动 |

实测验证（运行环境 `admin/admin123`，对比「全部」与「带参数」的 `total`）：

```
/inventory?product_id=1                   -> 9        （全部 3240）
/reports/inventory-status?warehouse_id=1  -> 360      （全部 3240）
/reports/product-summary?category_id=1    -> 24       （全部 365）
/purchase-orders?warehouse_id=1           -> 25594    （全部 219941）
/inventory/movements?warehouse_id=1       -> 323539   （全部 1846422）
/products?manufacturer_id=1               -> 6        （全部 365）
/products?is_active=false                 -> 5
/sales-returns?start_date=2026-01-01      -> 659      （全部 4962）
/sales-orders?warehouse_id=1              -> 211772   （与全部一致 → 参数被忽略）
/reports/order-detail?product_id=1        -> 1607812  （与全部一致 → 参数被忽略）
```

另外注意：运行环境里 `/api/gsp/batches` 返回 **0 条**（演示数据没有批次记录），所以批次管理页的列/筛选改造**无法用现有数据验收**，需要先造批次数据（`POST /api/gsp/batches`）或补演示数据。

### 4.4 已经用上的地方（作为统一后的目标形态）

- 客户：`SalesOrders.vue`（筛选 + 表单）、`Payments.vue`、`Receivables.vue`、`CustomerSummary.vue`、`OrderDetail.vue`、`Returns.vue`（筛选）——均已使用 `CustomerSelect`，只差**没有编码**。
- 关联对象远程搜索：`Certificates.vue:88`、`Qualification.vue` 已符合「编码 + 名称 + 按编码/名称搜索」，但实现与统一控件重复，后续应合并。
- 维护类列表页（客户 / 供应商 / 仓库 / 商品分类 / 生产厂家）：keyword 输入框 + 表格编码列已经齐备，不需要控件。

### 4.5 列表回显依赖「全量候选」（改远程搜索前必须先解决）

| 页面 | 现做法 | 风险 |
| --- | --- | --- |
| 采购订单 `PurchaseOrders.vue:189,192` | `suppliers.find(...)` / `warehouses.find(...)` 手写回显 | `PurchaseOrderOut` **没有** `supplier_name` / `warehouse_name`，候选一旦改成远程搜索，列表会退化成显示 ID |
| 批次管理 `Batches.vue:14` | 直接显示「商品 ID」列（裸主键） | `BatchOut` **没有** `product_sku` / `product_name`，既不显示 SKU 也不显示名称 |
| 库存流水 `Movements.vue:31` | `products` map 反查 | 同上，依赖全量候选 |
| 销售订单 `SalesOrders.vue:190` | 用后端 `customer_name` / `employee_name` / `warehouse_name` | ✅ 已经是正确形态 |

## 五、问题归纳（为什么必须统一）

1. **显示不统一**：只有名称（分类/厂家/供应商/仓库）、「SKU - 名称」（价格调整）、「名称（编码）」（库存流水）三种格式并存。
2. **搜索方式不统一**：`CrudPage` 的 select 默认不可输入；页面自建的是本地 `filterable`；GSP 是远程搜索。
3. **数据加载方式不统一且重复**：六个对象都是「一次性全量拉取」（`fetchAllOptions()` 最多翻 100 页 × 200 条）。商品 365 条会被采购/销售/退货/期初/价格调整/批次等多个页面各拉一遍。
4. **无缓存失效机制**：只有客户有 `refreshCustomerOptions()`；分类/厂家/供应商/仓库/商品改完后，其它页面的候选是旧的。
5. **无法按编码检索**：除 GSP 两页外，没有任何控件能输入编码搜索——而编码恰恰是业务人员手上最常用的定位手段。

## 六、目标方案（建议）

1. **一个通用控件 + 六个薄封装**
   - `components/EntitySelect.vue`：通用实现，接收 `entity` 名（或配置对象）。
   - `components/` 下薄封装：`ProductSelect.vue`、`CategorySelect.vue`、`ManufacturerSelect.vue`、`SupplierSelect.vue`、`WarehouseSelect.vue`；现有 `CustomerSelect.vue` 改为薄封装，保持现有用法与 `data-test` 不变。
2. **统一 label 格式**：`编码 - 名称`；商品的编码就是 SKU，label 用 `SKU - 名称`；厂家**没有编码字段**，只显示名称（不建议为它单独加 `code`）。
   配套硬规则：**商品主键不上屏**——`product_id` 只作接口传参，界面文本一律 `SKU + 名称`。
3. **统一搜索策略**
   - 小数据量：本地一次性拉全量 + 全站缓存，`filterable` 直接匹配含编码的 label（分类 7 / 仓库 9 / 供应商 37 / 厂家 148 / 商品 365）。
   - 大数据量：服务端 `keyword` 远程搜索（客户 1650），沿用 `utils/gsp.ts` 里 `searchEntityOptions` / `getEntityOption` 的做法，编辑态按主键回填。
4. **统一缓存层**：新增 `utils/catalogOptions.ts`（按实体分别缓存 + `ensureXxxOptions()` / `refreshXxxOptions()`），逐步取代 `utils/customerOptions.ts`。
5. **接入 `CrudPage`**：给 `FormField` / `SearchField` 增加 `entity` 类型字段（如 `{ prop:'category_id', entity:'category' }`），新增/编辑与查询栏都用控件渲染；`select` 类型保留给状态、证照类型这类枚举。
6. **`ItemsEditor.vue` 内部改用 `ProductSelect`**，候选不再由父页面各自传入；父页面只在需要单价/成本时保留 `product-change` 事件。
   明细行内部的 `v-model` 仍绑 `product_id`（接口需要），展示与搜索走 `SKU + 名称`。
7. **列表回显**：优先使用后端 `*_name`；缺字段的（采购单供应商/仓库、批次商品）要么后端补 `supplier_name` / `warehouse_name` / `product_sku` / `product_name`，要么前端按 id 回填。
8. **后端**：六个列表接口的 `keyword` 已足够，基本不用改；若全面改远程搜索，建议为 products 的远程候选加上 `size` 上限保护，并给 batches / purchase 补 name 字段。

## 七、TODO（按实施顺序，可勾选）

### 阶段 0：设计与基础

- [ ] T1 定义实体配置表（path / 编码字段 / label 构造 / keyword 参数），厂家特判为「仅名称」
- [ ] T2 新增 `utils/catalogOptions.ts`：六类候选的缓存、`ensureXxxOptions()`、`refreshXxxOptions()`（客户沿用远程搜索）

### 阶段 1：控件

- [ ] T3 新增 `components/EntitySelect.vue`（本地缓存模式 + 远程搜索模式，编辑回填，`data-test` 透传）
- [ ] T4 六个薄封装组件；`CustomerSelect.vue` 升级为 label 含编码（保持现有 props 与 `data-test` 兼容）
- [ ] T5 `CrudPage` 支持 `entity` 类型的 `formFields` / `searchFields`，新增/编辑与查询栏统一走控件
- [ ] T6 `ItemsEditor.vue` 内部改用 `ProductSelect`

### 阶段 2：页面替换

- [ ] T7 商品管理：查询「分类」、表单「分类 / 生产厂家 / 主要供应商」（`Products.vue:37,45,49,53`）
- [ ] T8 批次管理：查询栏「商品 ID」文本框 → 商品控件（按 SKU/名称搜）；表单「商品」→ 商品控件；列表「商品 ID」列 → 显示 `SKU + 名称`（`Batches.vue:14,20,23`）
- [ ] T9 采购订单：筛选「供应商」、表单「供应商 / 收货仓库」→ 控件（新增仓库筛选见 T31）
- [ ] T10 销售订单：表单「发货仓库」→ 仓库控件
- [ ] T11 库存查询：「仓库」筛选 → 仓库控件
- [ ] T12 库存流水：「商品」筛选 → 商品控件（显示保持编码+名称）；新增仓库筛选见 T28
- [ ] T13 期初入库：「仓库」→ 仓库控件；明细商品 → 商品控件
- [ ] T14 退货管理：明细商品 → 商品控件；（可选）原订单下拉改远程搜索
- [ ] T15 价格调整：「商品」→ 商品控件
- [ ] T16 GSP 证照 / 首营资质：`remote-select` 改为复用 `EntitySelect`（保持编码+名称的 label）

> 原 T17（库存状态报表补「仓库」、商品销售汇总补「分类」）已并入下面的阶段 2b（T27 / T33）。

### 阶段 2b：筛选能力补齐（按对象过滤）

对应 4.3 的逐页核对结果；标「需后端」的先改接口再加控件。

- [ ] T26 库存查询 `Inventory.vue`：筛选栏加「商品」控件（传 `product_id`，后端已支持）
- [x] T27 库存状态报表 `InventoryStatus.vue`：已加「商品 / 分类 / 厂家」控件（后端 `list_inventory` 增加 `category_id` / `manufacturer_id`，`product_id` 一并透过 `inventory_status` 透传）；**不加客户**（库存报表没有客户维度）；「仓库」控件仍未加
- [ ] T28 库存流水 `Movements.vue`：加「仓库」控件 + 变动日期区间（后端已支持 `warehouse_id` / `start_date` / `end_date`），与 T12 一起做
- [ ] T29 批次管理 `Batches.vue`：查询栏补「状态」下拉与批号关键词（后端已支持 `status` / `keyword`）；验收前先造批次数据（当前接口 0 条）
- [ ] T30 商品管理 `Products.vue`：查询栏补「生产厂家」控件与「在售」筛选（后端已支持 `manufacturer_id` / `is_active`）
- [ ] T31 采购订单 `PurchaseOrders.vue`：查询栏补「收货仓库」控件与下单日期区间（后端已支持）
- [ ] T32 销售订单 `SalesOrders.vue`：查询栏补「发货仓库」筛选 + 日期区间 / 销售员；**需后端**给 `/sales-orders` 增加 `warehouse_id` 参数
- [x] T33 商品销售汇总 `ProductSummary.vue`：已加「商品 / 分类 / 厂家」控件（后端 `product-summary` 增加 `product_id` / `manufacturer_id`，缓存键改为条件组合）；**不加客户**（报表行是商品，没有客户维度）
- [x] T34 订单明细报表 `OrderDetail.vue`：已加「商品 / 分类 / 厂家」控件（后端 `order-detail` 增加 `product_id` / `category_id` / `manufacturer_id`），客户筛选原有保留；**「仓库」筛选仍未加**
- [ ] T35 每日 / 月度销售汇总 `SalesReports.vue`：加日期区间（注意 `sales-monthly` 目前是全量取出后再内存过滤，改筛选时一并看是否需要下沉到数据库）
- [x] T36（低优先级）退货管理补退货日期区间、**销售员业绩汇总补销售员 / 部门筛选（已做，见第八轮补充）**、证照管理补证照状态筛选

### 阶段 3：回显与缓存失效

- [ ] T18 采购订单 / 批次列表名称回显：后端给 `PurchaseOrderOut` 补 `supplier_name` / `warehouse_name`，给 `BatchOut` 补 `product_sku` / `product_name`（或前端按 id 回填）
- [ ] T19 各维护页（商品/分类/厂家/供应商/仓库）保存成功后刷新对应缓存（现有 `CrudPage` 的 `saved` 事件已可挂接）
- [ ] T20 清理：删除页面里剩余的 `fetchAllOptions('/products' | '/suppliers' | '/warehouses' | '/categories' | '/manufacturers')` 与重复的 label 拼接逻辑

### 阶段 4：验证

- [ ] T21 `cd frontend && npm run build` 通过
- [ ] T22 `docker compose up -d --build medsales-api medsales-web`，用构建产物哈希确认部署已更新
- [ ] T23 新增 `frontend/tests/live/entity-select.spec.ts`：每个对象「输编码片段 → 命中」「输名称片段 → 命中」「选中后筛选/保存生效」
- [ ] T24 回归 `npx playwright test --config playwright.live.config.ts`（重点：`customer-select.spec.ts` 在 label 加编码后仍通过）
- [ ] T25 人工核对 `AGENTS.md` 的界面规范（分页靠左、操作按钮同行、表格单行显示）未被破坏

## 八、验收要点

- 每个对象的下拉：输入编码片段或名称片段都能命中；选中后表单/筛选提交的都是 ID。
- 编辑态回填：打开编辑弹窗时下拉显示「编码 - 名称」，不是空白或纯 ID。
- 列表回显：采购单、批次、库存流水的相关列不再出现裸 ID。
- 全仓搜索「商品 ID」字样应为 0 处；界面上不存在裸 `product_id`。
- 性能：客户下拉打开即出候选（实测 1650 条）；商品候选在整场会话中只拉一次，不被多个页面重复请求。
- 一致性：新增/编辑主数据后，其它页面同一对象的候选同步更新。
- 筛选真实性：4.3 里补的每个筛选项都要实测「选中后列表真的被过滤」（用运行环境数据核对返回条数），不能只看界面有控件；切换筛选条件时回到第 1 页。

## 九、风险与注意

- **厂家没有编码字段**，只能按名称搜索；若产品要求「编码 + 名称」硬性一致，需要后端为 manufacturer 补 `code`（属于数据结构变更，本次不建议）。
- **商品的编码是 SKU，不是主键**：不要把 `product_id` 当成可读标识（批次管理目前就是这种显示）。要展示商品就用 `sku`。
- **客户必须走远程搜索**（1650 条），不能沿用「全量缓存 + 本地过滤」；这样可以顺便去掉 `customerOptions.ts` 里一次性拉全量的开销。
- `CrudPage` 的 `optionsApi` 目前用在商品管理与批次管理，改成 `entity` 类型时要一起回归这两个页面。
- 现网 live 用例 `tests/live/customer-select.spec.ts` 依赖客户名称文本断言，label 加入编码后必须实跑确认（`hasText` 是部分匹配，预期仍通过，但不能只靠推断）。
