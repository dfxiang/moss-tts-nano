-- ============================================================================
-- medsalesdb：疫苗/药品/医疗器械销售公司销售管理系统数据库 DDL
-- 覆盖范围：2022-01-01 ~ 2026-07-31（约四年半演示数据）
-- 包含：18 张业务表、7 个视图、常用索引、表/视图/列中文注释
-- 公司背景：华康医药销售有限公司，约 500 名员工，年销售额约 500 亿元，
--           年销售毛利约 80 亿元
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 清理（便于重复执行）
-- ---------------------------------------------------------------------------
DROP VIEW IF EXISTS v_inventory_status CASCADE;
DROP VIEW IF EXISTS v_employee_sales_summary CASCADE;
DROP VIEW IF EXISTS v_customer_sales_summary CASCADE;
DROP VIEW IF EXISTS v_product_sales_summary CASCADE;
DROP VIEW IF EXISTS v_sales_monthly CASCADE;
DROP VIEW IF EXISTS v_sales_daily CASCADE;
DROP VIEW IF EXISTS v_order_detail CASCADE;

DROP TABLE IF EXISTS inventory_movement CASCADE;
DROP TABLE IF EXISTS inventory CASCADE;
DROP TABLE IF EXISTS purchase_order_item CASCADE;
DROP TABLE IF EXISTS purchase_order CASCADE;
DROP TABLE IF EXISTS payment_record CASCADE;
DROP TABLE IF EXISTS sales_return_item CASCADE;
DROP TABLE IF EXISTS sales_return CASCADE;
DROP TABLE IF EXISTS sales_order_item CASCADE;
DROP TABLE IF EXISTS sales_order CASCADE;
DROP TABLE IF EXISTS price_history CASCADE;
DROP TABLE IF EXISTS product CASCADE;
DROP TABLE IF EXISTS customer CASCADE;
DROP TABLE IF EXISTS employee CASCADE;
DROP TABLE IF EXISTS department CASCADE;
DROP TABLE IF EXISTS warehouse CASCADE;
DROP TABLE IF EXISTS supplier CASCADE;
DROP TABLE IF EXISTS manufacturer CASCADE;
DROP TABLE IF EXISTS product_category CASCADE;

-- ============================================================================
-- 一、基础档案表
-- ============================================================================

-- 商品分类表
CREATE TABLE product_category (
    id          SERIAL PRIMARY KEY,
    code        VARCHAR(20)  NOT NULL UNIQUE,                -- 分类编码
    name        VARCHAR(50)  NOT NULL,                       -- 分类名称
    description VARCHAR(200),                                -- 分类说明
    sort_order  SMALLINT     NOT NULL DEFAULT 0,             -- 显示顺序
    is_active   BOOLEAN      NOT NULL DEFAULT TRUE,          -- 是否启用
    created_at  TIMESTAMP    NOT NULL DEFAULT now()          -- 创建时间
);

COMMENT ON TABLE product_category IS '商品分类表：疫苗/药品/医疗器械的一级商品分类';
COMMENT ON COLUMN product_category.id IS '分类主键 ID';
COMMENT ON COLUMN product_category.code IS '分类编码，如 CAT-VAC';
COMMENT ON COLUMN product_category.name IS '分类名称，如 疫苗';
COMMENT ON COLUMN product_category.description IS '分类说明';
COMMENT ON COLUMN product_category.sort_order IS '显示顺序，越小越靠前';
COMMENT ON COLUMN product_category.is_active IS '是否启用，TRUE 启用 FALSE 停用';
COMMENT ON COLUMN product_category.created_at IS '创建时间';

-- 生产厂家表
CREATE TABLE manufacturer (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL UNIQUE,                -- 生产厂家/品牌名称
    country     VARCHAR(50),                                 -- 厂家所属国家/地区
    description VARCHAR(200),                                -- 厂家简介
    created_at  TIMESTAMP    NOT NULL DEFAULT now()          -- 创建时间
);

COMMENT ON TABLE manufacturer IS '生产厂家表：记录药品/疫苗/医疗器械生产企业（品牌）';
COMMENT ON COLUMN manufacturer.id IS '厂家主键 ID';
COMMENT ON COLUMN manufacturer.name IS '厂家名称，如 北京科兴生物制品有限公司';
COMMENT ON COLUMN manufacturer.country IS '厂家所属国家或地区';
COMMENT ON COLUMN manufacturer.description IS '厂家简介';
COMMENT ON COLUMN manufacturer.created_at IS '创建时间';

-- 供应商表
CREATE TABLE supplier (
    id             SERIAL PRIMARY KEY,
    code           VARCHAR(20)  NOT NULL UNIQUE,             -- 供应商编码
    name           VARCHAR(100) NOT NULL,                    -- 供应商名称
    contact_person VARCHAR(50),                              -- 联系人
    phone          VARCHAR(30),                              -- 联系电话
    email          VARCHAR(100),                             -- 电子邮箱
    province       VARCHAR(30),                              -- 所在省份
    city           VARCHAR(30),                              -- 所在城市
    address        VARCHAR(200),                             -- 详细地址
    credit_days    SMALLINT     NOT NULL DEFAULT 30,         -- 结算账期（天）
    status         VARCHAR(20)  NOT NULL DEFAULT '合作中',   -- 合作状态
    created_at     TIMESTAMP    NOT NULL DEFAULT now()       -- 创建时间
);

COMMENT ON TABLE supplier IS '供应商表：记录公司药品/疫苗/器械的采购上游（多为生产企业）';
COMMENT ON COLUMN supplier.id IS '供应商主键 ID';
COMMENT ON COLUMN supplier.code IS '供应商编码';
COMMENT ON COLUMN supplier.name IS '供应商全称';
COMMENT ON COLUMN supplier.contact_person IS '业务联系人姓名';
COMMENT ON COLUMN supplier.phone IS '联系电话';
COMMENT ON COLUMN supplier.email IS '联系邮箱';
COMMENT ON COLUMN supplier.province IS '所在省份';
COMMENT ON COLUMN supplier.city IS '所在城市';
COMMENT ON COLUMN supplier.address IS '详细地址';
COMMENT ON COLUMN supplier.credit_days IS '结算账期天数';
COMMENT ON COLUMN supplier.status IS '合作状态：合作中/暂停合作/已终止';
COMMENT ON COLUMN supplier.created_at IS '创建时间';

-- 仓库表
CREATE TABLE warehouse (
    id             SERIAL PRIMARY KEY,
    code           VARCHAR(20)  NOT NULL UNIQUE,             -- 仓库编码
    name           VARCHAR(100) NOT NULL,                    -- 仓库名称
    province       VARCHAR(30),                              -- 所在省份
    city           VARCHAR(30),                              -- 所在城市
    address        VARCHAR(200),                             -- 详细地址
    manager_name   VARCHAR(50),                              -- 仓管负责人
    phone          VARCHAR(30),                              -- 联系电话
    has_cold_chain BOOLEAN      NOT NULL DEFAULT TRUE,       -- 是否具备冷链库
    status         VARCHAR(20)  NOT NULL DEFAULT '正常',     -- 仓库状态
    created_at     TIMESTAMP    NOT NULL DEFAULT now()       -- 创建时间
);

