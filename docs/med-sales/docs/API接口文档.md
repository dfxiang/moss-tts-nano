# 医药销售管理系统 API 接口文档

> 自动生成：基于 OpenAPI 规范（FastAPI）

## 一、文档说明

| 项目 | 说明 |
| --- | --- |
| 接口版本 | 0.1.0 |
| 基础地址（容器部署） | http://127.0.0.1:8001/api |
| 基础地址（本地开发） | http://127.0.0.1:8000/api |
| 数据格式 | JSON（UTF-8） |
| 在线文档 | http://127.0.0.1:8001/docs（Swagger UI） |

### 1. 认证方式

除「登录」「健康检查」「通过 API Key 获取令牌」外，所有接口均需携带令牌：

```
Authorization: Bearer <access_token>
```

令牌获取方式：

1. 用户登录：`POST /api/auth/login`（用户名 + 密码）
2. 系统对接：`POST /api/auth/token`（环境变量 SYS_API_KEYS 配置的 API Key + 用户 ID）

### 2. 分页参数

| 参数 | 类型 | 必填 | 默认 | 说明 |
| --- | --- | --- | --- | --- |
| page | 整数 | 否 | 1 | 页码，从 1 开始 |
| size | 整数 | 否 | 20 | 每页条数，最大 200 |

分页响应结构：

```json
{"items": [], "total": 0, "page": 1, "size": 20}
```

### 3. 错误响应

接口错误统一返回：`{"detail": "错误描述"}`，常见状态码：

| 状态码 | 含义 |
| --- | --- |
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 / 业务规则不满足 |
| 401 | 未认证或令牌无效 / API Key 无效 |
| 403 | 已登录但缺少接口所需权限 |
| 404 | 资源不存在 |
| 422 | 请求体校验失败 |

### 4. 权限校验

接口在鉴权之外还会做**权限校验**：账号需经角色继承到对应权限编码，否则返回 403。

- 权限编码约定：`模块:动作` 或 `模块:对象:动作`，例如 `sales:view`、`system:user:manage`；
- 内置通配权限 `all`（绑定在「管理员」角色上）：拥有它即可访问全部接口；
- 当前登录账号的权限编码可调用 `GET /api/auth/me` 获取（返回 `permissions` 数组）；
- 权限清单由 `permissions` 表维护，接口启动时会幂等补齐内置清单，详见 [权限控制说明](./权限控制说明.md)。

---

## 二、接口索引

| 模块 | 接口数 |
| --- | --- |
| 一、认证 | 7 |
| 头像 | 1 |
| 二、系统管理 | 19 |
| 三、组织与员工 | 10 |
| 四、客户管理 | 5 |
| 五、商品管理 | 17 |
| 六、供应商管理 | 5 |
| 七、仓库管理 | 5 |
| 八、采购管理 | 6 |
| 九、销售管理 | 6 |
| 十、库存管理 | 5 |
| 十一、退货管理 | 5 |
| 十二、财务与收款 | 5 |
| 十三、报表与分析 | 8 |
| 十四、GSP 合规 | 21 |
| 健康检查 | 1 |

---

## 一、认证

| 方法 | 路径 | 接口名称 | 认证 | 所需权限 |
| --- | --- | --- | --- | --- |
| POST | `/api/auth/login` | 登录获取令牌 | 不需要 | — |
| GET | `/api/auth/me` | 获取当前登录用户信息（含权限编码） | 需要 | — |
| PUT | `/api/auth/me` | 更新当前用户个人资料 | 需要 | — |
| PUT | `/api/auth/me/password` | 修改当前用户登录密码 | 需要 | — |
| PUT | `/api/auth/me/avatar` | 上传/更换当前用户头像 | 需要 | — |
| DELETE | `/api/auth/me/avatar` | 恢复默认头像 | 需要 | — |
| POST | `/api/auth/token` | 通过 API Key + 用户 ID 获取令牌（系统对接） | 不需要 | — |

### POST /api/auth/login

**接口名称：** 登录获取令牌

**认证：** 不需要

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| username | 字符串 | 是 | 用户名 |
| password | 字符串 | 是 | 密码 |

**请求示例：**

```json
{
  "username": "string",
  "password": "string"
}
```

**响应示例（200/201）：**

```json
{
  "access_token": "string",
  "token_type": "bearer"
}
```

---

### GET /api/auth/me

**接口名称：** 获取当前登录用户信息（含权限编码）

**说明：** 返回当前用户的角色与扁平化权限编码，前端据此控制菜单、路由与按钮。

**认证：** 需要 Bearer Token

**响应示例（200/201）：**

```json
{
  "display_name": "string",
  "phone": "string",
  "email": "string",
  "id": 0,
  "username": "string",
  "employee_id": 0,
  "is_active": false,
  "created_at": "2026-09-01T00:00:00",
  "avatar_url": "string",
  "roles": [],
  "permissions": [],
  "is_superuser": false
}
```

---

### PUT /api/auth/me

**接口名称：** 更新当前用户个人资料

**说明：** 自助改资料：只能改自己、只能改"除用户名外"的资料字段。

**认证：** 需要 Bearer Token

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| display_name | 字符串 | 否 | 显示名称 |
| phone | 字符串 | 否 | 电话 |
| email | 字符串 | 否 | 邮箱 |

**请求示例：**

```json
{
  "display_name": "string",
  "phone": "string",
  "email": "string"
}
```

**响应示例（200/201）：**

```json
{
  "display_name": "string",
  "phone": "string",
  "email": "string",
  "id": 0,
  "username": "string",
  "employee_id": 0,
  "is_active": false,
  "created_at": "2026-09-01T00:00:00",
  "avatar_url": "string",
  "roles": [],
  "permissions": [],
  "is_superuser": false
}
```

---

### PUT /api/auth/me/password

**接口名称：** 修改当前用户登录密码

**说明：** 自助改密：校验原密码 + 新密码两次确认一致，并记录审计日志。

**认证：** 需要 Bearer Token

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| old_password | 字符串 | 是 | 原密码 |
| new_password | 字符串 | 是 | 新密码 |
| confirm_password | 字符串 | 是 | 确认新密码 |

**请求示例：**

```json
{
  "old_password": "string",
  "new_password": "string",
  "confirm_password": "string"
}
```

**响应示例（200/201）：**

```json
{
  "message": "string"
}
```

---

### PUT /api/auth/me/avatar

**接口名称：** 上传/更换当前用户头像

**说明：** 自助上传头像：服务端统一规范化为 256×256 PNG 后再入库（见设计文档 §5.5）。

**认证：** 需要 Bearer Token

**响应示例（200/201）：**

```json
{
  "display_name": "string",
  "phone": "string",
  "email": "string",
  "id": 0,
  "username": "string",
  "employee_id": 0,
  "is_active": false,
  "created_at": "2026-09-01T00:00:00",
  "avatar_url": "string",
  "roles": [],
  "permissions": [],
  "is_superuser": false
}
```

---

### DELETE /api/auth/me/avatar

**接口名称：** 恢复默认头像

**说明：** 清空头像（回落默认头像）；幂等：本来就没有头像时不写审计。

**认证：** 需要 Bearer Token

**响应示例（200/201）：**

```json
{
  "display_name": "string",
  "phone": "string",
  "email": "string",
  "id": 0,
  "username": "string",
  "employee_id": 0,
  "is_active": false,
  "created_at": "2026-09-01T00:00:00",
  "avatar_url": "string",
  "roles": [],
  "permissions": [],
  "is_superuser": false
}
```

---

### POST /api/auth/token

**接口名称：** 通过 API Key + 用户 ID 获取令牌（系统对接）

**说明：** 系统间对接：使用环境变量配置的 API Key + 用户 ID 换取 JWT，效果等同登录。

**认证：** 不需要

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| api_key | 字符串 | 是 | API Key |
| user_id | 整数 | 是 | 用户 ID |

**请求示例：**

```json
{
  "api_key": "string",
  "user_id": 0
}
```

**响应示例（200/201）：**

```json
{
  "access_token": "string",
  "token_type": "bearer"
}
```

---

## 头像

| 方法 | 路径 | 接口名称 | 认证 | 所需权限 |
| --- | --- | --- | --- | --- |
| GET | `/api/avatars/{filename}` | 读取头像（匿名访问） | 不需要 | — |

### GET /api/avatars/{filename}

**接口名称：** 读取头像（匿名访问）

**认证：** 不需要

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| filename | 路径 | 字符串 | 是 |  |  |

---

## 二、系统管理

| 方法 | 路径 | 接口名称 | 认证 | 所需权限 |
| --- | --- | --- | --- | --- |
| GET | `/api/users` | 用户列表 | 需要 | `system:user:view` |
| POST | `/api/users` | 创建用户 | 需要 | `system:user:manage` |
| GET | `/api/users/{user_id}` | 用户详情 | 需要 | `system:user:view` |
| PUT | `/api/users/{user_id}` | 更新用户 | 需要 | `system:user:manage` |
| DELETE | `/api/users/{user_id}` | 删除用户 | 需要 | `system:user:manage` |
| POST | `/api/users/{user_id}/reset-password` | 重置用户登录密码 | 需要 | `system:user:manage` |
| POST | `/api/users/{user_id}/roles` | 为用户分配角色 | 需要 | `system:user:manage` |
| GET | `/api/roles` | 角色列表 | 需要 | `system:role:view` |
| POST | `/api/roles` | 创建角色 | 需要 | `system:role:manage` |
| GET | `/api/roles/{role_id}` | 角色详情 | 需要 | `system:role:view` |
| PUT | `/api/roles/{role_id}` | 更新角色 | 需要 | `system:role:manage` |
| DELETE | `/api/roles/{role_id}` | 删除角色 | 需要 | `system:role:manage` |
| POST | `/api/roles/{role_id}/permissions` | 为角色分配权限 | 需要 | `system:role:manage` |
| GET | `/api/permissions` | 权限列表 | 需要 | `system:permission:view` |
| POST | `/api/permissions` | 创建权限 | 需要 | `system:permission:manage` |
| GET | `/api/permissions/{permission_id}` | 权限详情 | 需要 | `system:permission:view` |
| PUT | `/api/permissions/{permission_id}` | 更新权限 | 需要 | `system:permission:manage` |
| DELETE | `/api/permissions/{permission_id}` | 删除权限 | 需要 | `system:permission:manage` |
| GET | `/api/audit-logs` | 操作日志列表 | 需要 | `system:log:view` |

### GET /api/users

**接口名称：** 用户列表

**认证：** 需要 Bearer Token

**所需权限：** `system:user:view`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| keyword | 查询 | 字符串 | 否 |  | 关键词 |
| page | 查询 | 整数 | 否 | 1 | 页码，从 1 开始 |
| size | 查询 | 整数 | 否 | 20 | 每页条数，1-1000 |

**响应示例（200/201）：**

```json
{
  "items": [
    {
      "display_name": "string",
      "phone": "string",
      "email": "string",
      "id": 0,
      "username": "string",
      "employee_id": 0,
      "is_active": false,
      "created_at": "2026-09-01T00:00:00",
      "avatar_url": "string",
      "roles": []
    }
  ],
  "total": 0,
  "page": 0,
  "size": 0
}
```

---

### POST /api/users

**接口名称：** 创建用户

**认证：** 需要 Bearer Token

**所需权限：** `system:user:manage`

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| display_name | 字符串 | 否 | 显示名称 |
| phone | 字符串 | 否 | 电话 |
| email | 字符串 | 否 | 邮箱 |
| username | 字符串 | 是 | 用户名 |
| password | 字符串 | 是 | 密码 |
| employee_id | 整数 | 否 | 员工 ID |
| is_active | 布尔 | 否 | 是否启用 |

**请求示例：**

```json
{
  "display_name": "string",
  "phone": "string",
  "email": "string",
  "username": "string",
  "password": "string",
  "employee_id": 0,
  "is_active": true
}
```

**响应示例（200/201）：**

```json
{
  "display_name": "string",
  "phone": "string",
  "email": "string",
  "id": 0,
  "username": "string",
  "employee_id": 0,
  "is_active": false,
  "created_at": "2026-09-01T00:00:00",
  "avatar_url": "string",
  "roles": []
}
```

---

### GET /api/users/{user_id}

**接口名称：** 用户详情

**认证：** 需要 Bearer Token

**所需权限：** `system:user:view`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| user_id | 路径 | 整数 | 是 |  | 用户 ID |

**响应示例（200/201）：**

```json
{
  "display_name": "string",
  "phone": "string",
  "email": "string",
  "id": 0,
  "username": "string",
  "employee_id": 0,
  "is_active": false,
  "created_at": "2026-09-01T00:00:00",
  "avatar_url": "string",
  "roles": []
}
```

---

### PUT /api/users/{user_id}

**接口名称：** 更新用户

**认证：** 需要 Bearer Token

**所需权限：** `system:user:manage`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| user_id | 路径 | 整数 | 是 |  | 用户 ID |

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| display_name | 字符串 | 否 | 显示名称 |
| phone | 字符串 | 否 | 电话 |
| email | 字符串 | 否 | 邮箱 |
| password | 字符串 | 否 | 密码 |
| employee_id | 整数 | 否 | 员工 ID |
| is_active | 布尔 | 否 | 是否启用 |

**请求示例：**

```json
{
  "display_name": "string",
  "phone": "string",
  "email": "string",
  "password": "string",
  "employee_id": 0,
  "is_active": false
}
```

**响应示例（200/201）：**

```json
{
  "display_name": "string",
  "phone": "string",
  "email": "string",
  "id": 0,
  "username": "string",
  "employee_id": 0,
  "is_active": false,
  "created_at": "2026-09-01T00:00:00",
  "avatar_url": "string",
  "roles": []
}
```

---

### DELETE /api/users/{user_id}

**接口名称：** 删除用户

**认证：** 需要 Bearer Token

**所需权限：** `system:user:manage`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| user_id | 路径 | 整数 | 是 |  | 用户 ID |

**响应示例（200/201）：**

```json
{
  "message": "string"
}
```

---

### POST /api/users/{user_id}/reset-password

**接口名称：** 重置用户登录密码

**说明：** 管理员重置密码：不校验原密码、不做二次确认（见设计文档 §4.4）。

该能力等价于"账号接管"，因此只对 system:user:manage 开放，并写独立审计 action。

**认证：** 需要 Bearer Token

**所需权限：** `system:user:manage`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| user_id | 路径 | 整数 | 是 |  | 用户 ID |

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| new_password | 字符串 | 是 | 新密码 |

**请求示例：**

```json
{
  "new_password": "string"
}
```

**响应示例（200/201）：**

```json
{
  "message": "string"
}
```

---

### POST /api/users/{user_id}/roles

**接口名称：** 为用户分配角色

**认证：** 需要 Bearer Token

**所需权限：** `system:user:manage`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| user_id | 路径 | 整数 | 是 |  | 用户 ID |

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| role_ids | 整数[] | 否 | role_ids |

**请求示例：**

```json
{
  "role_ids": []
}
```

