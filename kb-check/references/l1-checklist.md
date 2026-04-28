# L1 检查清单 — 自动扫描项

> **读取时机**：执行 L1 快速扫描时（快速模式 / pre-write gate / 变更范围涉及相关项时）。
> **执行方式**：工具可直接验证，不需要 Read 文件内容后判断。

---

## Q1. LLM Wiki 规范合规（P0 — 阻断级）

**检查方法**：
```bash
# 根层结构
ls D:/Projects/geo-knowledge-base/GEO/GEO理论/知识库/
# 应有的子目录：概念/ 实体/ 来源摘要/ 对比/ 综合/ AI操作记录/
# 应有的根文件：索引.md 日志.md
```

**通过标准**：
- [ ] 知识库/ 下无散落文件（所有 .md 必须进子目录，除索引.md 和 日志.md）
- [ ] AI 操作记录只出现在 `AI操作记录/` 目录
- [ ] 原始资料/ 下无知识库编译产物
- [ ] 综合/ 下无 AI 过程文件（plan、决策路径、验证记录等）

**自动修复**：无（结构性问题需人工决策）

---

## Q3. 死链检测（P0 — 阻断级）

**检查方法**：

方法一（Obsidian CLI，推荐）：
```bash
obsidian unresolved
```
返回所有不存在的 wikilink 引用。

方法二（手动对比）：
1. Glob 列出知识库/ 下所有实际存在的 `.md` 文件
2. Grep 提取所有知识库页面中的 `[[xxx]]` 链接
3. 对比：wikilink 引用的路径是否在 Glob 列表中

**跨平台命令**：
```bash
# Bash (Git Bash) — 提取所有 wikilink
grep -orh "\[\[.*\]\]" D:/Projects/geo-knowledge-base/GEO/GEO理论/知识库/ --include="*.md" | sed 's/\[\[//;s/\]\]//' | sort -u

# PowerShell — 提取所有 wikilink
Get-ChildItem -Path "D:/Projects/geo-knowledge-base/GEO/GEO理论/知识库/" -Filter "*.md" -Recurse | ForEach-Object { Select-String -Path $_.FullName -Pattern "\[\[([^\]]+)\]\]" -AllMatches | ForEach-Object { $_.Matches.Groups[1].Value } } | Sort-Object -Unique
```

**通过标准**：
- [ ] 知识库页面中的 `[[wikilink]]` 指向的文件实际存在
- [ ] 无红色链接（Obsidian 术语，即不存在的页面引用）
- [ ] 概念页/实体页/来源摘要页的链接有效

**自动修复**：✅ 支持（见 SKILL.md "自动修复"章节）

---

## Q7. Frontmatter schema（P1 — 严重级）

**检查方法**：
```bash
# 检查概念页 frontmatter
grep -A 5 "^---$" D:/Projects/geo-knowledge-base/GEO/GEO理论/知识库/概念/*.md
# 检查实体页 frontmatter
grep -A 5 "^---$" D:/Projects/geo-knowledge-base/GEO/GEO理论/知识库/实体/*.md
```

**通过标准**：
- [ ] 概念页有：`type: 概念`、`可信度来源:`、`最后更新:`
- [ ] 实体页有：`type: 实体`、`实体类型:`、`最后更新:`
- [ ] `最后更新:` 日期 ≥ 最近修改日期
- [ ] `可信度来源:` 不为空（至少一个来源）

**自动修复**：✅ 支持（见 SKILL.md "自动修复"章节）

---

## Q11. 原始资料只读检查（P0 — 阻断级）

**检查方法**：
```bash
# Bash (Git Bash) — 检查原始资料的修改时间
ls -lt D:/Projects/geo-knowledge-base/GEO/GEO理论/原始资料/

# PowerShell
Get-ChildItem -Path "D:/Projects/geo-knowledge-base/GEO/GEO理论/原始资料/" | Sort-Object LastWriteTime -Descending | Select-Object -First 10 Name, LastWriteTime
```