COMMENT ON TABLE warehouse IS '仓库表：记录公司全国各区域医药仓库（含冷链库）';
COMMENT ON COLUMN warehouse.id IS '仓库主键 ID';
COMMENT ON COLUMN warehouse.code IS '仓库编码';
COMMENT ON COLUMN warehouse.name IS '仓库名称';
COMMENT ON COLUMN warehouse.province IS '所在省份';
COMMENT ON COLUMN warehouse.city IS '所在城市';
COMMENT ON COLUMN warehouse.address IS '详细地址';
COMMENT ON COLUMN warehouse.manager_name IS '仓管负责人姓名';
COMMENT ON COLUMN warehouse.phone IS '联系电话';
COMMENT ON COLUMN warehouse.has_cold_chain IS '是否具备 2~8℃ 冷链库';
COMMENT ON COLUMN warehouse.status IS '仓库状态：正常/停用';
COMMENT ON COLUMN warehouse.created_at IS '创建时间';

-- 部门表
CREATE TABLE department (
    id          SERIAL PRIMARY KEY,
    code        VARCHAR(20)  NOT NULL UNIQUE,                -- 部门编码
    name        VARCHAR(50)  NOT NULL,                       -- 部门名称
    description VARCHAR(200),                                -- 部门职责说明
    created_at  TIMESTAMP    NOT NULL DEFAULT now()          -- 创建时间
);

COMMENT ON TABLE department IS '部门表：记录公司组织架构（总部职能 + 九大区域销售部）';
COMMENT ON COLUMN department.id IS '部门主键 ID';
COMMENT ON COLUMN department.code IS '部门编码';
COMMENT ON COLUMN department.name IS '部门名称';
COMMENT ON COLUMN department.description IS '部门职责说明';
COMMENT ON COLUMN department.created_at IS '创建时间';

-- 员工表
CREATE TABLE employee (
    id                SERIAL PRIMARY KEY,
    code              VARCHAR(20)  NOT NULL UNIQUE,          -- 工号
    name              VARCHAR(50)  NOT NULL,                 -- 姓名
    gender            VARCHAR(10),                           -- 性别
    phone             VARCHAR(30),                           -- 联系电话
    email             VARCHAR(100),                          -- 电子邮箱
    department_id     INT          NOT NULL REFERENCES department (id), -- 所属部门
    position          VARCHAR(50),                           -- 职位
    manager_id        INT          REFERENCES employee (id), -- 直属上级
    hire_date         DATE         NOT NULL,                 -- 入职日期
    employment_status VARCHAR(20)  NOT NULL DEFAULT '在职',  -- 在职状态
    created_at        TIMESTAMP    NOT NULL DEFAULT now()    -- 创建时间
);

COMMENT ON TABLE employee IS '员工表：约 500 名员工（销售、采购、仓储、质量、财务等岗位）';
COMMENT ON COLUMN employee.id IS '员工主键 ID';
COMMENT ON COLUMN employee.code IS '员工工号';
COMMENT ON COLUMN employee.name IS '员工姓名';
COMMENT ON COLUMN employee.gender IS '性别：男/女';
COMMENT ON COLUMN employee.phone IS '联系电话';
COMMENT ON COLUMN employee.email IS '电子邮箱';
COMMENT ON COLUMN employee.department_id IS '所属部门 ID';
COMMENT ON COLUMN employee.position IS '职位名称';
COMMENT ON COLUMN employee.manager_id IS '直属上级员工 ID';
COMMENT ON COLUMN employee.hire_date IS '入职日期';
COMMENT ON COLUMN employee.employment_status IS '在职状态：在职/离职';
COMMENT ON COLUMN employee.created_at IS '创建时间';

-- 客户表
CREATE TABLE customer (
    id             SERIAL PRIMARY KEY,
    code           VARCHAR(20)   NOT NULL UNIQUE,            -- 客户编码
    name           VARCHAR(100)  NOT NULL,                   -- 客户名称
    customer_type  VARCHAR(30)   NOT NULL DEFAULT '单体药房',-- 客户类型
    coop_level     VARCHAR(20)   NOT NULL DEFAULT '普通客户',-- 合作等级
    contact_person VARCHAR(50),                              -- 联系人
    phone          VARCHAR(30),                              -- 联系电话
    email          VARCHAR(100),                             -- 电子邮箱
    province       VARCHAR(30),                              -- 所在省份
    city           VARCHAR(30),                              -- 所在城市
    address        VARCHAR(200),                             -- 收货地址
    license_no     VARCHAR(50),                              -- 证照编号
    credit_limit   NUMERIC(14,2) NOT NULL DEFAULT 0,         -- 信用额度
    status         VARCHAR(20)   NOT NULL DEFAULT '正常',    -- 客户状态
    remark         VARCHAR(200),                             -- 备注
    created_at     TIMESTAMP     NOT NULL DEFAULT now()      -- 建档时间
);

COMMENT ON TABLE customer IS '客户表：医院、疾控中心、连锁药房、诊所、经销商等客户档案';
COMMENT ON COLUMN customer.id IS '客户主键 ID';
COMMENT ON COLUMN customer.code IS '客户编码';
COMMENT ON COLUMN customer.name IS '客户名称（医院/机构/公司全称）';
COMMENT ON COLUMN customer.customer_type IS '客户类型：三级医院/二级医院/基层医疗机构/民营医院/疾控中心/连锁药房/单体药房/诊所/经销商/其他机构';
COMMENT ON COLUMN customer.coop_level IS '合作等级：战略合作/重点客户/普通客户/新客户';
COMMENT ON COLUMN customer.contact_person IS '采购联系人';
COMMENT ON COLUMN customer.phone IS '联系电话';
COMMENT ON COLUMN customer.email IS '电子邮箱';
COMMENT ON COLUMN customer.province IS '所在省份';
COMMENT ON COLUMN customer.city IS '所在城市';
COMMENT ON COLUMN customer.address IS '收货地址';
COMMENT ON COLUMN customer.license_no IS '医疗机构执业许可证/药品经营许可证/营业执照编号';
COMMENT ON COLUMN customer.credit_limit IS '信用额度（赊销上限）';
COMMENT ON COLUMN customer.status IS '客户状态：正常/冻结/流失/暂停合作';
COMMENT ON COLUMN customer.remark IS '备注';
COMMENT ON COLUMN customer.created_at IS '建档时间';

