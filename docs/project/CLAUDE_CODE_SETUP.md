# Claude Code Setup for the Swiss SIA / IESVE Project

## Purpose

This guide prepares Claude Code for safe, repeatable work on the Swiss SIA compliance checker and programmatic VE reference model. Repository configuration is committed under `CLAUDE.md` and `.claude/`; authentication, proxy values and personal permissions must remain outside Git.

## App-only path without administrator rights

Claude Desktop includes the Claude Code engine. A user who cannot install the CLI must use the **Code** tab, not the general **Chat** tab. No Node.js, WinGet package or terminal-level Claude installation is required for this path.

1. Open the company-provided Claude Desktop application and sign in with the approved IES account.
2. Select **Code** at the top of the application.
3. Select **Local** as the environment.
4. Choose the repository folder `C:\Users\ulysse.couliou\Documents\IES Internship\IES-Intership-general-repo`.
5. Keep the permission mode on **Manual** for normal implementation, or **Plan** for analysis without edits.
6. Review and accept the workspace trust prompt only after confirming the selected folder and project configuration.
7. Start a new session and ask Claude to read `CLAUDE.md`, `.claude/settings.json`, the relevant rules, and the available skill/agent definitions before doing work.

In the Code tab, type `/` in the prompt or use **+ -> Slash commands** to browse custom skills. Terminal-only configuration panels are not required. The project files are shared with Desktop automatically, so their effective content can also be verified by asking Claude to list the loaded instructions, skills, agents and permission rules with file paths.

Recommended first prompt:

```text
Work in Plan mode and do not edit files. Read CLAUDE.md and the project files
under .claude/. Confirm the repository root, summarize the non-negotiable SIA
and IESVE guardrails, list the five project skills and three project agents,
and report any configuration file that you could not load.
```

Recommended second prompt:

```text
Still without editing, inspect git status and run the existing read-only test
and release checks permitted by .claude/settings.json. Report exact commands,
exit codes, counts and environment limitations. Do not install anything.
```

If the application has only **Chat** and **Cowork**, if **Code** requests an upgrade, or if **Local** is disabled, the IES administrator must enable the Code entitlement or local-code policy. Do not work around that restriction by uploading the repository to Chat or a remote session.

## 1. Obtain IES approval before installation

Confirm the following with the IES Claude Code administrator or IT/security owner:

- the approved authentication route: IES Team/Enterprise SSO, an IES-managed gateway, Bedrock, Vertex AI, Microsoft Foundry, or another managed provider;
- whether this repository, customer VE models, generated reports, manager files and licensed SIA documents may be processed by that route;
- retention, training, regional processing, audit logging and incident-response policy;
- whether native Windows or WSL 2 is the supported execution environment;
- proxy, custom CA certificate and outbound-domain requirements;
- allowed Claude models and release/update channel;
- whether project skills, subagents, hooks, plugins and MCP servers are permitted;
- which external systems, if any, may be connected.

Do not create a personal API key, paste a token into a settings file, or install an unapproved MCP/plugin to bypass the enterprise route.

## 2. Recommended Windows installation

This repository uses Windows paths and IESVE is a Windows application. Native Windows Claude Code is therefore the default recommendation. Git for Windows is already suitable for its Bash tool. WSL 2 is useful only if IES policy requires command sandboxing; real IESVE/VEScripts execution still occurs in Windows.

Use the IES software portal or managed installer when one exists. If IT explicitly authorizes the public stable package, one documented option is:

```powershell
winget install Anthropic.ClaudeCode
```

Alternatively, follow the IES-provided native installer or gateway instructions. Do not run an internet-delivered install script without approval.

Verify the installation:

```powershell
claude --version
claude doctor
```

Start `claude` once and complete the company authentication flow. Do not select a personal account when the work must remain under the IES enterprise controls.

## 3. Open the correct repository root

Always start Claude Code from:

```powershell
cd "C:\Users\ulysse.couliou\Documents\IES Internship\IES-Intership-general-repo"
claude
```

Starting from the repository root is required so Claude discovers the shared `CLAUDE.md`, `.claude/settings.json`, rules, skills and subagents.

At the first launch, review the workspace trust prompt before accepting it. Then run:

```text
/memory
/permissions
/skills
/agents
/status
```

Expected project components:

