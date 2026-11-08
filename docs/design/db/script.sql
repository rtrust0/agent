-- ============================================================================
-- 辰光 Agent 平台 · 数据库详细设计脚本（V3）
-- ============================================================================
-- 数据库：SQLite（开发环境 rbac.db），后期上线切换 MySQL
-- 存放路径：docs/design/db/script.sql
-- 设计依据：
--   1. docs/spec/PROJECT_SPEC_V3.md（RBAC 授权需求增量）
--   2. docs/design/plans/rbac-plan.md
--   3. docs/design/plans/dashboard-plan.md
--   4. docs/design/plans/analytics-plan.md
--   5. docs/design/plans/conversation-plan.md
--   6. docs/design/plans/system-extension-plan.md
--   7. chenguang-agent-platform-v4 后端真实 ORM 模型
--
-- MySQL 迁移对照（后期上线时替换）：
--   INTEGER PRIMARY KEY AUTOINCREMENT  ->  BIGINT AUTO_INCREMENT PRIMARY KEY
--   JSON                               ->  JSON（MySQL 原生 JSON）
--   BOOLEAN / INTEGER(0/1)             ->  TINYINT(1)
--   PRAGMA foreign_keys = ON           ->  由 InnoDB 外键默认保证
--   CURRENT_TIMESTAMP                  ->  同义
--   datetime('now')（见 init-data.sql） ->  NOW()
-- ============================================================================

PRAGMA foreign_keys = ON;

