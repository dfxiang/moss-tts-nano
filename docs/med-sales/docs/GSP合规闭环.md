# GSP 合规业务闭环（med-sales）

> 本文说明系统 GSP 合规部分的完整业务闭环：首营资质建档 → 资质审核 → 交易准入校验 →
> 到期预警 → 换证归档，以及对应的数据模型、接口与前端页面。

## 一、业务闭环总览

```
                       ┌──────────────────────────────┐
   主体建档            │  客户 / 供应商 / 商品 / 厂家   │
   （已有主数据）      └──────────────┬───────────────┘
                                     │ 1. 录入证照
                                     ▼
                    ┌────────────────────────────────┐
                    │  certificates（证照）           │
                    │  证号 / 有效期 / 审核状态        │
                    └──────────────┬─────────────────┘
                                   │ 2. 上传扫描件（S3/MinIO）
                                   ▼
                    ┌────────────────────────────────┐
                    │  certificate_attachments        │
                    │  多版本：v1 历史 / vN 当前       │
                    └──────────────┬─────────────────┘
                                   │ 3. 质量员审核
                      ┌────────────┴────────────┐
                      ▼                         ▼
                已通过（有效资质）          已驳回（不可交易）
                      │
                      │ 4. 交易准入校验
                      ▼
    ┌──────────────────────────────────────────────────┐
    │ 销售下单 / 发货出库   →  校验客户 + 订购商品资质    │
    │ 采购下单 / 收货入库   →  校验供应商 + 采购商品资质  │
    │ 不合规 → HTTP 400 阻断 + 审计留痕（action=block）  │
    └──────────────────────────┬───────────────────────┘
                               │ 5. 到期前预警
                               ▼
    ┌──────────────────────────────────────────────────┐
    │ 预警中心 / 经营看板：已过期 · 30 天内 · 31-60 天   │
    │ 31-60/61-90 天 · 待审核资料                       │
    └──────────────────────────┬───────────────────────┘
                               │ 6. 换证
                               ▼
    上传新扫描件 → 旧版本自动转为历史留档；修改证号/有效期 → 自动回到「待审核」
```

## 二、状态模型

### 证照审核状态（`certificates.review_status`）

| 状态 | 说明 |
| --- | --- |
| 待审核 | 新建证照的初始状态；关键信息（证号/类型/有效期）变更后自动回到该状态 |
| 已通过 | 质量员审核通过，参与资质合规判定 |
| 已驳回 | 审核不通过并记录原因，阻断交易直至整改复审 |

### 证照综合状态（`effective_status`，由审核状态 + 有效期实时计算）

| 状态 | 判定 | 是否阻断交易 |
| --- | --- | --- |
| 已驳回 | `review_status = 已驳回` | 是 |
| 待审核 | `review_status = 待审核` | 是 |
| 已过期 | `valid_to < 今天` | 是 |
| 未生效 | `valid_from > 今天` | 是 |
| 即将到期 | `valid_to <= 今天 + GSP_EXPIRY_WARNING_DAYS` | 否（预警） |
| 有效 | 其余 | 否 |

## 三、交易准入规则

1. 校验作用于**销售下单、销售发货、采购下单、采购收货**四个节点；
2. 校验对象为订单涉及的**客户/供应商**以及**订单内的每个商品**；
3. 只有在该主体**已建立资质档案**（录入过至少一条证照）时才参与管控：
   - 存在「已驳回 / 待审核 / 已过期 / 未生效」的证照 → **拒绝交易**，返回 400 并列出全部问题；
   - 仅存在「即将到期」的证照 → 放行，但在资质档案与预警中心提示；
4. 完全未建档主体的处理由 `GSP_STRICT_QUALIFICATION` 决定（默认放行，便于在存量数据上逐步推行首营建档）；
5. 每次拦截写入审计日志（`module=gsp`、`action=block`），满足 GSP 留痕要求。

