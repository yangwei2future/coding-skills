---
name: dip-openapi-token
description: DIP OpenAPI IDaaS Token 获取工具。通过浏览器登录自动获取 IDaaS Access Token，供 DIP 数智平台 OpenAPI 接口调用使用。适用场景：用户需要接入 DIP OpenAPI、获取/刷新 IDaaS token、测试或调试 DIP 开放平台接口。触发关键词：获取 token、IDaaS 登录、DIP OpenAPI 认证、刷新 token、access token。
---

# DIP OpenAPI IDaaS Token 获取工具

## 用途

获取 DIP 数智平台 OpenAPI 所需的 IDaaS Access Token，支持 test / ontest / prod 三套环境。

整个流程分三步：
1. 自动打开浏览器到登录页，用户完成账号登录
2. 用户从登录后的页面复制 Refresh Token
3. 脚本自动调用 IDaaS `/api/token` 接口换取 Access Token

> **与 `dip-idaas-auth` 的区别**：`dip-idaas-auth` 使用 IDaaS SDK + 飞书扫码，本 skill 使用浏览器账号登录 + refresh_token 标准 OAuth 方式，是 DIP OpenAPI 接入文档要求的方式。

---

## 快速使用

直接运行脚本，传入目标环境参数：

```bash
bash ~/.claude/skills/dip-openapi-token/scripts/get_token.sh [test|ontest|prod]
```

脚本会：
1. 自动用 `open`（macOS）或 `xdg-open`（Linux）打开浏览器登录页
2. 提示用户粘贴 Refresh Token
3. 自动调用 IDaaS API，输出可直接使用的 `Bearer <access_token>`

---

## 环境配置

| 环境 | 登录地址 | IDaaS Token API |
|------|---------|-----------------|
| test | `https://account-ontest.lixiang.com/login?client_id=4wqmIzTQraqJn8QgC4NonY&redirect_uri=https%3A%2F%2Fdmp-api.ontest.k8s.chj.cloud%2F` | `https://id-ontest.lixiang.com/api/token` |
| ontest | `https://dmp-api.prod.k8s.chj.cloud/` | `https://id.lixiang.com/api/token` |
| prod | `https://dmp-api.prod.k8s.chj.cloud/` | `https://id.lixiang.com/api/token` |

`client_id` 固定为：`4wqmIzTQraqJn8QgC4NonY`

---

## 手动获取 Token（不使用脚本）

若需要手动操作，步骤如下：

**步骤 1 - 用户登录**：根据环境打开对应登录链接完成账号登录。

**步骤 2 - 复制 Refresh Token**：登录后跳转到 Token 展示页，点击右下角「复制」按钮。

**步骤 3 - 换取 Access Token**：

```bash
# test 环境
curl -X POST 'https://id-ontest.lixiang.com/api/token' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode 'client_id=4wqmIzTQraqJn8QgC4NonY' \
  --data-urlencode 'grant_type=refresh_token' \
  --data-urlencode 'refresh_token=<步骤2获取的值>'

# ontest/prod 环境
curl -X POST 'https://id.lixiang.com/api/token' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode 'client_id=4wqmIzTQraqJn8QgC4NonY' \
  --data-urlencode 'grant_type=refresh_token' \
  --data-urlencode 'refresh_token=<步骤2获取的值>'
```

---

## 使用 Token 调用 OpenAPI

获取到 Access Token 后，在 HTTP 请求 Header 中携带：

```
Authorization: Bearer <access_token>
```

---

## 注意事项

- **勿频繁刷新**：在 `expires_in` 时间内复用同一 Token，不要每次请求都刷新
- **Token 过期处理**：接口返回过期时再调用脚本重新获取
- **Refresh Token 安全**：Refresh Token 的重要性等同于密码，不要泄露
- **可配置化**：在代码中将 `refresh_token` 做成可配置项，便于失效后替换

---

## 常见问题

| 问题 | 解决方案 |
|------|---------|
| `invalid_grant` | Refresh Token 已过期，重新执行脚本登录 |
| 获取失败无报错 | 确认已连接公司 VPN |
| Token 接口无法访问 | 检查网络，确保可以访问 `id-ontest.lixiang.com` 或 `id.lixiang.com` |
| 粘贴后仍失败 | 检查 Refresh Token 前后是否有多余空格 |
