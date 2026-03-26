# GoBot

GoBot 是一个正在重构中的线索发现与 campaign intelligence 控制台，当前技术栈为：

- `Python 3.12`
- `uv`
- `FastAPI`
- `Vue 3`
- `Playwright`
- `SQLite`

该项目目前处于迁移阶段。旧仓库 `business-leads-ai-automation` 只作为业务逻辑参考，所有新实现都在当前仓库中完成。

英文文档见 [README.md](README.md)。

## 当前状态

已实现的能力：

- 基于 FastAPI 的后端服务
- 基于 SQLite 的任务和结果持久化
- 基于 Playwright 的 Google Maps 抓取
- `scrape job` 生命周期管理：`queued`、`running`、`completed`、`failed`
- 与 `scrape job` 关联的 `campaign` 领域模型
- campaign 结果的 lead intelligence 评分
- 基于 Vue 3 的前端控制台，支持：
  - 发起 campaign
  - 查看 campaign 队列
  - 查看 intelligence 评分后的 leads
  - 查看底层执行 job 与服务健康状态
- FastAPI 直接托管前端构建产物

尚未实现的能力：

- CRM 集成
- 外呼或营销自动化
- 邮件或 WhatsApp 内容生成
- Google Maps 之外的多数据源抓取
- 更完整的高级分析能力

## 仓库结构

```text
GoBot/
|-- backend/                  # FastAPI、领域逻辑、测试
|-- frontend/                 # Vue 3 + Vite 前端
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
- 通过 Playwright 抓取 Google Maps
- 将 jobs 与 campaign 结果持久化到 SQLite
- 对 leads 做 intelligence 评分并生成 summary
- 在存在前端构建产物时直接提供静态资源服务

关键文件：

- [backend/app/main.py](backend/app/main.py)
- [backend/app/api/routes/campaigns.py](backend/app/api/routes/campaigns.py)
- [backend/app/api/routes/scrape_jobs.py](backend/app/api/routes/scrape_jobs.py)
- [backend/app/core/database.py](backend/app/core/database.py)
- [backend/app/core/job_manager.py](backend/app/core/job_manager.py)
- [backend/app/services/scraping/providers/google_maps.py](backend/app/services/scraping/providers/google_maps.py)
- [backend/app/services/intelligence/scoring.py](backend/app/services/intelligence/scoring.py)

### 前端

前端目前采用 “campaign 优先” 的信息架构，把 campaign 作为主工作流，同时保留原始 scrape job 作为执行遥测视图。

主要界面包括：

- campaign 创建表单
- campaign 队列
- campaign intelligence 结果表格
- 关联 scrape job 详情
- 后端健康状态卡片

关键文件：

- [frontend/src/App.vue](frontend/src/App.vue)
- [frontend/src/components/CampaignComposer.vue](frontend/src/components/CampaignComposer.vue)
- [frontend/src/components/CampaignList.vue](frontend/src/components/CampaignList.vue)
- [frontend/src/components/CampaignResults.vue](frontend/src/components/CampaignResults.vue)
- [frontend/src/lib/api.ts](frontend/src/lib/api.ts)

## 运行前准备

需要安装：

- Python `3.12`
- Node.js `22+`
- `uv`
- `pnpm`

抓取前还需要安装 Playwright 浏览器：

```powershell
cd backend
uv run --no-cache playwright install chromium
```

如果你本机的 `uv` cache 目录存在权限问题，建议在 `uv` 命令中继续带上 `--no-cache`。

## 环境配置

复制示例环境文件：

```powershell
Copy-Item .env.example .env
```

当前支持的环境变量：

- `BACKEND_HOST`
- `BACKEND_PORT`
- `SCRAPER_DATABASE_PATH`
- `SCRAPER_HEADLESS`
- `SCRAPER_TIMEOUT_MS`
- `SCRAPER_SCROLL_PAUSE_MS`
- `SCRAPER_MAX_SCROLL_ATTEMPTS`

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

当前 API 包括：

### 健康检查

- `GET /api/v1/health`

### Campaign

- `POST /api/v1/campaigns`
- `GET /api/v1/campaigns`
- `GET /api/v1/campaigns/{campaign_id}`

### Scrape Job

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

提交一个 campaign 后，系统会按如下流程执行：

1. 创建 campaign 记录
2. 创建关联的 scrape job
3. 异步执行抓取
4. 对抓取结果进行 intelligence 评分
5. 将 enrich 后的 campaign 结果写入 SQLite

## 验证命令

后端验证：

```powershell
cd backend
python -m compileall .
```

前端验证：

```powershell
cd frontend
pnpm.cmd exec vue-tsc --noEmit
pnpm.cmd build
```

当前已覆盖的测试方向：

- 数据库存储
- lead 归一化
- intelligence 评分

## 已知限制

- 当前只支持 Google Maps 抓取
- 如果 Google Maps DOM 结构变化，抓取选择器可能需要更新
- 当前前端重点是 campaign 与执行遥测，不是完整 BI 仪表盘
- 还没有认证、多用户隔离或权限控制
- 项目仍处于迁移中，部分命名和边界后续可能继续调整

## 许可证

本项目遵循 [LICENSE](LICENSE) 中的许可条款。
