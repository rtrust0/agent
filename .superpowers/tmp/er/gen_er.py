# -*- coding: utf-8 -*-
"""Generate an ER diagram SVG/HTML from docs/design/db/script.sql (V3, 23 tables)."""
import html, os

W, H = 3220, 1880
FONT = "Microsoft YaHei, PingFang SC, Noto Sans SC, Arial, sans-serif"
MONO = "Consolas, Menlo, monospace"

GROUPS = {
    "rbac":   {"label": "核心 RBAC",     "x": 40,   "y": 140, "w": 880,  "h": 840,  "fill": "#eef2fc", "stroke": "#3e63dd"},
    "biz":    {"label": "业务与对话",    "x": 960,  "y": 140, "w": 900,  "h": 1500, "fill": "#e9f4ee", "stroke": "#1e7a5a"},
    "content":{"label": "内容与工具",    "x": 1900, "y": 140, "w": 620,  "h": 1720, "fill": "#fdf3e3", "stroke": "#e2a13c"},
    "system": {"label": "系统管理",      "x": 2560, "y": 140, "w": 600,  "h": 1210, "fill": "#fbeceb", "stroke": "#c2453c"},
}

# (name, type, key)  key: PK / FK / PK,FK / None
TABLES = {
    "users": ("rbac", [
        ("id","INT","PK"),("username","VARCHAR(50)",None),("email","VARCHAR(100)",None),
        ("hashed_password","VARCHAR(255)",None),("is_active","BOOLEAN",None),
        ("is_superuser","BOOLEAN",None),("last_login","DATETIME",None),
        ("data_scope","VARCHAR(20)",None),("created_by","INT","FK"),
        ("created_at","DATETIME",None),("updated_at","DATETIME",None)]),
    "roles": ("rbac", [
        ("id","INT","PK"),("code","VARCHAR(100)",None),("name","VARCHAR(100)",None),
        ("description","VARCHAR(200)",None),("created_at","DATETIME",None),("updated_at","DATETIME",None)]),
    "permissions": ("rbac", [
        ("id","INT","PK"),("code","VARCHAR(100)",None),("name","VARCHAR(100)",None),
        ("description","VARCHAR(200)",None),("created_at","DATETIME",None),("updated_at","DATETIME",None)]),
    "user_roles": ("rbac", [
        ("user_id","INT","PK,FK"),("role_id","INT","PK,FK")]),
    "role_permissions": ("rbac", [
        ("role_id","INT","PK,FK"),("permission_id","INT","PK,FK")]),
    "audit_logs": ("rbac", [
        ("id","INT","PK"),("user_id","INT","FK"),("username","VARCHAR(100)",None),
        ("action","VARCHAR(50)",None),("module","VARCHAR(50)",None),
        ("target_id","VARCHAR(100)",None),("target_name","VARCHAR(200)",None),
        ("detail","TEXT",None),("ip_address","VARCHAR(50)",None),
        ("user_agent","VARCHAR(300)",None),("created_at","DATETIME",None)]),
    "permission_applications": ("rbac", [
        ("id","INT","PK"),("applicant_id","INT","FK"),("applicant_name","VARCHAR(100)",None),
        ("permission_code","VARCHAR(100)",None),("reason","TEXT",None),
        ("status","VARCHAR(20)",None),("approver_id","INT","FK"),
        ("approver_name","VARCHAR(100)",None),("approved_at","DATETIME",None),
        ("expired_at","DATETIME",None),("created_at","DATETIME",None)]),

    "model_providers": ("biz", [
        ("id","INT","PK"),("name","VARCHAR(100)",None),("type","VARCHAR(50)",None),
        ("status","VARCHAR(50)",None),("endpoint","VARCHAR(500)",None),
        ("api_key","TEXT",None),("description","VARCHAR(500)",None),
        ("created_at","DATETIME",None),("updated_at","DATETIME",None)]),
    "models": ("biz", [
        ("id","INT","PK"),("name","VARCHAR(100)",None),("model_id","VARCHAR(100)",None),
        ("provider_id","INT","FK"),("capabilities","VARCHAR(500)",None),
        ("context_length","INT",None),("status","VARCHAR(50)",None),
        ("input_price","NUMERIC(10,6)",None),("output_price","NUMERIC(10,6)",None),
        ("currency","VARCHAR(10)",None),("is_default","BOOLEAN",None),
        ("description","TEXT",None),("created_at","DATETIME",None),("updated_at","DATETIME",None)]),
    "agents": ("biz", [
        ("id","INT","PK"),("name","VARCHAR(200)",None),("description","TEXT",None),
        ("type","VARCHAR(50)",None),("status","VARCHAR(50)",None),("model_id","INT","FK"),
        ("config","JSON",None),("success_rate","NUMERIC(5,2)",None),
        ("call_count_7d","INT",None),("version","VARCHAR(50)",None),
        ("created_by","VARCHAR(100)",None),("created_at","DATETIME",None),("updated_at","DATETIME",None)]),
    "agent_versions": ("biz", [
        ("id","INT","PK"),("agent_id","INT","FK"),("version","VARCHAR(50)",None),
        ("config","JSON",None),("changelog","VARCHAR(500)",None),("is_current","BOOLEAN",None),
        ("published_by","VARCHAR(100)",None),("published_at","DATETIME",None),
        ("created_at","DATETIME",None),("updated_at","DATETIME",None)]),
    "conversations": ("biz", [
        ("id","INT","PK"),("agent_id","INT","FK"),("agent_name","VARCHAR(100)",None),
        ("model_id","INT","FK"),("user_id","INT","FK"),("status","VARCHAR(50)",None),
        ("turn_count","INT",None),("input_tokens","INT",None),("output_tokens","INT",None),
        ("total_tokens","INT",None),("total_cost","NUMERIC(12,6)",None),("latency_ms","INT",None),
        ("satisfaction","VARCHAR(20)",None),("rating","INT",None),("tags","JSON",None),
        ("needs_optimization","BOOLEAN",None),("annotation","JSON",None),
        ("started_at","DATETIME",None),("ended_at","DATETIME",None),
        ("created_at","DATETIME",None),("updated_at","DATETIME",None)]),
    "conversation_turns": ("biz", [
        ("id","INT","PK"),("conversation_id","INT","FK"),("position","INT",None),
        ("role","VARCHAR(20)",None),("content","TEXT",None),
        ("timestamp","DATETIME",None),("trace","JSON",None),
        ("created_at","DATETIME",None),("updated_at","DATETIME",None)]),

    "prompts": ("content", [
        ("id","INT","PK"),("name","VARCHAR(200)",None),("description","VARCHAR(500)",None),
        ("category","VARCHAR(50)",None),("tags","JSON",None),("content","TEXT",None),
        ("variables","JSON",None),("version","VARCHAR(50)",None),("status","VARCHAR(50)",None),
        ("created_by","VARCHAR(100)",None),("created_at","DATETIME",None),("updated_at","DATETIME",None)]),
    "prompt_versions": ("content", [
        ("id","INT","PK"),("prompt_id","INT","FK"),("version","VARCHAR(50)",None),
        ("content","TEXT",None),("changelog","VARCHAR(500)",None),("is_current","BOOLEAN",None),
        ("published_by","VARCHAR(100)",None),("published_at","DATETIME",None),
        ("created_at","DATETIME",None),("updated_at","DATETIME",None)]),
    "knowledge_bases": ("content", [
        ("id","INT","PK"),("name","VARCHAR(200)",None),("description","VARCHAR(500)",None),
        ("status","VARCHAR(50)",None),("document_count","INT",None),("segment_count","INT",None),
        ("embedding_model","VARCHAR(100)",None),("chunk_method","VARCHAR(20)",None),
        ("chunk_size","INT",None),("chunk_overlap","INT",None),
        ("retrieval_strategy","VARCHAR(20)",None),("top_k","INT",None),
        ("similarity_threshold","FLOAT",None),("created_by","VARCHAR(100)",None),
        ("created_at","DATETIME",None),("updated_at","DATETIME",None)]),
    "documents": ("content", [
        ("id","INT","PK"),("knowledge_base_id","INT","FK"),("file_name","VARCHAR(500)",None),
        ("file_type","VARCHAR(50)",None),("file_size","VARCHAR(50)",None),
        ("minio_path","VARCHAR(1000)",None),("status","VARCHAR(50)",None),
        ("segment_count","INT",None),("word_count","INT",None),
        ("error_message","TEXT",None),("uploaded_by","VARCHAR(100)",None),
        ("processed_at","DATETIME",None),("created_at","DATETIME",None),("updated_at","DATETIME",None)]),
    "segments": ("content", [
        ("id","INT","PK"),("knowledge_base_id","INT","FK"),("document_id","INT","FK"),
        ("position","INT",None),("content","TEXT",None),("word_count","INT",None),
        ("token_count","INT",None),("hit_count","INT",None),
        ("created_at","DATETIME",None),("updated_at","DATETIME",None)]),
    "tools": ("content", [
        ("id","INT","PK"),("name","VARCHAR(200)",None),("description","TEXT",None),
        ("type","VARCHAR(50)",None),("status","VARCHAR(50)",None),("config","JSON",None),
        ("function_definition","JSON",None),("call_count_7d","INT",None),
        ("success_rate","NUMERIC(5,2)",None),("avg_latency","INT",None),
        ("created_by","VARCHAR(100)",None),("created_at","DATETIME",None),("updated_at","DATETIME",None)]),

    "api_keys": ("system", [
        ("id","INT","PK"),("name","VARCHAR(100)",None),("key","VARCHAR(100)",None),
        ("permissions","VARCHAR(20)",None),("status","VARCHAR(20)",None),
        ("rate_limit","INT",None),("call_count","INT",None),
        ("last_used_at","DATETIME",None),("expires_at","DATETIME",None),
        ("allowed_agent_ids","JSON",None),("created_by","VARCHAR(100)",None),
        ("created_at","DATETIME",None),("updated_at","DATETIME",None)]),
    "alert_rules": ("system", [
        ("id","INT","PK"),("name","VARCHAR(100)",None),("description","VARCHAR(200)",None),
        ("condition","JSON",None),("notification","JSON",None),("status","VARCHAR(20)",None),
        ("created_by","VARCHAR(100)",None),("created_at","DATETIME",None),("updated_at","DATETIME",None)]),
    "alerts": ("system", [
        ("id","INT","PK"),("type","VARCHAR(20)",None),("title","VARCHAR(200)",None),
        ("message","TEXT",None),("source","VARCHAR(50)",None),("severity","VARCHAR(20)",None),
        ("status","VARCHAR(20)",None),("count","INT",None),
        ("first_occurred_at","DATETIME",None),("last_occurred_at","DATETIME",None),
        ("acknowledged_by","VARCHAR(100)",None),("acknowledged_at","DATETIME",None),
        ("resolved_at","DATETIME",None),("created_at","DATETIME",None),("updated_at","DATETIME",None)]),
    "system_settings": ("system", [
        ("id","INT","PK"),("system_name","VARCHAR(100)",None),("system_description","TEXT",None),
        ("default_language","VARCHAR(20)",None),("default_model","VARCHAR(100)",None),
        ("default_temperature","FLOAT",None),("default_max_tokens","INT",None),
        ("smtp_server","VARCHAR(200)",None),("smtp_port","INT",None),
        ("sender_email","VARCHAR(100)",None),("created_at","DATETIME",None),("updated_at","DATETIME",None)]),
}