**通过标准**：
- [ ] 原始资料/ 下的文件在本次会话中未被修改
- [ ] 无知识库编译产物混入原始资料/
- [ ] ingest 时只追加回链，不改正文

**自动修复**：无（违反只读原则需人工处理）

---

## Q12. Wikilink 格式（P1 — 严重级）

**检查方法**：
```bash
# Bash (Git Bash)
grep -r "\[.*\](.*\.md)" D:/Projects/geo-knowledge-base/GEO/GEO理论/知识库/ --include="*.md"

# PowerShell
Get-ChildItem -Path "D:/Projects/geo-knowledge-base/GEO/GEO理论/知识库/" -Filter "*.md" -Recurse | Select-String -Pattern "\[.*\]\(.*\.md\)"
```

**通过标准**：
- [ ] 知识库内部链接全部使用 `[[xxx]]` 格式
- [ ] 无 `[文字](路径.md)` 格式的内部链接
- [ ] 外部 URL 可用标准 markdown 链接（这是例外）

**自动修复**：✅ 支持（见 SKILL.md "自动修复"章节）

---

## Q13. TODO 占位扫描（P1 — 严重级）

**检查方法**：
```bash
# Bash (Git Bash)
grep -r "\[TODO" D:/Projects/geo-knowledge-base/GEO/GEO理论/知识库/ --include="*.md"

# PowerShell
Get-ChildItem -Path "D:/Projects/geo-knowledge-base/GEO/GEO理论/知识库/" -Filter "*.md" -Recurse | Select-String -Pattern "\[TODO"
```

**通过标准**：
- [ ] 无 `[TODO: 说明]` 占位未处理（已完成的应删除，未完成的应处理或移至 AI操作记录/ 跟踪）
- [ ] 允许例外：AI操作记录/ 中的 TODO（属于进行中任务）

**自动修复**：✅ 支持（见 SKILL.md "自动修复"章节）

---

## Q16. 内容生命周期（P2 — 警告级）

**检查方法**：

**A. 过期文件检测**
```bash
# Bash (Git Bash)
find D:/Projects/geo-knowledge-base/GEO/GEO理论/知识库/AI操作记录/ -name "*.md" -mtime +30

# PowerShell
Get-ChildItem -Path "D:/Projects/geo-knowledge-base/GEO/GEO理论/知识库/AI操作记录/" -Filter "*.md" | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) }
```

**B. 孤立页面检测**

方法一（Obsidian CLI，推荐）：
```bash
obsidian orphans
```

方法二（手动对比）：
1. Glob 列出知识库/ 下所有 `.md` 文件
2. Grep 提取所有 `[[xxx]]` 链接中的被引用文件名
3. 从未出现在被引用列表中的文件 = 孤立页面

**C. 最后更新日期检查**
```bash
# Bash
grep -r "^最后更新:" D:/Projects/geo-knowledge-base/GEO/GEO理论/知识库/概念/
grep -r "^最后更新:" D:/Projects/geo-knowledge-base/GEO/GEO理论/知识库/实体/

# PowerShell
Get-ChildItem -Path "D:/Projects/geo-knowledge-base/GEO/GEO理论/知识库/概念/" -Filter "*.md" | ForEach-Object { $content = Get-Content $_.FullName -Raw; if ($content -match "最后更新:\s*(.+)") { "$($_.Name): $($matches[1])" } }
```

**通过标准**：
- [ ] `AI操作记录/` 中超过 30 天的文件已列清单，提醒用户清理
- [ ] 概念页/实体页 `最后更新:` 超过 90 天的，标记为"需复核"
- [ ] 无入链（在知识库中从未被 `[[xxx]]` 引用）的孤立页面已列清单
- [ ] 用户确认清理的，已执行删除并更新索引

**自动修复**：无（生命周期管理需人工决策）