-- 商品表
CREATE TABLE product (
    id               SERIAL PRIMARY KEY,
    sku              VARCHAR(30)   NOT NULL UNIQUE,          -- 商品 SKU
    name             VARCHAR(200)  NOT NULL,                 -- 商品名称
    category_id      INT           NOT NULL REFERENCES product_category (id), -- 商品分类
    manufacturer_id  INT           NOT NULL REFERENCES manufacturer (id),     -- 生产厂家
    supplier_id      INT           NOT NULL REFERENCES supplier (id),         -- 主要供应商
    approval_no      VARCHAR(60),                            -- 批准文号/注册证号
    specification    VARCHAR(100),                           -- 规格（剂型/含量/包装）
    unit             VARCHAR(20)   NOT NULL DEFAULT '盒',    -- 计量单位
    dosage_form      VARCHAR(30),                            -- 剂型
    storage_condition VARCHAR(30)  NOT NULL DEFAULT '常温',  -- 储存条件
    is_cold_chain    BOOLEAN       NOT NULL DEFAULT FALSE,   -- 是否需冷链运输
    shelf_life_months SMALLINT     NOT NULL DEFAULT 24,      -- 有效期（月）
    cost_price       NUMERIC(14,2) NOT NULL,                 -- 采购成本价
    standard_price   NUMERIC(14,2) NOT NULL,                 -- 挂网/标准售价
    is_active        BOOLEAN       NOT NULL DEFAULT TRUE,    -- 是否在售
    listed_date      DATE          NOT NULL,                 -- 上市/挂网日期
    created_at       TIMESTAMP     NOT NULL DEFAULT now()    -- 创建时间
);

COMMENT ON TABLE product IS '商品表：在售疫苗、药品、医疗器械（含批准文号与储存条件）';
COMMENT ON COLUMN product.id IS '商品主键 ID';
COMMENT ON COLUMN product.sku IS '商品 SKU 编码';
COMMENT ON COLUMN product.name IS '商品名称';
COMMENT ON COLUMN product.category_id IS '所属分类 ID';
COMMENT ON COLUMN product.manufacturer_id IS '生产厂家 ID';
COMMENT ON COLUMN product.supplier_id IS '主要供应商 ID';
COMMENT ON COLUMN product.approval_no IS '药品批准文号/医疗器械注册证号';
COMMENT ON COLUMN product.specification IS '规格参数，如 0.5ml/支、100mg*28片/盒';
COMMENT ON COLUMN product.unit IS '计量单位，如 支/盒/套/台';
COMMENT ON COLUMN product.dosage_form IS '剂型，如 注射剂/片剂/胶囊/植入材料';
COMMENT ON COLUMN product.storage_condition IS '储存条件：常温/阴凉/冷藏 2~8℃/冷冻';
COMMENT ON COLUMN product.is_cold_chain IS '是否需 2~8℃ 冷链运输';
COMMENT ON COLUMN product.shelf_life_months IS '有效期（月）';
COMMENT ON COLUMN product.cost_price IS '采购成本价';
COMMENT ON COLUMN product.standard_price IS '挂网价/标准售价';
COMMENT ON COLUMN product.is_active IS '是否在售：TRUE 在售 FALSE 下架';
COMMENT ON COLUMN product.listed_date IS '上市/挂网日期';
COMMENT ON COLUMN product.created_at IS '创建时间';

-- 价格调整历史表
CREATE TABLE price_history (
    id             SERIAL PRIMARY KEY,
    product_id     INT           NOT NULL REFERENCES product (id), -- 商品
    effective_date DATE          NOT NULL,                          -- 生效日期
    old_price      NUMERIC(14,2),                                   -- 调整前价格
    new_price      NUMERIC(14,2) NOT NULL,                          -- 调整后价格
    change_reason  VARCHAR(100),                                    -- 调价原因
    created_at     TIMESTAMP     NOT NULL DEFAULT now()             -- 创建时间
);

COMMENT ON TABLE price_history IS '价格调整历史表：记录挂网价/采购价的历次调整';
COMMENT ON COLUMN price_history.id IS '记录主键 ID';
COMMENT ON COLUMN price_history.product_id IS '商品 ID';
COMMENT ON COLUMN price_history.effective_date IS '调价生效日期';
COMMENT ON COLUMN price_history.old_price IS '调整前售价';
COMMENT ON COLUMN price_history.new_price IS '调整后售价';
COMMENT ON COLUMN price_history.change_reason IS '调价原因，如 国家集采/挂网价调整';
COMMENT ON COLUMN price_history.created_at IS '创建时间';

-- ============================================================================
-- 二、业务单据表
-- ============================================================================

-- 销售订单主表
CREATE TABLE sales_order (
    id               BIGSERIAL PRIMARY KEY,
    order_no         VARCHAR(30)   NOT NULL UNIQUE,          -- 订单编号
    customer_id      INT           NOT NULL REFERENCES customer (id), -- 客户
    employee_id      INT           NOT NULL REFERENCES employee (id), -- 销售员
    warehouse_id     INT           NOT NULL REFERENCES warehouse (id), -- 发货仓库
    order_date       DATE          NOT NULL,                 -- 下单日期
    status           VARCHAR(20)   NOT NULL DEFAULT '待付款', -- 订单状态
    item_count       INT           NOT NULL DEFAULT 0,       -- 商品行数
    total_quantity   INT           NOT NULL DEFAULT 0,       -- 商品总数量
    subtotal_amount  NUMERIC(14,2) NOT NULL DEFAULT 0,       -- 商品小计
    discount_amount  NUMERIC(14,2) NOT NULL DEFAULT 0,       -- 优惠金额
    total_amount     NUMERIC(14,2) NOT NULL DEFAULT 0,       -- 应收金额
    paid_amount      NUMERIC(14,2) NOT NULL DEFAULT 0,       -- 已收金额
    cost_amount      NUMERIC(14,2) NOT NULL DEFAULT 0,       -- 订单成本合计
    shipping_address VARCHAR(300),                           -- 收货地址
    invoice_type     VARCHAR(30)   NOT NULL DEFAULT '增值税专用发票', -- 开票类型
    settlement_method VARCHAR(30)  NOT NULL DEFAULT '现款',  -- 结算方式
    delivery_type    VARCHAR(30)   NOT NULL DEFAULT '常温运输', -- 配送方式
    delivery_date    DATE,                                   -- 发货日期
    remark           VARCHAR(200),                           -- 备注
    created_at       TIMESTAMP     NOT NULL DEFAULT now()    -- 创建时间
);

