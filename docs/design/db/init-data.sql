-- ============================================================================
-- 辰光 Agent 平台 · 数据库初始化数据脚本（V3）
-- ============================================================================
-- 数据库：SQLite（开发环境 rbac.db）
-- 存放路径：docs/design/db/init-data.sql
-- 内容：71 个权限码 + 3 个角色 + 3 个演示账号 + 授权关系 + 业务演示数据
-- 密码：admin / ops / viewer 均为 123456（bcrypt）
-- ============================================================================

PRAGMA foreign_keys = ON;

-- ----------------------------------------------------------------------------
-- 1. 权限码（71 个 = 核心 27 + 业务 44）
-- ----------------------------------------------------------------------------
INSERT OR IGNORE INTO permissions (id, code, name, description, created_at, updated_at) VALUES
-- V2 核心 22
(1,  'user:list',                 '用户列表查看',       '查看用户列表', datetime('now'), datetime('now')),
(2,  'user:read',                 '用户详情查看',       '查看用户详情', datetime('now'), datetime('now')),
(3,  'user:create',               '创建用户',           '创建用户', datetime('now'), datetime('now')),
(4,  'user:update',               '更新用户',           '更新用户信息', datetime('now'), datetime('now')),
(5,  'user:delete',               '删除用户',           '删除用户', datetime('now'), datetime('now')),
(6,  'user:assign_roles',         '给用户分配角色',     '给用户分配角色', datetime('now'), datetime('now')),
(7,  'user:read_roles',           '查看用户角色列表',   '查看用户所属角色', datetime('now'), datetime('now')),
(8,  'role:list',                 '角色列表查看',       '查看角色列表', datetime('now'), datetime('now')),
(9,  'role:read',                 '角色详情查看',       '查看角色详情', datetime('now'), datetime('now')),
(10, 'role:create',               '创建角色',           '创建角色', datetime('now'), datetime('now')),
(11, 'role:update',               '更新角色',           '更新角色信息', datetime('now'), datetime('now')),
(12, 'role:delete',               '删除角色',           '删除角色', datetime('now'), datetime('now')),
(13, 'role:assign_permissions',   '给角色分配权限',     '给角色分配权限', datetime('now'), datetime('now')),
(14, 'permission:list',           '权限列表查看',       '查看权限列表', datetime('now'), datetime('now')),
(15, 'permission:read',           '权限详情查看',       '查看权限详情', datetime('now'), datetime('now')),
(16, 'permission:create',         '创建权限',           '创建权限', datetime('now'), datetime('now')),
(17, 'permission:update',         '更新权限',           '更新权限信息（code 不可改）', datetime('now'), datetime('now')),
(18, 'permission:delete',         '删除权限',           '删除权限', datetime('now'), datetime('now')),
(19, 'system:api_keys',           'API 密钥管理',       'API 密钥管理', datetime('now'), datetime('now')),
(20, 'system:audit',              '审计日志查看',       '审计日志查看', datetime('now'), datetime('now')),
(21, 'system:alerts',             '告警规则管理',       '告警规则管理', datetime('now'), datetime('now')),
(22, 'system:settings',           '系统配置管理',       '系统配置管理', datetime('now'), datetime('now')),
-- V3 数据权限 3
(23, 'data_scope:own',            '本人数据权限',       '仅查看/编辑本人创建的数据', datetime('now'), datetime('now')),
(24, 'data_scope:dept',           '部门数据权限',       '查看/编辑本部门数据', datetime('now'), datetime('now')),
(25, 'data_scope:all',            '全量数据权限',       '查看/编辑全部数据', datetime('now'), datetime('now')),
-- V3 权限申请审批 2
(26, 'approval:apply',            '发起权限申请',       '申请临时或永久权限', datetime('now'), datetime('now')),
(27, 'approval:audit',            '审批权限申请',       '审批他人提交的权限申请', datetime('now'), datetime('now')),
-- 业务模块 44
(28, 'dashboard:read',            '工作台查看',         '查看工作台统计、趋势、排行榜、告警、资源用量', datetime('now'), datetime('now')),
(29, 'agent:list',                'Agent 列表查看',     'Agent 列表查看', datetime('now'), datetime('now')),
(30, 'agent:read',                'Agent 详情查看',     'Agent 详情查看', datetime('now'), datetime('now')),
(31, 'agent:create',              '创建 Agent',         '创建 Agent', datetime('now'), datetime('now')),
(32, 'agent:update',              '更新 Agent',         '更新 Agent', datetime('now'), datetime('now')),
(33, 'agent:delete',              '删除 Agent',         '删除 Agent', datetime('now'), datetime('now')),
(34, 'agent:publish',             '发布/下线 Agent',    '发布、下线、版本回滚', datetime('now'), datetime('now')),
(35, 'agent:test',                'Agent 调试测试',     'Agent 调试测试', datetime('now'), datetime('now')),
(36, 'agent:monitor',             'Agent 监控查看',     'Agent 监控查看', datetime('now'), datetime('now')),
(37, 'model:list',                '模型列表查看',       '模型列表查看', datetime('now'), datetime('now')),
(38, 'model:read',                '模型详情查看',       '模型详情查看', datetime('now'), datetime('now')),
(39, 'model:create',              '创建模型',           '创建模型', datetime('now'), datetime('now')),
(40, 'model:update',              '更新模型',           '更新模型', datetime('now'), datetime('now')),
(41, 'model:delete',              '删除模型',           '删除模型', datetime('now'), datetime('now')),
(42, 'model:provider_manage',     '模型供应商管理',     '模型供应商管理', datetime('now'), datetime('now')),
(43, 'model:test',                '模型连接测试',       '模型/供应商连接测试', datetime('now'), datetime('now')),
(44, 'prompt:list',               'Prompt 列表查看',    'Prompt 列表查看', datetime('now'), datetime('now')),
(45, 'prompt:read',               'Prompt 详情查看',    'Prompt 详情查看', datetime('now'), datetime('now')),
(46, 'prompt:create',             '创建 Prompt',        '创建 Prompt', datetime('now'), datetime('now')),
(47, 'prompt:update',             '更新 Prompt',        '更新 Prompt', datetime('now'), datetime('now')),
(48, 'prompt:delete',             '删除 Prompt',        '删除 Prompt', datetime('now'), datetime('now')),
(49, 'prompt:publish',            '发布/回滚 Prompt',   '发布、回滚 Prompt 版本', datetime('now'), datetime('now')),
(50, 'prompt:test',               'Prompt 调试测试',    'Prompt 调试测试', datetime('now'), datetime('now')),
(51, 'knowledge:list',            '知识库列表查看',     '知识库列表查看', datetime('now'), datetime('now')),
(52, 'knowledge:read',            '知识库详情查看',     '知识库详情/文档/分段查看', datetime('now'), datetime('now')),
(53, 'knowledge:create',          '创建知识库',         '创建知识库', datetime('now'), datetime('now')),
(54, 'knowledge:update',          '更新知识库配置',     '更新知识库配置', datetime('now'), datetime('now')),
(55, 'knowledge:delete',          '删除知识库',         '删除知识库', datetime('now'), datetime('now')),
(56, 'knowledge:document_upload', '上传/重试文档',      '上传、重试文档', datetime('now'), datetime('now')),
(57, 'knowledge:document_delete', '删除文档/分段',      '删除文档/分段', datetime('now'), datetime('now')),
(58, 'knowledge:retrieval_test',  '检索测试',           '检索测试', datetime('now'), datetime('now')),
(59, 'knowledge:reindex',         '重新索引',           '重新索引', datetime('now'), datetime('now')),
(60, 'tool:list',                 '工具列表查看',       '工具列表查看', datetime('now'), datetime('now')),
(61, 'tool:read',                 '工具详情查看',       '工具详情/调用日志查看', datetime('now'), datetime('now')),
(62, 'tool:create',               '注册工具',           '注册工具', datetime('now'), datetime('now')),
(63, 'tool:update',               '更新工具',           '更新工具', datetime('now'), datetime('now')),
(64, 'tool:delete',               '删除工具',           '删除工具', datetime('now'), datetime('now')),
(65, 'tool:test',                 '工具测试',           '工具测试', datetime('now'), datetime('now')),
(66, 'tool:toggle',               '启用/禁用工具',      '启用/禁用工具', datetime('now'), datetime('now')),
(67, 'conversation:list',         '对话列表查看',       '对话列表查看', datetime('now'), datetime('now')),
(68, 'conversation:read',         '对话详情查看',       '对话详情/轮次/链路追踪查看', datetime('now'), datetime('now')),
(69, 'conversation:annotate',     '对话标注',           '对话标注', datetime('now'), datetime('now')),
(70, 'conversation:export',       '对话导出',           '对话导出', datetime('now'), datetime('now')),
(71, 'analytics:read',            '数据统计查看',       '查看用量、费用、效果评估等统计', datetime('now'), datetime('now'));

