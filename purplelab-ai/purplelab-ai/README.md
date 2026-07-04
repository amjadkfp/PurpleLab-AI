# PurpleLab AI

**An educational Purple Team cybersecurity platform for authorized, isolated virtual lab environments.**

PurpleLab AI runs on your Kali Linux box and drives predefined, reviewed training
scenarios against an Ubuntu virtual machine over SSH — SSH authentication activity,
local user/group management, file permission changes, and scheduled task
persistence. It then collects the resulting logs, reconstructs a chronological
timeline, maps every action to **MITRE ATT&CK**, generates AI-assisted
explanations with detection and mitigation guidance, and renders an interactive
attack-flow graph — so you can see both the attacker's actions and the
defender's visibility into them, side by side.

It is built for **learning, portfolio projects, and interview prep** — not for
use against systems you don't own or control.

> ⚠️ **Scope & safety.** PurpleLab AI does **not** provide arbitrary remote
> command execution. Every command it can send over SSH is a fixed string
> defined in `backend/app/scenarios/definitions.py` and enforced by an
> allow-list in `backend/app/core/ssh_client.py`. The SSH client also refuses
> to connect to any host that isn't explicitly listed in `ALLOWED_LAB_HOSTS`.
> Only point this at a VM you own, on an isolated lab network.

---

## Table of contents