COMMENT ON TABLE sales_order IS '销售订单主表：记录每一笔销售订单头信息';
COMMENT ON COLUMN sales_order.id IS '订单主键 ID';
COMMENT ON COLUMN sales_order.order_no IS '订单编号，格式 SO+日期+序号';
COMMENT ON COLUMN sales_order.customer_id IS '客户 ID';
COMMENT ON COLUMN sales_order.employee_id IS '销售员 ID';
COMMENT ON COLUMN sales_order.warehouse_id IS '发货仓库 ID';
COMMENT ON COLUMN sales_order.order_date IS '下单日期';
COMMENT ON COLUMN sales_order.status IS '订单状态：已完成/已发货/已付款/待付款/已取消';
COMMENT ON COLUMN sales_order.item_count IS '订单包含的商品行数';
COMMENT ON COLUMN sales_order.total_quantity IS '订单商品总数量';
COMMENT ON COLUMN sales_order.subtotal_amount IS '商品小计金额';
COMMENT ON COLUMN sales_order.discount_amount IS '优惠金额（行折扣+订单返利）';
COMMENT ON COLUMN sales_order.total_amount IS '应收金额 = 小计 - 优惠';
COMMENT ON COLUMN sales_order.paid_amount IS '已收金额';
COMMENT ON COLUMN sales_order.cost_amount IS '订单成本合计（用于毛利分析）';
COMMENT ON COLUMN sales_order.shipping_address IS '收货地址';
COMMENT ON COLUMN sales_order.invoice_type IS '开票类型：增值税专用发票/增值税普通发票/不开发票';
COMMENT ON COLUMN sales_order.settlement_method IS '结算方式：现款/月结30天/月结60天/月结90天';
COMMENT ON COLUMN sales_order.delivery_type IS '配送方式：冷链运输/常温运输/快递配送/客户自提';
COMMENT ON COLUMN sales_order.delivery_date IS '发货日期';
COMMENT ON COLUMN sales_order.remark IS '订单备注';
COMMENT ON COLUMN sales_order.created_at IS '创建时间';

-- 销售订单明细表
CREATE TABLE sales_order_item (
    id              BIGSERIAL PRIMARY KEY,
    sales_order_id  BIGINT        NOT NULL REFERENCES sales_order (id), -- 所属订单
    product_id      INT           NOT NULL REFERENCES product (id),     -- 商品
    quantity        INT           NOT NULL CHECK (quantity > 0),        -- 数量
    unit_price      NUMERIC(14,2) NOT NULL,                             -- 成交单价
    unit_cost       NUMERIC(14,2) NOT NULL,                             -- 成本单价快照
    discount_rate   NUMERIC(5,4)  NOT NULL DEFAULT 0,                   -- 行折扣率
    discount_amount NUMERIC(14,2) NOT NULL DEFAULT 0,                   -- 行优惠金额
    amount          NUMERIC(14,2) NOT NULL                              -- 行实付金额
);

COMMENT ON TABLE sales_order_item IS '销售订单明细表：记录订单内每件商品的成交信息';
COMMENT ON COLUMN sales_order_item.id IS '明细主键 ID';
COMMENT ON COLUMN sales_order_item.sales_order_id IS '所属销售订单 ID';
COMMENT ON COLUMN sales_order_item.product_id IS '商品 ID';
COMMENT ON COLUMN sales_order_item.quantity IS '销售数量';
COMMENT ON COLUMN sales_order_item.unit_price IS '成交单价（按当日挂网价与折扣）';
COMMENT ON COLUMN sales_order_item.unit_cost IS '成本单价快照';
COMMENT ON COLUMN sales_order_item.discount_rate IS '行折扣率';
COMMENT ON COLUMN sales_order_item.discount_amount IS '行优惠金额';
COMMENT ON COLUMN sales_order_item.amount IS '行实付金额 = 单价*数量 - 行优惠';

-- 付款记录表
CREATE TABLE payment_record (
    id             BIGSERIAL PRIMARY KEY,
    sales_order_id BIGINT        NOT NULL REFERENCES sales_order (id), -- 订单
    customer_id    INT           NOT NULL REFERENCES customer (id),    -- 付款客户
    payment_date   DATE          NOT NULL,                             -- 付款日期
    amount         NUMERIC(14,2) NOT NULL CHECK (amount > 0),          -- 付款金额
    payment_method VARCHAR(20)   NOT NULL,                             -- 付款方式
    status         VARCHAR(20)   NOT NULL DEFAULT '成功',              -- 收款状态
    remark         VARCHAR(200),                                       -- 备注
    created_at     TIMESTAMP     NOT NULL DEFAULT now()                -- 创建时间
);

COMMENT ON TABLE payment_record IS '付款记录表：记录客户货款回款流水';
COMMENT ON COLUMN payment_record.id IS '付款记录主键 ID';
COMMENT ON COLUMN payment_record.sales_order_id IS '订单 ID';
COMMENT ON COLUMN payment_record.customer_id IS '付款客户 ID';
COMMENT ON COLUMN payment_record.payment_date IS '付款日期';
COMMENT ON COLUMN payment_record.amount IS '付款金额';
COMMENT ON COLUMN payment_record.payment_method IS '付款方式：银行转账/对公转账/承兑汇票/现金/网上银行';
COMMENT ON COLUMN payment_record.status IS '收款状态：成功/失败/冲正';
COMMENT ON COLUMN payment_record.remark IS '备注（常为订单编号）';
COMMENT ON COLUMN payment_record.created_at IS '创建时间';

-- 销售退货主表
CREATE TABLE sales_return (
    id            BIGSERIAL PRIMARY KEY,
    return_no     VARCHAR(30)   NOT NULL UNIQUE,             -- 退货单编号
    sales_order_id BIGINT       NOT NULL REFERENCES sales_order (id), -- 原订单
    customer_id   INT           NOT NULL REFERENCES customer (id),    -- 客户
    warehouse_id  INT           NOT NULL REFERENCES warehouse (id),   -- 退回仓库
    return_date   DATE          NOT NULL,                    -- 退货日期
    status        VARCHAR(20)   NOT NULL DEFAULT '待处理',   -- 处理状态
    reason        VARCHAR(100),                              -- 退货原因
    total_amount  NUMERIC(14,2) NOT NULL DEFAULT 0,          -- 退货金额
    remark        VARCHAR(200),                              -- 备注
    created_at    TIMESTAMP     NOT NULL DEFAULT now()       -- 创建时间
);

COMMENT ON TABLE sales_return IS '销售退货主表：记录质量/效期/滞销等退货单据';
COMMENT ON COLUMN sales_return.id IS '退货主键 ID';
COMMENT ON COLUMN sales_return.return_no IS '退货单编号，格式 RT+日期+序号';
COMMENT ON COLUMN sales_return.sales_order_id IS '原销售订单 ID';
COMMENT ON COLUMN sales_return.customer_id IS '客户 ID';
COMMENT ON COLUMN sales_return.warehouse_id IS '退回仓库 ID';
COMMENT ON COLUMN sales_return.return_date IS '退货日期';
COMMENT ON COLUMN sales_return.status IS '处理状态：已完成/待处理';
COMMENT ON COLUMN sales_return.reason IS '退货原因：质量问题/效期临近/冷链断链/发错货/滞销退货';
COMMENT ON COLUMN sales_return.total_amount IS '退货退款金额';
COMMENT ON COLUMN sales_return.remark IS '备注（常为原订单编号）';
COMMENT ON COLUMN sales_return.created_at IS '创建时间';

