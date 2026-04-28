# BibleHome — Database Migration Plan

## 1. 目标

本文档用于指导 BibleHome 从当前已初始化的 PostgreSQL 状态，逐步迁移到可支撑以下能力的数据库结构：

- 多语言多版本圣经引用体系
- 用户 annotation 系统
- 标签规范化与多语言映射
- RAG chunk 与向量存储
- 社区帖子与经文讨论
- 后续教堂 / 群组 / LBS 扩展

重点要求：

- 全系统以 `verse_id` 为语义层统一锚点
- `ref` 只作为显示层和版本上下文使用
- 数据结构为 RAG 与社区扩展留足空间

---

## 2. 当前已存在对象

已验证存在：

- PostgreSQL 扩展：`vector`, `postgis`, `uuid-ossp`, `pgcrypto`
- 表：
  - `bible.verses`
  - `annotation.annotations`
  - `annotation.tags`
  - `annotation.tag_translations`
  - `ai.chunks`

当前已知缺口：

- `core.users`
- `core.sessions`
- `community.posts`
- `community.groups`
- `community.memberships`
- `community.churches`
- `annotation.annotations.embedding`
- 最终 embedding 维度确认

---

## 3. 迁移原则

### 3.1 不破坏既有核心设计

必须坚持：

- 所有语义关联基于 `verse_id`
- 不允许回退到仅用 `ref`
- 社区和 RAG 均应围绕 `verse_id` 组织

### 3.2 先补基础对象，再扩展能力

建议顺序：

1. schema 完整化
2. 核心用户表
3. 社区基础表
4. annotation 向量扩展
5. 维度对齐与向量索引复核
6. 后续地理/LBS表

### 3.3 先做可逆、低风险迁移

- 先增加列/新表
- 后做数据回填
- 最后再加复杂约束与索引

---

## 4. 当前核心表回顾

## 4.1 `bible.verses`

用途：

- 存放经文引用索引
- 建立 `verse_id` 与 `ref` 的桥接
- 不承担正文主读取

当前结构：

```sql
CREATE TABLE bible.verses (
    id TEXT PRIMARY KEY,
    verse_id TEXT NOT NULL,
    lang TEXT NOT NULL,
    version TEXT NOT NULL,
    book INT NOT NULL,
    chapter INT NOT NULL,
    verse INT NOT NULL
);
```

当前索引：

- `idx_verse_id`
- `idx_lang_version`

建议保留，不做破坏性修改。

---

## 4.2 `annotation.annotations`

用途：

- 用户高亮、笔记、收藏
- 将来参与 RAG
- 将来可支持公开分享

当前结构：

```sql
CREATE TABLE annotation.annotations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    verse_id TEXT NOT NULL,
    ref TEXT,
    lang TEXT,
    type TEXT NOT NULL,
    content TEXT,
    color TEXT,
    tags TEXT[],
    visibility TEXT DEFAULT 'private',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

当前索引：

- `idx_user_verse`
- `idx_verse_public`
- `idx_tags`

关键未完成项：

- 增加 `embedding` 列

---

## 4.3 `annotation.tags` 与 `annotation.tag_translations`

当前结构已经符合方向，建议保留并在后续业务代码中真正用起来。

作用：

- canonical tag key
- 多语言标签翻译
- 跨语言搜索和聚类

---

## 4.4 `ai.chunks`

当前结构：

```sql
CREATE TABLE ai.chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    verse_ids TEXT[] NOT NULL,
    lang TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(768),
    created_at TIMESTAMP DEFAULT NOW()
);
```

当前索引：

```sql
CREATE INDEX idx_chunks_embedding
ON ai.chunks
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

注意：

- `VECTOR(768)` 必须与最终 embedding 模型输出维度再次核对
- 如最终模型维度不同，需要迁移该列和索引

---

## 5. 迁移阶段划分

## Phase A — 补齐 schema 与基础表

### A1. 确保 schema 存在

```sql
CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS bible;
CREATE SCHEMA IF NOT EXISTS annotation;
CREATE SCHEMA IF NOT EXISTS community;
CREATE SCHEMA IF NOT EXISTS ai;
```

### A2. 创建用户表

```sql
CREATE TABLE IF NOT EXISTS core.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE,
    password_hash TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### A3. 创建 session 表

```sql
CREATE TABLE IF NOT EXISTS core.sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES core.users(id),
    token TEXT,
    expires_at TIMESTAMP
);
```

推荐索引：

```sql
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON core.sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON core.sessions(token);
```

---

## Phase B — 补齐社区基础表

### B1. community.posts

```sql
CREATE TABLE IF NOT EXISTS community.posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES core.users(id),
    content TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    verse_id TEXT
);
```

推荐索引：

```sql
CREATE INDEX IF NOT EXISTS idx_posts_user_id ON community.posts(user_id);
CREATE INDEX IF NOT EXISTS idx_posts_verse_id ON community.posts(verse_id);
```

### B2. community.groups

```sql
CREATE TABLE IF NOT EXISTS community.groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    type TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### B3. community.memberships

```sql
CREATE TABLE IF NOT EXISTS community.memberships (
    user_id UUID REFERENCES core.users(id),
    group_id UUID REFERENCES community.groups(id),
    role TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, group_id)
);
```

说明：