- [Feature overview](#feature-overview)
- [Architecture](#architecture)
- [Project structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Lab environment setup](#lab-environment-setup)
- [Installation](#installation)
- [Running the app](#running-the-app)
- [Using PurpleLab AI](#using-purplelab-ai)
- [Predefined scenarios](#predefined-scenarios)
- [Safety model](#safety-model)
- [Configuration reference](#configuration-reference)
- [Troubleshooting](#troubleshooting)
- [Roadmap ideas](#roadmap-ideas)

---

## Feature overview

| Module | What it does |
|---|---|
| **Scenario Manager** | Browse and launch predefined training scenarios; each shows its steps and MITRE mapping before you run it. |
| **Timeline Viewer** | Chronological reconstruction of a run, laid out on a central "duality spine" — attacker-simulated actions on one side, defender/log activity on the other. |
| **Interactive Attack Flow Graph** | React Flow graph of a run's execution chain: draggable, zoomable nodes colored by severity, edges labeled with MITRE tactics. |
| **AI Security Copilot** | Chat interface to ask questions about any event, technique, or run; falls back to rule-based answers if no AI API key is configured. |
| **MITRE ATT&CK Mapping** | Reference library of techniques used by the platform, with a heatmap of how often each has actually been observed in your runs. |
| **Log Viewer** | Raw, parsed log lines pulled from the Ubuntu VM (`auth.log`, `syslog`), filterable by run and source. |
| **Analytics Dashboard** | Chart.js visualizations: severity distribution, events by MITRE tactic, runs by scenario. |
| **HTML/PDF Report Generator** | Exports a run — timeline, MITRE mapping, AI analysis — as a shareable HTML or PDF report. |

---

## Architecture

```
┌───────────────────────────────── Kali Linux host ─────────────────────────────────┐
│                                                                                     │
│   ┌─────────────────────────────┐        ┌───────────────────────────────────┐     │
│   │        React Frontend       │  HTTP  │           FastAPI Backend         │     │
│   │  (Vite, Tailwind, React     │◄──────►│                                   │     │
│   │   Flow, Chart.js)           │  /api  │  routers/  scenarios, events,     │     │
│   │                              │        │            mitre, copilot,        │     │
│   │  Scenario Manager           │        │            reports, analytics     │     │
│   │  Timeline Viewer            │        │                                    │     │
│   │  Attack Flow Graph          │        │  core/                             │     │
│   │  AI Security Copilot        │        │   ssh_client.py    (Paramiko,      │     │
│   │  MITRE Mapping              │        │                     allow-listed)  │     │
│   │  Log Viewer                 │        │   scenario_engine.py (orchestrator)│     │
│   │  Analytics                  │        │   log_collector.py  (log parsing)  │     │
│   │  Report Generator           │        │   mitre_mapper.py   (ATT&CK data)  │     │
│   └─────────────────────────────┘        │   ai_copilot.py     (Anthropic API)│     │
│                                            │   report_generator.py (Jinja2/    │     │
│                                            │                        WeasyPrint)│     │
│                                            │                                    │     │
│                                            │  scenarios/definitions.py         │     │
│                                            │   (the ONLY source of SSH commands)│    │
│                                            │                                    │     │
│                                            │  SQLite (scenario_runs, events,   │     │
│                                            │          reports)                  │     │
│                                            └──────────────┬─────────────────────┘     │
│                                                            │ SSH (Paramiko)            │
└────────────────────────────────────────────────────────────┼────────────────────────────┘
                                                             │
                                                             ▼
                                         ┌───────────────────────────────────┐
                                         │      Ubuntu Lab VM (isolated)     │
                                         │  auth.log · syslog · cron · users │
                                         │  (host-only / NAT-only network)   │
                                         └───────────────────────────────────┘
```

**Data flow for a single scenario run:**

1. `POST /api/scenarios/run` → `core/scenario_engine.py` opens one guarded SSH
   session and executes each step's fixed command in order.
2. Each step's result becomes a **scenario-sourced Event**.
3. The scenario's declared log files (`auth.log`, `syslog`) are tailed and
   parsed by `core/log_collector.py` into **log-sourced Events**.
4. `core/mitre_mapper.py` attaches ATT&CK tactic/technique metadata to every
   event.
5. `core/ai_copilot.py` generates a plain-English explanation plus detection
   and mitigation guidance for every event (via the Anthropic API, or a
   deterministic rule-based fallback if no key is configured).
6. Everything is persisted to SQLite and immediately available to the
   Timeline, Attack Graph, Log Viewer, Analytics, and Report modules.

---

## Project structure

```
purplelab-ai/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app + router wiring
│   │   ├── config.py                # Typed settings (.env driven)
│   │   ├── database.py              # SQLAlchemy engine/session/Base
│   │   ├── models/                  # ORM models: scenario_run, event, report
│   │   ├── schemas/                 # Pydantic request/response contracts
│   │   ├── scenarios/
│   │   │   └── definitions.py       # ⭐ Single source of truth for every SSH command
│   │   ├── core/
│   │   │   ├── ssh_client.py        # Paramiko wrapper + allow-list guardrails
│   │   │   ├── scenario_engine.py   # Orchestrates a run end-to-end
│   │   │   ├── log_collector.py     # Fetches + parses remote logs
│   │   │   ├── mitre_mapper.py      # MITRE ATT&CK lookups
│   │   │   ├── ai_copilot.py        # AI explanations + chat (Anthropic API)
│   │   │   └── report_generator.py  # Jinja2 → HTML, WeasyPrint → PDF
│   │   ├── routers/                 # One module per dashboard feature
│   │   └── utils/logger.py
│   ├── mitre_data/attack_mappings.json
│   ├── reports/                     # Generated HTML/PDF reports land here
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── api/client.js            # Single fetch wrapper for the backend
│   │   ├── components/
│   │   │   ├── Layout/               # Sidebar, Topbar
│   │   │   └── common/               # SeverityPill, ActorPill, StatusBadge
│   │   ├── pages/                    # One page per dashboard module
│   │   └── styles/index.css
│   ├── tailwind.config.js
│   ├── vite.config.js
│   └── package.json
├── LICENSE
└── README.md
```

---

## Prerequisites

**Attacker/control host (this app runs here):**
- Kali Linux (or any Linux/macOS host with Python 3.11+ and Node 18+)
- Network access to your isolated lab VM

**Target lab VM:**
- Ubuntu 22.04+ (a clean VM snapshot is ideal)
- SSH server enabled (`sudo apt install openssh-server`)
- A dedicated lab user with **passwordless sudo** for the specific commands
  PurpleLab AI needs (see below) — do not use a personal or production account
- `sshpass` installed (`sudo apt install sshpass`) — used only for the
  loopback SSH-auth simulation in the `ssh_auth` scenario

Both machines should be on a network **isolated from production** — a
VirtualBox/VMware host-only or NAT network shared only between your Kali host
and the lab VM is ideal.

### Recommended `/etc/sudoers.d/purplelab` entry on the lab VM

Grant the lab account passwordless sudo for exactly the commands PurpleLab AI
uses (avoid blanket `NOPASSWD: ALL`):

```
labadmin ALL=(ALL) NOPASSWD: /usr/bin/tail, /usr/bin/journalctl, /usr/sbin/useradd, \
  /usr/sbin/userdel, /usr/sbin/usermod, /usr/sbin/groupadd, /usr/bin/chmod, \
  /usr/bin/chown, /usr/bin/crontab, /usr/bin/tee, /bin/rm, /usr/bin/cat
```

Validate with `visudo -c` after editing.

---

## Lab environment setup

1. Create/clone an Ubuntu VM on an isolated network (host-only/NAT).
2. `sudo apt update && sudo apt install -y openssh-server sshpass`
3. Create the lab account: `sudo useradd -m -s /bin/bash labadmin && sudo passwd labadmin`
4. Add the sudoers entry above (or, more simply for a throwaway lab VM, grant
   full NOPASSWD sudo — never do this outside an isolated lab).
5. Note the VM's IP address (`ip a`) — you'll put it in `.env` as `LAB_VM_HOST`.
6. **Take a VM snapshot** now, so you can always roll back to a clean baseline.

---

## Installation

### 1. Backend (FastAPI)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env: set LAB_VM_HOST, LAB_VM_USERNAME, LAB_VM_PASSWORD or
# LAB_VM_SSH_KEY_PATH, ALLOWED_LAB_HOSTS, and (optionally) ANTHROPIC_API_KEY
```

> **PDF export** requires WeasyPrint's system libraries:
> `sudo apt install -y libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libcairo2`
> (HTML export works with no extra system dependencies.)

### 2. Frontend (React + Vite)

```bash
cd frontend
npm install
```

---

## Running the app

**Terminal 1 — backend:**
```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 — frontend:**
```bash
cd frontend
npm run dev
```

Open **http://localhost:5173**. The Vite dev server proxies `/api/*` to the
backend on port 8000 (see `frontend/vite.config.js`).

---

## Using PurpleLab AI

1. **Scenario Manager** → pick a scenario (e.g. "Local User & Group
   Manipulation") → **Run Scenario**. PurpleLab AI opens one SSH session,
   executes each fixed step, and collects the resulting logs.
2. **Timeline Viewer** → select the run you just launched to see every event
   in order, with attacker-simulated steps on the left and
   defender/log-derived events on the right.
3. **Attack Flow Graph** → the same run as an interactive, draggable node
   graph — useful for presentations and portfolio screenshots.
4. **MITRE ATT&CK Mapping** → see which techniques were touched and how often.
5. **AI Security Copilot** → ask "why does this matter?" or "how would I
   detect this in a SIEM?" about any event, scoped to the run if you like.
6. **Report Generator** → export the run as an HTML or PDF write-up you can
   attach to a portfolio or interview take-home.

---

## Predefined scenarios

| Scenario | MITRE techniques | What it does |
|---|---|---|
| **SSH Authentication Activity** | T1110, T1078 | Generates failed loopback SSH attempts, then a successful login, and collects the resulting `auth.log` entries. |
| **Local User & Group Manipulation** | T1136.001, T1078.003 | Creates a lab group/user, escalates its group membership, verifies state, then **cleans up**. |
| **File Permission & Ownership Changes** | T1005, T1222.002 | Creates a mock file, loosens permissions, changes ownership, verifies state, then **cleans up**. |
| **Scheduled Task Persistence** | T1053.003 | Installs a benign cron heartbeat job, verifies it, then **cleans up**. |
| **Full Lab Environment Cleanup** | — | Idempotently removes every artifact the above scenarios might have left behind. |

All commands for every scenario live in one file:
`backend/app/scenarios/definitions.py`. There is no other code path that
builds an SSH command from user input.

---

## Safety model

- **No arbitrary command execution.** `core/ssh_client.py` exposes `run()`,
  which only accepts commands starting with a prefix in
  `ALLOWED_COMMAND_PREFIXES`. Every prefix maps to a specific, reviewed
  scenario step.
- **Host allow-list.** `connect()` raises `SSHHostNotAllowed` unless the
  target host is explicitly listed in `ALLOWED_LAB_HOSTS`.
- **Idempotent cleanup.** Every state-changing scenario ships a cleanup step,
  plus a standalone "Full Lab Environment Cleanup" scenario as a safety net.
- **Least-privilege sudo.** The setup guide above scopes the lab account's
  sudo rights to only the commands PurpleLab AI needs.
- **Use a disposable VM.** Snapshot before you start; revert whenever you
  want a clean baseline.

---

## Configuration reference

See `backend/.env.example` for the full list. Key variables:

| Variable | Purpose |
|---|---|
| `LAB_VM_HOST` / `LAB_VM_PORT` / `LAB_VM_USERNAME` | SSH target |
| `LAB_VM_PASSWORD` or `LAB_VM_SSH_KEY_PATH` | Auth method (use a key in real use) |
| `ALLOWED_LAB_HOSTS` | Hard allow-list; must include `LAB_VM_HOST` |
| `ANTHROPIC_API_KEY` / `ANTHROPIC_MODEL` | Enables AI-generated explanations & chat; omit to run fully offline with rule-based fallbacks |
| `DATABASE_URL` | SQLite path |
| `REPORTS_DIR` | Where generated HTML/PDF reports are written |
| `CORS_ORIGINS` | Frontend origin(s) allowed to call the API |

---

## Troubleshooting

- **"Refusing to connect: host not in ALLOWED_LAB_HOSTS"** — add your VM's IP
  to `ALLOWED_LAB_HOSTS` in `.env` (it must match `LAB_VM_HOST` exactly).
- **`sudo: a password is required`** — the lab account needs passwordless
  sudo (`NOPASSWD`) for the commands listed above; PurpleLab AI always calls
  `sudo -n` (non-interactive) and will fail fast if a password is required.
- **PDF generation fails** — install WeasyPrint's system libraries (see
  Installation) or just use the HTML report.
- **AI Copilot says "offline mode"** — set `ANTHROPIC_API_KEY` in `.env` and
  restart the backend; everything else still works without it.
- **`sshpass: command not found`** on the lab VM — `sudo apt install sshpass`
  (only needed for the SSH Authentication Activity scenario).

---

## Roadmap ideas

- WebSocket streaming of scenario progress instead of a synchronous request
- Multi-VM lab topologies (attacker + victim + detection stack)
- Sigma rule export from the Detection guidance field
- User-authored custom scenarios via a reviewed YAML schema (still no
  free-text command execution)

---

Built for learning. Always get explicit authorization before testing security
tooling against any system, and never point PurpleLab AI at infrastructure
you don't own or control.
