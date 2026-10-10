# Ubuntu SMS Client Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task-by-task in the current session.

**Goal:** Build the Ubuntu Python SMS viewer approved by the user.

**Architecture:** Separate configuration and text processing, asynchronous Qt networking, and native desktop UI. Consume the existing PHP list endpoint without server changes.

**Tech Stack:** Python 3.10+, PySide6, unittest.

**Spec:** `docs/superpowers/specs/2026-10-10-sms-client-design.md`

## Global Constraints

- Write application files only in `/home/liyuxi/Dev/Ubuntu`.
- Use GET list only; no deletion functionality.
- Refresh every 10 seconds; 50 messages per page; newest first.
- Store Token in a file with mode 0600 and send via request headers.
- Preserve loaded SMS on refresh failure; use Chinese UI.

## Review Focus

- Servers hosted in a subdirectory must retain that path.
- Untrusted SMS text must not inject HTML or executable links.
- Corrupt config and malformed server responses must produce recoverable errors.
- Changing settings during a request must discard the stale response.
- Repeated refreshes must preserve the user's historical page and scroll position.

### Task 1: Configuration and message processing

Files: `sms_client/core.py`, `tests/test_core.py`.

Interfaces: `Settings(server_url, token)`, `ConfigStore(path).load()/save(settings)`, `api_url(address)`, `extract_code(content)`, `content_html(content)`, `parse_records(payload)`.

- [x] Write tests for subdirectory URLs, invalid URLs, permission-restricted config round trip, corrupt config, code extraction, safe links/HTML and latest-first API parsing.
- [x] Run `python3 -m unittest discover -s tests -v` and confirm missing implementation fails.
- [x] Implement the interfaces and run the full suite until passing.

### Task 2: Async API and desktop flow

Files: `sms_client/network.py`, `sms_client/ui.py`, `sms_client/__main__.py`, `tests/test_app.py`.

Interfaces: `SmsApi.fetch(settings)`, success/failure signals, `SmsApi.cancel()`, `SettingsDialog`, `MessageCard`, `MainWindow`.

- [x] Add tests using a real local HTTP fixture for header authentication, URL/action, sorted results, invalid Token, malformed JSON, redirects, cancellation and recovery.
- [x] Add offscreen GUI checks for first-run settings persistence, latest-first display, clipboard copying, safe hyperlink dispatch, pagination, preserving old content on errors and page preservation.
- [x] Run tests and confirm the new components are absent.
- [x] Implement async fetch with timeout and stale-response cancellation; implement dialog, bubbles, navigation, automatic/manual refresh and status handling.
- [x] Run `QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s tests -v`.

### Task 3: Runnable delivery

Files: `run.sh`, `requirements.txt`, `install-desktop.sh`, `README.md`, `.gitignore`.

- [x] Provide executable launch script, optional desktop-entry installer and Chinese Ubuntu installation instructions.
- [x] Verify shell syntax, compile Python and run full tests.
- [x] Generate a GUI preview with fixture messages and inspect rendering.
- [x] Report exact launch command and the limitation that a real server connection requires the user's address/Token.

## Verification result

2026-10-10: 25 unittest cases passed using offscreen Qt and local HTTP fixtures. Python compilation, Bash syntax, version entrypoint, first-run startup smoke check, desktop-entry validation, and visual inspection passed. Independent review found no Critical/Important issues; its balanced-parentheses URL finding was fixed with a regression test. Long URL clipping and text-view wheel handling were also reproduced and fixed with regression tests. No real server credentials were available, so production-server connectivity remains a user configuration step.
