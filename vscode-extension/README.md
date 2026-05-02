# BeingBijMantra: VS Code-First Contained Autonomy

This extension serves as the primary **IDE-Native Developer Control Plane** for the BijMantra project. It shifts the center of gravity for automated code-writing away from headless daemons and directly into your local Visual Studio Code environment, ensuring all AI-generated modifications remain visible, auditable, and easily reversible.

## Core Architecture

This extension sits in the middle of a hybrid autonomy model:
*   **The Developer Master Board (Python Control Plane)** remains the single authoritative source of truth for planning and mission intent.
*   **BeingBijMantra (This Extension)** interprets the Master Board, securely reads the workspace, and utilizes the local Copilot LLM to reason and execute actions.
*   **The Python Watchdog (OpenClaw)** is strictly demoted to supervising running processes and enforcing security policies. It explicitly yields full authority back to you whenever this extension is active.

## Features

1.  **Copilot-Native AI Brain**
    The extension natively links into your local `vscode.lm` (Language Model APIs), completely omitting the need to pipe sensitive repository code through third-party remote keys.

2.  **Dry-Run Workspace Safety**
    All AI edits proposed by the Pilot are routed through `WorkspaceTools`. No files are silently overwritten. Code modifications appear dynamically as unsaved buffers inside your editor, allowing you to easily review via the SCM tab or hit `Cmd+Z` inside the file.

3.  **Local Bridge Telemetry**
    The extension runs a continuous silent background loop maintaining a heartbeat at `.agent/state/ide-presence.json`. When the Python Watchdog detects this heartbeat, it permanently disables its headless autonomy logic and submits to your active editing session.

4.  **Integrated Notifications**
    Instead of burying errors in terminal logs, backend supervisors write payloads into `.agent/state/wakeup.json`. The extension native file-watcher intercepts these and raises immediate floating alert boxes right in your workspace.

5.  **Start Autonomous Pilot**
    You can trigger a bounded, human-governed "Continue-Until-Blocked" loop that automatically assesses active tasks, executes terminal checks (`pytest`/`bun`), refines code, and generates completion receipts.

## How to Compile & Run

### 1. Installation
This project natively utilizes `bun` for lightweight compilation instead of `npm`.
Ensure your workspace is rooted and navigate to the extension package:
```bash
cd vscode-extension
bun install
bun run compile
```

*(Alternatively, you can leave `bun run watch` running in a terminal tab to continuously rebuild when editing Typescript)*

### 2. Booting the Extension Sandbox
1. Open the project root `bijmantra.code-workspace` in VS Code.
2. Select the `vscode-extension/src/extension.ts` file or hit `F5`.
3. VS Code will pop out an **Extension Development Host**. This is your active pilot environment.

### 3. Usage Commands
Open the **Command Palette** (`Cmd+Shift+P` on Mac):

*   **`BijMantra: Pre-flight Copilot Connection`**
    Test the Native IDE LM linkage. The bridge will execute a quick sanity check and yield an unsaved test buffer if successful.

*   **`BijMantra: Start Autonomous Pilot`**
    Triggers the high-fidelity Copilot loop. The extension will read the canonical Master Board schema, look for an active autonomy-enabled lane, and automatically execute next actions natively in your editor.

*   **`BijMantra: Open Developer Board`**
    *In-Development*: Exposes the Control Plane webview panel tracking your active lanes and verification summaries.

## System Dependencies

To unlock the full potential of `BeingBijMantra`, ensure the backend suite is running:
1.  **FastAPI Control Plane**: The extension expects `http://localhost:8000/api/v2/developer-control-plane/active-board` to yield the canonical `.json` definitions for missions.
2.  **OpenClaw Watchdog**: `ops-private/claw-runtime/scripts/bijmantra_watchdog.py` must be running locally to consume the `.agent/state/ide-presence.json` telemetry.
