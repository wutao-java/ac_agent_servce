# Ecommerce Backend

小哲电商 Spring Boot API 服务，负责商城、管理后台、客服网关、身份认证和业务数据归属校验。前端已经拆分为同级项目 `ecommerce-frontend`，本服务不再托管静态页面。

## 技术栈

- Java 17
- Spring Boot 3.3.3
- Spring Web、Spring Security、Spring Data JPA
- MySQL 8
- Knife4j/OpenAPI

## 推荐启动方式

从仓库根目录使用统一 Compose 启动，参见 [部署说明](../deploy/README.md)。

本机直接启动时，需要安装 JDK 17 和 Maven，并显式指定可访问的 MySQL 地址：

```powershell
$env:SPRING_DATASOURCE_URL = "jdbc:mysql://localhost:3306/agent_demo?useUnicode=true&characterEncoding=utf8&serverTimezone=Asia/Shanghai"
$env:SPRING_DATASOURCE_USERNAME = "root"
$env:SPRING_DATASOURCE_PASSWORD = "your-password"
$env:AGENT_SERVICE_AUTH_TOKEN = "your-service-token"
mvn spring-boot:run -Dspring-boot.run.profiles=course-debug
```

服务默认监听 `8081`。

## 构建

```powershell
mvn test
mvn package
docker build -t xiaozhe-ecommerce-backend .
```

当前仓库尚未提供 Java 测试用例，`mvn test` 主要验证依赖解析和源码编译。

## API 分组

| 路径前缀 | 用途 |
| --- | --- |
| `/api/auth` | 登录、当前账号、退出登录 |
| `/api/shop` | 商品、购物车、订单、支付和余额 |
| `/api/admin` | 商品、活动、订单和售后管理 |
| `/api/customer-service` | 商城客服 Agent 网关 |
| `/api/orders`、`/api/users` | 用户或 Agent 服务访问的业务数据 |
| `/api/refund`、`/api/after-sale`、`/api/approvals` | 退款、售后和人工审批 |

API 文档：

- Knife4j：<http://localhost:8081/doc.html>
- OpenAPI JSON：<http://localhost:8081/v3/api-docs>
- 健康检查：<http://localhost:8081/actuator/health>

## Agent 服务配置

| 环境变量 | 说明 |
| --- | --- |
| `AGENT_SERVICE_BASE_URL` | Agent 服务基地址，默认 `http://host.docker.internal:8000` |
| `AGENT_SERVICE_AUTH_TOKEN` | 电商后端与 Agent 双向调用使用的共享服务令牌 |

电商后端调用 Agent 时会携带 `X-Agent-Service-Token`。Agent 调用受保护业务 API 时还必须携带同一服务令牌和 `X-Agent-User-Id`，由后端执行用户归属校验。管理员审批决定不能由 Agent 服务身份直接执行。