**响应示例（200/201）：**

```json
{
  "display_name": "string",
  "phone": "string",
  "email": "string",
  "id": 0,
  "username": "string",
  "employee_id": 0,
  "is_active": false,
  "created_at": "2026-09-01T00:00:00",
  "avatar_url": "string",
  "roles": []
}
```

---

### GET /api/roles

**接口名称：** 角色列表

**认证：** 需要 Bearer Token

**所需权限：** `system:role:view`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| keyword | 查询 | 字符串 | 否 |  | 关键词 |
| page | 查询 | 整数 | 否 | 1 | 页码，从 1 开始 |
| size | 查询 | 整数 | 否 | 20 | 每页条数，1-1000 |

**响应示例（200/201）：**

```json
{
  "items": [
    {
      "id": 0,
      "name": "string",
      "description": "string",
      "created_at": "2026-09-01T00:00:00",
      "permissions": []
    }
  ],
  "total": 0,
  "page": 0,
  "size": 0
}
```

---

### POST /api/roles

**接口名称：** 创建角色

**认证：** 需要 Bearer Token

**所需权限：** `system:role:manage`

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| name | 字符串 | 是 | 名称 |
| description | 字符串 | 否 | 说明 |

**请求示例：**

```json
{
  "name": "string",
  "description": "string"
}
```

**响应示例（200/201）：**

```json
{
  "id": 0,
  "name": "string",
  "description": "string",
  "created_at": "2026-09-01T00:00:00",
  "permissions": []
}
```

---

### GET /api/roles/{role_id}

**接口名称：** 角色详情

**认证：** 需要 Bearer Token

**所需权限：** `system:role:view`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| role_id | 路径 | 整数 | 是 |  |  |

**响应示例（200/201）：**

```json
{
  "id": 0,
  "name": "string",
  "description": "string",
  "created_at": "2026-09-01T00:00:00",
  "permissions": []
}
```

---

### PUT /api/roles/{role_id}

**接口名称：** 更新角色

**认证：** 需要 Bearer Token

**所需权限：** `system:role:manage`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| role_id | 路径 | 整数 | 是 |  |  |

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| name | 字符串 | 否 | 名称 |
| description | 字符串 | 否 | 说明 |

**请求示例：**

```json
{
  "name": "string",
  "description": "string"
}
```

**响应示例（200/201）：**

```json
{
  "id": 0,
  "name": "string",
  "description": "string",
  "created_at": "2026-09-01T00:00:00",
  "permissions": []
}
```

---

### DELETE /api/roles/{role_id}

**接口名称：** 删除角色

**认证：** 需要 Bearer Token

**所需权限：** `system:role:manage`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| role_id | 路径 | 整数 | 是 |  |  |

**响应示例（200/201）：**

```json
{
  "message": "string"
}
```

---

### POST /api/roles/{role_id}/permissions

**接口名称：** 为角色分配权限

**认证：** 需要 Bearer Token

**所需权限：** `system:role:manage`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| role_id | 路径 | 整数 | 是 |  |  |

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| permission_ids | 整数[] | 否 | permission_ids |

**请求示例：**

```json
{
  "permission_ids": []
}
```

**响应示例（200/201）：**

```json
{
  "id": 0,
  "name": "string",
  "description": "string",
  "created_at": "2026-09-01T00:00:00",
  "permissions": []
}
```

---

### GET /api/permissions

**接口名称：** 权限列表

**认证：** 需要 Bearer Token

**所需权限：** `system:permission:view`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| keyword | 查询 | 字符串 | 否 |  | 关键词 |
| page | 查询 | 整数 | 否 | 1 | 页码，从 1 开始 |
| size | 查询 | 整数 | 否 | 20 | 每页条数，1-1000 |

**响应示例（200/201）：**

```json
{
  "items": [
    {
      "id": 0,
      "code": "string",
      "name": "string",
      "description": "string",
      "created_at": "2026-09-01T00:00:00"
    }
  ],
  "total": 0,
  "page": 0,
  "size": 0
}
```

---

### POST /api/permissions

**接口名称：** 创建权限

**认证：** 需要 Bearer Token

**所需权限：** `system:permission:manage`

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| code | 字符串 | 是 | 编码 |
| name | 字符串 | 是 | 名称 |
| description | 字符串 | 否 | 说明 |

**请求示例：**

```json
{
  "code": "string",
  "name": "string",
  "description": "string"
}
```

**响应示例（200/201）：**

```json
{
  "id": 0,
  "code": "string",
  "name": "string",
  "description": "string",
  "created_at": "2026-09-01T00:00:00"
}
```

---

### GET /api/permissions/{permission_id}

**接口名称：** 权限详情

**认证：** 需要 Bearer Token

**所需权限：** `system:permission:view`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| permission_id | 路径 | 整数 | 是 |  |  |

**响应示例（200/201）：**

```json
{
  "id": 0,
  "code": "string",
  "name": "string",
  "description": "string",
  "created_at": "2026-09-01T00:00:00"
}
```

---

### PUT /api/permissions/{permission_id}

**接口名称：** 更新权限

**认证：** 需要 Bearer Token

**所需权限：** `system:permission:manage`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| permission_id | 路径 | 整数 | 是 |  |  |

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| name | 字符串 | 否 | 名称 |
| description | 字符串 | 否 | 说明 |

**请求示例：**

```json
{
  "name": "string",
  "description": "string"
}
```

**响应示例（200/201）：**

```json
{
  "id": 0,
  "code": "string",
  "name": "string",
  "description": "string",
  "created_at": "2026-09-01T00:00:00"
}
```

---

### DELETE /api/permissions/{permission_id}

**接口名称：** 删除权限

**认证：** 需要 Bearer Token

**所需权限：** `system:permission:manage`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| permission_id | 路径 | 整数 | 是 |  |  |

**响应示例（200/201）：**

```json
{
  "message": "string"
}
```

---

### GET /api/audit-logs

**接口名称：** 操作日志列表

**认证：** 需要 Bearer Token

**所需权限：** `system:log:view`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| username | 查询 | 字符串 | 否 |  | 用户名 |
| module | 查询 | 字符串 | 否 |  |  |
| page | 查询 | 整数 | 否 | 1 | 页码，从 1 开始 |
| size | 查询 | 整数 | 否 | 20 | 每页条数，1-1000 |

**响应示例（200/201）：**

```json
{
  "items": [
    {
      "id": 0,
      "user_id": 0,
      "username": "string",
      "action": "string",
      "module": "string",
      "detail": "string",
      "ip": "string",
      "created_at": "2026-09-01T00:00:00"
    }
  ],
  "total": 0,
  "page": 0,
  "size": 0
}
```

---

## 三、组织与员工

| 方法 | 路径 | 接口名称 | 认证 | 所需权限 |
| --- | --- | --- | --- | --- |
| GET | `/api/departments` | 部门列表 | 需要 | `org:department:view` |
| POST | `/api/departments` | 创建部门 | 需要 | `org:department:manage` |
| GET | `/api/departments/{department_id}` | 部门详情 | 需要 | `org:department:view` |
| PUT | `/api/departments/{department_id}` | 更新部门 | 需要 | `org:department:manage` |
| DELETE | `/api/departments/{department_id}` | 删除部门 | 需要 | `org:department:manage` |
| GET | `/api/employees` | 员工列表 | 需要 | `org:employee:view` |
| POST | `/api/employees` | 创建员工 | 需要 | `org:employee:manage` |
| GET | `/api/employees/{employee_id}` | 员工详情 | 需要 | `org:employee:view` |
| PUT | `/api/employees/{employee_id}` | 更新员工 | 需要 | `org:employee:manage` |
| DELETE | `/api/employees/{employee_id}` | 删除员工 | 需要 | `org:employee:manage` |

### GET /api/departments

**接口名称：** 部门列表

**认证：** 需要 Bearer Token

**所需权限：** `org:department:view`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| keyword | 查询 | 字符串 | 否 |  | 关键词 |
| page | 查询 | 整数 | 否 | 1 | 页码，从 1 开始 |
| size | 查询 | 整数 | 否 | 20 | 每页条数，1-1000 |

**响应示例（200/201）：**

```json
{
  "items": [
    {
      "id": 0,
      "code": "string",
      "name": "string",
      "description": "string",
      "created_at": "2026-09-01T00:00:00"
    }
  ],
  "total": 0,
  "page": 0,
  "size": 0
}
```

---

### POST /api/departments

**接口名称：** 创建部门

**认证：** 需要 Bearer Token

**所需权限：** `org:department:manage`

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| code | 字符串 | 是 | 编码 |
| name | 字符串 | 是 | 名称 |
| description | 字符串 | 否 | 说明 |

**请求示例：**

```json
{
  "code": "string",
  "name": "string",
  "description": "string"
}
```

**响应示例（200/201）：**

```json
{
  "id": 0,
  "code": "string",
  "name": "string",
  "description": "string",
  "created_at": "2026-09-01T00:00:00"
}
```

---

### GET /api/departments/{department_id}

**接口名称：** 部门详情

**认证：** 需要 Bearer Token

**所需权限：** `org:department:view`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| department_id | 路径 | 整数 | 是 |  | 部门 ID |

**响应示例（200/201）：**

```json
{
  "id": 0,
  "code": "string",
  "name": "string",
  "description": "string",
  "created_at": "2026-09-01T00:00:00"
}
```

---

### PUT /api/departments/{department_id}

**接口名称：** 更新部门

**认证：** 需要 Bearer Token

**所需权限：** `org:department:manage`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| department_id | 路径 | 整数 | 是 |  | 部门 ID |

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| code | 字符串 | 否 | 编码 |
| name | 字符串 | 否 | 名称 |
| description | 字符串 | 否 | 说明 |

**请求示例：**

```json
{
  "code": "string",
  "name": "string",
  "description": "string"
}
```

**响应示例（200/201）：**

```json
{
  "id": 0,
  "code": "string",
  "name": "string",
  "description": "string",
  "created_at": "2026-09-01T00:00:00"
}
```

---

### DELETE /api/departments/{department_id}

**接口名称：** 删除部门

**认证：** 需要 Bearer Token

**所需权限：** `org:department:manage`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| department_id | 路径 | 整数 | 是 |  | 部门 ID |

**响应示例（200/201）：**

```json
{
  "message": "string"
}
```

---

### GET /api/employees

**接口名称：** 员工列表

**认证：** 需要 Bearer Token

**所需权限：** `org:employee:view`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| department_id | 查询 | 整数 | 否 |  | 部门 ID |
| keyword | 查询 | 字符串 | 否 |  | 关键词 |
| employment_status | 查询 | 字符串 | 否 |  | 在职状态 |
| page | 查询 | 整数 | 否 | 1 | 页码，从 1 开始 |
| size | 查询 | 整数 | 否 | 20 | 每页条数，1-1000 |

**响应示例（200/201）：**

```json
{
  "items": [
    {
      "id": 0,
      "code": "string",
      "name": "string",
      "gender": "string",
      "phone": "string",
      "email": "string",
      "department_id": 0,
      "position": "string",
      "manager_id": 0,
      "hire_date": "2026-01-01",
      "employment_status": "string",
      "created_at": "2026-09-01T00:00:00"
    }
  ],
  "total": 0,
  "page": 0,
  "size": 0
}
```

---

### POST /api/employees

**接口名称：** 创建员工

**认证：** 需要 Bearer Token

**所需权限：** `org:employee:manage`

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| code | 字符串 | 是 | 编码 |
| name | 字符串 | 是 | 名称 |
| gender | 字符串 | 否 | 性别 |
| phone | 字符串 | 否 | 电话 |
| email | 字符串 | 否 | 邮箱 |
| department_id | 整数 | 是 | 部门 ID |
| position | 字符串 | 否 | 职位 |
| manager_id | 整数 | 否 | 上级员工 ID |
| hire_date | 日期 | 是 | 入职日期 |
| employment_status | 字符串 | 否 | 在职状态 |

**请求示例：**

```json
{
  "code": "string",
  "name": "string",
  "gender": "string",
  "phone": "string",
  "email": "string",
  "department_id": 0,
  "position": "string",
  "manager_id": 0,
  "hire_date": "2026-01-01",
  "employment_status": "在职"
}
```

**响应示例（200/201）：**

```json
{
  "id": 0,
  "code": "string",
  "name": "string",
  "gender": "string",
  "phone": "string",
  "email": "string",
  "department_id": 0,
  "position": "string",
  "manager_id": 0,
  "hire_date": "2026-01-01",
  "employment_status": "string",
  "created_at": "2026-09-01T00:00:00"
}
```

---

### GET /api/employees/{employee_id}

**接口名称：** 员工详情

**认证：** 需要 Bearer Token

**所需权限：** `org:employee:view`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| employee_id | 路径 | 整数 | 是 |  | 员工 ID |

**响应示例（200/201）：**

```json
{
  "id": 0,
  "code": "string",
  "name": "string",
  "gender": "string",
  "phone": "string",
  "email": "string",
  "department_id": 0,
  "position": "string",
  "manager_id": 0,
  "hire_date": "2026-01-01",
  "employment_status": "string",
  "created_at": "2026-09-01T00:00:00"
}
```

---

### PUT /api/employees/{employee_id}

**接口名称：** 更新员工

**认证：** 需要 Bearer Token

**所需权限：** `org:employee:manage`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| employee_id | 路径 | 整数 | 是 |  | 员工 ID |

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| name | 字符串 | 否 | 名称 |
| gender | 字符串 | 否 | 性别 |
| phone | 字符串 | 否 | 电话 |
| email | 字符串 | 否 | 邮箱 |
| department_id | 整数 | 否 | 部门 ID |
| position | 字符串 | 否 | 职位 |
| manager_id | 整数 | 否 | 上级员工 ID |
| hire_date | 日期 | 否 | 入职日期 |
| employment_status | 字符串 | 否 | 在职状态 |

**请求示例：**

```json
{
  "name": "string",
  "gender": "string",
  "phone": "string",
  "email": "string",
  "department_id": 0,
  "position": "string",
  "manager_id": 0,
  "hire_date": "2026-01-01",
  "employment_status": "string"
}
```

**响应示例（200/201）：**

```json
{
  "id": 0,
  "code": "string",
  "name": "string",
  "gender": "string",
  "phone": "string",
  "email": "string",
  "department_id": 0,
  "position": "string",
  "manager_id": 0,
  "hire_date": "2026-01-01",
  "employment_status": "string",
  "created_at": "2026-09-01T00:00:00"
}
```

---

### DELETE /api/employees/{employee_id}

**接口名称：** 删除员工

**认证：** 需要 Bearer Token

**所需权限：** `org:employee:manage`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| employee_id | 路径 | 整数 | 是 |  | 员工 ID |

**响应示例（200/201）：**

```json
{
  "message": "string"
}
```

---

## 四、客户管理