-- 销售退货明细表
CREATE TABLE sales_return_item (
    id              BIGSERIAL PRIMARY KEY,
    sales_return_id BIGINT        NOT NULL REFERENCES sales_return (id), -- 所属退货单
    product_id      INT           NOT NULL REFERENCES product (id),      -- 商品
    quantity        INT           NOT NULL CHECK (quantity > 0),         -- 退货数量
    unit_price      NUMERIC(14,2) NOT NULL,                              -- 退货单价
    amount          NUMERIC(14,2) NOT NULL,                              -- 退货金额
    reason          VARCHAR(100)                                         -- 明细退货原因
);

COMMENT ON TABLE sales_return_item IS '销售退货明细表：记录退货单内商品明细';
COMMENT ON COLUMN sales_return_item.id IS '明细主键 ID';
COMMENT ON COLUMN sales_return_item.sales_return_id IS '所属退货单 ID';
COMMENT ON COLUMN sales_return_item.product_id IS '商品 ID';
COMMENT ON COLUMN sales_return_item.quantity IS '退货数量';
COMMENT ON COLUMN sales_return_item.unit_price IS '退货单价（按原订单成交价）';
COMMENT ON COLUMN sales_return_item.amount IS '退货金额';
COMMENT ON COLUMN sales_return_item.reason IS '退货原因';

-- 采购订单主表
CREATE TABLE purchase_order (
    id             BIGSERIAL PRIMARY KEY,
    order_no       VARCHAR(30)   NOT NULL UNIQUE,            -- 采购单编号
    supplier_id    INT           NOT NULL REFERENCES supplier (id),      -- 供应商
    warehouse_id   INT           NOT NULL REFERENCES warehouse (id),     -- 收货仓库
    order_date     DATE          NOT NULL,                   -- 下单日期
    expected_date  DATE,                                     -- 预计到货日期
    received_date  DATE,                                     -- 实际到货日期
    status         VARCHAR(20)   NOT NULL DEFAULT '待收货',  -- 采购状态
    total_amount   NUMERIC(14,2) NOT NULL DEFAULT 0,         -- 采购金额
    delivery_type  VARCHAR(30)   NOT NULL DEFAULT '常温运输', -- 运输方式
    remark         VARCHAR(200),                             -- 备注
    created_at     TIMESTAMP     NOT NULL DEFAULT now()      -- 创建时间
);

COMMENT ON TABLE purchase_order IS '采购订单主表：向生产企业/供应商的采购补货单据';
COMMENT ON COLUMN purchase_order.id IS '采购单主键 ID';
COMMENT ON COLUMN purchase_order.order_no IS '采购单编号，格式 PO+日期+序号';
COMMENT ON COLUMN purchase_order.supplier_id IS '供应商 ID';
COMMENT ON COLUMN purchase_order.warehouse_id IS '收货仓库 ID';
COMMENT ON COLUMN purchase_order.order_date IS '下单日期';
COMMENT ON COLUMN purchase_order.expected_date IS '预计到货日期';
COMMENT ON COLUMN purchase_order.received_date IS '实际到货日期';
COMMENT ON COLUMN purchase_order.status IS '采购状态：待收货/部分收货/已完成';
COMMENT ON COLUMN purchase_order.total_amount IS '采购总金额';
COMMENT ON COLUMN purchase_order.delivery_type IS '运输方式：冷链运输/常温运输';
COMMENT ON COLUMN purchase_order.remark IS '备注';
COMMENT ON COLUMN purchase_order.created_at IS '创建时间';

-- 采购订单明细表
CREATE TABLE purchase_order_item (
    id                BIGSERIAL PRIMARY KEY,
    purchase_order_id BIGINT        NOT NULL REFERENCES purchase_order (id), -- 所属采购单
    product_id        INT           NOT NULL REFERENCES product (id),        -- 商品
    quantity          INT           NOT NULL CHECK (quantity > 0),           -- 采购数量
    unit_cost         NUMERIC(14,2) NOT NULL,                                -- 采购单价
    amount            NUMERIC(14,2) NOT NULL,                                -- 采购金额
    received_quantity INT           NOT NULL DEFAULT 0,                      -- 实收数量
    received_date     DATE                                                   -- 实收日期
);

COMMENT ON TABLE purchase_order_item IS '采购订单明细表：记录采购单内商品明细与实收情况';
COMMENT ON COLUMN purchase_order_item.id IS '明细主键 ID';
COMMENT ON COLUMN purchase_order_item.purchase_order_id IS '所属采购单 ID';
COMMENT ON COLUMN purchase_order_item.product_id IS '商品 ID';
COMMENT ON COLUMN purchase_order_item.quantity IS '采购数量';
COMMENT ON COLUMN purchase_order_item.unit_cost IS '采购单价';
COMMENT ON COLUMN purchase_order_item.amount IS '采购金额';
COMMENT ON COLUMN purchase_order_item.received_quantity IS '实收数量（0 表示未收货）';
COMMENT ON COLUMN purchase_order_item.received_date IS '实收日期';

-- ============================================================================
-- 三、库存表
-- ============================================================================

-- 库存表
CREATE TABLE inventory (
    id           SERIAL PRIMARY KEY,
    warehouse_id INT  NOT NULL REFERENCES warehouse (id),    -- 仓库
    product_id   INT  NOT NULL REFERENCES product (id),      -- 商品
    quantity     INT  NOT NULL DEFAULT 0 CHECK (quantity >= 0), -- 当前库存数量
    safety_stock INT  NOT NULL DEFAULT 0,                    -- 安全库存
    updated_at   TIMESTAMP NOT NULL DEFAULT now(),           -- 最近更新时间
    CONSTRAINT uq_inventory_warehouse_product UNIQUE (warehouse_id, product_id)
);

COMMENT ON TABLE inventory IS '库存表：记录各仓库商品的当前库存与安全库存';
COMMENT ON COLUMN inventory.id IS '库存记录主键 ID';
COMMENT ON COLUMN inventory.warehouse_id IS '仓库 ID';
COMMENT ON COLUMN inventory.product_id IS '商品 ID';
COMMENT ON COLUMN inventory.quantity IS '当前库存数量（不小于 0）';
COMMENT ON COLUMN inventory.safety_stock IS '安全库存下限';
COMMENT ON COLUMN inventory.updated_at IS '最近更新时间';

-- 库存流水表
CREATE TABLE inventory_movement (
    id            BIGSERIAL PRIMARY KEY,
    warehouse_id  INT           NOT NULL REFERENCES warehouse (id),  -- 仓库
    product_id    INT           NOT NULL REFERENCES product (id),    -- 商品
    movement_type VARCHAR(20)   NOT NULL,                            -- 流水类型
    quantity      INT           NOT NULL CHECK (quantity <> 0),      -- 变动数量（正入负出）
    movement_date DATE          NOT NULL,                            -- 变动日期
    ref_table     VARCHAR(40),                                       -- 关联单据表名
    ref_id        BIGINT,                                            -- 关联单据明细 ID
    created_by    INT           REFERENCES employee (id),            -- 经办人
    remark        VARCHAR(200),                                      -- 备注
    created_at    TIMESTAMP     NOT NULL DEFAULT now()               -- 创建时间
);

