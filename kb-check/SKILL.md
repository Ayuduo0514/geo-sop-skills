---
name: kb-check
description: |
  GEO 知识库质量审计 skill。每次知识库结构性改动后强制执行，17 项检查清单 + 自动修复 + 审计报告。不通过不交付。

  触发条件（以下任一）：
  - 修改了知识库目录结构、SOP、概念页、实体页、来源摘要
  - 修改了任意层级的 CLAUDE.md
  - ingest 了新的原始资料
  - 用户明确说「跑一下质检」「检查一下知识库」「kb-check」「安检」
  - 改完不跑质检就确认完成 — 这是结构性改动的强制门禁

  反触发条件：
  - 纯查询操作（只读不写）
  - 临时草稿明确不入库
  - 用户明确说「不用检查」「跳过质检」

  **注意**：写入前拦截已拆分为独立 skill `kb-save`，在 Write/Edit 知识库文件前自动调用。
---

# kb-check — 知识库质量审计（v2.1）

## 定位

不是可选的 lint，是**结构性改动的强制门禁**。改完不跑 kb-check = 不对齐的隐患直接入库。

**执行时机**：知识库改动完成后、用户确认任务完成前。不通过不交付。

**写入前拦截**：任何 Write/Edit 知识库文件前，先调用 `kb-save` skill 执行 L1 快速扫描。详情见该 skill，本文不重复。

---

## 执行纪律

1. **逐条执行**，不跳过。用户没问的不等于不重要。
2. **用工具验证**，不凭记忆。Glob 查文件、Grep 搜链接、Read 核对内容。
3. **未通过项必须修复**，不能标注"已知问题"就放行。
4. **产出审计报告**：写进 `知识库/AI操作记录/kb-check-{日期}.md`，同时在 `知识库/日志.md` append 一行。若当天已有同名文件，追加序号。
5. **自动修复优先**：L1 检查中发现机械性问题（死链、frontmatter 缺失、格式错误），先尝试自动修复，修复后重新验证。

---

## 自动修复（Auto-fix）

L1 扫描中发现以下问题时，先自动修复，不报告：

### 死链 → 自动创建 Stub

- **概念页死链**：创建 `概念/XXX.md`，最小 frontmatter + 定义占位
- **实体页死链**：创建 `实体/XXX.md`，最小 frontmatter + 基本信息占位
- **不自动创建**：来源摘要 stub（需人工提炼）、SOP stub（需完整骨架）

### Frontmatter 缺失 → 自动补全

- 概念/实体/来源摘要/SOP 各类型缺失的必填字段，按类型补全
- 来源摘要缺少 `原始资料:` → **不自动修复**（需人工确认路径）

### Markdown 链接 → 自动转 Wikilink

- `[文字](路径.md)` → `[[路径|文字]]`
- 外部 URL 保持不变

### TODO 占位 → 自动迁移

- 超过 7 天的 TODO → 迁移到 `AI操作记录/待处理-TODO.md`
- 7 天内的 TODO → 保留原位，记录到审计报告

---

## 变更范围检测（执行前置步骤）

kb-check 启动时，先确定"本次改动了什么"，再决定跑哪些检查项。

**检测方法**：
```bash
# Bash (Git Bash)
ls -lt D:/Projects/geo-knowledge-base/GEO/GEO理论/知识库/ | head -20

# PowerShell
Get-ChildItem -Path "D:/Projects/geo-knowledge-base/GEO/GEO理论/知识库/" -Recurse -Filter "*.md" | Sort-Object LastWriteTime -Descending | Select-Object -First 20 Name, LastWriteTime, Directory
```

**根据变更类型选择检查项**：

| 变更类型 | 必跑检查项 | 可选检查项 |
|---------|-----------|-----------|
| 改了概念页 | Q7, Q14, Q16 | Q3, Q8 |
| 改了实体页 | Q7, Q14, Q16 | Q3, Q8 |
| 改了来源摘要 | Q4, Q14, Q17 | Q6, Q8 |
| 改了 SOP | Q8, Q9, Q10, Q17 | Q3, Q6 |
| 改了原始资料 | Q6, Q11, Q14, Q17 | Q2 |
| 改了 CLAUDE.md | Q5 | — |
| 改了目录结构 | Q1 | Q3, Q5 |
| 批量/全量改动 | **全部 17 项** | — |