- 社区和经文的语义关联统一走 `verse_id`
- 如后续需要绑定具体版本上下文，可额外增加 `ref`

---

## Phase C — Annotation 向量化扩展

### C1. 增加 embedding 列

在确认最终 embedding 维度之后执行。当前文档仅示意：

```sql
ALTER TABLE annotation.annotations
ADD COLUMN IF NOT EXISTS embedding VECTOR(<final_dimension>);
```

### C2. 增加向量索引（如需要）

```sql
CREATE INDEX IF NOT EXISTS idx_annotations_embedding
ON annotation.annotations
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

说明：

- 只有当 annotation 进入 RAG 检索链路时才需要建立该索引
- 如果早期量很小，可先不建索引，避免写入复杂度增加

---

## Phase D — ai.chunks 向量维度核对与迁移

这是一个非常关键的待确认项。

### D1. 必须先确认最终 embedding 维度

Codex 需要核实：

- `intfloat-multilingual-e5-large-instruct` 在当前部署/推理方式下输出的实际向量维度
- 不能想当然沿用 768

### D2. 如果维度与当前不一致

不能直接沿用现有列，需要做迁移。

推荐迁移步骤：

1. 新增新列，例如 `embedding_new VECTOR(<new_dim>)`
2. 回填新 embedding
3. 新建索引
4. 验证查询
5. 删除旧索引
6. 删除旧列
7. 重命名新列

示例：

```sql
ALTER TABLE ai.chunks ADD COLUMN embedding_new VECTOR(<new_dim>);
```

完成回填后：

```sql
CREATE INDEX idx_chunks_embedding_new
ON ai.chunks
USING ivfflat (embedding_new vector_cosine_ops)
WITH (lists = 100);
```

注意：

- 不要直接 drop 老列，先保证数据完整
- 大批量回填时建议分批进行

---

## Phase E — 教堂/LBS 表

待社区基础完成后再补。

### E1. community.churches

```sql
CREATE TABLE IF NOT EXISTS community.churches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    location GEOGRAPHY(POINT),
    created_at TIMESTAMP DEFAULT NOW()
);
```

推荐索引：

```sql
CREATE INDEX IF NOT EXISTS idx_churches_location
ON community.churches
USING GIST (location);
```

### E2. community.groups 增加 church_id

后续可按需求迁移：

```sql
ALTER TABLE community.groups
ADD COLUMN IF NOT EXISTS church_id UUID REFERENCES community.churches(id);
```

---

## 6. 数据导入相关迁移原则

数据库迁移只是结构层，后续还会有数据级迁移或导入，需要与结构协同。

## 6.1 Bible 原始数据导入原则

原始记录需要至少标准化为：

- `lang`
- `version`
- `book`
- `chapter`
- `verse`
- `text`
- `verse_id`
- `ref`

其中：

- `bible.verses` 存索引和引用
- 正文仍走静态 JSON

## 6.2 RAG chunk 导入原则

导入 `ai.chunks` 时：

- 不按单节做 chunk
- 按连续经文语义聚合
- 所有语言必须用同一个 embedding 模型
- 全量正式向量库不能混用 q8_0 与 f16

---

## 7. Migration 执行顺序建议

### Step 1
补齐缺失 schema 和基础表：

- `core.users`
- `core.sessions`
- `community.posts`
- `community.groups`
- `community.memberships`

### Step 2
确认 embedding 模型最终输出维度

### Step 3
如有必要，迁移 `ai.chunks.embedding`

### Step 4
为 `annotation.annotations` 增加 embedding 列

### Step 5
再推进社区与 LBS 表

建议不要一开始就把所有扩展表一次性铺满，先把“用户 + annotation + RAG 基础链路”打通。

---

## 8. 已拒绝的迁移方向

### 8.1 不迁移到 Cloudflare D1 主库

原因：

- 关系能力不足
- 不利于 annotation / 社区 / RAG 长期扩展

### 8.2 不拆分为两个 PostgreSQL 实例分别处理向量与地理

原因：

- 增加跨库复杂度
- 不利于统一管理和权限控制

### 8.3 不将正文主读取逻辑迁移进数据库 API

原因：

- 会破坏静态正文 + CDN 的高性能设计

---

## 9. Codex 执行这份迁移计划时必须关注的事项

### 9.1 必须优先核对 embedding 维度

这是当前最可能埋雷的点。

### 9.2 所有表设计都不能破坏 verse_id 语义核心

### 9.3 migration 脚本应尽量使用 `IF NOT EXISTS`

因为当前数据库已经部分创建成功。

### 9.4 大型向量列迁移要分步进行

不要粗暴 drop / recreate，避免正式数据导入后重做代价太大。

### 9.5 annotation 和 community 未来都可能进入 RAG

所以 schema 设计时不要只按当前 UI 需求思考。

---

## 10. 当前建议的近期迁移目标

Codex 在拿到这份文档后，建议优先完成：

1. `core` 表迁移脚本
2. `community` 基础表迁移脚本
3. `annotation` embedding 扩展预留脚本
4. `ai.chunks` 维度确认与必要迁移脚本
5. 将这些迁移组织成统一 migration 管理体系

等这些完成后，再进入：

- 原始 Bible 数据标准化导入
- chunk 切分
- 批量 embedding
- annotation API
- RAG query API