COMMENT ON TABLE inventory_movement IS '库存流水表：记录期初、采购入库、销售出库、退货入库等变动';
COMMENT ON COLUMN inventory_movement.id IS '流水主键 ID';
COMMENT ON COLUMN inventory_movement.warehouse_id IS '仓库 ID';
COMMENT ON COLUMN inventory_movement.product_id IS '商品 ID';
COMMENT ON COLUMN inventory_movement.movement_type IS '流水类型：期初入库/采购入库/销售出库/退货入库';
COMMENT ON COLUMN inventory_movement.quantity IS '变动数量，正数为入库、负数为出库';
COMMENT ON COLUMN inventory_movement.movement_date IS '变动日期';
COMMENT ON COLUMN inventory_movement.ref_table IS '关联单据表名';
COMMENT ON COLUMN inventory_movement.ref_id IS '关联单据明细 ID';
COMMENT ON COLUMN inventory_movement.created_by IS '经办员工 ID';
COMMENT ON COLUMN inventory_movement.remark IS '备注（常为单据编号）';
COMMENT ON COLUMN inventory_movement.created_at IS '创建时间';

-- ============================================================================
-- 四、索引
-- ============================================================================

CREATE INDEX idx_employee_department      ON employee (department_id);
CREATE INDEX idx_customer_type_level      ON customer (customer_type, coop_level);
CREATE INDEX idx_customer_city            ON customer (city);
CREATE INDEX idx_customer_created_at      ON customer (created_at);

CREATE INDEX idx_product_category         ON product (category_id);
CREATE INDEX idx_product_manufacturer     ON product (manufacturer_id);
CREATE INDEX idx_product_supplier         ON product (supplier_id);
CREATE INDEX idx_product_name             ON product (name);
CREATE INDEX idx_product_active           ON product (is_active) WHERE is_active;

CREATE INDEX idx_price_history_product_date ON price_history (product_id, effective_date);

CREATE INDEX idx_sales_order_date         ON sales_order (order_date);
CREATE INDEX idx_sales_order_customer     ON sales_order (customer_id, order_date);
CREATE INDEX idx_sales_order_employee     ON sales_order (employee_id, order_date);
CREATE INDEX idx_sales_order_status       ON sales_order (status);
CREATE INDEX idx_sales_order_item_order   ON sales_order_item (sales_order_id);
CREATE INDEX idx_sales_order_item_product ON sales_order_item (product_id, sales_order_id);

CREATE INDEX idx_payment_order            ON payment_record (sales_order_id);
CREATE INDEX idx_payment_date             ON payment_record (payment_date);

CREATE INDEX idx_sales_return_date        ON sales_return (return_date);
CREATE INDEX idx_sales_return_order       ON sales_return (sales_order_id);
CREATE INDEX idx_sales_return_item_return ON sales_return_item (sales_return_id);

CREATE INDEX idx_purchase_order_date      ON purchase_order (order_date);
CREATE INDEX idx_purchase_order_supplier  ON purchase_order (supplier_id, order_date);
CREATE INDEX idx_purchase_order_status    ON purchase_order (status);
CREATE INDEX idx_purchase_order_item_order   ON purchase_order_item (purchase_order_id);
CREATE INDEX idx_purchase_order_item_product ON purchase_order_item (product_id);

CREATE INDEX idx_inventory_product        ON inventory (product_id);
CREATE INDEX idx_inventory_quantity       ON inventory (quantity) WHERE quantity < safety_stock;
CREATE INDEX idx_inventory_movement_date  ON inventory_movement (movement_date);
CREATE INDEX idx_inventory_movement_product ON inventory_movement (product_id, movement_date);
CREATE INDEX idx_inventory_movement_type  ON inventory_movement (movement_type);

-- ============================================================================
-- 五、视图
-- ============================================================================

-- 1. 订单明细视图：订单 + 商品 + 客户 + 销售员 + 仓库 全维度明细
CREATE OR REPLACE VIEW v_order_detail AS
SELECT
    so.id              AS order_id,
    so.order_no        AS order_no,
    so.order_date      AS order_date,
    so.status          AS order_status,
    c.id               AS customer_id,
    c.name             AS customer_name,
    c.customer_type    AS customer_type,
    c.coop_level       AS coop_level,
    e.id               AS employee_id,
    e.name             AS employee_name,
    d.name             AS department_name,
    w.name             AS warehouse_name,
    p.id               AS product_id,
    p.sku              AS sku,
    p.name             AS product_name,
    pc.name            AS category_name,
    m.name             AS manufacturer_name,
    soi.quantity       AS quantity,
    soi.unit_price     AS unit_price,
    soi.discount_amount AS discount_amount,
    soi.amount         AS line_amount,
    so.total_amount    AS order_amount,
    so.paid_amount     AS paid_amount
FROM sales_order so
JOIN customer c         ON c.id = so.customer_id
JOIN employee e         ON e.id = so.employee_id
JOIN department d       ON d.id = e.department_id
JOIN warehouse w        ON w.id = so.warehouse_id
JOIN sales_order_item soi ON soi.sales_order_id = so.id
JOIN product p          ON p.id = soi.product_id
JOIN product_category pc ON pc.id = p.category_id
JOIN manufacturer m     ON m.id = p.manufacturer_id;

COMMENT ON VIEW v_order_detail IS '订单明细视图：按订单行展示销售明细、客户、销售员、仓库与商品信息';
COMMENT ON COLUMN v_order_detail.order_id IS '订单 ID';
COMMENT ON COLUMN v_order_detail.order_no IS '订单编号';
COMMENT ON COLUMN v_order_detail.order_date IS '下单日期';
COMMENT ON COLUMN v_order_detail.order_status IS '订单状态';
COMMENT ON COLUMN v_order_detail.customer_id IS '客户 ID';
COMMENT ON COLUMN v_order_detail.customer_name IS '客户名称';
COMMENT ON COLUMN v_order_detail.customer_type IS '客户类型';
COMMENT ON COLUMN v_order_detail.coop_level IS '合作等级';
COMMENT ON COLUMN v_order_detail.employee_id IS '销售员 ID';
COMMENT ON COLUMN v_order_detail.employee_name IS '销售员姓名';
COMMENT ON COLUMN v_order_detail.department_name IS '销售员所属部门';
COMMENT ON COLUMN v_order_detail.warehouse_name IS '发货仓库';
COMMENT ON COLUMN v_order_detail.product_id IS '商品 ID';
COMMENT ON COLUMN v_order_detail.sku IS '商品 SKU';
COMMENT ON COLUMN v_order_detail.product_name IS '商品名称';
COMMENT ON COLUMN v_order_detail.category_name IS '商品分类';
COMMENT ON COLUMN v_order_detail.manufacturer_name IS '生产厂家';
COMMENT ON COLUMN v_order_detail.quantity IS '数量';
COMMENT ON COLUMN v_order_detail.unit_price IS '成交单价';
COMMENT ON COLUMN v_order_detail.discount_amount IS '行优惠金额';
COMMENT ON COLUMN v_order_detail.line_amount IS '行实付金额';
COMMENT ON COLUMN v_order_detail.order_amount IS '订单应收金额';
COMMENT ON COLUMN v_order_detail.paid_amount IS '订单已收金额';

