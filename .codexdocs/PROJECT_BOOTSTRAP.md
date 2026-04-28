# BibleHome — Project Bootstrap

## 1. 项目定位

BibleHome 不是单纯的圣经阅读器，而是一个长期演进的平台型项目，当前和未来目标包括：

- 多语言、多版本、多年代圣经浏览
- 多版本并排对比
- 用户标注、高亮、笔记、收藏、标签
- 跨语言围绕同一经文交流
- Bible RAG 问答
- 心理学、哲学等专业辅导型 RAG
- 教堂为核心的 LBS 社区互动
- 未来扩展 AI 语音、图片能力

核心目标是：在保证圣经正文浏览极快响应的同时，为动态用户数据、社区数据和 AI 能力预留长期兼容空间。

---

## 2. 架构总原则

### 2.1 已确认采用的架构

- 前端：Next.js / React
- Bible 正文：静态 JSON 文件，通过 CDN 分发
- API：仅服务用户动态能力，不参与正文主阅读路径
- 数据库：PostgreSQL
- 向量：pgvector
- 地理：PostGIS
- 部署：前端/静态资源走 Cloudflare，后端和数据库走 VPS

### 2.2 为什么这样选

Bible 是典型“读多写少”场景。正文一旦确定，绝大多数访问都是读取，极适合走静态化分发；而用户标注、社区互动、RAG 检索都是动态数据，适合放进 PostgreSQL 统一管理。

### 2.3 明确不采用的主路径

以下方案已经讨论过但不采用作为当前主设计：

- Bible 正文全部走 REST API
- Cloudflare D1 作为主数据库
- Cloudflare Vectorize 作为主向量库
- 拆成两个数据库分别处理 pgvector 和 PostGIS
- VPS CPU 作为全量 embedding 主力

原因见文末“已拒绝方案摘要”。

---

## 3. 最重要的核心设计：双层引用体系

这是整个项目最关键的长期稳定设计。

### 3.1 语义层：verse_id

用于跨语言、跨版本、跨模块的统一语义锚点。

格式：

```text
book-chapter-verse
```

示例：

```text
43-3-16
```

特点：

- 与语言无关
- 与版本无关
- 全系统唯一语义锚点

用途：

- annotation 关联
- RAG chunk 关联
- 社区帖子引用
- AI 问答引用
- 跨语言用户围绕同一经文互动

### 3.2 显示层：ref

用于具体语言、具体版本的显示层引用。

格式：

```text
lang-version-book-chapter-verse
```

示例：

```text
zh-CUV-43-3-16
```

特点：

- 绑定具体语言和译本
- 用于 UI 和具体版本定位

### 3.3 强规则

- 所有跨语言语义关联必须基于 `verse_id`
- `ref` 只是显示层，不是跨语言主键
- 任何后续模块都不能退化回只用 `ref`

---

## 4. 前端与静态正文数据设计

### 4.1 前端技术路线

推荐：

- Next.js
- SSG + CSR

### 4.2 页面路由建议

```text
/[lang]/[version]/[book]/[chapter]
```

例如：

- `/zh/CUV/john/3`
- `/en/KJV/john/3`

### 4.3 正文静态数据分发

路径模式：

```text
/data/{lang}/{version}/{book}/{chapter}.json
```

例如：

- `/data/zh/CUV/john/3.json`
- `/data/en/KJV/john/3.json`

### 4.4 JSON 结构建议

```json
{
  "book": 43,
  "chapter": 3,
  "verses": [
    "第1节文本",
    "第2节文本"
  ]
}
```

原则：

- 冗余字段尽量少
- 按章组织
- 依赖 CDN 的 gzip / brotli 压缩
- 不让数据库承担正文主读取

### 4.5 性能要求

CDN 缓存建议：

```http
Cache-Control: public, max-age=31536000, immutable
```

前端后续要支持：

- 章节预加载
- IndexedDB / localStorage 缓存
- 正文与 annotation 的前端合并渲染

---

## 5. 当前数据库能力状态

### 5.1 已验证成功

当前环境：

- Ubuntu 24.x ARM
- Docker
- PostgreSQL 16 自建镜像

已验证扩展：

- `plpgsql`
- `vector`
- `postgis`
- `uuid-ossp`
- `pgcrypto`

### 5.2 自建镜像原因

需要同时支持：

- pgvector
- PostGIS
- ARM 架构

因此采用：

- `postgres:16-bookworm`
- 安装 `postgresql-16-postgis-3`
- 安装 `postgresql-server-dev-16`
- 源码编译安装 `pgvector`

### 5.3 已踩过的坑

曾出现：

```text
fatal error: postgres.h: No such file or directory
```

根因：缺少 `postgresql-server-dev-16`

当前已修复并构建成功。

---

## 6. 当前数据库对象状态

### 6.1 已创建表

- `bible.verses`
- `annotation.annotations`
- `annotation.tags`
- `annotation.tag_translations`
- `ai.chunks`

### 6.2 已成功测试

- `annotation.annotations` 已成功插入测试记录

### 6.3 尚未补齐

- `core.users`
- `core.sessions`
- `community.posts`
- `community.groups`
- `community.memberships`
- `community.churches`

### 6.4 当前需要注意

- `ai.chunks.embedding` 维度要和最终 embedding 模型对齐
- `annotation.annotations` 后续要增加 embedding 列

---

## 7. Annotation 系统设计基线

### 7.1 目标

支持：

- 高亮
- 笔记
- 收藏
- 标签
- 私有 / 公开可见性
- 后续 annotation 参与 RAG

