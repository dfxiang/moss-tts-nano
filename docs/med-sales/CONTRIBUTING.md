# 贡献指南

感谢你愿意为本项目出力。下面是环境要求、改动流程与提交前的检查项。

## 仓库与沟通

- 公开仓库托管在 **GitHub**：https://github.com/dfxiang/med-sales ——它是本项目的发布镜像；
  主要开发在内网 GitLab 上进行，改动会定期同步到公开仓库。
- 提 Issue 前请先搜索是否已有同类问题。报告问题时请附上：提交号或版本、复现步骤、期望结果与实际结果、相关日志。
- 安全漏洞请不要公开提 Issue，请按 [SECURITY.md](SECURITY.md) 的渠道私下报告。

## 环境要求

| 组件 | 版本 | 说明 |
| --- | --- | --- |
| Python | 3.12+ | 后端与 `db/` 造数脚本 |
| Node.js | 20+ | 前端构建（镜像内使用 Node 24） |
| PostgreSQL | 17（UTF-8 + 中文拼音排序 ICU `zh-u-co-pinyin`） | 默认连接 `127.0.0.1:5688`；安装与排序配置见[数据库部署与配置](docs/数据库部署与配置.md) |
| Docker + Compose v2 | 最新稳定版 | 容器化部署与运行环境回归 |

## 本地开发

```bash
# 起数据库（自带 PostgreSQL 17 + MinIO）
docker compose up -d medsales-db
cd db && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python run_all.py && cd ..

# 后端
cd api
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env                                   # 按实际数据库连接修改
.venv/bin/python scripts/create_admin.py --username admin --password admin123
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000

# 前端
cd frontend
npm install
npm run dev                                            # http://127.0.0.1:5273
```

## 提交前必须通过

```bash
cd api && .venv/bin/python -m pytest -q                 # 后端接口测试
cd frontend && npm run build                            # 前端构建
cd frontend && npx playwright test                      # 隔离环境 E2E
```

改动了后端或前端代码后，还需要重建本机 Docker 部署，并基于运行环境回归：

```bash
docker compose up -d --build medsales-api medsales-web
cd frontend && npx playwright test --config playwright.live.config.ts
```

> 判定部署是否真的更新：核对构建产物哈希
> （`docker exec medsales-web sh -c "ls /usr/share/nginx/html/assets"`），避免「源码已改、8088 还是旧界面」的假验证。

## 代码约定

- **提交信息**：`类型(范围): 说明`，例如 `fix(库存流水): 商品筛选改为可选可搜的下拉`。
  常用类型 `feat` / `fix` / `perf` / `refactor` / `test` / `docs` / `style` / `chore`；
  一个提交只做一件事，说明写清「为什么改」。
- **接口变更**：同步更新 `docs/API接口文档.md`（`api/scripts/gen_api_docs.py` 可重新生成）。
- **Python**：PEP 8、类型标注齐全、路由与会话全异步。
- **前端**：Vue 3 组合式 API + TypeScript；列表页必须带分页控件且分页栏**靠左**
  （顺序：每页条数 → 总数 → 页码），见 [AGENTS.md](AGENTS.md)。
- **统一选择控件**：选择客户/商品/分类/厂家/供应商/仓库/员工/部门时使用
  `frontend/src/components/EntitySelect.vue`，候选数据只来自 `GET /api/options/{entity}`，
  不要拿管理页列表接口当候选数据源（原因见 [docs/权限控制说明.md](docs/权限控制说明.md)）。
- **不要提交**密钥、真实客户/员工数据、生产环境地址；演示数据一律由 `db/` 下的脚本生成。

## 许可

本项目采用 **Apache-2.0 + Commons Clause**（见 [LICENSE](LICENSE)）。
你提交的贡献将按同一许可分发；请确认你有权提交这些代码。