-- 2. 每日销售汇总视图
CREATE OR REPLACE VIEW v_sales_daily AS
SELECT
    so.order_date            AS sale_date,
    COUNT(*)                 AS order_count,
    COALESCE(SUM(ls.item_count), 0) AS item_count,
    COALESCE(SUM(ls.quantity), 0)   AS quantity,
    SUM(so.total_amount)     AS total_amount,
    SUM(so.discount_amount)  AS discount_amount,
    SUM(so.cost_amount)      AS cost_amount,
    ROUND(SUM(so.total_amount) - SUM(so.cost_amount), 2) AS profit_amount
FROM sales_order so
LEFT JOIN LATERAL (
    SELECT COUNT(*) AS item_count, COALESCE(SUM(quantity), 0) AS quantity
    FROM sales_order_item soi
    WHERE soi.sales_order_id = so.id
) ls ON TRUE
WHERE so.status <> '已取消'
GROUP BY so.order_date;

COMMENT ON VIEW v_sales_daily IS '每日销售汇总视图：按日统计订单数、销量、销售额、成本与毛利';
COMMENT ON COLUMN v_sales_daily.sale_date IS '销售日期';
COMMENT ON COLUMN v_sales_daily.order_count IS '订单数';
COMMENT ON COLUMN v_sales_daily.item_count IS '商品行数';
COMMENT ON COLUMN v_sales_daily.quantity IS '销售总数量';
COMMENT ON COLUMN v_sales_daily.total_amount IS '销售额（应收金额）';
COMMENT ON COLUMN v_sales_daily.discount_amount IS '优惠金额';
COMMENT ON COLUMN v_sales_daily.cost_amount IS '销售成本';
COMMENT ON COLUMN v_sales_daily.profit_amount IS '毛利';

-- 3. 月度销售汇总视图（含环比增速）
CREATE OR REPLACE VIEW v_sales_monthly AS
SELECT
    month,
    order_count,
    item_count,
    quantity,
    total_amount,
    discount_amount,
    cost_amount,
    profit_amount,
    LAG(total_amount) OVER (ORDER BY month) AS prev_month_amount,
    CASE
        WHEN LAG(total_amount) OVER (ORDER BY month) IS NULL
          OR LAG(total_amount) OVER (ORDER BY month) = 0 THEN NULL
        ELSE ROUND(
            (total_amount - LAG(total_amount) OVER (ORDER BY month))
            / LAG(total_amount) OVER (ORDER BY month) * 100, 2)
    END AS amount_growth_rate
FROM (
    SELECT
        date_trunc('month', so.order_date)::date AS month,
        COUNT(*)                 AS order_count,
        COALESCE(SUM(ls.item_count), 0) AS item_count,
        COALESCE(SUM(ls.quantity), 0)   AS quantity,
        SUM(so.total_amount)     AS total_amount,
        SUM(so.discount_amount)  AS discount_amount,
        SUM(so.cost_amount)      AS cost_amount,
        ROUND(SUM(so.total_amount) - SUM(so.cost_amount), 2) AS profit_amount
    FROM sales_order so
    LEFT JOIN LATERAL (
        SELECT COUNT(*) AS item_count, COALESCE(SUM(quantity), 0) AS quantity
        FROM sales_order_item soi
        WHERE soi.sales_order_id = so.id
    ) ls ON TRUE
    WHERE so.status <> '已取消'
    GROUP BY 1
) t;

COMMENT ON VIEW v_sales_monthly IS '月度销售汇总视图：按月统计销售指标并计算环比增速';
COMMENT ON COLUMN v_sales_monthly.month IS '月份';
COMMENT ON COLUMN v_sales_monthly.order_count IS '订单数';
COMMENT ON COLUMN v_sales_monthly.item_count IS '商品行数';
COMMENT ON COLUMN v_sales_monthly.quantity IS '销售总数量';
COMMENT ON COLUMN v_sales_monthly.total_amount IS '销售额';
COMMENT ON COLUMN v_sales_monthly.discount_amount IS '优惠金额';
COMMENT ON COLUMN v_sales_monthly.cost_amount IS '销售成本';
COMMENT ON COLUMN v_sales_monthly.profit_amount IS '毛利';
COMMENT ON COLUMN v_sales_monthly.prev_month_amount IS '上月销售额';
COMMENT ON COLUMN v_sales_monthly.amount_growth_rate IS '销售额环比增速（%）';

-- 4. 商品销售汇总视图
CREATE OR REPLACE VIEW v_product_sales_summary AS
SELECT
    p.id                 AS product_id,
    p.sku                AS sku,
    p.name               AS product_name,
    pc.name              AS category_name,
    m.name               AS manufacturer_name,
    p.cost_price         AS cost_price,
    p.standard_price     AS standard_price,
    COALESCE(SUM(soi.quantity), 0)                          AS sold_quantity,
    COALESCE(SUM(soi.amount), 0)                            AS sales_amount,
    COALESCE(SUM(soi.amount) - SUM(soi.quantity * soi.unit_cost), 0) AS gross_profit,
    COUNT(DISTINCT so.id)                                   AS order_count
FROM product p
LEFT JOIN sales_order_item soi ON soi.product_id = p.id
LEFT JOIN sales_order so ON so.id = soi.sales_order_id AND so.status <> '已取消'
LEFT JOIN product_category pc ON pc.id = p.category_id
LEFT JOIN manufacturer m ON m.id = p.manufacturer_id
GROUP BY p.id, pc.name, m.name;

COMMENT ON VIEW v_product_sales_summary IS '商品销售汇总视图：统计各商品销量、销售额、毛利与订单数';
COMMENT ON COLUMN v_product_sales_summary.product_id IS '商品 ID';
COMMENT ON COLUMN v_product_sales_summary.sku IS '商品 SKU';
COMMENT ON COLUMN v_product_sales_summary.product_name IS '商品名称';
COMMENT ON COLUMN v_product_sales_summary.category_name IS '商品分类';
COMMENT ON COLUMN v_product_sales_summary.manufacturer_name IS '生产厂家';
COMMENT ON COLUMN v_product_sales_summary.cost_price IS '成本价';
COMMENT ON COLUMN v_product_sales_summary.standard_price IS '标准售价';
COMMENT ON COLUMN v_product_sales_summary.sold_quantity IS '累计销量';
COMMENT ON COLUMN v_product_sales_summary.sales_amount IS '累计销售额';
COMMENT ON COLUMN v_product_sales_summary.gross_profit IS '累计毛利';
COMMENT ON COLUMN v_product_sales_summary.order_count IS '关联订单数';

