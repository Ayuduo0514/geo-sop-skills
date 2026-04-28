# Sample Violation Case for kb-qa Testing

## Setup

A vault with these intentional violations:

1. **Q1 violation**: `知识库/草稿.md` (orphan file not in any subdirectory)
2. **Q3 violation**: `[[概念/不存在的概念]]` in a SOP file
3. **Q6 violation**: New source `原始资料/新文章.md` ingested but not referenced in any SOP
4. **Q7 violation**: Concept page missing `最后更新:` frontmatter
5. **Q14 violation**: Source `原始资料/白皮书.md` has `适用概念: [[概念/GEO定义]]` but `概念/GEO定义.md` last updated date is 2026-01-01 (before ingest)
6. **Q15 violation**: Structural change made (new SOP created) but no AI operation record file exists
7. **Q16 violation**: `AI操作记录/2026-01-01-old.md` is 100 days old
8. **Q17 violation**: SOP references `来源[L2]：原始资料/已删除报告.md` which no longer exists

## Expected kb-qa Output

All 8 violations should be flagged in the audit report.
