# Agent Debug UI

面向 Agent 开发和课程演示的调试界面，用于查看对话、工作流、运行轨迹、评测和反馈。它不是商城用户前台，也不参与电商生产部署。

## 技术栈

- React 18
- TypeScript 5.8
- Vite 8

## 配置

可在本目录创建 `.env.local` 覆盖服务地址：

```dotenv
VITE_AGENT_BASE_URL=http://localhost:8000
VITE_ECOMMERCE_BASE_URL=http://localhost:8081
```

默认值与上面一致。电商后端需要启用 `course-debug` Profile，调试 UI 才能读取课程调试上下文。

## 开发与构建

```powershell
npm ci
npm run dev
npm run build
```

开发地址：<http://localhost:5173>。

## 预期 Agent 接口

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| `GET` | `/capabilities` | 查询 Agent 版本与能力 |
| `POST` | `/chat` | 发起对话 |
| `POST` | `/chat/resume` | 恢复人工确认后的工作流 |
| `GET` | `/sessions/{sessionId}/trace` | 查询运行轨迹 |
| `POST` | `/eval/run` | 执行评测 |
| `POST` | `/feedback/submit` | 提交反馈 |

当前 `agent-center` 尚未完整提供这些接口，因此调试 UI 主要用于后续小哲 Agent 的开发验收。
