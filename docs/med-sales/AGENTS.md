# AGENTS.md

本文件为在本仓库工作的编码代理提供约定，修改代码前请先阅读。

## 前端

### 分页控件（强制）

- **所有列表页的分页控件一律靠左布局，不得靠右。** 包括「每页条数」选择器在内，整体位于分页栏**左侧**。
- 分页栏内的顺序固定为：**每页条数 → 总数 → 上一页/页码/下一页**，即 Element Plus
  `layout="total, sizes, prev, pager, next"`。
- 每页条数选项统一为 `[10, 20, 50, 100]`，默认 `20`。
- 实现要求：
  - 分页根元素的 `.pagination` 样式使用 `justify-content: flex-start`（不要写 `flex-end`/`space-between`）。
  - 全局兜底规则位于 `frontend/src/styles.css`：`.el-pagination { justify-content: flex-start; }`。
  - 新增列表页时必须带分页控件，并遵循上述对齐与顺序。
- 行为要求：切换筛选条件 / 每页条数时回到第 1 页；分页数据来自服务端（`page` / `size` / `total`）。

### 页面标题与操作区

- 页面标题**只出现在顶栏**（`MainLayout` 的 `.header-title`），页面内的 `el-card` 不再重复显示同名标题。
- `新增` 等操作按钮与筛选/查询按钮放在**同一行**（统一使用 `frontend/src/styles.css` 的 `.page-toolbar` /
  `.page-toolbar-actions`：筛选在左、操作在右）；筛选条件换行时，操作按钮与「查询」底对齐。
- 例外：页面内的**区块标题**（如经营看板「月度销售趋势」、销售报表「每日/月度销售汇总」）应保留。

### 表格布局（避免换行）

- 表格单元格统一**单行显示**：由 `frontend/src/main.ts` 的 Element Plus 全局配置
  `table: { showOverflowTooltip: true }` 兜底，长文本以省略号截断、悬停显示完整内容，
  不允许把行高撑成多行。
- 「操作」列必须显式写 `:show-overflow-tooltip="false"`：按钮宁可换行，也不能被省略号裁掉。
- 名称类列（供应商/客户/商品/员工等）要留足宽度，避免常见内容一进入就被截断；
  调宽前先在运行环境实测（比较 `.cell` 的 `scrollWidth` 与 `clientWidth`），不要凭感觉给数字。

### 统一业务对象选择控件（强制）

- 选择客户 / 商品 / 分类 / 厂家 / 供应商 / 仓库 / 员工 / 部门，统一用
  `frontend/src/components/EntitySelect.vue` 或其薄封装（`CustomerSelect.vue`、`ProductSelect.vue`
  …），不要在页面里各自写 `el-select` 并各自拉列表。
- 候选数据只来自 `GET /api/options/{entity}`：**登录即可访问，只返回 id / 编码 / 名称**，
  由 `frontend/src/utils/catalogOptions.ts` 全站缓存（整场会话只拉一次），
  主数据变更后调用 `refreshEntityOptions()` 失效。
- **不要拿管理页列表接口（`/customers`、`/products`、`/employees` …）当候选数据源**：
  它们需要 `xxx:view` 权限、且会带出商品成本价、客户联系方式等敏感字段
  （原因与约束见 `docs/权限控制说明.md` §1.1）。

## 验证

- 前端构建：`cd frontend && npm run build`
- 前端 E2E（隔离环境）：`cd frontend && npx playwright test`
- **针对运行中部署的验证（默认必做）：`cd frontend && npx playwright test --config playwright.live.config.ts`**

### 交付前必须重建本机部署

- 只跑隔离环境（自带后端 + dev server）**不算验证完成**。改了后端或前端代码后，必须先重建本机
  Docker 部署，再基于运行环境验证：

  ```bash
  docker compose up -d --build medsales-api medsales-web
  curl -s http://127.0.0.1:8088/                       # 前端 http://127.0.0.1:8088
  curl -s http://127.0.0.1:8001/openapi.json | head    # 后端 http://127.0.0.1:8001
  cd frontend && npx playwright test --config playwright.live.config.ts
  ```

- 判断部署是否真的更新：用构建产物哈希核对（`docker exec medsales-web sh -c "ls /usr/share/nginx/html/assets"`），
  或直接 curl 页面引用的 chunk；否则很容易出现「源码已改、8088 还是旧界面」的假验证。
- 面向运行环境的界面回归用例放在 `frontend/tests/live/`。
