# GoBot

GoBot 是一个正在重构中的线索发现与 Campaign Intelligence 控制台，当前技术栈包括：

- `Python 3.12`
- `uv`
- `FastAPI`
- `Vue 3`
- `Scrapling`
- `SQLite`

项目目前仍处于迁移阶段。旧仓库 `business-leads-ai-automation` 只作为逻辑参考，所有新的实现都放在当前仓库中。

英文文档见 [README.md](README.md)。

## 当前状态

目前已经实现：

- 基于 FastAPI 的后端服务
- 基于 SQLite 的任务与结果持久化
- 基于 Scrapling 的 Google Maps 抓取
- `scrape_job` 生命周期管理：`queued`、`running`、`completed`、`failed`
- 与抓取任务关联的 `campaign` 模型
- 线索的 intelligence 评分与活动汇总指标
- 基于 Vue 3 的新控制台工作区：
  - `Overview`
  - `Campaigns`
  - `Jobs`
  - `System`
- 抽屉式活动创建流程
- `en` / `zh-CN` 双语界面支持
- FastAPI 直接托管前端构建产物

尚未实现：

- CRM 集成
- 外呼或营销自动化
- 邮件或 WhatsApp 内容生成
- Google Maps 之外的多数据源抓取
- 登录鉴权与多用户隔离

## 仓库结构

```text
GoBot/
|-- backend/                  # FastAPI 应用、领域逻辑、测试
|-- frontend/                 # Vue 3 + Vite 前端
|-- docs/plans/               # 实施计划文档
|-- .env.example
|-- README.md
`-- README_CN.md
```

后端核心目录：

```text
backend/app/
|-- api/                      # REST 路由
|-- core/                     # 配置、数据库、任务编排
|-- schemas/                  # Pydantic 模型
`-- services/                 # 抓取与 intelligence 服务
```

## 架构说明

### 后端

后端当前负责：

- `campaign` 的创建与查询
- 关联 `scrape_job` 的执行
- 通过 Scrapling 抓取 Google Maps
- SQLite 持久化任务与活动结果
- 线索归一化、去重、评分与汇总
- 在存在前端构建产物时直接提供静态资源

关键文件：

- [backend/app/main.py](backend/app/main.py)
- [backend/app/api/routes/campaigns.py](backend/app/api/routes/campaigns.py)
- [backend/app/api/routes/scrape_jobs.py](backend/app/api/routes/scrape_jobs.py)
- [backend/app/api/routes/health.py](backend/app/api/routes/health.py)
- [backend/app/core/database.py](backend/app/core/database.py)
- [backend/app/core/job_manager.py](backend/app/core/job_manager.py)
- [backend/app/services/scraping/normalizers.py](backend/app/services/scraping/normalizers.py)
- [backend/app/services/intelligence/scoring.py](backend/app/services/intelligence/scoring.py)

### 前端

前端现在采用“Campaign 优先”的工作区结构：

- `Overview`：展示系统健康度与队列概览
- `Campaigns`：主工作台，包含活动队列、选中活动摘要与已评分线索
- `Jobs`：运行中心，查看原始任务与原始结果
- `System`：查看运行时细节
- `New Campaign` 以抽屉形式打开，而不是长期占据主屏
- 支持 `en` 与 `zh-CN`，会根据浏览器语言和本地存储自动选择语言

关键文件：

- [frontend/src/App.vue](frontend/src/App.vue)
- [frontend/src/lib/i18n.ts](frontend/src/lib/i18n.ts)
- [frontend/src/composables/useConsoleWorkspace.ts](frontend/src/composables/useConsoleWorkspace.ts)
- [frontend/src/components/layout/ConsoleShell.vue](frontend/src/components/layout/ConsoleShell.vue)
- [frontend/src/components/campaigns/CampaignCreationDrawer.vue](frontend/src/components/campaigns/CampaignCreationDrawer.vue)
- [frontend/src/components/campaigns/CampaignWorkbench.vue](frontend/src/components/campaigns/CampaignWorkbench.vue)
- [frontend/src/components/jobs/OperationsCenter.vue](frontend/src/components/jobs/OperationsCenter.vue)

