# Active Context

_Current focus, decisions, and work in progress._

## Current Project: Autoclicker for VS Code Copilot Chat

**Goal:** Create a Python-based autoclicker that monitors screen positions for specific visual cues (color, text) and automatically clicks when conditions are met. This is intended to automate the "Continue" button in VS Code Copilot Chat.

**Current Phase:** PHASE 3 - Code Generation
**Active Feature:** `/memory-bank/autoclicker/`

## Recent Decisions
- **Tech Stack:** Python with Tkinter UI, PyAutoGUI for automation, OpenCV for detection
- **Architecture:** Modular design with separate UI, detection, and clicking components
- **Platform Focus:** macOS primary, cross-platform design where possible

## Work in Progress
- **Completed:** AC-1 (UI), AC-2 (Screen Monitoring & Detection Engine), AC-3 (Delay/Popup & User Intervention), AC-4 (Mouse Click Simulation), AC-5 (Logging & Error Handling)
- **Status:** All acceptance criteria complete! 🎉

## Current Context
Working through systematic task breakdown using Kiro-Lite workflow. Each task is implemented individually with diffs, tests, and review cycles.