## 四、接口清单

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/gsp/certificates` | 证照台账（分页；支持 `keyword` / `entity_type` / `entity_id` / `review_status`） |
| POST | `/api/gsp/certificates` | 新建证照（初始为待审核） |
| PUT | `/api/gsp/certificates/{id}` | 更新证照（关键信息变更自动重置为待审核） |
| POST | `/api/gsp/certificates/{id}/review` | **首营资料审核**：`action=approve\|reject` + `remark` |
| GET | `/api/gsp/qualification/{entity_type}/{entity_id}` | **一户一档**：主体资质档案、准入结论、阻断/预警清单 |
| GET | `/api/gsp/certificates/{id}/attachments` | 扫描件列表（`include_history=true` 返回历史版本） |
| POST | `/api/gsp/certificates/{id}/attachments` | 上传扫描件（新版本生效，旧版本自动留档） |
| GET | `/api/gsp/attachments/{id}/preview` | **在线预览**：以 `inline` 方式回传 S3 对象，浏览器原生渲染 PDF / 图片 |
| GET | `/api/gsp/attachments/{id}/download` | 下载扫描件（写审计日志 `action=download`） |
| DELETE | `/api/gsp/attachments/{id}` | 删除扫描件 |
| GET | `/api/gsp/alerts` | 到期预警中心（证照 + 批次，按 `category` / `level` 过滤，分页） |
| GET | `/api/gsp/alerts/summary` | 预警统计（已过期 / 30 天内 / 31-60 天 / 61-90 天 / 待审核） |
| GET/POST/PUT/DELETE | `/api/gsp/batches*` | 批次批号与效期管理 |

## 五、前端页面

| 页面 | 路由 | 说明 |
| --- | --- | --- |
| 证照管理 | `/gsp/certificates` | 证照台账：新增/编辑/删除、审核通过/驳回、扫描件抽屉（预览/下载/换证留档）、跳转资质档案 |
| 资质档案 | `/gsp/qualification` | 一户一档：选择主体 → 合规横幅 + 阻断/预警清单 + 证照列表（分页）+ 建档/审核/扫描件 |
| 预警中心 | `/gsp/alerts` | 分级统计卡片（可点击下钻）+ 证照/批次预警列表（分页） |
| 批次管理 | `/gsp/batches` | 批次批号与效期管理 |
| 客户 / 供应商 / 商品列表 | `/customers` 等 | 每行提供「资质」入口，直达该主体的资质档案 |
| 经营看板 | `/dashboard` | GSP 合规预警卡片，可跳转预警中心 |

所有列表页分页控件遵循仓库约定：靠左布局、`layout="total, sizes, prev, pager, next"`、
每页条数 `[10, 20, 50, 100]` 默认 20、切换筛选回到第 1 页。

## 六、对象存储（S3 / MinIO）

- 证照扫描件通过 `app/core/storage.py` 写入本系统专用 MinIO（bucket 私有读写）；
- 对象键：`gsp/certificates/{证照ID}/{uuid}{后缀}`；
- 数据库只存元数据（文件名、类型、大小、版本、是否当前版本、上传人）；
- 换证时新文件成为当前版本，旧文件保留在对象存储中，附件记录标记为历史版本；
- 删除证照会级联删除附件记录并清理对象存储文件；下载与上传均写审计日志。

### 在线预览

扫描件由 API 代理回传（不把 MinIO 暴露给浏览器）：

- `GET /api/gsp/attachments/{id}/preview` 以 `Content-Disposition: inline` 返回对象，
  `Content-Type` 优先取上传时的类型、缺失时按扩展名兜底（PDF 固定为 `application/pdf`），
  并带 `X-Content-Type-Options: nosniff`；
- 浏览器凭据仍走 `Authorization` 头，前端用 axios 取回 Blob 再生成 `URL.createObjectURL`，
  因此不需要把令牌暴露在 URL 上，也不需要让浏览器直连 MinIO；
- 渲染完全交给浏览器原生能力：PDF 用内置阅读器（`<iframe>`），
  JPG / PNG / WebP / GIF / BMP 用 `<img>`；TIFF、Word 等无法原生渲染的格式提示改为下载；
- 附件接口返回 `kind`（`pdf`/`image`/`other`）与 `previewable` 字段，前端据此决定是否显示「预览」按钮；
- 预览与下载分别写审计日志（`action=preview` / `action=download`）。

## 七、配置项

| 环境变量 | 默认值 | 说明 |
| --- | --- | --- |
| `GSP_ENFORCE_QUALIFICATION` | `true` | 交易准入校验总开关 |
| `GSP_STRICT_QUALIFICATION` | `false` | 严格模式：未建档主体同样禁止交易 |
| `GSP_EXPIRY_WARNING_DAYS` | `90` | 「即将到期」阈值（天） |
| `S3_*` | 见 `.env.example` | 对象存储连接参数 |

## 八、验证

```bash
cd api && .venv/bin/python -m pytest -q
cd frontend && npm run build
cd frontend && npx playwright test
cd frontend && npx playwright test --config playwright.live.config.ts
```

运行环境实测（`medsalesdb`）已验证：过期证照下单被拦截 → 换证改期自动回到待审核 →
复审通过后下单成功 → 拦截与审核记录均可在操作日志中查询。