| 方法 | 路径 | 接口名称 | 认证 | 所需权限 |
| --- | --- | --- | --- | --- |
| GET | `/api/customers` | 客户列表 | 需要 | — |
| POST | `/api/customers` | 创建客户 | 需要 | — |
| GET | `/api/customers/{customer_id}` | 客户详情 | 需要 | `customer:view` |
| PUT | `/api/customers/{customer_id}` | 更新客户 | 需要 | `customer:manage` |
| DELETE | `/api/customers/{customer_id}` | 删除客户 | 需要 | `customer:manage` |

### GET /api/customers

**接口名称：** 客户列表

**认证：** 需要 Bearer Token

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| keyword | 查询 | 字符串 | 否 |  | 关键词 |
| customer_type | 查询 | 字符串 | 否 |  | 客户类型 |
| coop_level | 查询 | 字符串 | 否 |  | 合作等级 |
| status | 查询 | 字符串 | 否 |  | 状态 |
| province | 查询 | 字符串 | 否 |  | 省份 |
| page | 查询 | 整数 | 否 | 1 | 页码，从 1 开始 |
| size | 查询 | 整数 | 否 | 20 | 每页条数，1-1000 |

**响应示例（200/201）：**

```json
{
  "items": [
    {
      "id": 0,
      "code": "string",
      "name": "string",
      "customer_type": "string",
      "coop_level": "string",
      "contact_person": "string",
      "phone": "string",
      "email": "string",
      "province": "string",
      "city": "string",
      "address": "string",
      "license_no": "string",
      "credit_limit": 0.0,
      "status": "string",
      "remark": "string",
      "created_at": "2026-09-01T00:00:00"
    }
  ],
  "total": 0,
  "page": 0,
  "size": 0
}
```

---

### POST /api/customers

**接口名称：** 创建客户

**认证：** 需要 Bearer Token

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| code | 字符串 | 是 | 编码 |
| name | 字符串 | 是 | 名称 |
| customer_type | 字符串 | 否 | 客户类型 |
| coop_level | 字符串 | 否 | 合作等级 |
| contact_person | 字符串 | 否 | 联系人 |
| phone | 字符串 | 否 | 电话 |
| email | 字符串 | 否 | 邮箱 |
| province | 字符串 | 否 | 省份 |
| city | 字符串 | 否 | 城市 |
| address | 字符串 | 否 | 地址 |
| license_no | 字符串 | 否 | 证照编号 |
| credit_limit | 数值 | 否 | 信用额度 |
| status | 字符串 | 否 | 状态 |
| remark | 字符串 | 否 | 备注 |

**请求示例：**

```json
{
  "code": "string",
  "name": "string",
  "customer_type": "单体药房",
  "coop_level": "普通客户",
  "contact_person": "string",
  "phone": "string",
  "email": "string",
  "province": "string",
  "city": "string",
  "address": "string",
  "license_no": "string",
  "credit_limit": 0,
  "status": "正常",
  "remark": "string"
}
```

**响应示例（200/201）：**

```json
{
  "id": 0,
  "code": "string",
  "name": "string",
  "customer_type": "string",
  "coop_level": "string",
  "contact_person": "string",
  "phone": "string",
  "email": "string",
  "province": "string",
  "city": "string",
  "address": "string",
  "license_no": "string",
  "credit_limit": 0.0,
  "status": "string",
  "remark": "string",
  "created_at": "2026-09-01T00:00:00"
}
```

---

### GET /api/customers/{customer_id}

**接口名称：** 客户详情

**认证：** 需要 Bearer Token

**所需权限：** `customer:view`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| customer_id | 路径 | 整数 | 是 |  | 客户 ID |

**响应示例（200/201）：**

```json
{
  "id": 0,
  "code": "string",
  "name": "string",
  "customer_type": "string",
  "coop_level": "string",
  "contact_person": "string",
  "phone": "string",
  "email": "string",
  "province": "string",
  "city": "string",
  "address": "string",
  "license_no": "string",
  "credit_limit": 0.0,
  "status": "string",
  "remark": "string",
  "created_at": "2026-09-01T00:00:00"
}
```

---

### PUT /api/customers/{customer_id}

**接口名称：** 更新客户

**认证：** 需要 Bearer Token

**所需权限：** `customer:manage`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| customer_id | 路径 | 整数 | 是 |  | 客户 ID |

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| name | 字符串 | 否 | 名称 |
| customer_type | 字符串 | 否 | 客户类型 |
| coop_level | 字符串 | 否 | 合作等级 |
| contact_person | 字符串 | 否 | 联系人 |
| phone | 字符串 | 否 | 电话 |
| email | 字符串 | 否 | 邮箱 |
| province | 字符串 | 否 | 省份 |
| city | 字符串 | 否 | 城市 |
| address | 字符串 | 否 | 地址 |
| license_no | 字符串 | 否 | 证照编号 |
| credit_limit | 数值 | 否 | 信用额度 |
| status | 字符串 | 否 | 状态 |
| remark | 字符串 | 否 | 备注 |

**请求示例：**

```json
{
  "name": "string",
  "customer_type": "string",
  "coop_level": "string",
  "contact_person": "string",
  "phone": "string",
  "email": "string",
  "province": "string",
  "city": "string",
  "address": "string",
  "license_no": "string",
  "credit_limit": 0.0,
  "status": "string",
  "remark": "string"
}
```

**响应示例（200/201）：**

```json
{
  "id": 0,
  "code": "string",
  "name": "string",
  "customer_type": "string",
  "coop_level": "string",
  "contact_person": "string",
  "phone": "string",
  "email": "string",
  "province": "string",
  "city": "string",
  "address": "string",
  "license_no": "string",
  "credit_limit": 0.0,
  "status": "string",
  "remark": "string",
  "created_at": "2026-09-01T00:00:00"
}
```

---

### DELETE /api/customers/{customer_id}

**接口名称：** 删除客户

**认证：** 需要 Bearer Token

**所需权限：** `customer:manage`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| customer_id | 路径 | 整数 | 是 |  | 客户 ID |

**响应示例（200/201）：**

```json
{
  "message": "string"
}
```

---

## 五、商品管理

| 方法 | 路径 | 接口名称 | 认证 | 所需权限 |
| --- | --- | --- | --- | --- |
| GET | `/api/categories` | 商品分类列表 | 需要 | `product:view` |
| POST | `/api/categories` | 创建商品分类 | 需要 | `product:manage` |
| GET | `/api/categories/{category_id}` | 商品分类详情 | 需要 | `product:view` |
| PUT | `/api/categories/{category_id}` | 更新商品分类 | 需要 | `product:manage` |
| DELETE | `/api/categories/{category_id}` | 删除商品分类 | 需要 | `product:manage` |
| GET | `/api/manufacturers` | 生产厂家列表 | 需要 | `product:view` |
| POST | `/api/manufacturers` | 创建厂家 | 需要 | `product:manage` |
| GET | `/api/manufacturers/{manufacturer_id}` | 厂家详情 | 需要 | `product:view` |
| PUT | `/api/manufacturers/{manufacturer_id}` | 更新厂家 | 需要 | `product:manage` |
| DELETE | `/api/manufacturers/{manufacturer_id}` | 删除厂家 | 需要 | `product:manage` |
| GET | `/api/products` | 商品列表 | 需要 | `product:view` |
| POST | `/api/products` | 创建商品 | 需要 | `product:manage` |
| GET | `/api/products/{product_id}` | 商品详情 | 需要 | `product:view` |
| PUT | `/api/products/{product_id}` | 更新商品 | 需要 | `product:manage` |
| DELETE | `/api/products/{product_id}` | 删除商品 | 需要 | `product:manage` |
| GET | `/api/products/{product_id}/prices` | 价格调整历史 | 需要 | `product:view` |
| POST | `/api/products/{product_id}/prices` | 价格调整 | 需要 | `product:manage` |

### GET /api/categories

**接口名称：** 商品分类列表

**认证：** 需要 Bearer Token

**所需权限：** `product:view`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| keyword | 查询 | 字符串 | 否 |  | 关键词 |
| page | 查询 | 整数 | 否 | 1 | 页码，从 1 开始 |
| size | 查询 | 整数 | 否 | 20 | 每页条数，1-1000 |

**响应示例（200/201）：**

```json
{
  "items": [
    {
      "id": 0,
      "code": "string",
      "name": "string",
      "description": "string",
      "sort_order": 0,
      "is_active": false,
      "created_at": "2026-09-01T00:00:00"
    }
  ],
  "total": 0,
  "page": 0,
  "size": 0
}
```

---

### POST /api/categories

**接口名称：** 创建商品分类

**认证：** 需要 Bearer Token

**所需权限：** `product:manage`

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| code | 字符串 | 是 | 编码 |
| name | 字符串 | 是 | 名称 |
| description | 字符串 | 否 | 说明 |
| sort_order | 整数 | 否 | 排序 |
| is_active | 布尔 | 否 | 是否启用 |

**请求示例：**

```json
{
  "code": "string",
  "name": "string",
  "description": "string",
  "sort_order": 0,
  "is_active": true
}
```

**响应示例（200/201）：**

```json
{
  "id": 0,
  "code": "string",
  "name": "string",
  "description": "string",
  "sort_order": 0,
  "is_active": false,
  "created_at": "2026-09-01T00:00:00"
}
```

---

### GET /api/categories/{category_id}

**接口名称：** 商品分类详情

**认证：** 需要 Bearer Token

**所需权限：** `product:view`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| category_id | 路径 | 整数 | 是 |  | 分类 ID |

**响应示例（200/201）：**

```json
{
  "id": 0,
  "code": "string",
  "name": "string",
  "description": "string",
  "sort_order": 0,
  "is_active": false,
  "created_at": "2026-09-01T00:00:00"
}
```

---

### PUT /api/categories/{category_id}

**接口名称：** 更新商品分类

**认证：** 需要 Bearer Token

**所需权限：** `product:manage`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| category_id | 路径 | 整数 | 是 |  | 分类 ID |

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| code | 字符串 | 否 | 编码 |
| name | 字符串 | 否 | 名称 |
| description | 字符串 | 否 | 说明 |
| sort_order | 整数 | 否 | 排序 |
| is_active | 布尔 | 否 | 是否启用 |

**请求示例：**

```json
{
  "code": "string",
  "name": "string",
  "description": "string",
  "sort_order": 0,
  "is_active": false
}
```

**响应示例（200/201）：**

```json
{
  "id": 0,
  "code": "string",
  "name": "string",
  "description": "string",
  "sort_order": 0,
  "is_active": false,
  "created_at": "2026-09-01T00:00:00"
}
```

---

### DELETE /api/categories/{category_id}

**接口名称：** 删除商品分类

**认证：** 需要 Bearer Token

**所需权限：** `product:manage`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| category_id | 路径 | 整数 | 是 |  | 分类 ID |

**响应示例（200/201）：**

```json
{
  "message": "string"
}
```

---

### GET /api/manufacturers

**接口名称：** 生产厂家列表

**认证：** 需要 Bearer Token

**所需权限：** `product:view`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| keyword | 查询 | 字符串 | 否 |  | 关键词 |
| page | 查询 | 整数 | 否 | 1 | 页码，从 1 开始 |
| size | 查询 | 整数 | 否 | 20 | 每页条数，1-1000 |

**响应示例（200/201）：**

```json
{
  "items": [
    {
      "id": 0,
      "name": "string",
      "country": "string",
      "description": "string",
      "created_at": "2026-09-01T00:00:00"
    }
  ],
  "total": 0,
  "page": 0,
  "size": 0
}
```

---

### POST /api/manufacturers

**接口名称：** 创建厂家

**认证：** 需要 Bearer Token

**所需权限：** `product:manage`

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| name | 字符串 | 是 | 名称 |
| country | 字符串 | 否 | country |
| description | 字符串 | 否 | 说明 |

**请求示例：**

```json
{
  "name": "string",
  "country": "string",
  "description": "string"
}
```

**响应示例（200/201）：**

```json
{
  "id": 0,
  "name": "string",
  "country": "string",
  "description": "string",
  "created_at": "2026-09-01T00:00:00"
}
```

---

### GET /api/manufacturers/{manufacturer_id}

**接口名称：** 厂家详情

**认证：** 需要 Bearer Token

**所需权限：** `product:view`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| manufacturer_id | 路径 | 整数 | 是 |  | 生产厂家 ID |

**响应示例（200/201）：**

```json
{
  "id": 0,
  "name": "string",
  "country": "string",
  "description": "string",
  "created_at": "2026-09-01T00:00:00"
}
```

---

### PUT /api/manufacturers/{manufacturer_id}

**接口名称：** 更新厂家

**认证：** 需要 Bearer Token

**所需权限：** `product:manage`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| manufacturer_id | 路径 | 整数 | 是 |  | 生产厂家 ID |

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| name | 字符串 | 否 | 名称 |
| country | 字符串 | 否 | country |
| description | 字符串 | 否 | 说明 |

**请求示例：**

```json
{
  "name": "string",
  "country": "string",
  "description": "string"
}
```

**响应示例（200/201）：**

```json
{
  "id": 0,
  "name": "string",
  "country": "string",
  "description": "string",
  "created_at": "2026-09-01T00:00:00"
}
```

---

### DELETE /api/manufacturers/{manufacturer_id}

**接口名称：** 删除厂家

**认证：** 需要 Bearer Token

**所需权限：** `product:manage`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| manufacturer_id | 路径 | 整数 | 是 |  | 生产厂家 ID |

**响应示例（200/201）：**

```json
{
  "message": "string"
}
```

---

### GET /api/products

**接口名称：** 商品列表

**认证：** 需要 Bearer Token

**所需权限：** `product:view`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| keyword | 查询 | 字符串 | 否 |  | 关键词 |
| category_id | 查询 | 整数 | 否 |  | 分类 ID |
| manufacturer_id | 查询 | 整数 | 否 |  | 生产厂家 ID |
| is_active | 查询 | 布尔 | 否 |  | 是否启用 |
| page | 查询 | 整数 | 否 | 1 | 页码，从 1 开始 |
| size | 查询 | 整数 | 否 | 20 | 每页条数，1-1000 |

**响应示例（200/201）：**

```json
{
  "items": [
    {
      "id": 0,
      "sku": "string",
      "name": "string",
      "category_id": 0,
      "category_name": "string",
      "manufacturer_id": 0,
      "supplier_id": 0,
      "approval_no": "string",
      "specification": "string",
      "unit": "string",
      "dosage_form": "string",
      "storage_condition": "string",
      "is_cold_chain": false,
      "shelf_life_months": 0,
      "cost_price": 0.0,
      "standard_price": 0.0,
      "is_active": false,
      "listed_date": "2026-01-01",
      "created_at": "2026-09-01T00:00:00"
    }
  ],
  "total": 0,
  "page": 0,
  "size": 0
}
```

---

### POST /api/products

**接口名称：** 创建商品

**认证：** 需要 Bearer Token

