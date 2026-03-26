# 任务：邮箱管理与邮件收发

状态：已完成  
创建：2026-03-26 20:00  
更新：2026-03-26 21:40

## 需求摘要

- 新增邮箱管理菜单。
- 支持添加多个邮箱，并为邮箱添加备注。
- 选择不同邮箱后，分别展示收件箱与已发送邮件列表。
- 支持手动发送邮件。
- 支持从已采集线索中选择邮箱作为收件人。
- 首版不包含 AI 写信，仅完成邮箱接入、邮件读取与发送闭环。

## 关键决策

- 首版仅支持预设邮箱服务商，不开放自定义 IMAP/SMTP。
- 认证方式使用邮箱地址加授权码或应用专用密码。
- 邮件列表采用进入页面加载和手动刷新，不做后台轮询。
- 本地敏感凭据使用 Windows DPAPI 加密存储。
- 线索集成范围限定为“从 lead email 导入收件人”，不扩展为完整联系人系统。

## 实现结果

- [x] 1. 新增后端邮箱模型、SQLite 持久化、加密凭据存储与邮件服务。
- [x] 2. 新增邮件 API、线索收件人接口，以及后端数据库/API 测试。
- [x] 3. 新增前端 Mail 菜单、邮箱工作台、收件/已发送列表、邮件详情与写信面板。
- [x] 4. 修复前端邮件接入后的 `App` 启动 mock、轮询测试与构建校验。

## 关键文件

- `backend/app/schemas/mail.py`
- `backend/app/services/mail/providers.py`
- `backend/app/services/mail/crypto.py`
- `backend/app/services/mail/service.py`
- `backend/app/api/routes/mail.py`
- `backend/app/core/database.py`
- `backend/tests/test_mail_api.py`
- `backend/tests/test_database.py`
- `frontend/src/components/mail/MailWorkspace.vue`
- `frontend/src/App.vue`
- `frontend/src/lib/api.ts`
- `frontend/src/types.ts`
- `frontend/src/locales/en.ts`
- `frontend/src/locales/zh-CN.ts`
- `frontend/src/App.locale-switch.test.ts`
- `frontend/src/App.polling.test.ts`

## 验证结果

- 前端单测通过：
  `pnpm.cmd test:unit -- src/App.locale-switch.test.ts src/App.polling.test.ts src/components/layout/ConsoleShell.test.ts`
- 前端构建通过：
  `pnpm.cmd build`
- 后端测试通过：
  `.\\.venv\\Scripts\\python.exe -m pytest tests/test_database.py tests/test_mail_api.py --basetemp .verification-db`

## 后续建议

- 增加邮箱删除、断开连接、重连授权码等管理动作。
- 为邮件列表补充分页、搜索与未读筛选。
- 在 lead 详情和邮件发送之间建立更直接的上下文联动。
- 下一阶段再接入 AI 邮件草稿生成与模板能力。
