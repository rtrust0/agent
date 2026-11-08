# RBAC / 平台数据库详细设计说明（V3）

> 数据库：SQLite（开发）→ MySQL（上线）
> 文件：`docs/design/db/`
> 设计依据：`docs/spec/PROJECT_SPEC_V3.md` + `docs/design/plans/*-*-plan.md` + `chenguang-agent-platform-v4` 后端真实 ORM

---

## 一、产物

| 文件 | 说明 |
|---|---|
| `script.sql` | 建表脚本：23 张表 + 索引 |
| `init-data.sql` | 初始化数据：71 权限码、3 角色、3 用户、授权关系、业务演示数据 |
| `rbac.db` | SQLite 数据库文件（由上述两个脚本生成） |
| `README.md` | 本说明 |

### 重建命令（SQLite）

```bash
cd docs/design/db
rm -f rbac.db
python - <<'PY'
import sqlite3
conn = sqlite3.connect('rbac.db')
for f in ('script.sql', 'init-data.sql'):
    conn.executescript(open(f, encoding='utf-8').read())
conn.close()
PY
```

---

## 二、表清单（23 张）

### 2.1 核心 RBAC（7 张）

| 表 | 来源 | 说明 |
|---|---|---|
| `users` | V1/V2 + V3 | 用户；V3 新增 `data_scope`、`created_by` |
| `roles` | V1/V2 | 角色 |
| `permissions` | V1/V2 + V3 | 权限码（V3 扩展为 71 个） |
| `user_roles` | V1/V2 | 用户-角色（复合主键） |
| `role_permissions` | V1/V2 | 角色-权限（复合主键） |
| `audit_logs` | V3 + system-extension-plan | 权限操作审计日志 |
| `permission_applications` | V3 | 权限申请与审批 |

### 2.2 业务模块（11 张，后端 ORM 已实现）

| 表 | 来源 | 说明 |
|---|---|---|
| `model_providers` | provider/model.py | 模型供应商 |
| `models` | model/model.py | 大语言模型 |
| `agents` | agent/model.py | Agent |
| `agent_versions` | agent/model.py | Agent 版本 |
| `prompts` | prompt/model.py | Prompt 模板 |
| `prompt_versions` | prompt/model.py | Prompt 版本 |
| `knowledge_bases` | knowledge/model.py | 知识库 |
| `documents` | knowledge/model.py | 知识库文档 |
| `segments` | knowledge/model.py | 文档分段 |
| `tools` | tool/model.py | 工具 |
| （无） | — | 其余业务表见 V1 待实现清单 |

### 2.3 计划新增（5 张）

| 表 | 来源 | 说明 |
|---|---|---|
| `conversations` | analytics-plan + conversation-plan | 对话（两版合并，见第四节） |
| `conversation_turns` | conversation-plan | 对话轮次与链路追踪 |
| `api_keys` | system-extension-plan | API 密钥 |
| `alert_rules` | system-extension-plan | 告警规则 |
| `alerts` | system-extension-plan | 告警记录 |
| `system_settings` | system-extension-plan | 系统配置（单行） |

---

## 三、ER 关系概览

```
users ──M:N──> roles ──M:N──> permissions
  │                              (user_roles / role_permissions)
  │
  ├──< permission_applications >── users (approver)
  ├──< audit_logs
  └──< conversations >── agents ──> models ──> model_providers
                         │            │
                         └──< agent_versions
                                      └──< conversation_turns

prompts ──< prompt_versions
knowledge_bases ──< documents ──< segments
tools
api_keys / alert_rules / alerts / system_settings（独立）
```

---

## 四、计划冲突与收敛（重要）

### 4.1 `conversations` 两版计划字段不一致

| 字段 | analytics-plan | conversation-plan | 本设计采用 | 说明 |
|---|---|---|---|---|
| agent_id | `int`（FK agents.id） | `str` | **INTEGER（FK agents.id）** | 统一为整型 ID，保证引用完整 |
| agent_name | 无 | `str` | 保留 | 冗余名称，便于列表展示 |
| model_id | `int`（FK models.id） | 无 | 保留 | analytics 按模型聚合需要 |
| user_id | `int` | `str` | **INTEGER（FK users.id）** | 统一为整型 ID |
| cost / total_cost | `cost Numeric(12,4)` | `total_cost Numeric(12,6)` | **total_cost Numeric(12,6)** | 统一命名；analytics 的 `cost` 读 `total_cost` |
| latency_ms / total_duration | `latency_ms` | `total_duration` | **latency_ms** | 语义相同，保留 `latency_ms` |
| turn_count | 无 | `int` | 保留 | |
| input/output/total_tokens | input/output | total_tokens | 三者都保留 | 便于统计 |
| rating / tags / needs_optimization | 有 | 无 | 保留 | analytics 需要 |
| annotation | 无 | JSON | 保留 | conversation 标注需要 |
| satisfaction / started_at / ended_at | 有 | 有 | 保留 | 两版一致 |

> **后续动作**：analytics 计划的 Repository 需将 `cost` 改为 `total_cost`、`total_duration` 改为 `latency_ms`；conversation 计划的 Schema 需将 `agent_id/user_id` 由 `str` 改为 `int`。这是两版计划合并的必然收敛，已在本设计固定。