**所需权限：** `product:manage`

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| sku | 字符串 | 是 | SKU |
| name | 字符串 | 是 | 名称 |
| category_id | 整数 | 是 | 分类 ID |
| manufacturer_id | 整数 | 是 | 生产厂家 ID |
| supplier_id | 整数 | 是 | 供应商 ID |
| approval_no | 字符串 | 否 | 批准文号 |
| specification | 字符串 | 否 | 规格 |
| unit | 字符串 | 否 | 单位 |
| dosage_form | 字符串 | 否 | 剂型 |
| storage_condition | 字符串 | 否 | 储存条件 |
| is_cold_chain | 布尔 | 否 | 是否冷链 |
| shelf_life_months | 整数 | 否 | 有效期（月） |
| cost_price | 数值 | 是 | 成本价 |
| standard_price | 数值 | 是 | 标准售价 |
| is_active | 布尔 | 否 | 是否启用 |
| listed_date | 日期 | 是 | listed_date |

**请求示例：**

```json
{
  "sku": "string",
  "name": "string",
  "category_id": 0,
  "manufacturer_id": 0,
  "supplier_id": 0,
  "approval_no": "string",
  "specification": "string",
  "unit": "盒",
  "dosage_form": "string",
  "storage_condition": "常温",
  "is_cold_chain": false,
  "shelf_life_months": 24,
  "cost_price": 0.0,
  "standard_price": 0.0,
  "is_active": true,
  "listed_date": "2026-01-01"
}
```

**响应示例（200/201）：**

```json
{
  "id": 0,
  "sku": "string",
  "name": "string",
  "category_id": 0,
  "category_name": "string",
  "manufacturer_id": 0,
  "supplier_id": 0,
  "approval_no": "string",
  "specification": "string",
  "unit": "string",
  "dosage_form": "string",
  "storage_condition": "string",
  "is_cold_chain": false,
  "shelf_life_months": 0,
  "cost_price": 0.0,
  "standard_price": 0.0,
  "is_active": false,
  "listed_date": "2026-01-01",
  "created_at": "2026-09-01T00:00:00"
}
```

---

### GET /api/products/{product_id}

**接口名称：** 商品详情

**认证：** 需要 Bearer Token

**所需权限：** `product:view`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| product_id | 路径 | 整数 | 是 |  | 商品 ID |

**响应示例（200/201）：**

```json
{
  "id": 0,
  "sku": "string",
  "name": "string",
  "category_id": 0,
  "category_name": "string",
  "manufacturer_id": 0,
  "supplier_id": 0,
  "approval_no": "string",
  "specification": "string",
  "unit": "string",
  "dosage_form": "string",
  "storage_condition": "string",
  "is_cold_chain": false,
  "shelf_life_months": 0,
  "cost_price": 0.0,
  "standard_price": 0.0,
  "is_active": false,
  "listed_date": "2026-01-01",
  "created_at": "2026-09-01T00:00:00"
}
```

---

### PUT /api/products/{product_id}

**接口名称：** 更新商品

**认证：** 需要 Bearer Token

**所需权限：** `product:manage`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| product_id | 路径 | 整数 | 是 |  | 商品 ID |

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| name | 字符串 | 否 | 名称 |
| category_id | 整数 | 否 | 分类 ID |
| manufacturer_id | 整数 | 否 | 生产厂家 ID |
| supplier_id | 整数 | 否 | 供应商 ID |
| approval_no | 字符串 | 否 | 批准文号 |
| specification | 字符串 | 否 | 规格 |
| unit | 字符串 | 否 | 单位 |
| dosage_form | 字符串 | 否 | 剂型 |
| storage_condition | 字符串 | 否 | 储存条件 |
| is_cold_chain | 布尔 | 否 | 是否冷链 |
| shelf_life_months | 整数 | 否 | 有效期（月） |
| cost_price | 数值 | 否 | 成本价 |
| standard_price | 数值 | 否 | 标准售价 |
| is_active | 布尔 | 否 | 是否启用 |
| listed_date | 日期 | 否 | listed_date |

**请求示例：**

```json
{
  "name": "string",
  "category_id": 0,
  "manufacturer_id": 0,
  "supplier_id": 0,
  "approval_no": "string",
  "specification": "string",
  "unit": "string",
  "dosage_form": "string",
  "storage_condition": "string",
  "is_cold_chain": false,
  "shelf_life_months": 0,
  "cost_price": 0.0,
  "standard_price": 0.0,
  "is_active": false,
  "listed_date": "2026-01-01"
}
```

**响应示例（200/201）：**

```json
{
  "id": 0,
  "sku": "string",
  "name": "string",
  "category_id": 0,
  "category_name": "string",
  "manufacturer_id": 0,
  "supplier_id": 0,
  "approval_no": "string",
  "specification": "string",
  "unit": "string",
  "dosage_form": "string",
  "storage_condition": "string",
  "is_cold_chain": false,
  "shelf_life_months": 0,
  "cost_price": 0.0,
  "standard_price": 0.0,
  "is_active": false,
  "listed_date": "2026-01-01",
  "created_at": "2026-09-01T00:00:00"
}
```

---

### DELETE /api/products/{product_id}

**接口名称：** 删除商品

**认证：** 需要 Bearer Token

**所需权限：** `product:manage`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| product_id | 路径 | 整数 | 是 |  | 商品 ID |

**响应示例（200/201）：**

```json
{
  "message": "string"
}
```

---

### GET /api/products/{product_id}/prices

**接口名称：** 价格调整历史

**认证：** 需要 Bearer Token

**所需权限：** `product:view`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| product_id | 路径 | 整数 | 是 |  | 商品 ID |
| page | 查询 | 整数 | 否 | 1 | 页码，从 1 开始 |
| size | 查询 | 整数 | 否 | 20 | 每页条数，1-1000 |

**响应示例（200/201）：**

```json
{
  "items": [
    {
      "id": 0,
      "product_id": 0,
      "effective_date": "2026-01-01",
      "old_price": 0.0,
      "new_price": 0.0,
      "change_reason": "string",
      "created_at": "2026-09-01T00:00:00"
    }
  ],
  "total": 0,
  "page": 0,
  "size": 0
}
```

---

### POST /api/products/{product_id}/prices

**接口名称：** 价格调整

**认证：** 需要 Bearer Token

**所需权限：** `product:manage`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| product_id | 路径 | 整数 | 是 |  | 商品 ID |

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| effective_date | 日期 | 是 | 生效日期 |
| new_price | 数值 | 是 | 调整后价格 |
| change_reason | 字符串 | 否 | 调价原因 |

**请求示例：**

```json
{
  "effective_date": "2026-01-01",
  "new_price": 0.0,
  "change_reason": "string"
}
```

**响应示例（200/201）：**

```json
{
  "id": 0,
  "product_id": 0,
  "effective_date": "2026-01-01",
  "old_price": 0.0,
  "new_price": 0.0,
  "change_reason": "string",
  "created_at": "2026-09-01T00:00:00"
}
```

---

## 六、供应商管理

| 方法 | 路径 | 接口名称 | 认证 | 所需权限 |
| --- | --- | --- | --- | --- |
| GET | `/api/suppliers` | 供应商列表 | 需要 | — |
| POST | `/api/suppliers` | 创建供应商 | 需要 | — |
| GET | `/api/suppliers/{supplier_id}` | 供应商详情 | 需要 | `supplier:view` |
| PUT | `/api/suppliers/{supplier_id}` | 更新供应商 | 需要 | `supplier:manage` |
| DELETE | `/api/suppliers/{supplier_id}` | 删除供应商 | 需要 | `supplier:manage` |

### GET /api/suppliers

**接口名称：** 供应商列表

**认证：** 需要 Bearer Token

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| keyword | 查询 | 字符串 | 否 |  | 关键词 |
| status | 查询 | 字符串 | 否 |  | 状态 |
| page | 查询 | 整数 | 否 | 1 | 页码，从 1 开始 |
| size | 查询 | 整数 | 否 | 20 | 每页条数，1-1000 |

**响应示例（200/201）：**

```json
{
  "items": [
    {
      "id": 0,
      "code": "string",
      "name": "string",
      "contact_person": "string",
      "phone": "string",
      "email": "string",
      "province": "string",
      "city": "string",
      "address": "string",
      "credit_days": 0,
      "status": "string",
      "created_at": "2026-09-01T00:00:00"
    }
  ],
  "total": 0,
  "page": 0,
  "size": 0
}
```

---

### POST /api/suppliers

**接口名称：** 创建供应商

**认证：** 需要 Bearer Token

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| code | 字符串 | 是 | 编码 |
| name | 字符串 | 是 | 名称 |
| contact_person | 字符串 | 否 | 联系人 |
| phone | 字符串 | 否 | 电话 |
| email | 字符串 | 否 | 邮箱 |
| province | 字符串 | 否 | 省份 |
| city | 字符串 | 否 | 城市 |
| address | 字符串 | 否 | 地址 |
| credit_days | 整数 | 否 | 账期天数 |
| status | 字符串 | 否 | 状态 |

**请求示例：**

```json
{
  "code": "string",
  "name": "string",
  "contact_person": "string",
  "phone": "string",
  "email": "string",
  "province": "string",
  "city": "string",
  "address": "string",
  "credit_days": 30,
  "status": "合作中"
}
```

**响应示例（200/201）：**

```json
{
  "id": 0,
  "code": "string",
  "name": "string",
  "contact_person": "string",
  "phone": "string",
  "email": "string",
  "province": "string",
  "city": "string",
  "address": "string",
  "credit_days": 0,
  "status": "string",
  "created_at": "2026-09-01T00:00:00"
}
```

---

### GET /api/suppliers/{supplier_id}

**接口名称：** 供应商详情

**认证：** 需要 Bearer Token

**所需权限：** `supplier:view`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| supplier_id | 路径 | 整数 | 是 |  | 供应商 ID |

**响应示例（200/201）：**

```json
{
  "id": 0,
  "code": "string",
  "name": "string",
  "contact_person": "string",
  "phone": "string",
  "email": "string",
  "province": "string",
  "city": "string",
  "address": "string",
  "credit_days": 0,
  "status": "string",
  "created_at": "2026-09-01T00:00:00"
}
```

---

### PUT /api/suppliers/{supplier_id}

**接口名称：** 更新供应商

**认证：** 需要 Bearer Token

**所需权限：** `supplier:manage`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| supplier_id | 路径 | 整数 | 是 |  | 供应商 ID |

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| name | 字符串 | 否 | 名称 |
| contact_person | 字符串 | 否 | 联系人 |
| phone | 字符串 | 否 | 电话 |
| email | 字符串 | 否 | 邮箱 |
| province | 字符串 | 否 | 省份 |
| city | 字符串 | 否 | 城市 |
| address | 字符串 | 否 | 地址 |
| credit_days | 整数 | 否 | 账期天数 |
| status | 字符串 | 否 | 状态 |

**请求示例：**

```json
{
  "name": "string",
  "contact_person": "string",
  "phone": "string",
  "email": "string",
  "province": "string",
  "city": "string",
  "address": "string",
  "credit_days": 0,
  "status": "string"
}
```

**响应示例（200/201）：**

```json
{
  "id": 0,
  "code": "string",
  "name": "string",
  "contact_person": "string",
  "phone": "string",
  "email": "string",
  "province": "string",
  "city": "string",
  "address": "string",
  "credit_days": 0,
  "status": "string",
  "created_at": "2026-09-01T00:00:00"
}
```

---

### DELETE /api/suppliers/{supplier_id}

**接口名称：** 删除供应商

**认证：** 需要 Bearer Token

**所需权限：** `supplier:manage`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| supplier_id | 路径 | 整数 | 是 |  | 供应商 ID |

**响应示例（200/201）：**

```json
{
  "message": "string"
}
```

---

## 七、仓库管理

| 方法 | 路径 | 接口名称 | 认证 | 所需权限 |
| --- | --- | --- | --- | --- |
| GET | `/api/warehouses` | 仓库列表 | 需要 | — |
| POST | `/api/warehouses` | 创建仓库 | 需要 | — |
| GET | `/api/warehouses/{warehouse_id}` | 仓库详情 | 需要 | `warehouse:view` |
| PUT | `/api/warehouses/{warehouse_id}` | 更新仓库 | 需要 | `warehouse:manage` |
| DELETE | `/api/warehouses/{warehouse_id}` | 删除仓库 | 需要 | `warehouse:manage` |

### GET /api/warehouses

**接口名称：** 仓库列表

**认证：** 需要 Bearer Token

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| keyword | 查询 | 字符串 | 否 |  | 关键词 |
| status | 查询 | 字符串 | 否 |  | 状态 |
| page | 查询 | 整数 | 否 | 1 | 页码，从 1 开始 |
| size | 查询 | 整数 | 否 | 20 | 每页条数，1-1000 |

**响应示例（200/201）：**

```json
{
  "items": [
    {
      "id": 0,
      "code": "string",
      "name": "string",
      "province": "string",
      "city": "string",
      "address": "string",
      "manager_name": "string",
      "phone": "string",
      "has_cold_chain": false,
      "status": "string",
      "created_at": "2026-09-01T00:00:00"
    }
  ],
  "total": 0,
  "page": 0,
  "size": 0
}
```

---

### POST /api/warehouses

**接口名称：** 创建仓库

**认证：** 需要 Bearer Token

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| code | 字符串 | 是 | 编码 |
| name | 字符串 | 是 | 名称 |
| province | 字符串 | 否 | 省份 |
| city | 字符串 | 否 | 城市 |
| address | 字符串 | 否 | 地址 |
| manager_name | 字符串 | 否 | 负责人 |
| phone | 字符串 | 否 | 电话 |
| has_cold_chain | 布尔 | 否 | 具备冷链 |
| status | 字符串 | 否 | 状态 |

**请求示例：**

```json
{
  "code": "string",
  "name": "string",
  "province": "string",
  "city": "string",
  "address": "string",
  "manager_name": "string",
  "phone": "string",
  "has_cold_chain": true,
  "status": "正常"
}
```

**响应示例（200/201）：**

```json
{
  "id": 0,
  "code": "string",
  "name": "string",
  "province": "string",
  "city": "string",
  "address": "string",
  "manager_name": "string",
  "phone": "string",
  "has_cold_chain": false,
  "status": "string",
  "created_at": "2026-09-01T00:00:00"
}
```

---

### GET /api/warehouses/{warehouse_id}

**接口名称：** 仓库详情

**认证：** 需要 Bearer Token

**所需权限：** `warehouse:view`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| warehouse_id | 路径 | 整数 | 是 |  | 仓库 ID |

**响应示例（200/201）：**

```json
{
  "id": 0,
  "code": "string",
  "name": "string",
  "province": "string",
  "city": "string",
  "address": "string",
  "manager_name": "string",
  "phone": "string",
  "has_cold_chain": false,
  "status": "string",
  "created_at": "2026-09-01T00:00:00"
}
```

---

### PUT /api/warehouses/{warehouse_id}

**接口名称：** 更新仓库

**认证：** 需要 Bearer Token