# Column layout: (x, width, [tables in stacking order])
COLUMNS = [
    (70,   390, ["users","roles","permissions"]),
    (500,  390, ["user_roles","role_permissions","audit_logs","permission_applications"]),
    (1010, 420, ["model_providers","models","agents","conversations","conversation_turns"]),
    (1470, 380, ["agent_versions"]),
    (1930, 560, ["prompts","prompt_versions","knowledge_bases","documents","segments","tools"]),
    (2590, 540, ["api_keys","alert_rules","alerts","system_settings"]),
]
GAP = 40
HEADER = 30
ROW = 16
PAD_BOTTOM = 8

POS = {}
for cx, cw, names in COLUMNS:
    group_key = TABLES[names[0]][0]
    y = GROUPS[group_key]["y"] + 60
    if names[0] == "agent_versions":
        y = POS["agents"]["y"]          # 与 agents 对齐
    for name in names:
        cols = TABLES[name][1]
        h = HEADER + len(cols) * ROW + PAD_BOTTOM
        POS[name] = {"x": cx, "y": y, "w": cw, "h": h, "cols": cols}
        y += h + GAP

def row_y(name, colname):
    t = POS[name]
    for i, (cn, _, _) in enumerate(t["cols"]):
        if cn == colname:
            return t["y"] + HEADER + i * ROW + ROW / 2
    raise KeyError(colname)