---

## 快速模式（30 秒安检）

用户说「快速检查」「安检」时，只跑 L1 的 7 项，30 秒内排除结构性硬伤：

**执行项**：Q1, Q3, Q7, Q11, Q12, Q13, Q16
**跳过项**：Q2, Q4, Q5, Q6, Q8, Q9, Q10, Q14, Q15, Q17
**产出**：简化审计报告，只列未通过的 P0 项和自动修复记录。

---

## 17 项检查清单索引

**执行检查项前，读取对应的 references 文件获取详细方法：**

| 项 | 名称 | 级别 | 类型 | 详细方法位置 |
|---|------|------|------|-------------|
| Q1 | 目录结构合规 | P0 | L1 自动 | [references/l1-checklist.md](references/l1-checklist.md) |
| Q2 | 双向链接完整性 | P1 | L2 人工 | [references/l2-checklist.md](references/l2-checklist.md) |
| Q3 | 死链检测 | P0 | L1 自动 | [references/l1-checklist.md](references/l1-checklist.md) |
| Q4 | 日志/索引同步 | P1 | L2 人工 | [references/l2-checklist.md](references/l2-checklist.md) |
| Q5 | CLAUDE.md 一致性 | P1 | L2 人工 | [references/l2-checklist.md](references/l2-checklist.md) |
| Q6 | 下游影响 | P1 | L2 人工 | [references/l2-checklist.md](references/l2-checklist.md) |
| Q7 | Frontmatter schema | P1 | L1 自动 | [references/l1-checklist.md](references/l1-checklist.md) |
| Q8 | 来源标注完整性 | P1 | L2 人工 | [references/l2-checklist.md](references/l2-checklist.md) |
| Q9 | SOP 四要素 | P1 | L2 人工 | [references/l2-checklist.md](references/l2-checklist.md) |
| Q10 | SOP 五节骨架 | P1 | L2 人工 | [references/l2-checklist.md](references/l2-checklist.md) |
| Q11 | 原始资料只读 | P0 | L1 自动 | [references/l1-checklist.md](references/l1-checklist.md) |
| Q12 | Wikilink 格式 | P1 | L1 自动 | [references/l1-checklist.md](references/l1-checklist.md) |
| Q13 | TODO 占位 | P1 | L1 自动 | [references/l1-checklist.md](references/l1-checklist.md) |
| Q14 | 概念/实体/来源同步 | P1 | L2 人工 | [references/l2-checklist.md](references/l2-checklist.md) |
| Q15 | AI 操作记录完整 | P2 | L2 人工 | [references/l2-checklist.md](references/l2-checklist.md) |
| Q16 | 内容生命周期 | P2 | L1 自动 | [references/l1-checklist.md](references/l1-checklist.md) |
| Q17 | 引用时效性 | P1 | L2 人工 | [references/l2-checklist.md](references/l2-checklist.md) |

**L1 vs L2 的区别**：
- **L1 自动扫描**：工具可直接验证（Glob/Grep/ls），不需要 Read 文件内容。如"文件是否存在""frontmatter 是否完整"。
- **L2 人工判断**：需要 Read 文件后判断内容质量。如"来源标注是否准确""SOP 四要素是否完整"。

**执行顺序**：先跑 L1 快速排除硬伤 → 再跑 L2 确保内容质量。

---

## 审计报告格式

**执行效率分级**：
- **L1 自动扫描**（工具可直接验证）：Q1, Q3, Q7, Q11, Q12, Q13, Q16（日期部分）
- **L2 人工判断**（需要 Read 后判断）：Q2, Q4, Q5, Q6, Q8, Q9, Q10, Q14, Q15, Q17

优先执行 L1，快速排除硬伤；再执行 L2，确保质量。

未通过项必须写入报告：