**所需权限：** `warehouse:manage`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| warehouse_id | 路径 | 整数 | 是 |  | 仓库 ID |

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| name | 字符串 | 否 | 名称 |
| province | 字符串 | 否 | 省份 |
| city | 字符串 | 否 | 城市 |
| address | 字符串 | 否 | 地址 |
| manager_name | 字符串 | 否 | 负责人 |
| phone | 字符串 | 否 | 电话 |
| has_cold_chain | 布尔 | 否 | 具备冷链 |
| status | 字符串 | 否 | 状态 |

**请求示例：**

```json
{
  "name": "string",
  "province": "string",
  "city": "string",
  "address": "string",
  "manager_name": "string",
  "phone": "string",
  "has_cold_chain": false,
  "status": "string"
}
```

**响应示例（200/201）：**

```json
{
  "id": 0,
  "code": "string",
  "name": "string",
  "province": "string",
  "city": "string",
  "address": "string",
  "manager_name": "string",
  "phone": "string",
  "has_cold_chain": false,
  "status": "string",
  "created_at": "2026-09-01T00:00:00"
}
```

---

### DELETE /api/warehouses/{warehouse_id}

**接口名称：** 删除仓库

**认证：** 需要 Bearer Token

**所需权限：** `warehouse:manage`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| warehouse_id | 路径 | 整数 | 是 |  | 仓库 ID |

**响应示例（200/201）：**

```json
{
  "message": "string"
}
```

---

## 八、采购管理

| 方法 | 路径 | 接口名称 | 认证 | 所需权限 |
| --- | --- | --- | --- | --- |
| GET | `/api/purchase-orders` | 采购单列表 | 需要 | — |
| POST | `/api/purchase-orders` | 创建采购单 | 需要 | — |
| GET | `/api/purchase-orders/{order_id}` | 采购单详情 | 需要 | `purchase:view` |
| PUT | `/api/purchase-orders/{order_id}` | 更新采购单 | 需要 | `purchase:manage` |
| DELETE | `/api/purchase-orders/{order_id}` | 删除采购单 | 需要 | `purchase:manage` |
| POST | `/api/purchase-orders/{order_id}/receive` | 采购收货 | 需要 | `purchase:manage` |

### GET /api/purchase-orders

**接口名称：** 采购单列表

**认证：** 需要 Bearer Token

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| supplier_id | 查询 | 整数 | 否 |  | 供应商 ID |
| warehouse_id | 查询 | 整数 | 否 |  | 仓库 ID |
| order_no | 查询 | 字符串 | 否 |  | 订单编号 |
| status | 查询 | 字符串 | 否 |  | 状态 |
| start_date | 查询 | 日期 | 否 |  | 开始日期 |
| end_date | 查询 | 日期 | 否 |  | 结束日期 |
| page | 查询 | 整数 | 否 | 1 | 页码，从 1 开始 |
| size | 查询 | 整数 | 否 | 20 | 每页条数，1-1000 |

**响应示例（200/201）：**

```json
{
  "items": [
    {
      "id": 0,
      "order_no": "string",
      "supplier_id": 0,
      "supplier_name": "string",
      "warehouse_id": 0,
      "warehouse_name": "string",
      "order_date": "2026-01-01",
      "expected_date": "2026-01-01",
      "received_date": "2026-01-01",
      "status": "string",
      "total_amount": 0.0,
      "delivery_type": "string",
      "remark": "string",
      "created_at": "2026-09-01T00:00:00",
      "items": []
    }
  ],
  "total": 0,
  "page": 0,
  "size": 0
}
```

---

### POST /api/purchase-orders

**接口名称：** 创建采购单

**认证：** 需要 Bearer Token

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| supplier_id | 整数 | 是 | 供应商 ID |
| warehouse_id | 整数 | 是 | 仓库 ID |
| order_date | 日期 | 是 | 下单日期 |
| expected_date | 日期 | 否 | 预计到货日期 |
| delivery_type | 字符串 | 否 | 配送方式 |
| remark | 字符串 | 否 | 备注 |
| items | PurchaseOrderItemIn[] | 是 | 明细列表 |

**请求示例：**

```json
{
  "supplier_id": 0,
  "warehouse_id": 0,
  "order_date": "2026-01-01",
  "expected_date": "2026-01-01",
  "delivery_type": "常温运输",
  "remark": "string",
  "items": [
    {
      "product_id": 0,
      "quantity": 0,
      "unit_cost": 0.0
    }
  ]
}
```

**响应示例（200/201）：**

```json
{
  "id": 0,
  "order_no": "string",
  "supplier_id": 0,
  "supplier_name": "string",
  "warehouse_id": 0,
  "warehouse_name": "string",
  "order_date": "2026-01-01",
  "expected_date": "2026-01-01",
  "received_date": "2026-01-01",
  "status": "string",
  "total_amount": 0.0,
  "delivery_type": "string",
  "remark": "string",
  "created_at": "2026-09-01T00:00:00",
  "items": []
}
```

---

### GET /api/purchase-orders/{order_id}

**接口名称：** 采购单详情

**认证：** 需要 Bearer Token

**所需权限：** `purchase:view`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| order_id | 路径 | 整数 | 是 |  | 订单 ID |

**响应示例（200/201）：**

```json
{
  "id": 0,
  "order_no": "string",
  "supplier_id": 0,
  "supplier_name": "string",
  "warehouse_id": 0,
  "warehouse_name": "string",
  "order_date": "2026-01-01",
  "expected_date": "2026-01-01",
  "received_date": "2026-01-01",
  "status": "string",
  "total_amount": 0.0,
  "delivery_type": "string",
  "remark": "string",
  "created_at": "2026-09-01T00:00:00",
  "items": []
}
```

---

### PUT /api/purchase-orders/{order_id}

**接口名称：** 更新采购单

**认证：** 需要 Bearer Token

**所需权限：** `purchase:manage`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| order_id | 路径 | 整数 | 是 |  | 订单 ID |

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| supplier_id | 整数 | 是 | 供应商 ID |
| warehouse_id | 整数 | 是 | 仓库 ID |
| order_date | 日期 | 是 | 下单日期 |
| expected_date | 日期 | 否 | 预计到货日期 |
| delivery_type | 字符串 | 否 | 配送方式 |
| remark | 字符串 | 否 | 备注 |
| items | PurchaseOrderItemIn[] | 是 | 明细列表 |

**请求示例：**

```json
{
  "supplier_id": 0,
  "warehouse_id": 0,
  "order_date": "2026-01-01",
  "expected_date": "2026-01-01",
  "delivery_type": "常温运输",
  "remark": "string",
  "items": [
    {
      "product_id": 0,
      "quantity": 0,
      "unit_cost": 0.0
    }
  ]
}
```

**响应示例（200/201）：**

```json
{
  "id": 0,
  "order_no": "string",
  "supplier_id": 0,
  "supplier_name": "string",
  "warehouse_id": 0,
  "warehouse_name": "string",
  "order_date": "2026-01-01",
  "expected_date": "2026-01-01",
  "received_date": "2026-01-01",
  "status": "string",
  "total_amount": 0.0,
  "delivery_type": "string",
  "remark": "string",
  "created_at": "2026-09-01T00:00:00",
  "items": []
}
```

---

### DELETE /api/purchase-orders/{order_id}

**接口名称：** 删除采购单

**认证：** 需要 Bearer Token

**所需权限：** `purchase:manage`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| order_id | 路径 | 整数 | 是 |  | 订单 ID |

**响应示例（200/201）：**

```json
{
  "message": "string"
}
```

---

### POST /api/purchase-orders/{order_id}/receive

**接口名称：** 采购收货

**认证：** 需要 Bearer Token

**所需权限：** `purchase:manage`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| order_id | 路径 | 整数 | 是 |  | 订单 ID |

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| received_date | 日期 | 是 | 实收日期 |
| items | ReceiveItemIn[] | 是 | 明细列表 |

**请求示例：**

```json
{
  "received_date": "2026-01-01",
  "items": [
    {
      "item_id": 0,
      "received_quantity": 0
    }
  ]
}
```

**响应示例（200/201）：**

```json
{
  "id": 0,
  "order_no": "string",
  "supplier_id": 0,
  "supplier_name": "string",
  "warehouse_id": 0,
  "warehouse_name": "string",
  "order_date": "2026-01-01",
  "expected_date": "2026-01-01",
  "received_date": "2026-01-01",
  "status": "string",
  "total_amount": 0.0,
  "delivery_type": "string",
  "remark": "string",
  "created_at": "2026-09-01T00:00:00",
  "items": []
}
```

---

## 九、销售管理

| 方法 | 路径 | 接口名称 | 认证 | 所需权限 |
| --- | --- | --- | --- | --- |
| GET | `/api/sales-orders` | 销售订单列表 | 需要 | — |
| POST | `/api/sales-orders` | 创建销售订单 | 需要 | — |
| GET | `/api/sales-orders/{order_id}` | 销售订单详情 | 需要 | `sales:view` |
| DELETE | `/api/sales-orders/{order_id}` | 删除销售订单 | 需要 | `sales:manage` |
| POST | `/api/sales-orders/{order_id}/ship` | 销售发货出库 | 需要 | `sales:manage` |
| POST | `/api/sales-orders/{order_id}/cancel` | 取消销售订单 | 需要 | `sales:manage` |

### GET /api/sales-orders

**接口名称：** 销售订单列表

**认证：** 需要 Bearer Token

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| customer_id | 查询 | 整数 | 否 |  | 客户 ID |
| employee_id | 查询 | 整数 | 否 |  | 员工 ID |
| order_no | 查询 | 字符串 | 否 |  | 订单编号 |
| status | 查询 | 字符串 | 否 |  | 状态 |
| start_date | 查询 | 日期 | 否 |  | 开始日期 |
| end_date | 查询 | 日期 | 否 |  | 结束日期 |
| page | 查询 | 整数 | 否 | 1 | 页码，从 1 开始 |
| size | 查询 | 整数 | 否 | 20 | 每页条数，1-1000 |

**响应示例（200/201）：**

```json
{
  "items": [
    {
      "id": 0,
      "order_no": "string",
      "customer_id": 0,
      "customer_name": "string",
      "employee_id": 0,
      "employee_name": "string",
      "warehouse_id": 0,
      "warehouse_name": "string",
      "order_date": "2026-01-01",
      "status": "string",
      "item_count": 0,
      "total_quantity": 0,
      "subtotal_amount": 0.0,
      "discount_amount": 0.0,
      "total_amount": 0.0,
      "paid_amount": 0.0,
      "cost_amount": 0.0,
      "shipping_address": "string",
      "invoice_type": "string",
      "settlement_method": "string",
      "delivery_type": "string",
      "delivery_date": "2026-01-01",
      "remark": "string",
      "created_at": "2026-09-01T00:00:00",
      "items": []
    }
  ],
  "total": 0,
  "page": 0,
  "size": 0
}
```

---

### POST /api/sales-orders

**接口名称：** 创建销售订单

**认证：** 需要 Bearer Token

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| customer_id | 整数 | 是 | 客户 ID |
| employee_id | 整数 | 是 | 员工 ID |
| warehouse_id | 整数 | 是 | 仓库 ID |
| order_date | 日期 | 是 | 下单日期 |
| shipping_address | 字符串 | 否 | 收货地址 |
| invoice_type | 字符串 | 否 | 开票类型 |
| settlement_method | 字符串 | 否 | 结算方式 |
| delivery_type | 字符串 | 否 | 配送方式 |
| delivery_date | 日期 | 否 | 发货日期 |
| remark | 字符串 | 否 | 备注 |
| items | SalesOrderItemIn[] | 是 | 明细列表 |

**请求示例：**

```json
{
  "customer_id": 0,
  "employee_id": 0,
  "warehouse_id": 0,
  "order_date": "2026-01-01",
  "shipping_address": "string",
  "invoice_type": "增值税专用发票",
  "settlement_method": "现款",
  "delivery_type": "常温运输",
  "delivery_date": "2026-01-01",
  "remark": "string",
  "items": [
    {
      "product_id": 0,
      "quantity": 0,
      "discount_rate": 0
    }
  ]
}
```

**响应示例（200/201）：**

```json
{
  "id": 0,
  "order_no": "string",
  "customer_id": 0,
  "customer_name": "string",
  "employee_id": 0,
  "employee_name": "string",
  "warehouse_id": 0,
  "warehouse_name": "string",
  "order_date": "2026-01-01",
  "status": "string",
  "item_count": 0,
  "total_quantity": 0,
  "subtotal_amount": 0.0,
  "discount_amount": 0.0,
  "total_amount": 0.0,
  "paid_amount": 0.0,
  "cost_amount": 0.0,
  "shipping_address": "string",
  "invoice_type": "string",
  "settlement_method": "string",
  "delivery_type": "string",
  "delivery_date": "2026-01-01",
  "remark": "string",
  "created_at": "2026-09-01T00:00:00",
  "items": []
}
```

---

### GET /api/sales-orders/{order_id}

**接口名称：** 销售订单详情

**认证：** 需要 Bearer Token

**所需权限：** `sales:view`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| order_id | 路径 | 整数 | 是 |  | 订单 ID |

**响应示例（200/201）：**

```json
{
  "id": 0,
  "order_no": "string",
  "customer_id": 0,
  "customer_name": "string",
  "employee_id": 0,
  "employee_name": "string",
  "warehouse_id": 0,
  "warehouse_name": "string",
  "order_date": "2026-01-01",
  "status": "string",
  "item_count": 0,
  "total_quantity": 0,
  "subtotal_amount": 0.0,
  "discount_amount": 0.0,
  "total_amount": 0.0,
  "paid_amount": 0.0,
  "cost_amount": 0.0,
  "shipping_address": "string",
  "invoice_type": "string",
  "settlement_method": "string",
  "delivery_type": "string",
  "delivery_date": "2026-01-01",
  "remark": "string",
  "created_at": "2026-09-01T00:00:00",
  "items": []
}
```

---

### DELETE /api/sales-orders/{order_id}

**接口名称：** 删除销售订单

**认证：** 需要 Bearer Token

**所需权限：** `sales:manage`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| order_id | 路径 | 整数 | 是 |  | 订单 ID |

**响应示例（200/201）：**

```json
{
  "message": "string"
}
```

---

### POST /api/sales-orders/{order_id}/ship

**接口名称：** 销售发货出库

**认证：** 需要 Bearer Token

**所需权限：** `sales:manage`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| order_id | 路径 | 整数 | 是 |  | 订单 ID |

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| delivery_date | 日期 | 是 | 发货日期 |

**请求示例：**

```json
{
  "delivery_date": "2026-01-01"
}
```

**响应示例（200/201）：**

```json
{
  "id": 0,
  "order_no": "string",
  "customer_id": 0,
  "customer_name": "string",
  "employee_id": 0,
  "employee_name": "string",
  "warehouse_id": 0,
  "warehouse_name": "string",
  "order_date": "2026-01-01",
  "status": "string",
  "item_count": 0,
  "total_quantity": 0,
  "subtotal_amount": 0.0,
  "discount_amount": 0.0,
  "total_amount": 0.0,
  "paid_amount": 0.0,
  "cost_amount": 0.0,
  "shipping_address": "string",
  "invoice_type": "string",
  "settlement_method": "string",
  "delivery_type": "string",
  "delivery_date": "2026-01-01",
  "remark": "string",
  "created_at": "2026-09-01T00:00:00",
  "items": []
}
```