-- ----------------------------------------------------------------------------
-- 2. 角色（3 个）
-- ----------------------------------------------------------------------------
INSERT OR IGNORE INTO roles (id, code, name, description, created_at, updated_at) VALUES
(1, 'super_admin', '超级管理员', '拥有平台全部权限，可管理一切资源', datetime('now'), datetime('now')),
(2, 'ops_admin',   '运营管理员', '负责日常运营：增改用户/角色/业务内容，不可删除或分配权限', datetime('now'), datetime('now')),
(3, 'viewer',      '只读观察者', '只能查看各模块，不可做任何修改', datetime('now'), datetime('now'));

-- ----------------------------------------------------------------------------
-- 3. 用户（3 个演示账号，密码均为 123456）
-- ----------------------------------------------------------------------------
INSERT OR IGNORE INTO users (id, username, email, hashed_password, is_active, is_superuser, last_login, data_scope, created_by, created_at, updated_at) VALUES
(1, 'admin',  'admin@chenguang.ai',  '$2b$12$ferqWax8q2pdCe/j2Mych.6ryucNIkoCeX95rdrITxXbs/gG4NOtS', 1, 1, datetime('now'), 'all',  NULL, datetime('now'), datetime('now')),
(2, 'ops',    'ops@chenguang.ai',    '$2b$12$ferqWax8q2pdCe/j2Mych.6ryucNIkoCeX95rdrITxXbs/gG4NOtS', 1, 0, datetime('now'), 'dept', 1,    datetime('now'), datetime('now')),
(3, 'viewer', 'viewer@chenguang.ai', '$2b$12$ferqWax8q2pdCe/j2Mych.6ryucNIkoCeX95rdrITxXbs/gG4NOtS', 1, 0, datetime('now'), 'own',  1,    datetime('now'), datetime('now'));