### 7.2 关键字段逻辑

- `verse_id`：跨语言语义关联
- `ref`：具体版本上下文
- `lang`：标注内容本身语言
- `visibility`：`private` / `public`

### 7.3 API 设计方向

- `POST /api/annotations`
- `GET /api/annotations`
- `PUT /api/annotations/{id}`
- `DELETE /api/annotations/{id}`

### 7.4 前后端职责划分

- 后端返回标注数据
- 前端负责把章节正文与标注合并渲染

---

## 8. 标签系统设计基线

### 8.1 规范化标签

annotation 里不能只靠自然语言标签文本，否则跨语言搜索和聚合会失效。

推荐模式：

- `annotation.tags.key` 存 canonical key，例如 `love`
- `annotation.tag_translations` 存多语言标签名，例如“爱”/“love”/“Liebe”

### 8.2 作用

- 多语言标签展示
- 跨语言标签搜索
- 未来社区和 RAG 的主题聚合

---

## 9. RAG 设计基线

### 9.1 总体流程

```text
原始多语言多版本数据
→ 标准化为 verse 记录
→ 生成 verse_id / ref
→ 按章节/语言分组
→ 连续经文切 chunk
→ embedding
→ 写入 ai.chunks
→ 查询时 embedding 问题
→ pgvector 检索 topK
→ 结合 LLM 输出答案
```

### 9.2 chunk 设计原则

明确不采用：

- 一节一个 chunk

推荐采用：

- 连续经文组成语义 chunk
- 保持语义连续
- 长度控制在适合 embedding 的范围

### 9.3 多语言 embedding 原则

所有语言必须使用**同一个 embedding 模型**。

禁止：

- 中文一个模型
- 英文另一个模型

否则向量空间不一致，跨语言检索会失效。

### 9.4 annotation 参与 RAG

后续需要：

- 给 `annotation.annotations` 增加 `embedding` 列
- 用户笔记和公开笔记可参与检索
- 支持个性化 RAG

---

## 10. 本地 embedding 策略基线

### 10.1 为什么选择本地处理

由于圣经多语言多版本原始数据量较大，线上 embedding 服务在以下方面不优：

- 成本
- 速度
- 长期外部依赖

因此当前更适合采用本地批量 embedding。

### 10.2 模型选择

候选模型：

- `jeffh/intfloat-multilingual-e5-large-instruct:q8_0`
- `jeffh/intfloat-multilingual-e5-large-instruct:f16`

当前推荐默认值：

- `q8_0`

理由：

- embedding 场景中与 f16 差异很小
- 显存占用更低
- 速度更好
- 对 Tesla P4 更友好

### 10.3 硬件结论

- 4 核 Neoverse-N1 VPS：仅测试，不适合全量 embedding
- Tesla P4：可用于增量任务，不适合作为主力全量处理
- RTX 5070 Ti：推荐作为主力 embedding 设备

最终建议：

- 主力 embedding：RTX 5070 Ti
- 增量/备用：Tesla P4
- VPS：只做 API / 查询，不做全量 embedding

### 10.4 严格一致性要求

正式向量库不能混用：

- q8_0 和 f16
- 不同 embedding 模型
- 不同 preprocessing 规则

---

## 11. 社区与 LBS 设计基线

### 11.1 社区目标

- 多语言用户围绕同一节经文交流
- 群组互动
- 公开帖子与 RAG 联动

### 11.2 LBS 目标

- 教堂附近检索
- 基于位置的群组/教会发现

### 11.3 数据库要求

必须采用：

- PostGIS

### 11.4 绑定规则

社区内容和经文绑定统一走：

- `verse_id`

而不是：

- 单独的具体语言版本 `ref`

---

## 12. 已拒绝方案摘要

### 12.1 Bible 正文走实时 API

拒绝原因：

- 性能差
- 失去 CDN 优势
- 对读多写少场景不合适

### 12.2 Cloudflare D1 做主库

拒绝原因：

- 不适合复杂关系与未来扩展

### 12.3 Cloudflare Vectorize 做主向量库

拒绝原因：

- 不适合当前强关系、多表过滤、权限控制需求

### 12.4 拆成两个数据库分别做向量和地理

拒绝原因：

- 跨库复杂
- 运维成本高
- 不利于长期协同

### 12.5 VPS CPU 做 embedding 主力

拒绝原因：

- 速度不可接受

---

## 13. 当前风险与易遗漏点

### 13.1 必须始终牢记

- `verse_id` 是唯一语义锚点
- `ref` 不是跨语言主键
- Bible 正文主阅读路径不走 API
- embedding 模型与量化版本必须统一
- 标签必须规范化且支持多语言翻译
- annotation 后续必须可接入 RAG
- 社区与经文讨论必须绑定 `verse_id`

### 13.2 当前未完成项

- community 表补齐
- core 表补齐
- annotation embedding 列
- embedding 维度最终确认
- 原始数据标准化脚本
- chunk 切分脚本
- 批量 embedding 导入脚本
- annotation API
- RAG query API

---

## 14. 建议 Codex 的起始执行顺序

1. 补齐 SQL migration（core / community / annotation embedding）
2. 确认最终 embedding 向量维度
3. 实现原始 Bible 数据标准化脚本
4. 实现 chunk 切分脚本
5. 实现本地 GPU embedding 批量导入脚本
6. 实现 annotation API
7. 实现基础 RAG query API
8. 实现前端章节页正文 + annotation 合并逻辑
9. 再推进 community / LBS / AI 扩展