---

### POST /api/sales-orders/{order_id}/cancel

**接口名称：** 取消销售订单

**认证：** 需要 Bearer Token

**所需权限：** `sales:manage`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| order_id | 路径 | 整数 | 是 |  | 订单 ID |

**响应示例（200/201）：**

```json
{
  "id": 0,
  "order_no": "string",
  "customer_id": 0,
  "customer_name": "string",
  "employee_id": 0,
  "employee_name": "string",
  "warehouse_id": 0,
  "warehouse_name": "string",
  "order_date": "2026-01-01",
  "status": "string",
  "item_count": 0,
  "total_quantity": 0,
  "subtotal_amount": 0.0,
  "discount_amount": 0.0,
  "total_amount": 0.0,
  "paid_amount": 0.0,
  "cost_amount": 0.0,
  "shipping_address": "string",
  "invoice_type": "string",
  "settlement_method": "string",
  "delivery_type": "string",
  "delivery_date": "2026-01-01",
  "remark": "string",
  "created_at": "2026-09-01T00:00:00",
  "items": []
}
```

---

## 十、库存管理

| 方法 | 路径 | 接口名称 | 认证 | 所需权限 |
| --- | --- | --- | --- | --- |
| GET | `/api/inventory` | 库存列表（含状态） | 需要 | — |
| GET | `/api/inventory/movements` | 库存流水列表 | 需要 | `inventory:view` |
| GET | `/api/inventory/movements/{movement_id}` | 库存流水详情 | 需要 | `inventory:view` |
| GET | `/api/inventory/{inventory_id}` | 库存详情 | 需要 | `inventory:view` |
| POST | `/api/inventory/open-stock` | 期初建账入库 | 需要 | `inventory:manage` |

### GET /api/inventory

**接口名称：** 库存列表（含状态）

**认证：** 需要 Bearer Token

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| warehouse_id | 查询 | 整数 | 否 |  | 仓库 ID |
| product_id | 查询 | 整数 | 否 |  | 商品 ID |
| category_id | 查询 | 整数 | 否 |  | 分类 ID |
| manufacturer_id | 查询 | 整数 | 否 |  | 生产厂家 ID |
| status | 查询 | 字符串 | 否 |  | 状态 |
| page | 查询 | 整数 | 否 | 1 | 页码，从 1 开始 |
| size | 查询 | 整数 | 否 | 20 | 每页条数，1-1000 |

**响应示例（200/201）：**

```json
{
  "items": [
    {
      "id": 0,
      "warehouse_id": 0,
      "product_id": 0,
      "quantity": 0,
      "safety_stock": 0,
      "updated_at": "2026-09-01T00:00:00",
      "warehouse_name": "string",
      "product_name": "string",
      "sku": "string",
      "category_name": "string",
      "stock_status": "string",
      "stock_value": 0.0
    }
  ],
  "total": 0,
  "page": 0,
  "size": 0
}
```

---

### GET /api/inventory/movements

**接口名称：** 库存流水列表

**认证：** 需要 Bearer Token

**所需权限：** `inventory:view`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| warehouse_id | 查询 | 整数 | 否 |  | 仓库 ID |
| product_id | 查询 | 整数 | 否 |  | 商品 ID |
| movement_type | 查询 | 字符串 | 否 |  | 流水类型 |
| start_date | 查询 | 日期 | 否 |  | 开始日期 |
| end_date | 查询 | 日期 | 否 |  | 结束日期 |
| page | 查询 | 整数 | 否 | 1 | 页码，从 1 开始 |
| size | 查询 | 整数 | 否 | 20 | 每页条数，1-1000 |

**响应示例（200/201）：**

```json
{
  "items": [
    {
      "id": 0,
      "warehouse_id": 0,
      "product_id": 0,
      "movement_type": "string",
      "quantity": 0,
      "movement_date": "2026-01-01",
      "ref_table": "string",
      "ref_id": 0,
      "created_by": 0,
      "remark": "string",
      "created_at": "2026-09-01T00:00:00"
    }
  ],
  "total": 0,
  "page": 0,
  "size": 0
}
```

---

### GET /api/inventory/movements/{movement_id}

**接口名称：** 库存流水详情

**认证：** 需要 Bearer Token

**所需权限：** `inventory:view`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| movement_id | 路径 | 整数 | 是 |  |  |

**响应示例（200/201）：**

```json
{
  "id": 0,
  "warehouse_id": 0,
  "product_id": 0,
  "movement_type": "string",
  "quantity": 0,
  "movement_date": "2026-01-01",
  "ref_table": "string",
  "ref_id": 0,
  "created_by": 0,
  "remark": "string",
  "created_at": "2026-09-01T00:00:00"
}
```

---

### GET /api/inventory/{inventory_id}

**接口名称：** 库存详情

**认证：** 需要 Bearer Token

**所需权限：** `inventory:view`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| inventory_id | 路径 | 整数 | 是 |  | 库存记录 ID |

**响应示例（200/201）：**

```json
{
  "id": 0,
  "warehouse_id": 0,
  "product_id": 0,
  "quantity": 0,
  "safety_stock": 0,
  "updated_at": "2026-09-01T00:00:00",
  "warehouse_name": "string",
  "product_name": "string",
  "sku": "string",
  "category_name": "string",
  "stock_status": "string",
  "stock_value": 0.0
}
```

---

### POST /api/inventory/open-stock

**接口名称：** 期初建账入库

**认证：** 需要 Bearer Token

**所需权限：** `inventory:manage`

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| warehouse_id | 整数 | 是 | 仓库 ID |
| movement_date | 日期 | 是 | 变动日期 |
| items | OpenStockItem[] | 是 | 明细列表 |

**请求示例：**

```json
{
  "warehouse_id": 0,
  "movement_date": "2026-01-01",
  "items": [
    {
      "product_id": 0,
      "quantity": 0
    }
  ]
}
```

**响应示例（200/201）：**

```json
{
  "message": "string"
}
```

---

## 十一、退货管理

| 方法 | 路径 | 接口名称 | 认证 | 所需权限 |
| --- | --- | --- | --- | --- |
| GET | `/api/sales-returns` | 退货单列表 | 需要 | — |
| POST | `/api/sales-returns` | 创建退货单 | 需要 | — |
| GET | `/api/sales-returns/{return_id}` | 退货单详情 | 需要 | `return:view` |
| DELETE | `/api/sales-returns/{return_id}` | 删除退货单 | 需要 | `return:manage` |
| POST | `/api/sales-returns/{return_id}/process` | 处理退货并入库 | 需要 | `return:manage` |

### GET /api/sales-returns

**接口名称：** 退货单列表

**认证：** 需要 Bearer Token

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| customer_id | 查询 | 整数 | 否 |  | 客户 ID |
| status | 查询 | 字符串 | 否 |  | 状态 |
| start_date | 查询 | 日期 | 否 |  | 开始日期 |
| end_date | 查询 | 日期 | 否 |  | 结束日期 |
| page | 查询 | 整数 | 否 | 1 | 页码，从 1 开始 |
| size | 查询 | 整数 | 否 | 20 | 每页条数，1-1000 |

**响应示例（200/201）：**

```json
{
  "items": [
    {
      "id": 0,
      "return_no": "string",
      "sales_order_id": 0,
      "order_no": "string",
      "customer_id": 0,
      "customer_name": "string",
      "warehouse_id": 0,
      "return_date": "2026-01-01",
      "status": "string",
      "reason": "string",
      "total_amount": 0.0,
      "remark": "string",
      "created_at": "2026-09-01T00:00:00",
      "items": []
    }
  ],
  "total": 0,
  "page": 0,
  "size": 0
}
```

---

### POST /api/sales-returns

**接口名称：** 创建退货单

**认证：** 需要 Bearer Token

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| sales_order_id | 整数 | 是 | 原销售订单 ID |
| return_date | 日期 | 是 | 退货日期 |
| reason | 字符串 | 否 | 原因 |
| remark | 字符串 | 否 | 备注 |
| items | SalesReturnItemIn[] | 是 | 明细列表 |

**请求示例：**

```json
{
  "sales_order_id": 0,
  "return_date": "2026-01-01",
  "reason": "string",
  "remark": "string",
  "items": [
    {
      "product_id": 0,
      "quantity": 0,
      "unit_price": 0.0,
      "reason": "string"
    }
  ]
}
```

**响应示例（200/201）：**

```json
{
  "id": 0,
  "return_no": "string",
  "sales_order_id": 0,
  "order_no": "string",
  "customer_id": 0,
  "customer_name": "string",
  "warehouse_id": 0,
  "return_date": "2026-01-01",
  "status": "string",
  "reason": "string",
  "total_amount": 0.0,
  "remark": "string",
  "created_at": "2026-09-01T00:00:00",
  "items": []
}
```

---

### GET /api/sales-returns/{return_id}

**接口名称：** 退货单详情

**认证：** 需要 Bearer Token

**所需权限：** `return:view`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| return_id | 路径 | 整数 | 是 |  | 退货单 ID |

**响应示例（200/201）：**

```json
{
  "id": 0,
  "return_no": "string",
  "sales_order_id": 0,
  "order_no": "string",
  "customer_id": 0,
  "customer_name": "string",
  "warehouse_id": 0,
  "return_date": "2026-01-01",
  "status": "string",
  "reason": "string",
  "total_amount": 0.0,
  "remark": "string",
  "created_at": "2026-09-01T00:00:00",
  "items": []
}
```

---

### DELETE /api/sales-returns/{return_id}

**接口名称：** 删除退货单

**认证：** 需要 Bearer Token

**所需权限：** `return:manage`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| return_id | 路径 | 整数 | 是 |  | 退货单 ID |

**响应示例（200/201）：**

```json
{
  "message": "string"
}
```

---

### POST /api/sales-returns/{return_id}/process

**接口名称：** 处理退货并入库

**认证：** 需要 Bearer Token

**所需权限：** `return:manage`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| return_id | 路径 | 整数 | 是 |  | 退货单 ID |

**响应示例（200/201）：**

```json
{
  "id": 0,
  "return_no": "string",
  "sales_order_id": 0,
  "order_no": "string",
  "customer_id": 0,
  "customer_name": "string",
  "warehouse_id": 0,
  "return_date": "2026-01-01",
  "status": "string",
  "reason": "string",
  "total_amount": 0.0,
  "remark": "string",
  "created_at": "2026-09-01T00:00:00",
  "items": []
}
```

---

## 十二、财务与收款

| 方法 | 路径 | 接口名称 | 认证 | 所需权限 |
| --- | --- | --- | --- | --- |
| GET | `/api/payments` | 收款记录列表 | 需要 | `finance:view` |
| POST | `/api/payments` | 登记收款 | 需要 | `finance:manage` |
| GET | `/api/payments/{payment_id}` | 收款记录详情 | 需要 | `finance:view` |
| DELETE | `/api/payments/{payment_id}` | 删除收款记录 | 需要 | `finance:manage` |
| GET | `/api/receivables` | 应收账龄分析 | 需要 | `finance:view` |

### GET /api/payments

**接口名称：** 收款记录列表

**认证：** 需要 Bearer Token

**所需权限：** `finance:view`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| customer_id | 查询 | 整数 | 否 |  | 客户 ID |
| customer_name | 查询 | 字符串 | 否 |  | 客户名称 |
| sales_order_id | 查询 | 整数 | 否 |  | 原销售订单 ID |
| order_no | 查询 | 字符串 | 否 |  | 订单编号 |
| start_date | 查询 | 日期 | 否 |  | 开始日期 |
| end_date | 查询 | 日期 | 否 |  | 结束日期 |
| page | 查询 | 整数 | 否 | 1 | 页码，从 1 开始 |
| size | 查询 | 整数 | 否 | 20 | 每页条数，1-1000 |

**响应示例（200/201）：**

```json
{
  "items": [
    {
      "id": 0,
      "sales_order_id": 0,
      "order_no": "string",
      "customer_id": 0,
      "customer_name": "string",
      "payment_date": "2026-01-01",
      "amount": 0.0,
      "payment_method": "string",
      "status": "string",
      "remark": "string",
      "created_at": "2026-09-01T00:00:00"
    }
  ],
  "total": 0,
  "page": 0,
  "size": 0
}
```

---

### POST /api/payments

**接口名称：** 登记收款

**认证：** 需要 Bearer Token

**所需权限：** `finance:manage`

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| sales_order_id | 整数 | 是 | 原销售订单 ID |
| payment_date | 日期 | 是 | 付款日期 |
| amount | 数值 | 是 | 金额 |
| payment_method | 字符串 | 是 | 付款方式 |
| status | 字符串 | 否 | 状态 |
| remark | 字符串 | 否 | 备注 |

**请求示例：**

```json
{
  "sales_order_id": 0,
  "payment_date": "2026-01-01",
  "amount": 0.0,
  "payment_method": "string",
  "status": "成功",
  "remark": "string"
}
```

**响应示例（200/201）：**

```json
{
  "id": 0,
  "sales_order_id": 0,
  "order_no": "string",
  "customer_id": 0,
  "customer_name": "string",
  "payment_date": "2026-01-01",
  "amount": 0.0,
  "payment_method": "string",
  "status": "string",
  "remark": "string",
  "created_at": "2026-09-01T00:00:00"
}
```

---

### GET /api/payments/{payment_id}

**接口名称：** 收款记录详情

**认证：** 需要 Bearer Token

**所需权限：** `finance:view`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| payment_id | 路径 | 整数 | 是 |  | 收款记录 ID |

**响应示例（200/201）：**

```json
{
  "id": 0,
  "sales_order_id": 0,
  "order_no": "string",
  "customer_id": 0,
  "customer_name": "string",
  "payment_date": "2026-01-01",
  "amount": 0.0,
  "payment_method": "string",
  "status": "string",
  "remark": "string",
  "created_at": "2026-09-01T00:00:00"
}
```

---

### DELETE /api/payments/{payment_id}

**接口名称：** 删除收款记录

**认证：** 需要 Bearer Token

**所需权限：** `finance:manage`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| payment_id | 路径 | 整数 | 是 |  | 收款记录 ID |

**响应示例（200/201）：**

```json
{
  "message": "string"
}
```

---

### GET /api/receivables

**接口名称：** 应收账龄分析

**认证：** 需要 Bearer Token

**所需权限：** `finance:view`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| as_of | 查询 | 日期 | 否 |  |  |
| customer_id | 查询 | 整数 | 否 |  | 客户 ID |
| settlement_method | 查询 | 字符串 | 否 |  | 结算方式 |
| overdue_only | 查询 | 布尔 | 否 | False |  |
| page | 查询 | 整数 | 否 | 1 | 页码，从 1 开始 |
| size | 查询 | 整数 | 否 | 20 | 每页条数，1-1000 |