-- ----------------------------------------------------------------------------
-- 1. model_providers —— 模型供应商（后端 ORM 已实现）
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS model_providers (
    id          INTEGER      PRIMARY KEY AUTOINCREMENT,
    name        VARCHAR(100) NOT NULL,
    type        VARCHAR(50)  NOT NULL,
    status      VARCHAR(50)  NOT NULL DEFAULT 'disconnected',
    endpoint    VARCHAR(500) NOT NULL,
    api_key     TEXT,
    description VARCHAR(500),
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 2. models —— 大语言模型（后端 ORM 已实现）
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS models (
    id             INTEGER       PRIMARY KEY AUTOINCREMENT,
    name           VARCHAR(100)  NOT NULL,
    model_id       VARCHAR(100)  NOT NULL UNIQUE,
    provider_id    INTEGER       NOT NULL,
    capabilities   VARCHAR(500),
    context_length INTEGER       NOT NULL DEFAULT 4096,
    status         VARCHAR(50)   NOT NULL DEFAULT 'available',
    input_price    NUMERIC(10,6) NOT NULL DEFAULT 0,
    output_price   NUMERIC(10,6) NOT NULL DEFAULT 0,
    currency       VARCHAR(10)   NOT NULL DEFAULT 'USD',
    is_default     BOOLEAN       NOT NULL DEFAULT 0,
    description    TEXT,
    created_at     DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_models_provider FOREIGN KEY (provider_id) REFERENCES model_providers(id) ON DELETE CASCADE
);

-- ----------------------------------------------------------------------------
-- 3. users —— 用户（V1/V2 模型 + V3 新增 data_scope / created_by）
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id              INTEGER      PRIMARY KEY AUTOINCREMENT,
    username        VARCHAR(50)  NOT NULL UNIQUE,
    email           VARCHAR(100) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    is_active       BOOLEAN      NOT NULL DEFAULT 1,
    is_superuser    BOOLEAN      NOT NULL DEFAULT 0,
    last_login      DATETIME,
    data_scope      VARCHAR(20)  NOT NULL DEFAULT 'own',   -- V3: own / dept / all
    created_by      INTEGER,                                -- V3: 数据归属（本人数据过滤）
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_users_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- ----------------------------------------------------------------------------
-- 4. roles —— 角色（V1/V2 模型）
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS roles (
    id          INTEGER      PRIMARY KEY AUTOINCREMENT,
    code        VARCHAR(100) NOT NULL UNIQUE,
    name        VARCHAR(100) NOT NULL,
    description VARCHAR(200),
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 5. permissions —— 权限（V1/V2 模型，V3 扩展为 71 个权限码）
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS permissions (
    id          INTEGER      PRIMARY KEY AUTOINCREMENT,
    code        VARCHAR(100) NOT NULL UNIQUE,
    name        VARCHAR(100) NOT NULL,
    description VARCHAR(200),
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 6. user_roles —— 用户-角色关联（复合主键）
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_roles (
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    PRIMARY KEY (user_id, role_id),
    CONSTRAINT fk_user_roles_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_user_roles_role FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
);

-- ----------------------------------------------------------------------------
-- 7. role_permissions —— 角色-权限关联（复合主键）
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS role_permissions (
    role_id       INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    PRIMARY KEY (role_id, permission_id),
    CONSTRAINT fk_role_permissions_role       FOREIGN KEY (role_id)       REFERENCES roles(id)       ON DELETE CASCADE,
    CONSTRAINT fk_role_permissions_permission FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE
);

-- ----------------------------------------------------------------------------
-- 8. agents —— Agent（后端 ORM 已实现）
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS agents (
    id            INTEGER       PRIMARY KEY AUTOINCREMENT,
    name          VARCHAR(200)  NOT NULL,
    description   TEXT,
    type          VARCHAR(50)   NOT NULL,               -- conversation/tool/analysis/creative/workflow
    status        VARCHAR(50)   NOT NULL DEFAULT 'draft', -- active/inactive/error/draft
    model_id      INTEGER,
    config        JSON,
    success_rate  NUMERIC(5,2)  NOT NULL DEFAULT 0,
    call_count_7d INTEGER       NOT NULL DEFAULT 0,
    version       VARCHAR(50)   NOT NULL DEFAULT 'v0.1',
    created_by    VARCHAR(100),
    created_at    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_agents_model FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE SET NULL
);

-- ----------------------------------------------------------------------------
-- 9. agent_versions —— Agent 版本（后端 ORM 已实现）
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS agent_versions (
    id           INTEGER     PRIMARY KEY AUTOINCREMENT,
    agent_id     INTEGER     NOT NULL,
    version      VARCHAR(50) NOT NULL,
    config       JSON,
    changelog    VARCHAR(500),
    is_current   BOOLEAN     NOT NULL DEFAULT 0,
    published_by VARCHAR(100),
    published_at DATETIME,
    created_at   DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_agent_versions_agent FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
);

-- ----------------------------------------------------------------------------
-- 10. prompts —— Prompt 模板（后端 ORM 已实现）
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS prompts (
    id          INTEGER      PRIMARY KEY AUTOINCREMENT,
    name        VARCHAR(200) NOT NULL,
    description VARCHAR(500),
    category    VARCHAR(50)  NOT NULL DEFAULT 'general',
    tags        JSON,
    content     TEXT         NOT NULL,
    variables   JSON,
    version     VARCHAR(50)  NOT NULL DEFAULT 'v0.1',
    status      VARCHAR(50)  NOT NULL DEFAULT 'draft', -- draft/published
    created_by  VARCHAR(100),
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 11. prompt_versions —— Prompt 版本（后端 ORM 已实现）
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS prompt_versions (
    id           INTEGER      PRIMARY KEY AUTOINCREMENT,
    prompt_id    INTEGER      NOT NULL,
    version      VARCHAR(50)  NOT NULL,
    content      TEXT         NOT NULL,
    changelog    VARCHAR(500),
    is_current   BOOLEAN      NOT NULL DEFAULT 0,
    published_by VARCHAR(100),
    published_at DATETIME,
    created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_prompt_versions_prompt FOREIGN KEY (prompt_id) REFERENCES prompts(id) ON DELETE CASCADE
);

-- ----------------------------------------------------------------------------
-- 12. knowledge_bases —— 知识库（后端 ORM 已实现）
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS knowledge_bases (
    id                   INTEGER      PRIMARY KEY AUTOINCREMENT,
    name                 VARCHAR(200) NOT NULL,
    description          VARCHAR(500),
    status               VARCHAR(50)  NOT NULL DEFAULT 'empty', -- ready/indexing/error/empty
    document_count       INTEGER      NOT NULL DEFAULT 0,
    segment_count        INTEGER      NOT NULL DEFAULT 0,
    embedding_model      VARCHAR(100) NOT NULL DEFAULT 'text-embedding-ada-002',
    chunk_method         VARCHAR(20)  NOT NULL DEFAULT 'fixed',
    chunk_size           INTEGER      NOT NULL DEFAULT 500,
    chunk_overlap        INTEGER      NOT NULL DEFAULT 50,
    retrieval_strategy   VARCHAR(20)  NOT NULL DEFAULT 'hybrid',
    top_k                INTEGER      NOT NULL DEFAULT 5,
    similarity_threshold FLOAT        NOT NULL DEFAULT 0.7,
    created_by           VARCHAR(100),
    created_at           DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at           DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 13. documents —— 知识库文档（后端 ORM 已实现）
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS documents (
    id                INTEGER      PRIMARY KEY AUTOINCREMENT,
    knowledge_base_id INTEGER      NOT NULL,
    file_name         VARCHAR(500) NOT NULL,
    file_type         VARCHAR(50)  NOT NULL,            -- pdf/docx/md/txt/html/csv
    file_size         VARCHAR(50),
    minio_path        VARCHAR(1000),
    status            VARCHAR(50)  NOT NULL DEFAULT 'pending', -- pending/processing/completed/failed
    segment_count     INTEGER      NOT NULL DEFAULT 0,
    word_count        INTEGER      NOT NULL DEFAULT 0,
    error_message     TEXT,
    uploaded_by       VARCHAR(100),
    processed_at      DATETIME,
    created_at        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_documents_kb FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases(id) ON DELETE CASCADE
);

-- ----------------------------------------------------------------------------
-- 14. segments —— 文档分段（后端 ORM 已实现）
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS segments (
    id                INTEGER  PRIMARY KEY AUTOINCREMENT,
    knowledge_base_id INTEGER  NOT NULL,
    document_id       INTEGER  NOT NULL,
    position          INTEGER  NOT NULL,
    content           TEXT     NOT NULL,
    word_count        INTEGER  NOT NULL DEFAULT 0,
    token_count       INTEGER  NOT NULL DEFAULT 0,
    hit_count         INTEGER  NOT NULL DEFAULT 0,
    created_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_segments_kb       FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    CONSTRAINT fk_segments_document FOREIGN KEY (document_id)       REFERENCES documents(id)       ON DELETE CASCADE
);

-- ----------------------------------------------------------------------------
-- 15. tools —— 工具（后端 ORM 已实现）
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tools (
    id                  INTEGER      PRIMARY KEY AUTOINCREMENT,
    name                VARCHAR(200) NOT NULL UNIQUE,
    description         TEXT,
    type                VARCHAR(50)  NOT NULL,          -- builtin/http_api/custom_function
    status              VARCHAR(50)  NOT NULL DEFAULT 'disabled', -- enabled/disabled/error
    config              JSON,
    function_definition JSON,
    call_count_7d       INTEGER      NOT NULL DEFAULT 0,
    success_rate        NUMERIC(5,2) NOT NULL DEFAULT 0,
    avg_latency         INTEGER      NOT NULL DEFAULT 0,
    created_by          VARCHAR(100),
    created_at          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 16. conversations —— 对话（analytics-plan 与 conversation-plan 的合并契约）
-- ----------------------------------------------------------------------------
-- 说明：两版计划对 conversations 字段命名不同，此处取并集并统一命名：
--   analytics.cost           -> total_cost
--   analytics.latency_ms     -> latency_ms（保留，总耗时）
--   conversation.total_duration -> 不使用（等价于 latency_ms）
--   conversation.agent_id/user_id 的 str -> INTEGER（与 users.id / agents.id 对齐）
-- 详见 docs/design/db/README.md「计划冲突与收敛」。
CREATE TABLE IF NOT EXISTS conversations (
    id                 INTEGER       PRIMARY KEY AUTOINCREMENT,
    agent_id           INTEGER,
    agent_name         VARCHAR(100),
    model_id           INTEGER,
    user_id            INTEGER,
    status             VARCHAR(50)   NOT NULL DEFAULT 'completed', -- active/completed/error
    turn_count         INTEGER       NOT NULL DEFAULT 0,
    input_tokens       INTEGER       NOT NULL DEFAULT 0,
    output_tokens      INTEGER       NOT NULL DEFAULT 0,
    total_tokens       INTEGER       NOT NULL DEFAULT 0,
    total_cost         NUMERIC(12,6) NOT NULL DEFAULT 0,
    latency_ms         INTEGER       NOT NULL DEFAULT 0,
    satisfaction       VARCHAR(20),                    -- positive/negative
    rating             INTEGER,                        -- 标注评分 1-5
    tags               JSON,
    needs_optimization BOOLEAN,
    annotation         JSON,
    started_at         DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at           DATETIME,
    created_at         DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at         DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_conversations_agent FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE SET NULL,
    CONSTRAINT fk_conversations_model FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE SET NULL,
    CONSTRAINT fk_conversations_user  FOREIGN KEY (user_id)  REFERENCES users(id)  ON DELETE SET NULL
);

-- ----------------------------------------------------------------------------
-- 17. conversation_turns —— 对话轮次（conversation-plan）
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS conversation_turns (
    id              INTEGER  PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER  NOT NULL,
    position        INTEGER  NOT NULL,
    role            VARCHAR(20) NOT NULL,              -- user/assistant
    content         TEXT     NOT NULL,
    timestamp       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    trace           JSON,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_conversation_turns_conversation FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

-- ----------------------------------------------------------------------------
-- 18. api_keys —— API 密钥（system-extension-plan）
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS api_keys (
    id                INTEGER      PRIMARY KEY AUTOINCREMENT,
    name              VARCHAR(100) NOT NULL,
    key               VARCHAR(100) NOT NULL UNIQUE,
    permissions       VARCHAR(20)  NOT NULL DEFAULT 'all',   -- all/readonly/agent_only
    status            VARCHAR(20)  NOT NULL DEFAULT 'active', -- active/disabled/expired
    rate_limit        INTEGER      NOT NULL DEFAULT 60,
    call_count        INTEGER      NOT NULL DEFAULT 0,
    last_used_at      DATETIME,
    expires_at        DATETIME,
    allowed_agent_ids JSON,
    created_by        VARCHAR(100),
    created_at        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 19. alert_rules —— 告警规则（system-extension-plan）
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS alert_rules (
    id           INTEGER      PRIMARY KEY AUTOINCREMENT,
    name         VARCHAR(100) NOT NULL,
    description  VARCHAR(200),
    condition    JSON         NOT NULL,                -- {metric,operator,threshold,duration,scope}
    notification JSON,                                 -- {channels,recipients}
    status       VARCHAR(20)  NOT NULL DEFAULT 'enabled', -- enabled/disabled
    created_by   VARCHAR(100),
    created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 20. alerts —— 告警记录（system-extension-plan）
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS alerts (
    id                INTEGER      PRIMARY KEY AUTOINCREMENT,
    type              VARCHAR(20)  NOT NULL,
    title             VARCHAR(200) NOT NULL,
    message           TEXT         NOT NULL,
    source            VARCHAR(50)  NOT NULL,
    severity          VARCHAR(20)  NOT NULL,
    status            VARCHAR(20)  NOT NULL DEFAULT 'active', -- active/acknowledged/resolved
    count             INTEGER      NOT NULL DEFAULT 1,
    first_occurred_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_occurred_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    acknowledged_by   VARCHAR(100),
    acknowledged_at   DATETIME,
    resolved_at       DATETIME,
    created_at        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 21. system_settings —— 系统配置（system-extension-plan，单行）
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS system_settings (
    id                  INTEGER      PRIMARY KEY AUTOINCREMENT,
    system_name         VARCHAR(100) NOT NULL DEFAULT '辰光Agent平台',
    system_description  TEXT,
    default_language    VARCHAR(20)  NOT NULL DEFAULT 'zh-CN',
    default_model       VARCHAR(100) NOT NULL DEFAULT 'GPT-4',
    default_temperature FLOAT        NOT NULL DEFAULT 0.7,
    default_max_tokens  INTEGER      NOT NULL DEFAULT 4096,
    smtp_server         VARCHAR(200),
    smtp_port           INTEGER      NOT NULL DEFAULT 587,
    sender_email        VARCHAR(100),
    created_at          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 22. audit_logs —— 权限操作审计日志（V3 + system-extension-plan 合并）
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_logs (
    id          INTEGER      PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER,                                -- 允许为空：用户删除后仍保留审计记录
    username    VARCHAR(100) NOT NULL,
    action      VARCHAR(50)  NOT NULL,                  -- create/update/delete/assign/approve/apply/export
    module      VARCHAR(50)  NOT NULL,                  -- user/role/.../system/approval
    target_id   VARCHAR(100),
    target_name VARCHAR(200),
    detail      TEXT,
    ip_address  VARCHAR(50)  NOT NULL DEFAULT '',
    user_agent  VARCHAR(300),
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_audit_logs_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- ----------------------------------------------------------------------------
-- 23. permission_applications —— 权限申请与审批（V3）
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS permission_applications (
    id              INTEGER      PRIMARY KEY AUTOINCREMENT,
    applicant_id    INTEGER      NOT NULL,
    applicant_name  VARCHAR(100) NOT NULL,
    permission_code VARCHAR(100) NOT NULL,
    reason          TEXT         NOT NULL,
    status          VARCHAR(20)  NOT NULL DEFAULT 'pending', -- pending/approved/rejected/expired
    approver_id     INTEGER,
    approver_name   VARCHAR(100),
    approved_at     DATETIME,
    expired_at      DATETIME,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_permission_applications_applicant FOREIGN KEY (applicant_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_permission_applications_approver  FOREIGN KEY (approver_id)  REFERENCES users(id) ON DELETE SET NULL
);

-- ----------------------------------------------------------------------------
-- 索引
-- ----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_users_username        ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email           ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_data_scope      ON users(data_scope);
CREATE INDEX IF NOT EXISTS idx_users_is_superuser    ON users(is_superuser);
CREATE INDEX IF NOT EXISTS idx_users_is_active       ON users(is_active);

CREATE INDEX IF NOT EXISTS idx_roles_code            ON roles(code);
CREATE INDEX IF NOT EXISTS idx_permissions_code      ON permissions(code);
CREATE INDEX IF NOT EXISTS idx_user_roles_user_id    ON user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_role_id    ON user_roles(role_id);
CREATE INDEX IF NOT EXISTS idx_role_permissions_role ON role_permissions(role_id);

CREATE INDEX IF NOT EXISTS idx_models_provider       ON models(provider_id);
CREATE INDEX IF NOT EXISTS idx_agents_model          ON agents(model_id);
CREATE INDEX IF NOT EXISTS idx_agent_versions_agent  ON agent_versions(agent_id);
CREATE INDEX IF NOT EXISTS idx_prompt_versions_prompt ON prompt_versions(prompt_id);
CREATE INDEX IF NOT EXISTS idx_documents_kb          ON documents(knowledge_base_id);
CREATE INDEX IF NOT EXISTS idx_segments_kb           ON segments(knowledge_base_id);
CREATE INDEX IF NOT EXISTS idx_segments_document     ON segments(document_id);

CREATE INDEX IF NOT EXISTS idx_conversations_agent   ON conversations(agent_id);
CREATE INDEX IF NOT EXISTS idx_conversations_model   ON conversations(model_id);
CREATE INDEX IF NOT EXISTS idx_conversations_user    ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_started ON conversations(started_at);
CREATE INDEX IF NOT EXISTS idx_conversation_turns_conversation ON conversation_turns(conversation_id);

CREATE INDEX IF NOT EXISTS idx_api_keys_status       ON api_keys(status);
CREATE INDEX IF NOT EXISTS idx_alert_rules_status    ON alert_rules(status);
CREATE INDEX IF NOT EXISTS idx_alerts_status         ON alerts(status);
CREATE INDEX IF NOT EXISTS idx_alerts_severity       ON alerts(severity);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id    ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action     ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_module     ON audit_logs(module);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);

CREATE INDEX IF NOT EXISTS idx_permission_applications_applicant ON permission_applications(applicant_id);
CREATE INDEX IF NOT EXISTS idx_permission_applications_status    ON permission_applications(status);
CREATE INDEX IF NOT EXISTS idx_permission_applications_code      ON permission_applications(permission_code);

-- ============================================================================
-- 脚本结束：共 23 张表
-- ============================================================================