-- ----------------------------------------------------------------------------
-- 4. 用户-角色关系
-- ----------------------------------------------------------------------------
INSERT OR IGNORE INTO user_roles (user_id, role_id) VALUES
(1, 1),  -- admin  -> super_admin
(2, 2),  -- ops    -> ops_admin
(3, 3);  -- viewer -> viewer

-- ----------------------------------------------------------------------------
-- 5. 角色-权限关系
-- super_admin：全部 71 个
-- ops_admin：核心 11 + data_scope:dept + approval:apply + 业务可写权限
-- viewer：核心 7 + data_scope:own + approval:apply + 业务只读权限
-- ----------------------------------------------------------------------------
-- super_admin (role_id=1) -> 1..71
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT 1, id FROM permissions WHERE id BETWEEN 1 AND 71;

-- ops_admin (role_id=2)
INSERT OR IGNORE INTO role_permissions (role_id, permission_id) VALUES
(2, 1), (2, 2), (2, 3), (2, 4), (2, 7),
(2, 8), (2, 9), (2, 10), (2, 11),
(2, 14), (2, 15),
(2, 24), (2, 26),
(2, 28),
(2, 29), (2, 30), (2, 31), (2, 32), (2, 34), (2, 35), (2, 36),
(2, 37), (2, 38), (2, 43),
(2, 44), (2, 45), (2, 46), (2, 47), (2, 49), (2, 50),
(2, 51), (2, 52), (2, 53), (2, 54), (2, 56), (2, 58), (2, 59),
(2, 60), (2, 61), (2, 65),
(2, 67), (2, 68), (2, 69), (2, 70),
(2, 71);

-- viewer (role_id=3)
INSERT OR IGNORE INTO role_permissions (role_id, permission_id) VALUES
(3, 1), (3, 2), (3, 7),
(3, 8), (3, 9),
(3, 14), (3, 15),
(3, 23), (3, 26),
(3, 28),
(3, 29), (3, 30),
(3, 37), (3, 38),
(3, 44), (3, 45),
(3, 51), (3, 52),
(3, 60), (3, 61),
(3, 67), (3, 68),
(3, 71);