**响应示例（200/201）：**

```json
{
  "items": [
    {
      "customer_id": 0,
      "customer_name": "string",
      "order_id": 0,
      "order_no": "string",
      "order_date": "2026-01-01",
      "total_amount": 0.0,
      "paid_amount": 0.0,
      "receivable": 0.0,
      "settlement_method": "string",
      "days_overdue": 0
    }
  ],
  "total": 0,
  "page": 0,
  "size": 0
}
```

---

## 十三、报表与分析

| 方法 | 路径 | 接口名称 | 认证 | 所需权限 |
| --- | --- | --- | --- | --- |
| GET | `/api/reports/sales-daily` | 每日销售汇总 | 需要 | `report:view` |
| GET | `/api/reports/sales-monthly` | 月度销售汇总（含环比） | 需要 | `report:view` |
| GET | `/api/reports/customer-summary` | 客户销售汇总 | 需要 | `report:view` |
| GET | `/api/reports/employee-summary` | 销售员业绩汇总 | 需要 | `report:view` |
| GET | `/api/reports/product-summary` | 商品销售汇总 | 需要 | `report:view` |
| GET | `/api/reports/order-detail` | 订单明细报表 | 需要 | `report:view` |
| GET | `/api/reports/inventory-status` | 库存状态报表 | 需要 | `report:view` |
| GET | `/api/reports/dashboard` | 综合经营看板 | 需要 | `dashboard:view` |

### GET /api/reports/sales-daily

**接口名称：** 每日销售汇总

**认证：** 需要 Bearer Token

**所需权限：** `report:view`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| start_date | 查询 | 日期 | 否 |  | 开始日期 |
| end_date | 查询 | 日期 | 否 |  | 结束日期 |
| page | 查询 | 整数 | 否 | 1 | 页码，从 1 开始 |
| size | 查询 | 整数 | 否 | 20 | 每页条数，1-1000 |

**响应示例（200/201）：**

```json
{
  "items": [
    {
      "sale_date": "2026-01-01",
      "order_count": 0,
      "item_count": 0,
      "quantity": 0,
      "total_amount": 0.0,
      "discount_amount": 0.0,
      "cost_amount": 0.0,
      "profit_amount": 0.0
    }
  ],
  "total": 0,
  "page": 0,
  "size": 0
}
```

---

### GET /api/reports/sales-monthly

**接口名称：** 月度销售汇总（含环比）

**认证：** 需要 Bearer Token

**所需权限：** `report:view`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| start_month | 查询 | 字符串 | 否 |  |  |
| end_month | 查询 | 字符串 | 否 |  |  |
| page | 查询 | 整数 | 否 | 1 | 页码，从 1 开始 |
| size | 查询 | 整数 | 否 | 20 | 每页条数，1-1000 |

**响应示例（200/201）：**

```json
{
  "items": [
    {
      "month": "string",
      "order_count": 0,
      "item_count": 0,
      "quantity": 0,
      "total_amount": 0.0,
      "discount_amount": 0.0,
      "cost_amount": 0.0,
      "profit_amount": 0.0,
      "prev_month_amount": 0.0,
      "amount_growth_rate": 0.0
    }
  ],
  "total": 0,
  "page": 0,
  "size": 0
}
```

---

### GET /api/reports/customer-summary

**接口名称：** 客户销售汇总

**认证：** 需要 Bearer Token

**所需权限：** `report:view`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| keyword | 查询 | 字符串 | 否 |  | 关键词 |
| customer_id | 查询 | 整数 | 否 |  | 客户 ID |
| page | 查询 | 整数 | 否 | 1 | 页码，从 1 开始 |
| size | 查询 | 整数 | 否 | 20 | 每页条数，1-1000 |

**响应示例（200/201）：**

```json
{
  "items": [
    {
      "customer_id": 0,
      "customer_code": "string",
      "customer_name": "string",
      "customer_type": "string",
      "coop_level": "string",
      "province": "string",
      "city": "string",
      "phone": "string",
      "order_count": 0,
      "total_amount": 0.0,
      "cost_amount": 0.0,
      "profit_amount": 0.0,
      "last_order_date": "2026-01-01"
    }
  ],
  "total": 0,
  "page": 0,
  "size": 0
}
```

---

### GET /api/reports/employee-summary

**接口名称：** 销售员业绩汇总

**认证：** 需要 Bearer Token

**所需权限：** `report:view`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| employee_id | 查询 | 整数 | 否 |  | 员工 ID |
| department_id | 查询 | 整数 | 否 |  | 部门 ID |
| page | 查询 | 整数 | 否 | 1 | 页码，从 1 开始 |
| size | 查询 | 整数 | 否 | 20 | 每页条数，1-1000 |

**响应示例（200/201）：**

```json
{
  "items": [
    {
      "employee_id": 0,
      "employee_code": "string",
      "employee_name": "string",
      "department_name": "string",
      "position": "string",
      "order_count": 0,
      "total_amount": 0.0,
      "cost_amount": 0.0,
      "profit_amount": 0.0,
      "customer_count": 0
    }
  ],
  "total": 0,
  "page": 0,
  "size": 0
}
```

---

### GET /api/reports/product-summary

**接口名称：** 商品销售汇总

**认证：** 需要 Bearer Token

**所需权限：** `report:view`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| product_id | 查询 | 整数 | 否 |  | 商品 ID |
| category_id | 查询 | 整数 | 否 |  | 分类 ID |
| manufacturer_id | 查询 | 整数 | 否 |  | 生产厂家 ID |
| page | 查询 | 整数 | 否 | 1 | 页码，从 1 开始 |
| size | 查询 | 整数 | 否 | 20 | 每页条数，1-1000 |

**响应示例（200/201）：**

```json
{
  "items": [
    {
      "product_id": 0,
      "sku": "string",
      "product_name": "string",
      "category_name": "string",
      "manufacturer_name": "string",
      "cost_price": 0.0,
      "standard_price": 0.0,
      "sold_quantity": 0,
      "sales_amount": 0.0,
      "gross_profit": 0.0,
      "order_count": 0
    }
  ],
  "total": 0,
  "page": 0,
  "size": 0
}
```

---

### GET /api/reports/order-detail

**接口名称：** 订单明细报表

**认证：** 需要 Bearer Token

**所需权限：** `report:view`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| order_id | 查询 | 整数 | 否 |  | 订单 ID |
| order_no | 查询 | 字符串 | 否 |  | 订单编号 |
| customer_id | 查询 | 整数 | 否 |  | 客户 ID |
| product_id | 查询 | 整数 | 否 |  | 商品 ID |
| category_id | 查询 | 整数 | 否 |  | 分类 ID |
| manufacturer_id | 查询 | 整数 | 否 |  | 生产厂家 ID |
| status | 查询 | 字符串 | 否 |  | 状态 |
| start_date | 查询 | 日期 | 否 |  | 开始日期 |
| end_date | 查询 | 日期 | 否 |  | 结束日期 |
| page | 查询 | 整数 | 否 | 1 | 页码，从 1 开始 |
| size | 查询 | 整数 | 否 | 20 | 每页条数，1-1000 |

**响应示例（200/201）：**

```json
{
  "items": [
    {
      "order_id": 0,
      "order_no": "string",
      "order_date": "2026-01-01",
      "order_status": "string",
      "customer_id": 0,
      "customer_name": "string",
      "customer_type": "string",
      "coop_level": "string",
      "employee_id": 0,
      "employee_name": "string",
      "department_name": "string",
      "warehouse_name": "string",
      "product_id": 0,
      "sku": "string",
      "product_name": "string",
      "category_name": "string",
      "manufacturer_name": "string",
      "quantity": 0,
      "unit_price": 0.0,
      "discount_amount": 0.0,
      "line_amount": 0.0,
      "order_amount": 0.0,
      "paid_amount": 0.0
    }
  ],
  "total": 0,
  "page": 0,
  "size": 0
}
```

---

### GET /api/reports/inventory-status

**接口名称：** 库存状态报表

**认证：** 需要 Bearer Token

**所需权限：** `report:view`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| warehouse_id | 查询 | 整数 | 否 |  | 仓库 ID |
| product_id | 查询 | 整数 | 否 |  | 商品 ID |
| category_id | 查询 | 整数 | 否 |  | 分类 ID |
| manufacturer_id | 查询 | 整数 | 否 |  | 生产厂家 ID |
| page | 查询 | 整数 | 否 | 1 | 页码，从 1 开始 |
| size | 查询 | 整数 | 否 | 20 | 每页条数，1-1000 |

**响应示例（200/201）：**

```json
{
  "items": [
    {
      "id": 0,
      "warehouse_id": 0,
      "product_id": 0,
      "quantity": 0,
      "safety_stock": 0,
      "updated_at": "2026-09-01T00:00:00",
      "warehouse_name": "string",
      "product_name": "string",
      "sku": "string",
      "category_name": "string",
      "stock_status": "string",
      "stock_value": 0.0
    }
  ],
  "total": 0,
  "page": 0,
  "size": 0
}
```

---

### GET /api/reports/dashboard

**接口名称：** 综合经营看板

**认证：** 需要 Bearer Token

**所需权限：** `dashboard:view`

**响应示例（200/201）：**

```json
{
  "today_order_count": 0,
  "today_sales_amount": 0.0,
  "today_profit": 0.0,
  "month_order_count": 0,
  "month_sales_amount": 0.0,
  "month_profit": 0.0,
  "low_stock_count": 0,
  "pending_return_count": 0,
  "total_receivable": 0.0
}
```

---

## 十四、GSP 合规

| 方法 | 路径 | 接口名称 | 认证 | 所需权限 |
| --- | --- | --- | --- | --- |
| GET | `/api/gsp/certificates` | 证照列表 | 需要 | `gsp:view` |
| POST | `/api/gsp/certificates` | 创建证照 | 需要 | `gsp:manage` |
| GET | `/api/gsp/certificates/expiring` | 即将到期证照 | 需要 | `gsp:view` |
| GET | `/api/gsp/certificates/{certificate_id}` | 证照详情 | 需要 | `gsp:view` |
| PUT | `/api/gsp/certificates/{certificate_id}` | 更新证照 | 需要 | `gsp:manage` |
| DELETE | `/api/gsp/certificates/{certificate_id}` | 删除证照 | 需要 | `gsp:manage` |
| POST | `/api/gsp/certificates/{certificate_id}/review` | 证照审核（首营资料审批） | 需要 | `gsp:manage` |
| GET | `/api/gsp/qualification/{entity_type}/{entity_id}` | 主体资质档案与准入结论 | 需要 | `gsp:view` |
| GET | `/api/gsp/certificates/{certificate_id}/attachments` | 证照附件列表 | 需要 | `gsp:view` |
| POST | `/api/gsp/certificates/{certificate_id}/attachments` | 上传证照附件 | 需要 | `gsp:manage` |
| GET | `/api/gsp/attachments/{attachment_id}/preview` | 在线预览证照附件 | 需要 | `gsp:view` |
| GET | `/api/gsp/attachments/{attachment_id}/download` | 下载证照附件 | 需要 | `gsp:view` |
| DELETE | `/api/gsp/attachments/{attachment_id}` | 删除证照附件 | 需要 | `gsp:manage` |
| GET | `/api/gsp/alerts` | GSP 到期预警（证照+批次） | 需要 | `gsp:view` |
| GET | `/api/gsp/alerts/summary` | GSP 预警统计 | 需要 | `gsp:view` |
| GET | `/api/gsp/batches` | 批次列表 | 需要 | `gsp:view` |
| POST | `/api/gsp/batches` | 创建批次 | 需要 | `gsp:manage` |
| GET | `/api/gsp/batches/expiring` | 近效期批次 | 需要 | `gsp:view` |
| GET | `/api/gsp/batches/{batch_id}` | 批次详情 | 需要 | `gsp:view` |
| PUT | `/api/gsp/batches/{batch_id}` | 更新批次 | 需要 | `gsp:manage` |
| DELETE | `/api/gsp/batches/{batch_id}` | 删除批次 | 需要 | `gsp:manage` |

### GET /api/gsp/certificates

**接口名称：** 证照列表

**认证：** 需要 Bearer Token

**所需权限：** `gsp:view`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| entity_type | 查询 | 字符串 | 否 |  | 关联对象类型 |
| entity_id | 查询 | 整数 | 否 |  | 关联对象 ID |
| status | 查询 | 字符串 | 否 |  | 状态 |
| review_status | 查询 | 字符串 | 否 |  |  |
| keyword | 查询 | 字符串 | 否 |  | 关键词 |
| page | 查询 | 整数 | 否 | 1 | 页码，从 1 开始 |
| size | 查询 | 整数 | 否 | 20 | 每页条数，1-1000 |

**响应示例（200/201）：**

```json
{
  "items": [
    {
      "id": 0,
      "entity_type": "string",
      "entity_id": 0,
      "entity_name": "string",
      "cert_type": "string",
      "cert_no": "string",
      "valid_from": "2026-01-01",
      "valid_to": "2026-01-01",
      "status": "string",
      "remark": "string",
      "review_status": "待审核",
      "reviewed_by": 0,
      "review_remark": "string",
      "reviewed_at": "2026-09-01T00:00:00",
      "effective_status": "有效",
      "days_to_expiry": 0,
      "attachment_count": 0,
      "created_at": "2026-09-01T00:00:00"
    }
  ],
  "total": 0,
  "page": 0,
  "size": 0
}
```

---

### POST /api/gsp/certificates

**接口名称：** 创建证照

**认证：** 需要 Bearer Token

**所需权限：** `gsp:manage`

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| entity_type | 字符串 | 是 | 关联对象类型 |
| entity_id | 整数 | 是 | 关联对象 ID |
| cert_type | 字符串 | 是 | 证照类型 |
| cert_no | 字符串 | 否 | 证照编号 |
| valid_from | 日期 | 否 | 生效日期 |
| valid_to | 日期 | 否 | 到期日期 |
| status | 字符串 | 否 | 状态 |
| remark | 字符串 | 否 | 备注 |

**请求示例：**

```json
{
  "entity_type": "string",
  "entity_id": 0,
  "cert_type": "string",
  "cert_no": "string",
  "valid_from": "2026-01-01",
  "valid_to": "2026-01-01",
  "status": "有效",
  "remark": "string"
}
```

**响应示例（200/201）：**

```json
{
  "id": 0,
  "entity_type": "string",
  "entity_id": 0,
  "entity_name": "string",
  "cert_type": "string",
  "cert_no": "string",
  "valid_from": "2026-01-01",
  "valid_to": "2026-01-01",
  "status": "string",
  "remark": "string",
  "review_status": "待审核",
  "reviewed_by": 0,
  "review_remark": "string",
  "reviewed_at": "2026-09-01T00:00:00",
  "effective_status": "有效",
  "days_to_expiry": 0,
  "attachment_count": 0,
  "created_at": "2026-09-01T00:00:00"
}
```

