## 🚨 Never Upload Secrets

- Do not store API keys or `.env` in repo.
- Use `.env.example` with placeholders.
- If a secret is leaked: rotate credentials, purge history, notify team.

## 🔄 Kiro-Lite Workflow Rules

- **Always follow the phase sequence:** PRD → Design → Tasks → Code
- **Never skip phases** or generate code before PHASE 3
- **Wait for explicit slash commands** before proceeding
- **Implement one task at a time** with full diffs and tests
- **Review and pause** after each implementation

## 🐍 Python Development Standards

- Use type hints for all function parameters and returns
- Follow PEP 8 style guidelines
- Include comprehensive error handling
- Write unit tests for all core functionality
- Use dataclasses for configuration models
- Keep modules focused and loosely coupled

## 🖱️ Automation Ethics

- **User consent required** for all screen automation
- **Provide cancellation mechanisms** (delays, popups)
- **Log all automated actions** for transparency
- **Respect application terms of service**
- **Test thoroughly** to avoid unintended clicks