-- 5. 客户销售汇总视图
CREATE OR REPLACE VIEW v_customer_sales_summary AS
SELECT
    c.id                 AS customer_id,
    c.code               AS customer_code,
    c.name               AS customer_name,
    c.customer_type      AS customer_type,
    c.coop_level         AS coop_level,
    c.province           AS province,
    c.city               AS city,
    c.phone              AS phone,
    COUNT(so.id) FILTER (WHERE so.status <> '已取消') AS order_count,
    COALESCE(SUM(so.total_amount) FILTER (WHERE so.status <> '已取消'), 0) AS total_amount,
    COALESCE(SUM(so.cost_amount) FILTER (WHERE so.status <> '已取消'), 0)  AS cost_amount,
    COALESCE(SUM(so.total_amount) FILTER (WHERE so.status <> '已取消'), 0)
      - COALESCE(SUM(so.cost_amount) FILTER (WHERE so.status <> '已取消'), 0) AS profit_amount,
    MAX(so.order_date) FILTER (WHERE so.status <> '已取消') AS last_order_date
FROM customer c
LEFT JOIN sales_order so ON so.customer_id = c.id
GROUP BY c.id;

COMMENT ON VIEW v_customer_sales_summary IS '客户销售汇总视图：统计客户订单数、销售额、毛利与最近下单日期';
COMMENT ON COLUMN v_customer_sales_summary.customer_id IS '客户 ID';
COMMENT ON COLUMN v_customer_sales_summary.customer_code IS '客户编码';
COMMENT ON COLUMN v_customer_sales_summary.customer_name IS '客户名称';
COMMENT ON COLUMN v_customer_sales_summary.customer_type IS '客户类型';
COMMENT ON COLUMN v_customer_sales_summary.coop_level IS '合作等级';
COMMENT ON COLUMN v_customer_sales_summary.province IS '省份';
COMMENT ON COLUMN v_customer_sales_summary.city IS '城市';
COMMENT ON COLUMN v_customer_sales_summary.phone IS '联系电话';
COMMENT ON COLUMN v_customer_sales_summary.order_count IS '有效订单数';
COMMENT ON COLUMN v_customer_sales_summary.total_amount IS '累计销售额';
COMMENT ON COLUMN v_customer_sales_summary.cost_amount IS '累计成本';
COMMENT ON COLUMN v_customer_sales_summary.profit_amount IS '累计毛利';
COMMENT ON COLUMN v_customer_sales_summary.last_order_date IS '最近下单日期';

-- 6. 销售员业绩汇总视图
CREATE OR REPLACE VIEW v_employee_sales_summary AS
SELECT
    e.id                 AS employee_id,
    e.code               AS employee_code,
    e.name               AS employee_name,
    d.name               AS department_name,
    e.position           AS position,
    COUNT(so.id) FILTER (WHERE so.status <> '已取消') AS order_count,
    COALESCE(SUM(so.total_amount) FILTER (WHERE so.status <> '已取消'), 0) AS total_amount,
    COALESCE(SUM(so.cost_amount) FILTER (WHERE so.status <> '已取消'), 0)  AS cost_amount,
    COALESCE(SUM(so.total_amount) FILTER (WHERE so.status <> '已取消'), 0)
      - COALESCE(SUM(so.cost_amount) FILTER (WHERE so.status <> '已取消'), 0) AS profit_amount,
    COUNT(DISTINCT so.customer_id) FILTER (WHERE so.status <> '已取消') AS customer_count
FROM employee e
LEFT JOIN department d ON d.id = e.department_id
LEFT JOIN sales_order so ON so.employee_id = e.id
GROUP BY e.id, d.name, e.position;

COMMENT ON VIEW v_employee_sales_summary IS '销售员业绩汇总视图：统计各员工订单数、销售额、毛利与客户数';
COMMENT ON COLUMN v_employee_sales_summary.employee_id IS '员工 ID';
COMMENT ON COLUMN v_employee_sales_summary.employee_code IS '工号';
COMMENT ON COLUMN v_employee_sales_summary.employee_name IS '员工姓名';
COMMENT ON COLUMN v_employee_sales_summary.department_name IS '所属部门';
COMMENT ON COLUMN v_employee_sales_summary.position IS '职位';
COMMENT ON COLUMN v_employee_sales_summary.order_count IS '有效订单数';
COMMENT ON COLUMN v_employee_sales_summary.total_amount IS '累计销售额';
COMMENT ON COLUMN v_employee_sales_summary.cost_amount IS '累计成本';
COMMENT ON COLUMN v_employee_sales_summary.profit_amount IS '累计毛利';
COMMENT ON COLUMN v_employee_sales_summary.customer_count IS '服务客户数';

-- 7. 库存状态视图
CREATE OR REPLACE VIEW v_inventory_status AS
SELECT
    inv.id               AS inventory_id,
    w.name               AS warehouse_name,
    p.id                 AS product_id,
    p.sku                AS sku,
    p.name               AS product_name,
    pc.name              AS category_name,
    inv.quantity         AS quantity,
    inv.safety_stock     AS safety_stock,
    inv.quantity - inv.safety_stock AS stock_diff,
    CASE
        WHEN inv.quantity < inv.safety_stock THEN '库存不足'
        WHEN inv.quantity <= inv.safety_stock * 1.2 THEN '库存预警'
        ELSE '库存充足'
    END AS stock_status,
    ROUND(inv.quantity * p.cost_price, 2) AS stock_value
FROM inventory inv
JOIN warehouse w          ON w.id = inv.warehouse_id
JOIN product p            ON p.id = inv.product_id
JOIN product_category pc  ON pc.id = p.category_id;

COMMENT ON VIEW v_inventory_status IS '库存状态视图：展示各仓库商品库存、安全库存与库存价值';
COMMENT ON COLUMN v_inventory_status.inventory_id IS '库存记录 ID';
COMMENT ON COLUMN v_inventory_status.warehouse_name IS '仓库名称';
COMMENT ON COLUMN v_inventory_status.product_id IS '商品 ID';
COMMENT ON COLUMN v_inventory_status.sku IS '商品 SKU';
COMMENT ON COLUMN v_inventory_status.product_name IS '商品名称';
COMMENT ON COLUMN v_inventory_status.category_name IS '商品分类';
COMMENT ON COLUMN v_inventory_status.quantity IS '当前库存';
COMMENT ON COLUMN v_inventory_status.safety_stock IS '安全库存';
COMMENT ON COLUMN v_inventory_status.stock_diff IS '库存与安全库存差值';
COMMENT ON COLUMN v_inventory_status.stock_status IS '库存状态：库存不足/库存预警/库存充足';
COMMENT ON COLUMN v_inventory_status.stock_value IS '库存价值（按成本价）';

-- ============================================================================
-- 结束
-- ============================================================================
