# 安全策略

## 报告漏洞

请不要用公开 Issue 报告安全问题。请优先使用 GitHub 的私密漏洞报告
（仓库 **Security → Report a vulnerability**：
https://github.com/dfxiang/med-sales/security/advisories/new ，
需要在仓库 Settings → Code security 中开启 Private vulnerability reporting），
或发送邮件到 `4198166@qq.com`（微信同号：`4198166`）。

报告时请尽量提供：受影响的提交号 / 版本、复现步骤或 PoC、影响范围与利用前提。
我们会在 7 个工作日内回复，确认后在修复版本中说明并致谢（如你愿意署名）。

## 支持范围

只有 `main` 分支的最新代码会收到安全修复。本项目按「原样」提供，不承诺 SLA。

## 自托管安全清单（部署方必读）

- 改掉所有默认凭据：`JWT_SECRET`、数据库口令、MinIO 的 `MINIO_ROOT_USER` /
  `MINIO_ROOT_PASSWORD`；初始管理员账号首次登录后立即修改密码。
- 不要把 `CORS_ORIGINS` 留成 `*`，按实际域名收紧。
- 只通过 HTTPS 暴露前端入口，`/api` 由 nginx 同源反向代理到后端容器。
- `SYS_API_KEYS`（系统对接用的 API Key）只发给可信系统；怀疑泄露时立即轮换
  ——支持同时配置新旧两个 Key，可平滑切换。
- 生产环境不要使用仓库中的演示数据脚本；`/docs`（Swagger）与开放接口建议在生产
  关闭或加访问控制。
- 定期备份业务数据库与对象存储（MinIO）bucket。

## 已知设计取舍

- **JWT 为无状态令牌**（默认有效期 1440 分钟）：服务端不维护吊销列表，前端退出登录
  只是清除本地令牌；如需让全部已签发令牌立即失效，请轮换 `JWT_SECRET`。
- **权限校验在后端**：前端 `v-permission` 只做交互收敛，真正的拦截在
  `require_permission`（见 [docs/权限控制说明.md](docs/权限控制说明.md)）。
- **对象存储为私有 bucket**：证照扫描件不通过预签名 URL 直连，而是由 API 取回后
  流式回传（容器内主机名浏览器不可达）。