-- ----------------------------------------------------------------------------
-- 6. 模型供应商
-- ----------------------------------------------------------------------------
INSERT OR IGNORE INTO model_providers (id, name, type, status, endpoint, api_key, description, created_at, updated_at) VALUES
(1, 'OpenAI',    'openai',    'connected', 'https://api.openai.com/v1',    'sk-demo-openai',    'OpenAI 官方接口', datetime('now'), datetime('now')),
(2, 'Anthropic', 'anthropic', 'connected', 'https://api.anthropic.com/v1', 'sk-demo-anthropic', 'Anthropic 官方接口', datetime('now'), datetime('now'));

-- ----------------------------------------------------------------------------
-- 7. 模型
-- ----------------------------------------------------------------------------
INSERT OR IGNORE INTO models (id, name, model_id, provider_id, capabilities, context_length, status, input_price, output_price, currency, is_default, description, created_at, updated_at) VALUES
(1, 'GPT-4o',           'gpt-4o',         1, 'function_call,vision,streaming', 128000, 'available', 0.005000, 0.015000, 'USD', 1, 'OpenAI 多模态旗舰模型', datetime('now'), datetime('now')),
(2, 'Claude Sonnet 4',  'claude-sonnet-4', 2, 'function_call,vision,streaming', 200000, 'available', 0.003000, 0.015000, 'USD', 0, 'Anthropic 高性价比模型', datetime('now'), datetime('now'));

-- ----------------------------------------------------------------------------
-- 8. Agent
-- ----------------------------------------------------------------------------
INSERT OR IGNORE INTO agents (id, name, description, type, status, model_id, config, success_rate, call_count_7d, version, created_by, created_at, updated_at) VALUES
(1, '客服助手', '处理产品咨询与常见问题', 'conversation', 'active', 1, '{"system_prompt":"你是辰光客服助手，请准确、简洁地回答用户问题。"}', 98.50, 1200, 'v1.0', 'admin', datetime('now'), datetime('now')),
(2, '数据分析助手', '分析对话日志与用量数据', 'analysis', 'draft', 2, '{"system_prompt":"你是数据分析助手，请基于数据给出结论。"}', 0.00, 0, 'v0.1', 'ops', datetime('now'), datetime('now'));

-- ----------------------------------------------------------------------------
-- 9. Agent 版本
-- ----------------------------------------------------------------------------
INSERT OR IGNORE INTO agent_versions (id, agent_id, version, config, changelog, is_current, published_by, published_at, created_at, updated_at) VALUES
(1, 1, 'v1.0', '{"system_prompt":"你是辰光客服助手，请准确、简洁地回答用户问题。"}', '初始版本', 1, 'admin', datetime('now'), datetime('now'), datetime('now')),
(2, 2, 'v0.1', '{"system_prompt":"你是数据分析助手，请基于数据给出结论。"}', '草稿版本', 1, 'ops', datetime('now'), datetime('now'), datetime('now'));

-- ----------------------------------------------------------------------------
-- 10. Prompt
-- ----------------------------------------------------------------------------
INSERT OR IGNORE INTO prompts (id, name, description, category, tags, content, variables, version, status, created_by, created_at, updated_at) VALUES
(1, '客服系统提示词', '客服场景系统提示词', 'customer_service', '["客服","问答"]', '你是辰光客服助手。请基于知识库准确回答，不确定时说明。', '[]', 'v1.0', 'published', 'admin', datetime('now'), datetime('now')),
(2, '数据分析提示词', '数据分析场景提示词', 'analysis', '["分析","统计"]', '你是数据分析助手。请基于给定数据输出结论与建议。', '[]', 'v0.1', 'draft', 'ops', datetime('now'), datetime('now'));

-- ----------------------------------------------------------------------------
-- 11. Prompt 版本
-- ----------------------------------------------------------------------------
INSERT OR IGNORE INTO prompt_versions (id, prompt_id, version, content, changelog, is_current, published_by, published_at, created_at, updated_at) VALUES
(1, 1, 'v1.0', '你是辰光客服助手。请基于知识库准确回答，不确定时说明。', '初始发布', 1, 'admin', datetime('now'), datetime('now'), datetime('now')),
(2, 2, 'v0.1', '你是数据分析助手。请基于给定数据输出结论与建议。', '草稿', 1, 'ops', datetime('now'), datetime('now'), datetime('now'));