- root memory: `CLAUDE.md`;
- shared settings: `.claude/settings.json`;
- conditional rules: `.claude/rules/`;
- five project skills: `/sia-compliance-change`, `/iesve-api-change`, `/reference-model`, `/release-check`, `/sia4010-evidence`;
- three subagents: `sia-traceability-auditor`, `iesve-api-reviewer`, `release-runner`.

If the new `skills` or `agents` directories were created while Claude was already running, restart the session once.

## 4. Local machine settings

Copy `.claude/settings.local.example.json` to `.claude/settings.local.json` only if Claude cannot locate Git Bash:

```powershell
Copy-Item .claude/settings.local.example.json .claude/settings.local.json
```

Adjust the Git Bash path only when the installed location differs. The local settings file is ignored by Git. Never store tokens, passwords or proxy credentials in it.

Proxy and certificate variables must be provisioned through the approved IES mechanism. Ask IT for the exact values; do not guess them or commit them.

## 5. Python development environment

The repository has no need for Node.js after a native Claude Code installation. Use the Python environment already approved for this project.

The release validator requires:

```powershell
python -m pip install -r scripts/quality/requirements.txt
```

Only run installation after approval. The `iesve` module cannot be installed from PyPI and is expected to exist only inside the IESVE VEScripts runtime.

Baseline verification:

```powershell
python -m unittest discover -s tests -p "test_*.py"
python scripts/quality/validate_release.py
git diff --check
```

## 6. Daily operating workflow

Start each cohesive task in a new Claude session and give it a concrete outcome. Useful prompts:

```text
Read CLAUDE.md and inspect the current git status. Diagnose this failure without editing yet: <failure>.
```

```text
/reference-model Implement <change>. Preserve all placeholders and source traceability, add tests, and stop before any real VE mutation.
```

```text
/sia-compliance-change Review <requirement> against the approved local source and identify what is automated, partial, reviewer-dependent, or not checkable.
```

```text
Use the iesve-api-reviewer agent to review the current diff. Do not edit files.
```

```text
Use the sia-traceability-auditor agent to inspect changed compliance logic and return line-specific findings.
```

```text
/release-check
```

Use Plan Mode for large or uncertain work. Ask Claude to diagnose before implementing when the cause is unknown. Keep one session focused on one deliverable to reduce context contamination.

## 7. Real IESVE qualification

Claude Code can edit and test the pure-Python repository, but it does not turn local API doubles into real IESVE evidence. For VE integration changes:

1. run focused pure-Python tests;
2. run the reference-model dry run;
3. inspect the generated report and audit output;
4. open a disposable, saved blank project in the target IESVE release;
5. run the VEScript launcher manually from the VE Scripts editor;
6. preserve the console output, report and VE version as qualification evidence;
7. discard a project that failed after partial mutation unless rollback has been proven;
8. have the responsible IESVE/API and Swiss compliance reviewers approve the result.

## 8. Plugins, MCP and hooks

Do not install plugins or MCP servers by default. They expand the data and action boundary and require an IES security review. Add one only when it has a specific product need, a named owner, least-privilege permissions and an approved data-flow record.

No project hook is enabled initially. Hooks execute deterministically and can run commands whenever files or tools change; enabling them before the Windows/enterprise environment is qualified would create unnecessary risk. Add only reviewed, cross-platform hooks after the baseline setup is stable.

## 9. Team governance

- Commit `CLAUDE.md`, `.claude/settings.json`, rules, skills and agents so the team shares the same behavior.
- Keep `.claude/settings.local.json`, credentials and personal preferences uncommitted.
- Review AI-generated changes exactly like human changes; require a human owner for compliance interpretation.
- Never let Claude merge, push, publish reports or assert certification autonomously.
- Re-run `claude doctor` after upgrades and revalidate skills/agents after material Claude Code releases.
- Reassess the setup when the target IESVE version, Python runtime, SIA edition or official SIA 4010 files change.

## Acceptance checklist

- Company authentication and data policy confirmed.
- `claude --version` and `claude doctor` succeed.
- Workspace trust accepted after reviewing project configuration.
- `/memory`, `/permissions`, `/skills` and `/agents` show the expected project files.
- Full Python tests pass.
- Release validator passes or only documents accepted optional evidence warnings.
- No secrets are visible to Claude or stored in Git.
- A disposable real-VE smoke test is completed before relying on generated VE objects.
