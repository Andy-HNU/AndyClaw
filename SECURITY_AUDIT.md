# SECURITY_AUDIT.md

Audit target: `https://github.com/affaan-m/everything-claude-code`

- Clone location (isolated temp): `/tmp/ecc-faWR/repo`
- Audited commit: `da4db99c94cf272d3341910bc8c8a26d2e6e6960`
- Audit date: 2026-03-12 (Asia/Shanghai)

## Tool availability

- `gitleaks`: unavailable
- `trufflehog`: unavailable
- `ripgrep (rg)`: unavailable
- `npm`: available
- `pip-audit`: unavailable
- `osv-scanner`: unavailable

## Methods used

1. **Secret scan**: grep-based fallback across repo (excluding binaries/.git)
2. **Dangerous pattern scan**: grep-based rules for `curl|bash`, reverse shell indicators, `eval`, `os.system`, shell-enabled subprocess and JS exec patterns
3. **Dependency audit**: `npm audit --omit=dev --json`

Artifacts kept during run:
- `/tmp/ecc-faWR/out/secret_scan.txt`
- `/tmp/ecc-faWR/out/danger_scan.txt`
- `/tmp/ecc-faWR/out/npm_audit.json`

## Findings summary

### A) Secrets
- Multiple matches were found, but all inspected hits were **documentation/test examples** (e.g., `sk-abc123`, `ghp_xxxxx`, `API_KEY` placeholders), not live credentials.
- No confirmed production secrets found in upstream snapshot.

### B) Dangerous behavior patterns
Detected matches were mostly educational text or scanner definitions:
- `skills/autonomous-loops/SKILL.md` and localized docs include `curl ... | bash` examples.
- `.opencode/tools/security-audit.ts` contains `eval(` as a detection pattern.
- `docs/ja-JP/agents/python-reviewer.md` contains `os.system(f"curl {url}")` as example content.

**Assessment:** No immediate malicious payload discovered, but some modules include risky operational guidance if adopted blindly.

### C) Dependency vulnerabilities
`npm audit --omit=dev` returned:
- `high: 0`, `critical: 0`, total vulnerabilities: `0`

## Verdict per module (top-level)

| Module | Verdict | Notes |
|---|---|---|
| `rules/` | LOW | Static markdown guidance; safe to reuse selectively. |
| `agents/` | MEDIUM | Prompt/agent behavior content; useful but requires adaptation to local policy. |
| `skills/` | MEDIUM | Large set; some skills include risky instructions (`curl|bash` examples). |
| `scripts/` | MEDIUM | Executable scripts; not integrated without deeper review. |
| `commands/` | MEDIUM | Automation behaviors vary; not integrated in this pass. |
| `.opencode/` | MEDIUM | Tooling internals; contains scanning logic but no direct malicious code identified. |
| `docs/` | LOW-MEDIUM | Mostly docs; includes risky examples for teaching. |
| `install.sh` | MEDIUM | Installer script with filesystem writes; no malicious behavior seen, but not imported. |

## High-risk gating outcome

No confirmed malicious high-risk payloads were identified. However, modules containing risky execution guidance were **not integrated** in this pass (security-first filtering).
## Phase-2 targeted re-audit (docs/rules/templates only)

- Re-audit date: 2026-03-12 (Asia/Shanghai)
- Re-audit clone: `/tmp/ecc-phase2-h23S/repo`
- Commit verified: `da4db99c94cf272d3341910bc8c8a26d2e6e6960`
- Candidate set (selected before import):
  - `rules/README.md`
  - `rules/common/coding-style.md`
  - `rules/common/development-workflow.md`
  - `rules/common/git-workflow.md`
  - `rules/common/patterns.md`
  - `rules/common/testing.md`

### Phase-2 scan method

Focused grep scan over selected candidates for high-risk indicators:
- remote piping: `curl|bash`, `wget|bash`
- command execution patterns: `eval(`, `os.system(`, shell-enabled subprocess, JS exec/spawn
- autonomous loop indicators: `while(true)`, `for(;;)`, `autonomous`

Artifact:
- `/tmp/ecc-phase2-h23S/out/phase2-danger-scan.txt`

### Phase-2 results

- **No dangerous-pattern hits** in selected phase-2 candidates.
- Imported set remains markdown-only, no executable files.
- Explicitly excluded from this phase: `install.sh`, `scripts/`, `hooks.md`, autonomous-loop related content, and any module containing remote script piping guidance.

### Phase-2 gate decision

✅ Approved for import under `skills/external/ecc/phase2/` as documentation-only references.