-- ----------------------------------------------------------------------------
-- 12. 知识库
-- ----------------------------------------------------------------------------
INSERT OR IGNORE INTO knowledge_bases (id, name, description, status, document_count, segment_count, embedding_model, chunk_method, chunk_size, chunk_overlap, retrieval_strategy, top_k, similarity_threshold, created_by, created_at, updated_at) VALUES
(1, '产品知识库', '产品手册与常见问题', 'ready', 1, 2, 'text-embedding-ada-002', 'fixed', 500, 50, 'hybrid', 5, 0.7, 'admin', datetime('now'), datetime('now'));

-- ----------------------------------------------------------------------------
-- 13. 文档
-- ----------------------------------------------------------------------------
INSERT OR IGNORE INTO documents (id, knowledge_base_id, file_name, file_type, file_size, minio_path, status, segment_count, word_count, error_message, uploaded_by, processed_at, created_at, updated_at) VALUES
(1, 1, '产品手册.pdf', 'pdf', '2.4MB', 'knowledge-docs/产品手册.pdf', 'completed', 2, 1200, NULL, 'admin', datetime('now'), datetime('now'), datetime('now'));

-- ----------------------------------------------------------------------------
-- 14. 分段
-- ----------------------------------------------------------------------------
INSERT OR IGNORE INTO segments (id, knowledge_base_id, document_id, position, content, word_count, token_count, hit_count, created_at, updated_at) VALUES
(1, 1, 1, 1, '辰光 Agent 平台支持 Agent 全生命周期管理。', 18, 24, 3, datetime('now'), datetime('now')),
(2, 1, 1, 2, '知识库支持 PDF、DOCX、Markdown 等格式。', 16, 22, 1, datetime('now'), datetime('now'));

-- ----------------------------------------------------------------------------
-- 15. 工具
-- ----------------------------------------------------------------------------
INSERT OR IGNORE INTO tools (id, name, description, type, status, config, function_definition, call_count_7d, success_rate, avg_latency, created_by, created_at, updated_at) VALUES
(1, '天气查询', '查询指定城市天气', 'builtin', 'enabled', '{"city_param":"city"}', '{"name":"get_weather","parameters":{"type":"object","properties":{"city":{"type":"string"}}}}', 320, 99.20, 180, 'admin', datetime('now'), datetime('now')),
(2, 'HTTP 请求', '通用 HTTP 调用工具', 'http_api', 'disabled', '{"method":"GET"}', NULL, 0, 0.00, 0, 'ops', datetime('now'), datetime('now'));

-- ----------------------------------------------------------------------------
-- 16. 对话
-- ----------------------------------------------------------------------------
INSERT OR IGNORE INTO conversations (id, agent_id, agent_name, model_id, user_id, status, turn_count, input_tokens, output_tokens, total_tokens, total_cost, latency_ms, satisfaction, rating, tags, needs_optimization, annotation, started_at, ended_at, created_at, updated_at) VALUES
(1, 1, '客服助手', 1, 3, 'completed', 2, 120, 80, 200, 0.001200, 2300, 'positive', 5, '["准确"]', 0, '{"note":"回答准确"}', datetime('now','-1 day'), datetime('now','-1 day','+5 minutes'), datetime('now'), datetime('now')),
(2, 1, '客服助手', 1, 3, 'completed', 1, 90, 40, 130, 0.000900, 3100, 'negative', 2, '["需优化"]', 1, '{"note":"未命中知识库"}', datetime('now','-2 day'), datetime('now','-2 day','+3 minutes'), datetime('now'), datetime('now')),
(3, 2, '数据分析助手', 2, 2, 'error', 1, 60, 0, 60, 0.000400, 5200, NULL, NULL, NULL, NULL, NULL, datetime('now','-3 day'), datetime('now','-3 day','+1 minutes'), datetime('now'), datetime('now'));

