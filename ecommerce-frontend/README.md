# Ecommerce Frontend

小哲电商商城前台和管理后台。项目使用 Vite 多入口构建，生产环境由 Nginx 托管并将 `/api` 代理到电商后端。

## 技术栈

- React 19
- TypeScript 5.9
- Vite 7
- Lucide React
- Nginx 1.27

## 页面入口

| 页面 | 开发地址 |
| --- | --- |
| 商城 | <http://localhost:5174> |
| 管理后台 | <http://localhost:5174/admin> |

商城和管理后台使用浏览器 Cookie 登录。开发服务器已将 `/api` 代理到 `http://localhost:8081`，无需在前端配置后端绝对地址。

## 开发

```powershell
npm ci
npm run dev
```

前置条件：电商后端已在 `8081` 端口启动。

## 构建

```powershell
npm run build
npm run preview
docker build -t xiaozhe-ecommerce-frontend .
```

构建输出位于 `dist/`，其中：

- `index.html` 是商城入口。
- `admin/index.html` 是管理后台入口。

生产 Nginx 配置支持商城与管理后台的前端深层路由，并通过 Compose 服务名 `ecommerce-backend` 转发 API。

演示登录账号见[仓库根文档](../README.md#快速启动电商应用)。
