# openclaw / RULES

1. 根层文件只保留稳定、通用、长期有效的信息。
2. 项目差异通过 `projects/*` 扩展，而不是写入 root 层。
3. 默认不放开 OpenClaw 对根层文件的自由改写权限。
4. 先让 Codex 部署，再让 OpenClaw 在既定骨架中运行。
5. 每次新增项目时，沿用 `PROJECT.md`、`PROFILE.md`、`RULES.md` 三件套。