def anchor(name, colname, side):
    t = POS[name]
    if side == "left":
        return (t["x"], row_y(name, colname))
    if side == "right":
        return (t["x"] + t["w"], row_y(name, colname))
    if side == "top":
        return (t["x"] + t["w"] / 2, t["y"])
    return (t["x"] + t["w"] / 2, t["y"] + t["h"])

def esc(s):
    return html.escape(str(s), quote=True)

out = []
out.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
out.append(f'<rect width="{W}" height="{H}" fill="#f7f8fa"/>')

# 标题
out.append(f'<text x="40" y="58" font-family="{FONT}" font-size="30" font-weight="700" fill="#0f1b2d">辰光 Agent 平台 · 数据库 ER 图（V3）</text>')
out.append(f'<text x="40" y="88" font-family="{FONT}" font-size="14" fill="#5a6675">23 张表 · 71 个权限码 · 数据源 docs/design/db/script.sql</text>')

# 图例
lx = 2350
out.append(f'<g font-family="{FONT}" font-size="12" fill="#5a6675">')
out.append(f'<rect x="{lx}" y="34" width="20" height="14" rx="3" fill="#fbf1de" stroke="#e2a13c"/><text x="{lx+26}" y="46">主键 PK</text>')
out.append(f'<rect x="{lx+110}" y="34" width="20" height="14" rx="3" fill="#eef2fc" stroke="#3e63dd"/><text x="{lx+136}" y="46">外键 FK</text>')
# 1:N 鸦爪图例
out.append(f'<line x1="{lx+232}" y1="42" x2="{lx+262}" y2="42" stroke="#3e63dd" stroke-width="1.6"/>')
out.append(f'<line x1="{lx+262}" y1="42" x2="{lx+250}" y2="36" stroke="#3e63dd" stroke-width="1.6"/>')
out.append(f'<line x1="{lx+262}" y1="42" x2="{lx+250}" y2="48" stroke="#3e63dd" stroke-width="1.6"/>')
out.append(f'<line x1="{lx+262}" y1="42" x2="{lx+250}" y2="42" stroke="#3e63dd" stroke-width="1.6"/>')
out.append(f'<text x="{lx+270}" y="46">1:N 关系（鸦爪）</text>')
out.append(f'<line x1="{lx+390}" y1="42" x2="{lx+430}" y2="42" stroke="#3e63dd" stroke-width="1.6" stroke-dasharray="5 4"/><text x="{lx+438}" y="46">跨组外键</text>')
out.append('</g>')

