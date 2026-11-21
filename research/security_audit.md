# Security Audit — Workspace and Downloaded Data

**Date:** 21 November 2026
**Scope:** workspace code, downloaded telemetry data, installed dependencies, PDF active content, persistence checks.
**Method:** static inspection, hash verification, `pip check`, PyPI provenance, Windows Defender custom scan.
**Limit:** not a reverse-engineering audit of every wheel; no formal CVE audit.

## 1. Downloaded GitHub data

- Source: `TracingInsights-Archive/2025`, Apache-2.0.
- Only JSON files were downloaded: telemetry laps and laptimes. No repository Python file was executed or saved.
- SHA-256 hashes match `datasets/telemetry/manifest.json`.
- JSON contains only numeric telemetry channels plus `dataKey`. No URLs, scripts, base64, or commands.
- Repository scripts (`tel.py`, `utils.py`) were inspected via raw text only. They use FastF1/MultiViewer and write JSON; no `eval`, `exec`, `subprocess`, obfuscation, or exfiltration.

## 2. Workspace code

- No `eval`, `exec`, dynamic `compile`, `subprocess`, `os.system`, registry, scheduled task, or startup persistence in application code.
- No scheduled tasks or startup entries reference the workspace.
- No listeners on ports 8000/8501/8502/9222 after testing.
- File writes in `app/`, `scripts/`, and `tests/` target the workspace (`storage/`, `datasets/`, `knowledge_base/`, `research/`).
- No secrets in logs; `.env` is absent and gitignored.
- Git is local, no remote, no non-sample hooks.

## 3. Dependencies

- All packages installed from PyPI; no `direct_url.json` entries.
- `pip check`: no broken requirements.
- `httpx2` / `httpcore2` are genuine Pydantic packages required by `huggingface_hub` 2.4.0; installed before this session.
- `fastf1==3.9.2` installed from a wheel; it downgraded pandas to 2.3.3. This is a dependency change, not a security incident.
- No `.pth` injection, `sitecustomize.py`, or `usercustomize.py`.

## 4. PDF active content

- `2024.konvens-main.6.pdf`: `OpenAction` is `/GoTo` page navigation.
- Backward-chaining journal: `EmbeddedFiles` contains `folder.joboptions`, an Adobe Distiller configuration stream; no executable and `embfile_count=0`.
- FIA `/JS` marker in one PDF is a compressed-byte false positive; no JavaScript action objects were found.
- No PDF contains an embedded executable.

## 5. Windows Defender

- Real-time protection enabled; signatures updated.
- Custom scan of the workspace completed with exit 0.
- `Get-MpThreatDetection`: no detections.

## 6. Residual risks and mitigations

| Risk | Status |
|---|---|
| `joblib.load` unsafe deserialization | **Mitigated**: SHA-256 sidecar checked before load; mismatch forces rebuild. |
| CORS wildcard | **Mitigated**: explicit `CORS_ORIGINS` allowlist. |
| Oversized requests | **Mitigated**: `MAX_REQUEST_BYTES` returns 413; API fields have max lengths. |
| API without auth | **Open**: local prototype; do not expose publicly without auth/reverse proxy. |
| LLM data egress / prompt injection | **Not active**: no provider. Server-side facts, claim citations, and evidence delimiters are in place; semantic audit still pending. |
| Docker image drift | **Mitigated**: `qdrant/qdrant:v1.20.2` pinned by tag, not digest. |
| Pip hash pinning | **Open**: versions pinned, hashes not enforced. |
| `.agent_harnesses.json` | Pre-existing data catalog of agent env var names; not executed, no token values. Remove if not needed. |
| Pip cache outside workspace | Pre-existing, not modified in this session; set `PIP_CACHE_DIR` inside workspace for strict isolation. |

## 7. Conclusion

No virus, malware, backdoor, or system-escalation mechanism was found in the downloaded data, workspace code, or installed dependencies. The remaining items are prototype security weaknesses and supply-chain hygiene items, not active malware.
