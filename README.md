# GEO SOP Skills

GEO（生成式引擎优化）工作流 skill 集合，用于 Claude Code。

## Skills

| Skill | 用途 |
|-------|------|
| `geo-intent-mining` | 意图词挖掘，生成询问句词库 |
| `geo` | GEO 多 agent 工作流主 skill |
| `kb-check` | 知识库质量审计（17 项检查） |
| `kb-create` | 知识库新建页面 |
| `kb-save` | 知识库写入前拦截器（30 项检查） |
| `kb-update` | 知识库智能融合 |

## 安装

将各 skill 目录复制到 `~/.claude/skills/` 下即可。

## 自包含

所有 skill 不依赖本地 Obsidian 知识库或外部 SOP 文档，可在任意机器上使用。