```markdown
---
type: AI操作记录
audit_type: kb-check
date: YYYY-MM-DD
result: pass | fail
---

# kb-check 审计报告 — [日期]

## 执行范围
{本次改动的文件列表}

## 自动修复记录

| 项 | 修复前 | 修复动作 | 修复后 |
|---|--------|---------|--------|
| Q3 死链 | `[[概念/XXX]]` 不存在 | 创建 stub `概念/XXX.md` | ✅ 已创建 |
| Q7 frontmatter | `概念/YYY.md` 缺少 `最后更新` | 添加 `最后更新: YYYY-MM-DD` | ✅ 已补全 |

## 健康度摘要

| 指标 | 当前值 | 阈值 | 状态 |
|------|--------|------|------|
| 死链率 | {死链数/总链接数}% | 0% | ✅/❌ |
| 来源标注覆盖率 | {有来源的论断数/总论断数}% | ≥90% | ✅/❌ |
| 双向链接完整率 | {有回链的资料数/被引用资料数}% | 100% | ✅/❌ |
| 过期内容率 | {过期文件数/总文件数}% | ≤10% | ✅/❌ |
| TODO 待处理数 | {N} 个 | 0 | ✅/❌ |

## 检查结果（按优先级排序）

| 项 | 级别 | 结果 | 说明 |
|---|------|------|------|
| Q1 目录结构 | P0 | ✅/❌ | |
| Q3 死链检测 | P0 | ✅/❌ | |
| Q11 原始资料只读 | P0 | ✅/❌ | |
| Q2 双向链接 | P1 | ✅/❌ | |
| Q4 日志索引同步 | P1 | ✅/❌ | |
| Q5 CLAUDE.md一致性 | P1 | ✅/❌ | |
| Q6 下游影响 | P1 | ✅/❌ | |
| Q7 Frontmatter | P1 | ✅/❌ | |
| Q8 来源标注 | P1 | ✅/❌ | |
| Q9 SOP四要素 | P1 | ✅/❌ | |
| Q10 SOP五节骨架 | P1 | ✅/❌ | |
| Q12 Wikilink格式 | P1 | ✅/❌ | |
| Q13 TODO占位 | P1 | ✅/❌ | |
| Q14 概念实体同步 | P1 | ✅/❌ | |
| Q15 AI记录完整 | P1 | ✅/❌ | |
| Q17 引用时效性 | P1 | ✅/❌ | |
| Q16 内容生命周期 | P2 | ✅/❌ | |

## 未通过项详情

### Q{N}: {名称}（{级别}）
- **问题**：{描述}
- **影响**：{不修会怎样}
- **修复动作**：{具体步骤}

## 修复确认
{修复后重新检查的结果}
```

---

## 关系索引刷新（kb-check 完成后）

**执行时机**：审计报告写入后、标记任务完成前。只读查询时跳过。

**命令**：
```bash
node D:/Projects/_ops/geo-sync/generate-link-index.js
```

**效果**：生成 `知识库/关系索引-静态.md`，含出入链矩阵、死链检测、Hub 节点 TOP10。

**失败时**：在审计报告末尾追加 `⚠️ 关系索引刷新失败：{错误信息}`。

---

## 与三层 CLAUDE.md 的关系

kb-check 是**执行机制**，CLAUDE.md 是**规范来源**。检查项对应的规范：

| 检查项 | 规范来源 |
|-------|---------|
| Q1, Q11, Q12 | 根层 CLAUDE.md — 全局 LLM Wiki 核心约定 |
| Q2 | 根层 CLAUDE.md — 双向链接规则 |
| Q4 | 根层 CLAUDE.md — 日志/索引格式 + 双写原则 |
| Q5 | 根层 CLAUDE.md — 修改触发矩阵 |
| Q7 | GEO理论/CLAUDE.md — 概念页/实体页格式 |
| Q8, Q9, Q10 | GEO理论/CLAUDE.md — SOP 写作规范 |
| Q6 | GEO理论/CLAUDE.md — 每次 ingest 必须同时更新 |
| Q3 | 隐含规范 — 死链破坏知识网络 |
| Q13 | 根层 CLAUDE.md — 防幻觉约束（TODO 标注） |
| Q14 | GEO理论/CLAUDE.md — 每次 ingest 必须同时更新 + 概念页/实体页格式 |
| Q15 | 根层 CLAUDE.md — 操作日志双写原则 |
| Q16 | 根层 CLAUDE.md — AI操作记录规范（30天生命周期） |
| Q17 | 根层 CLAUDE.md — 防幻觉约束（每个论断溯源） |