---

### GET /api/gsp/certificates/expiring

**接口名称：** 即将到期证照

**认证：** 需要 Bearer Token

**所需权限：** `gsp:view`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| days | 查询 | 整数 | 否 | 90 | 天数 |
| page | 查询 | 整数 | 否 | 1 | 页码，从 1 开始 |
| size | 查询 | 整数 | 否 | 20 | 每页条数，1-1000 |

**响应示例（200/201）：**

```json
{
  "items": [
    {
      "id": 0,
      "entity_type": "string",
      "entity_id": 0,
      "entity_name": "string",
      "cert_type": "string",
      "cert_no": "string",
      "valid_from": "2026-01-01",
      "valid_to": "2026-01-01",
      "status": "string",
      "remark": "string",
      "review_status": "待审核",
      "reviewed_by": 0,
      "review_remark": "string",
      "reviewed_at": "2026-09-01T00:00:00",
      "effective_status": "有效",
      "days_to_expiry": 0,
      "attachment_count": 0,
      "created_at": "2026-09-01T00:00:00"
    }
  ],
  "total": 0,
  "page": 0,
  "size": 0
}
```

---

### GET /api/gsp/certificates/{certificate_id}

**接口名称：** 证照详情

**认证：** 需要 Bearer Token

**所需权限：** `gsp:view`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| certificate_id | 路径 | 整数 | 是 |  | 证照 ID |

**响应示例（200/201）：**

```json
{
  "id": 0,
  "entity_type": "string",
  "entity_id": 0,
  "entity_name": "string",
  "cert_type": "string",
  "cert_no": "string",
  "valid_from": "2026-01-01",
  "valid_to": "2026-01-01",
  "status": "string",
  "remark": "string",
  "review_status": "待审核",
  "reviewed_by": 0,
  "review_remark": "string",
  "reviewed_at": "2026-09-01T00:00:00",
  "effective_status": "有效",
  "days_to_expiry": 0,
  "attachment_count": 0,
  "created_at": "2026-09-01T00:00:00"
}
```

---

### PUT /api/gsp/certificates/{certificate_id}

**接口名称：** 更新证照

**认证：** 需要 Bearer Token

**所需权限：** `gsp:manage`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| certificate_id | 路径 | 整数 | 是 |  | 证照 ID |

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| cert_type | 字符串 | 否 | 证照类型 |
| cert_no | 字符串 | 否 | 证照编号 |
| valid_from | 日期 | 否 | 生效日期 |
| valid_to | 日期 | 否 | 到期日期 |
| status | 字符串 | 否 | 状态 |
| remark | 字符串 | 否 | 备注 |

**请求示例：**

```json
{
  "cert_type": "string",
  "cert_no": "string",
  "valid_from": "2026-01-01",
  "valid_to": "2026-01-01",
  "status": "string",
  "remark": "string"
}
```

**响应示例（200/201）：**

```json
{
  "id": 0,
  "entity_type": "string",
  "entity_id": 0,
  "entity_name": "string",
  "cert_type": "string",
  "cert_no": "string",
  "valid_from": "2026-01-01",
  "valid_to": "2026-01-01",
  "status": "string",
  "remark": "string",
  "review_status": "待审核",
  "reviewed_by": 0,
  "review_remark": "string",
  "reviewed_at": "2026-09-01T00:00:00",
  "effective_status": "有效",
  "days_to_expiry": 0,
  "attachment_count": 0,
  "created_at": "2026-09-01T00:00:00"
}
```

---

### DELETE /api/gsp/certificates/{certificate_id}

**接口名称：** 删除证照

**认证：** 需要 Bearer Token

**所需权限：** `gsp:manage`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| certificate_id | 路径 | 整数 | 是 |  | 证照 ID |

**响应示例（200/201）：**

```json
{
  "message": "string"
}
```

---

### POST /api/gsp/certificates/{certificate_id}/review

**接口名称：** 证照审核（首营资料审批）

**认证：** 需要 Bearer Token

**所需权限：** `gsp:manage`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| certificate_id | 路径 | 整数 | 是 |  | 证照 ID |

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| action | 字符串 | 是 | approve=通过，reject=驳回 |
| remark | 字符串 | 否 | 审核意见/驳回原因 |

**请求示例：**

```json
{
  "action": "string",
  "remark": "string"
}
```

**响应示例（200/201）：**

```json
{
  "id": 0,
  "entity_type": "string",
  "entity_id": 0,
  "entity_name": "string",
  "cert_type": "string",
  "cert_no": "string",
  "valid_from": "2026-01-01",
  "valid_to": "2026-01-01",
  "status": "string",
  "remark": "string",
  "review_status": "待审核",
  "reviewed_by": 0,
  "review_remark": "string",
  "reviewed_at": "2026-09-01T00:00:00",
  "effective_status": "有效",
  "days_to_expiry": 0,
  "attachment_count": 0,
  "created_at": "2026-09-01T00:00:00"
}
```

---

### GET /api/gsp/qualification/{entity_type}/{entity_id}

**接口名称：** 主体资质档案与准入结论

**认证：** 需要 Bearer Token

**所需权限：** `gsp:view`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| entity_type | 路径 | 字符串 | 是 |  | 关联对象类型 |
| entity_id | 路径 | 整数 | 是 |  | 关联对象 ID |

**响应示例（200/201）：**

```json
{
  "entity_type": "string",
  "entity_id": 0,
  "entity_name": "string",
  "has_profile": false,
  "compliant": false,
  "blocking": [
    {
      "cert_id": 0,
      "cert_type": "string",
      "kind": "string",
      "detail": "string"
    }
  ],
  "warnings": [
    {
      "cert_id": 0,
      "cert_type": "string",
      "kind": "string",
      "detail": "string"
    }
  ],
  "certificates": [
    {
      "id": 0,
      "entity_type": "string",
      "entity_id": 0,
      "entity_name": "string",
      "cert_type": "string",
      "cert_no": "string",
      "valid_from": "2026-01-01",
      "valid_to": "2026-01-01",
      "status": "string",
      "remark": "string",
      "review_status": "待审核",
      "reviewed_by": 0,
      "review_remark": "string",
      "reviewed_at": "2026-09-01T00:00:00",
      "effective_status": "有效",
      "days_to_expiry": 0,
      "attachment_count": 0,
      "created_at": "2026-09-01T00:00:00"
    }
  ]
}
```

---

### GET /api/gsp/certificates/{certificate_id}/attachments

**接口名称：** 证照附件列表

**认证：** 需要 Bearer Token

**所需权限：** `gsp:view`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| certificate_id | 路径 | 整数 | 是 |  | 证照 ID |
| include_history | 查询 | 布尔 | 否 | False | 是否包含换证留档的历史版本 |

**响应示例（200/201）：**

```json
[
  {
    "id": 0,
    "certificate_id": 0,
    "file_name": "string",
    "content_type": "string",
    "size": 0,
    "uploaded_by": 0,
    "version": 1,
    "is_current": true,
    "kind": "other",
    "media_type": "application/octet-stream",
    "previewable": false,
    "created_at": "2026-09-01T00:00:00"
  }
]
```

---

### POST /api/gsp/certificates/{certificate_id}/attachments

**接口名称：** 上传证照附件

**认证：** 需要 Bearer Token

**所需权限：** `gsp:manage`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| certificate_id | 路径 | 整数 | 是 |  | 证照 ID |

**响应示例（200/201）：**

```json
{
  "id": 0,
  "certificate_id": 0,
  "file_name": "string",
  "content_type": "string",
  "size": 0,
  "uploaded_by": 0,
  "version": 1,
  "is_current": true,
  "kind": "other",
  "media_type": "application/octet-stream",
  "previewable": false,
  "created_at": "2026-09-01T00:00:00"
}
```

---

### GET /api/gsp/attachments/{attachment_id}/preview

**接口名称：** 在线预览证照附件

**说明：** 以 inline 方式回传扫描件，浏览器可直接渲染 PDF / JPG / PNG 等。

**认证：** 需要 Bearer Token

**所需权限：** `gsp:view`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| attachment_id | 路径 | 整数 | 是 |  |  |

---

### GET /api/gsp/attachments/{attachment_id}/download

**接口名称：** 下载证照附件

**认证：** 需要 Bearer Token

**所需权限：** `gsp:view`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| attachment_id | 路径 | 整数 | 是 |  |  |

---

### DELETE /api/gsp/attachments/{attachment_id}

**接口名称：** 删除证照附件

**认证：** 需要 Bearer Token

**所需权限：** `gsp:manage`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| attachment_id | 路径 | 整数 | 是 |  |  |

**响应示例（200/201）：**

```json
{
  "message": "string"
}
```

---

### GET /api/gsp/alerts

**接口名称：** GSP 到期预警（证照+批次）

**认证：** 需要 Bearer Token

**所需权限：** `gsp:view`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| category | 查询 | 字符串 | 否 | all |  |
| level | 查询 | 字符串 | 否 | all |  |
| days | 查询 | 整数 | 否 | 90 | level=all 时的预警窗口天数 |
| page | 查询 | 整数 | 否 | 1 | 页码，从 1 开始 |
| size | 查询 | 整数 | 否 | 20 | 每页条数，1-1000 |

**响应示例（200/201）：**

```json
{
  "items": [
    {
      "category": "string",
      "ref_id": 0,
      "title": "string",
      "subject": "string",
      "entity_type": "string",
      "entity_id": 0,
      "valid_to": "2026-01-01",
      "days_left": 0,
      "level": "string"
    }
  ],
  "total": 0,
  "page": 0,
  "size": 0
}
```

---

### GET /api/gsp/alerts/summary

**接口名称：** GSP 预警统计

**认证：** 需要 Bearer Token

**所需权限：** `gsp:view`

**响应示例（200/201）：**

```json
{
  "expired": 0,
  "within_30": 0,
  "within_60": 0,
  "within_90": 0,
  "pending_review": 0,
  "certificate_total": 0,
  "batch_total": 0
}
```

---

### GET /api/gsp/batches

**接口名称：** 批次列表

**认证：** 需要 Bearer Token

**所需权限：** `gsp:view`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| product_id | 查询 | 整数 | 否 |  | 商品 ID |
| status | 查询 | 字符串 | 否 |  | 状态 |
| keyword | 查询 | 字符串 | 否 |  | 关键词 |
| page | 查询 | 整数 | 否 | 1 | 页码，从 1 开始 |
| size | 查询 | 整数 | 否 | 20 | 每页条数，1-1000 |

**响应示例（200/201）：**

```json
{
  "items": [
    {
      "id": 0,
      "product_id": 0,
      "batch_no": "string",
      "production_date": "2026-01-01",
      "expiry_date": "2026-01-01",
      "quantity": 0,
      "status": "string",
      "remark": "string",
      "created_at": "2026-09-01T00:00:00"
    }
  ],
  "total": 0,
  "page": 0,
  "size": 0
}
```

---

### POST /api/gsp/batches

**接口名称：** 创建批次

**认证：** 需要 Bearer Token

**所需权限：** `gsp:manage`

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| product_id | 整数 | 是 | 商品 ID |
| batch_no | 字符串 | 是 | 批号 |
| production_date | 日期 | 否 | 生产日期 |
| expiry_date | 日期 | 否 | 有效期至 |
| quantity | 整数 | 否 | 数量 |
| status | 字符串 | 否 | 状态 |
| remark | 字符串 | 否 | 备注 |

**请求示例：**

```json
{
  "product_id": 0,
  "batch_no": "string",
  "production_date": "2026-01-01",
  "expiry_date": "2026-01-01",
  "quantity": 0,
  "status": "正常",
  "remark": "string"
}
```

**响应示例（200/201）：**

```json
{
  "id": 0,
  "product_id": 0,
  "batch_no": "string",
  "production_date": "2026-01-01",
  "expiry_date": "2026-01-01",
  "quantity": 0,
  "status": "string",
  "remark": "string",
  "created_at": "2026-09-01T00:00:00"
}
```

---

### GET /api/gsp/batches/expiring

**接口名称：** 近效期批次

**认证：** 需要 Bearer Token

**所需权限：** `gsp:view`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| days | 查询 | 整数 | 否 | 180 | 天数 |
| page | 查询 | 整数 | 否 | 1 | 页码，从 1 开始 |
| size | 查询 | 整数 | 否 | 20 | 每页条数，1-1000 |

**响应示例（200/201）：**

```json
{
  "items": [
    {
      "id": 0,
      "product_id": 0,
      "batch_no": "string",
      "production_date": "2026-01-01",
      "expiry_date": "2026-01-01",
      "quantity": 0,
      "status": "string",
      "remark": "string",
      "created_at": "2026-09-01T00:00:00"
    }
  ],
  "total": 0,
  "page": 0,
  "size": 0
}
```

---

### GET /api/gsp/batches/{batch_id}

**接口名称：** 批次详情

**认证：** 需要 Bearer Token

**所需权限：** `gsp:view`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| batch_id | 路径 | 整数 | 是 |  | 批次 ID |

**响应示例（200/201）：**

```json
{
  "id": 0,
  "product_id": 0,
  "batch_no": "string",
  "production_date": "2026-01-01",
  "expiry_date": "2026-01-01",
  "quantity": 0,
  "status": "string",
  "remark": "string",
  "created_at": "2026-09-01T00:00:00"
}
```

---

### PUT /api/gsp/batches/{batch_id}

**接口名称：** 更新批次

**认证：** 需要 Bearer Token

**所需权限：** `gsp:manage`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| batch_id | 路径 | 整数 | 是 |  | 批次 ID |

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| production_date | 日期 | 否 | 生产日期 |
| expiry_date | 日期 | 否 | 有效期至 |
| quantity | 整数 | 否 | 数量 |
| status | 字符串 | 否 | 状态 |
| remark | 字符串 | 否 | 备注 |

**请求示例：**

```json
{
  "production_date": "2026-01-01",
  "expiry_date": "2026-01-01",
  "quantity": 0,
  "status": "string",
  "remark": "string"
}
```

**响应示例（200/201）：**

```json
{
  "id": 0,
  "product_id": 0,
  "batch_no": "string",
  "production_date": "2026-01-01",
  "expiry_date": "2026-01-01",
  "quantity": 0,
  "status": "string",
  "remark": "string",
  "created_at": "2026-09-01T00:00:00"
}
```

---

### DELETE /api/gsp/batches/{batch_id}

**接口名称：** 删除批次

**认证：** 需要 Bearer Token

**所需权限：** `gsp:manage`

**请求参数：**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| batch_id | 路径 | 整数 | 是 |  | 批次 ID |

**响应示例（200/201）：**

```json
{
  "message": "string"
}
```

---

## 健康检查

| 方法 | 路径 | 接口名称 | 认证 | 所需权限 |
| --- | --- | --- | --- | --- |
| GET | `/` | 服务健康检查 | 不需要 | — |

### GET /

**接口名称：** 服务健康检查

**认证：** 不需要

**响应示例（200/201）：**

```json
"string"
```

---