-- ----------------------------------------------------------------------------
-- 17. 对话轮次
-- ----------------------------------------------------------------------------
INSERT OR IGNORE INTO conversation_turns (id, conversation_id, position, role, content, timestamp, trace, created_at, updated_at) VALUES
(1, 1, 1, 'user',      '你们的平台支持哪些功能？', datetime('now','-1 day'), NULL, datetime('now'), datetime('now')),
(2, 1, 2, 'assistant', '辰光 Agent 平台支持 Agent 管理、知识库、Prompt、模型与工具编排。', datetime('now','-1 day','+1 minutes'), '{"steps":[{"type":"retrieval","hits":2},{"type":"llm_call","model":"gpt-4o"}]}', datetime('now'), datetime('now')),
(3, 2, 1, 'user',      '如何上传知识库文档？', datetime('now','-2 day'), NULL, datetime('now'), datetime('now')),
(4, 3, 1, 'user',      '分析最近一周的调用趋势', datetime('now','-3 day'), NULL, datetime('now'), datetime('now'));

-- ----------------------------------------------------------------------------
-- 18. API 密钥
-- ----------------------------------------------------------------------------
INSERT OR IGNORE INTO api_keys (id, name, key, permissions, status, rate_limit, call_count, last_used_at, expires_at, allowed_agent_ids, created_by, created_at, updated_at) VALUES
(1, '默认密钥', 'sk-chenguang-demo-001', 'all', 'active', 120, 42, datetime('now'), NULL, '[1,2]', 'admin', datetime('now'), datetime('now'));

-- ----------------------------------------------------------------------------
-- 19. 告警规则
-- ----------------------------------------------------------------------------
INSERT OR IGNORE INTO alert_rules (id, name, description, condition, notification, status, created_by, created_at, updated_at) VALUES
(1, '高错误率告警', '错误率超过 5% 持续 5 分钟', '{"metric":"error_rate","operator":"gt","threshold":5,"duration":300,"scope":"all"}', '{"channels":["email"],"recipients":["admin@chenguang.ai"]}', 'enabled', 'admin', datetime('now'), datetime('now'));

-- ----------------------------------------------------------------------------
-- 20. 告警记录
-- ----------------------------------------------------------------------------
INSERT OR IGNORE INTO alerts (id, type, title, message, source, severity, status, count, first_occurred_at, last_occurred_at, acknowledged_by, acknowledged_at, resolved_at, created_at, updated_at) VALUES
(1, 'error', '接口错误率升高', '近 5 分钟 Agent 调用错误率达到 8%', 'agent:1', 'high', 'active', 3, datetime('now','-10 minutes'), datetime('now'), NULL, NULL, NULL, datetime('now'), datetime('now'));

-- ----------------------------------------------------------------------------
-- 21. 系统配置（单行）
-- ----------------------------------------------------------------------------
INSERT OR IGNORE INTO system_settings (id, system_name, system_description, default_language, default_model, default_temperature, default_max_tokens, smtp_server, smtp_port, sender_email, created_at, updated_at) VALUES
(1, '辰光Agent平台', '企业级 AI Agent 管理平台', 'zh-CN', 'GPT-4o', 0.7, 4096, 'smtp.example.com', 587, 'noreply@chenguang.ai', datetime('now'), datetime('now'));

-- ----------------------------------------------------------------------------
-- 22. 审计日志（示例）
-- ----------------------------------------------------------------------------
INSERT OR IGNORE INTO audit_logs (id, user_id, username, action, module, target_id, target_name, detail, ip_address, user_agent, created_at) VALUES
(1, 1, 'admin', 'create', 'user', '2', 'ops', '{"after":{"username":"ops","email":"ops@chenguang.ai"}}', '127.0.0.1', 'Mozilla/5.0', datetime('now','-2 day')),
(2, 2, 'ops',   'update', 'agent', '1', '客服助手', '{"before":{"status":"draft"},"after":{"status":"active"}}', '127.0.0.1', 'Mozilla/5.0', datetime('now','-1 day'));

-- ----------------------------------------------------------------------------
-- 23. 权限申请（示例）
-- ----------------------------------------------------------------------------
INSERT OR IGNORE INTO permission_applications (id, applicant_id, applicant_name, permission_code, reason, status, approver_id, approver_name, approved_at, expired_at, created_at) VALUES
(1, 3, 'viewer', 'agent:create', '需要创建演示用 Agent', 'pending', NULL, NULL, NULL, NULL, datetime('now','-1 day')),
(2, 2, 'ops',    'permission:create', '需要为新业务模块创建权限码', 'approved', 1, 'admin', datetime('now','-2 day'), NULL, datetime('now','-3 day'));

-- ============================================================================
-- 脚本结束：71 权限码 / 3 角色 / 3 用户 / 业务演示数据
-- ============================================================================