# 分组面板
for key, g in GROUPS.items():
    out.append(f'<rect x="{g["x"]}" y="{g["y"]}" width="{g["w"]}" height="{g["h"]}" rx="14" fill="{g["fill"]}" fill-opacity="0.55" stroke="{g["stroke"]}" stroke-opacity="0.35" stroke-dasharray="6 5"/>')
    out.append(f'<text x="{g["x"]+18}" y="{g["y"]+30}" font-family="{FONT}" font-size="16" font-weight="700" fill="{g["stroke"]}">{esc(g["label"])}</text>')

# 关系线（先画，置于表下方）
def bezier(p1, p2, c1, c2, dh):
    parts = [f'M {p1[0]:.1f},{p1[1]:.1f} C {c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}']
    color = "#3e63dd"
    out.append(f'<path d="{" ".join(parts)}" fill="none" stroke="{color}" stroke-width="1.6" stroke-opacity="0.75" {"stroke-dasharray=\"6 4\"" if dh else ""}/>')

def bar(p, side):
    x, y = p
    if side in ("left", "right"):
        out.append(f'<line x1="{x:.1f}" y1="{y-7:.1f}" x2="{x:.1f}" y2="{y+7:.1f}" stroke="#3e63dd" stroke-width="2"/>')
    else:
        out.append(f'<line x1="{x-7:.1f}" y1="{y:.1f}" x2="{x+7:.1f}" y2="{y:.1f}" stroke="#3e63dd" stroke-width="2"/>')

