import * as vscode from 'vscode';
import { ControlPlanePanel } from './panel';
import { WorkspaceTools } from './adapter/WorkspaceTools';
import { CopilotAdapter } from './adapter/CopilotAdapter';
import { AutonomousPilot } from './ai/AutonomousPilot';
import { WakeupListener } from './ai/WakeupListener';
import { MissionDispatchListener } from './ai/MissionDispatchListener';

export function activate(context: vscode.ExtensionContext) {
    console.log('BeingBijMantra extension is now active');

    // --- IDE Presence Heartbeat ---
    if (vscode.workspace.workspaceFolders && vscode.workspace.workspaceFolders.length > 0) {
        const rootUri = vscode.workspace.workspaceFolders[0].uri;
        const presenceUri = vscode.Uri.joinPath(rootUri, '.agent/state/ide-presence.json');
        
        const updatePresence = async (isOpen: boolean) => {
            try {
                const payload = {
                    is_vscode_open: isOpen,
                    timestamp: new Date().toISOString()
                };
                await vscode.workspace.fs.writeFile(presenceUri, new TextEncoder().encode(JSON.stringify(payload, null, 2)));
            } catch (e) {
                console.error("Failed to write IDE presence heartbeat", e);
            }
        };

        // Initialize heartbeat as alive
        updatePresence(true);
        // Ping every 60 seconds
        const heartbeatInterval = setInterval(() => updatePresence(true), 60000);
        
        // Teardown
        context.subscriptions.push({
            dispose: () => {
                clearInterval(heartbeatInterval);
                updatePresence(false); // Graceful demotion upon editor close
            }
        });

        // --- IDE Bridge Wakeup Listener ---
        WakeupListener.activate(context);

        // --- Mission Dispatch Listener (OpenClaw → Copilot bridge) ---
        MissionDispatchListener.activate(context);
    }

    const disposableBoard = vscode.commands.registerCommand('beingbijmantra.openDeveloperBoard', () => {
        ControlPlanePanel.createOrShow();
    });

    const disposableTestCopilot = vscode.commands.registerCommand('beingbijmantra.testCopilot', async () => {
        vscode.window.showInformationMessage("Checking Copilot Availability...");
        try {
            const result = await CopilotAdapter.checkAvailability();
            if (!result.available) {
                vscode.window.showErrorMessage(`Copilot not available: ${result.reason}`);
                return;
            }
            vscode.window.showInformationMessage("Copilot is connected! Running a dry-run test payload...");
            
            // Hardcoded test objective
            const res = await CopilotAdapter.runDryRunPlan("State a cheerful 1-sentence hello world message.");
            
            await WorkspaceTools.applyWorkspaceEditDryRun('.agent/state/copilot-handshake-test.json', JSON.stringify({
                status: "success",
                handshakeData: res,
                timestamp: new Date().toISOString()
            }, null, 2));

        } catch (e: any) {
            vscode.window.showErrorMessage(`Copilot test failed: ${e.message}`);
        }
    });

    const disposableStartPilot = vscode.commands.registerCommand('beingbijmantra.startAutonomousPilot', () => {
        AutonomousPilot.startMission();
    });

    context.subscriptions.push(disposableBoard, disposableTestCopilot, disposableStartPilot);
}

export function deactivate() {}