## 运行前准备

- Python `3.12`
- Node.js `22+`
- `uv`
- `pnpm`

如果本机 `uv` cache 目录有权限问题，建议继续使用 `--no-cache`。

当前抓取流程不会启动浏览器。`playwright` 仍保留在后端依赖中，是因为 `Scrapling 0.4.2` 内部仍会导入它。

## 环境配置

复制示例环境文件：

```powershell
Copy-Item .env.example .env
```

当前支持的环境变量：

- `BACKEND_HOST`
- `BACKEND_PORT`
- `SCRAPER_DATABASE_PATH`
- `SCRAPER_TIMEOUT_MS`
- `SCRAPER_VERIFY_TLS`

SQLite 数据库会在后端首次启动时自动创建。

## 开发模式

### 1. 启动后端

安装依赖：

```powershell
cd backend
uv sync --no-cache
```

启动服务：

```powershell
uv run --no-cache main.py
```

默认地址为 `http://127.0.0.1:8000`。

### 2. 启动前端

安装依赖：

```powershell
cd frontend
pnpm.cmd install
```

启动开发服务器：

```powershell
pnpm.cmd dev
```

默认地址为 `http://127.0.0.1:5173`，并会把 `/api` 请求代理到后端。

## 本地一体化运行

如果希望由 FastAPI 直接托管前端页面：

1. 先构建前端：

```powershell
cd frontend
pnpm.cmd build
```

2. 再启动后端：

```powershell
cd ..\backend
uv run --no-cache main.py
```

然后访问：

- `http://127.0.0.1:8000/` 查看前端页面
- `http://127.0.0.1:8000/docs` 查看 Swagger 文档

## API 概览

### Health

- `GET /api/v1/health`

### Campaigns

- `POST /api/v1/campaigns`
- `GET /api/v1/campaigns`
- `GET /api/v1/campaigns/{campaign_id}`

### Scrape Jobs

- `POST /api/v1/scrape-jobs`
- `GET /api/v1/scrape-jobs`
- `GET /api/v1/scrape-jobs/{job_id}`
- `GET /api/v1/scrape-jobs/{job_id}/results`

## Campaign 请求示例

```json
{
  "name": "Jakarta Coffee Shops",
  "industry": "restaurant",
  "location": "Jakarta",
  "query": "Coffee shops Jakarta Selatan",
  "max_results": 20,
  "source": "google_maps"
}
```

提交一个 `campaign` 后，系统会按以下流程执行：

1. 创建活动记录
2. 创建关联的抓取任务
3. 异步执行抓取
4. 对抓取结果进行 intelligence 评分
5. 将 enrich 后的活动结果写入 SQLite

## 验证命令

后端验证：

```powershell
cd backend
python -m compileall .
uv run --no-cache pytest tests/test_health_api.py -v --basetemp=.pytest-tmp
```

前端验证：

```powershell
cd frontend
pnpm.cmd test:unit
pnpm.cmd build
```

当前前端测试已覆盖：

- i18n 初始化与语言解析
- console workspace 状态层
- console shell 渲染
- 活动创建抽屉行为
- 活动工作台渲染
- 运行中心渲染

## 已知限制

- 当前只支持 Google Maps 抓取
- 如果 Google Maps 内部 payload 结构变化，解析逻辑可能需要调整
- `SCRAPER_VERIFY_TLS=false` 仍是部分 Windows 环境下的实用默认值，用于绕过 `curl_cffi` 证书链校验失败
- 界面已经支持双语，但历史组件仍可能有少量未完全本地化的文案
- 还没有登录认证、多用户隔离与权限控制
- 项目仍处于迁移中，命名和边界后续可能继续调整
- 后端全量 `pytest` 在部分 Windows 环境下可能受临时目录权限影响

## 许可证

本项目遵循 [LICENSE](LICENSE) 中的许可条款。