def crow(p, side):
    x, y = p
    if side == "left":
        pts = [(x-10, y-6), (x-14, y), (x-10, y+6)]
    elif side == "right":
        pts = [(x+10, y-6), (x+14, y), (x+10, y+6)]
    elif side == "top":
        pts = [(x-6, y-10), (x, y-14), (x+6, y-10)]
    else:
        pts = [(x-6, y+10), (x, y+14), (x+6, y+10)]
    for px, py in pts:
        out.append(f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{px:.1f}" y2="{py:.1f}" stroke="#3e63dd" stroke-width="1.6"/>')

def rel(src, scol, sside, dst, dcol, dside, dashed=False):
    p1 = anchor(src, scol, sside)
    p2 = anchor(dst, dcol, dside)
    def ctrl(p, side, dist=50):
        x, y = p
        if side == "left":  return (x-dist, y)
        if side == "right": return (x+dist, y)
        if side == "top":   return (x, y-dist)
        return (x, y+dist)
    bezier(p1, p2, ctrl(p1, sside), ctrl(p2, dside), dashed)
    bar(p1, sside)
    crow(p2, dside)

RELS = [
    ("users","id","right","user_roles","user_id","left",False),
    ("roles","id","right","user_roles","role_id","left",False),
    ("roles","id","right","role_permissions","role_id","left",False),
    ("permissions","id","right","role_permissions","permission_id","left",False),
    ("users","id","right","audit_logs","user_id","left",False),
    ("users","id","right","permission_applications","applicant_id","left",False),
    ("users","id","right","permission_applications","approver_id","left",True),
    ("model_providers","id","bottom","models","provider_id","top",False),
    ("models","id","bottom","agents","model_id","top",False),
    ("agents","id","bottom","conversations","agent_id","top",False),
    ("agents","id","right","agent_versions","agent_id","left",False),
    ("conversations","id","bottom","conversation_turns","conversation_id","top",False),
    ("prompts","id","bottom","prompt_versions","prompt_id","top",False),
    ("knowledge_bases","id","bottom","documents","knowledge_base_id","top",False),
    ("documents","id","bottom","segments","document_id","top",False),
]
for r in RELS:
    rel(*r)

# models -> conversations（同列，右侧绕行，虚线）
p1 = (POS["models"]["x"]+POS["models"]["w"], row_y("models","id"))
p2 = (POS["conversations"]["x"]+POS["conversations"]["w"], row_y("conversations","model_id"))
out.append(f'<path d="M {p1[0]},{p1[1]} C {p1[0]+22},{p1[1]} {p2[0]+22},{p2[1]} {p2[0]},{p2[1]}" fill="none" stroke="#3e63dd" stroke-width="1.6" stroke-opacity="0.75" stroke-dasharray="6 4"/>')
bar(p1, "right"); crow(p2, "right")

# users -> conversations（跨面板，走面板间隙，虚线）
y1 = row_y("users","id")
y2 = row_y("conversations","user_id")
x_gap = 940
p1 = (POS["users"]["x"]+POS["users"]["w"], y1)
p2 = (POS["conversations"]["x"], y2)
out.append(f'<path d="M {p1[0]},{p1[1]} H {x_gap} V {p2[1]} H {p2[0]}" fill="none" stroke="#3e63dd" stroke-width="1.6" stroke-opacity="0.75" stroke-dasharray="6 4"/>')
bar(p1, "right"); crow(p2, "left")

# knowledge_bases -> segments（同列，右侧绕行）
p1 = (POS["knowledge_bases"]["x"]+POS["knowledge_bases"]["w"], row_y("knowledge_bases","id"))
p2 = (POS["segments"]["x"]+POS["segments"]["w"], row_y("segments","knowledge_base_id"))
out.append(f'<path d="M {p1[0]},{p1[1]} C {p1[0]+26},{p1[1]} {p2[0]+26},{p2[1]} {p2[0]},{p2[1]}" fill="none" stroke="#3e63dd" stroke-width="1.6" stroke-opacity="0.75"/>')
bar(p1, "right"); crow(p2, "right")

# users 自引用（created_by）左侧回环
yc = row_y("users","created_by")
p1 = (POS["users"]["x"], yc-8); p2 = (POS["users"]["x"], yc+8)
out.append(f'<path d="M {p1[0]},{p1[1]} C 18,{p1[1]} 18,{p2[1]} {p2[0]},{p2[1]}" fill="none" stroke="#3e63dd" stroke-width="1.6" stroke-opacity="0.75" stroke-dasharray="6 4"/>')
bar(p1, "left"); crow(p2, "left")

# 表
for name, (gkey, cols) in TABLES.items():
    t = POS[name]; x, y, w, h = t["x"], t["y"], t["w"], t["h"]
    g = GROUPS[gkey]
    out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="7" fill="#ffffff" stroke="{g["stroke"]}" stroke-opacity="0.55"/>')
    out.append(f'<path d="M {x+7} {y} H {x+w-7} A 7 7 0 0 1 {x+w} {y+7} V {y+HEADER} H {x} V {y+7} A 7 7 0 0 1 {x+7} {y} Z" fill="#0f1b2d"/>')
    out.append(f'<text x="{x+12}" y="{y+20}" font-family="{MONO}" font-size="12.5" font-weight="700" fill="#ffffff">{esc(name)}</text>')
    for i, (cn, ct, ck) in enumerate(cols):
        ry = y + HEADER + i*ROW
        if i % 2 == 1:
            out.append(f'<rect x="{x+1}" y="{ry}" width="{w-2}" height="{ROW}" fill="#f8fafc"/>')
        weight = "600" if ck else "400"
        out.append(f'<text x="{x+12}" y="{ry+11}" font-family="{MONO}" font-size="9.5" font-weight="{weight}" fill="#18212e">{esc(cn)}</text>')
        out.append(f'<text x="{x+w-10}" y="{ry+11}" text-anchor="end" font-family="{MONO}" font-size="8.2" fill="#8b95a3">{esc(ct)}</text>')
        if ck:
            bw = 26 if ck == "PK,FK" else 20
            bx = x + w - 10 - 8.2*len(ct)*0.55 - bw - 6
            fill = "#fbf1de" if ck == "PK" else "#eef2fc" if ck == "FK" else "#f1eafe"
            stroke = "#e2a13c" if ck == "PK" else "#3e63dd" if ck == "FK" else "#7c5cd6"
            color = "#a6761f" if ck == "PK" else "#3e63dd" if ck == "FK" else "#6b46c1"
            out.append(f'<rect x="{bx:.1f}" y="{ry+2.5}" width="{bw}" height="11" rx="2.5" fill="{fill}" stroke="{stroke}" stroke-opacity="0.6"/>')
            out.append(f'<text x="{bx+bw/2:.1f}" y="{ry+10.6}" text-anchor="middle" font-family="{FONT}" font-size="6.8" fill="{color}">{esc(ck)}</text>')

out.append('</svg>')

svg = "\n".join(out)
here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(here, "er.html"), "w", encoding="utf-8") as f:
    f.write(f'''<!DOCTYPE html><html><head><meta charset="utf-8"><style>
html,body{{margin:0;padding:0;background:#f7f8fa;}} svg{{display:block;}}
</style></head><body>{svg}</body></html>''')
print("wrote er.html", len(svg), "bytes")