### 4.2 `audit_logs` 两处定义不一致

| 字段 | V3 | system-extension-plan | 本设计 |
|---|---|---|---|
| user_id | INTEGER | String(50) | INTEGER（可空，FK users ON DELETE SET NULL） |
| action | String(50) | String(20) | VARCHAR(50) |
| module | String(50) | String(30) | VARCHAR(50) |
| target_id | String(100) | String(50) | VARCHAR(100) |
| user_agent | 无 | String(300) | 保留 |
| updated_at | 无 | BaseModel 有 | **不设**（审计日志只增不改不删） |

---

## 五、V3 关键设计

### 5.1 资源级数据权限

`users.data_scope`（`own` / `dept` / `all`，默认 `own`）+ `users.created_by`（数据归属）：

| 值 | 过滤规则 |
|---|---|
| `own` | `WHERE created_by = current_user.id` |
| `dept` | `WHERE department_id = current_user.department_id`（部门字段在业务表扩展时补充） |
| `all` | 无额外条件 |

> 说明：当前业务表使用 `created_by`（用户名，VARCHAR）而非部门 ID。若启用 `dept` 范围，需在对应业务表补充 `department_id`（V3 未强制，保持 V1 现状）。

### 5.2 审计日志

- 只增不改不删；`user_id` 可空（用户删除后保留记录，`username` 仍可追溯）；
- 索引：`user_id`、`action`、`module`、`created_at`。

### 5.3 权限申请与审批

- `status`：`pending` / `approved` / `rejected` / `expired`；
- `expired_at` 为空表示永久授权；
- `approver_id` 可空，审批后写入。

---

## 六、权限码与角色授权

### 6.1 权限码（71 个）

- 核心 27：user 7、role 6、permission 5、system 4、data_scope 3、approval 2
- 业务 44：dashboard 1、agent 8、model 7、prompt 7、knowledge 9、tool 7、conversation 4、analytics 1

### 6.2 角色默认授权

| 角色 | 权限数 | 说明 |
|---|---:|---|
| `super_admin` | 71 | 全部权限（且 `is_superuser` 直接放行） |
| `ops_admin` | 45 | 核心读+增改、`data_scope:dept`、`approval:apply`、业务可写（无删除/供应商管理/系统配置） |
| `viewer` | 23 | 核心只读、`data_scope:own`、`approval:apply`、业务只读 |

### 6.3 演示账号

| 账号 | 密码 | 角色 | data_scope |
|---|---|---|---|
| `admin` | `123456` | super_admin | all |
| `ops` | `123456` | ops_admin | dept |
| `viewer` | `123456` | viewer | own |

> 密码为 bcrypt 哈希（rounds=12），已验证 `123456` 可正确校验。

---

## 七、初始化数据概览

| 表 | 条数 | 内容 |
|---|---:|---|
| permissions | 71 | 全部权限码 |
| roles | 3 | super_admin / ops_admin / viewer |
| users | 3 | admin / ops / viewer |
| user_roles | 3 | 账号-角色 |
| role_permissions | 139 | 角色-权限授权 |
| model_providers | 2 | OpenAI / Anthropic |
| models | 2 | GPT-4o / Claude Sonnet 4 |
| agents | 2 | 客服助手 / 数据分析助手 |
| agent_versions | 2 | 对应版本 |
| prompts | 2 | 客服 / 分析提示词 |
| prompt_versions | 2 | 对应版本 |
| knowledge_bases | 1 | 产品知识库 |
| documents | 1 | 产品手册.pdf |
| segments | 2 | 文档分段 |
| tools | 2 | 天气查询 / HTTP 请求 |
| conversations | 3 | 已完成 / 已完成 / 错误 |
| conversation_turns | 4 | 轮次与 trace |
| api_keys | 1 | 默认密钥 |
| alert_rules | 1 | 高错误率告警 |
| alerts | 1 | 活跃告警 |
| system_settings | 1 | 平台默认配置 |
| audit_logs | 2 | 示例审计记录 |
| permission_applications | 2 | 待审批 / 已通过 |

---

## 八、MySQL 迁移清单（上线时）

| SQLite | MySQL |
|---|---|
| `INTEGER PRIMARY KEY AUTOINCREMENT` | `BIGINT AUTO_INCREMENT PRIMARY KEY` |
| `JSON`（TEXT 亲和） | `JSON` |
| `BOOLEAN`（0/1） | `TINYINT(1)` |
| `PRAGMA foreign_keys = ON` | InnoDB 外键默认生效 |
| `DATETIME DEFAULT CURRENT_TIMESTAMP` | 同义 |
| `datetime('now')`（初始化脚本） | `NOW()` |
| `INSERT OR IGNORE` | `INSERT IGNORE` |
| `AUTOINCREMENT` 自增序列 | `AUTO_INCREMENT` |

> 建议：上线前用 Alembic 从 ORM 模型生成 MySQL 迁移，并与本脚本逐表比对。

---

## 九、未纳入范围

以下内容 V3 未提及或后端未定义，**保持 V1 现状**，本脚本不创建：

- 部门表 `departments`（`data_scope:dept` 的部门字段需业务表补充）；
- Agent/模型/Prompt/知识库/工具之外的业务表（如对话导出任务表等）；
- 审计日志归档表、定时任务表等运维表。
