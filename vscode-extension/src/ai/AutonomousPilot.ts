import * as vscode from 'vscode';
import * as http from 'http';
import { CopilotAdapter } from '../adapter/CopilotAdapter';
import { WorkspaceTools } from '../adapter/WorkspaceTools';

export class AutonomousPilot {
    public static async startMission() {
        vscode.window.showInformationMessage("Starting High-Fidelity Autonomous Pilot Loop...");

        let boardData: any;
        try {
            const data = await AutonomousPilot.fetchActiveBoard();
            if (!data.exists || !data.record) {
                vscode.window.showErrorMessage("No active Canonical Board found on backend.");
                return;
            }
            boardData = JSON.parse(data.record.canonical_board_json);
        } catch (e: any) {
            vscode.window.showErrorMessage(`Control Plane Unreachable. Is FastAPI running? ${e.message}`);
            return;
        }

        if (!boardData.autonomy_contract || !boardData.autonomy_contract.enabled) {
            vscode.window.showWarningMessage("Autonomous Pilot is explicitly disabled in the Master Board.");
            return;
        }

        const activeLanes = boardData.lanes?.filter((l: any) => l.status === "active") || [];
        if (activeLanes.length === 0) {
            vscode.window.showInformationMessage("No active lanes found for Pilot execution.");
            return;
        }

        const targetLane = activeLanes[0];
        const stopConditions = boardData.autonomy_contract.stop_conditions || [];

        let previousVerification = "";
        try {
            if (vscode.workspace.workspaceFolders && vscode.workspace.workspaceFolders.length > 0) {
                const rootUri = vscode.workspace.workspaceFolders[0].uri;
                const logUri = vscode.Uri.joinPath(rootUri, '.agent/state/latest_verification.log');
                const logData = await vscode.workspace.fs.readFile(logUri);
                previousVerification = `\nLast Verification Iteration Results:\n${new TextDecoder().decode(logData)}\n`;
            }
        } catch(e) {
            // File might not exist on first loop
        }

        const prompt = `You are BeingBijMantra, executing a bounded autonomy loop.
Objective: ${targetLane.objective}
Stop Conditions: ${stopConditions.join(', ')}
${previousVerification}
Please examine the workspace context provided. What is the single immediate next action required?
Your response MUST be precisely formatted as a raw JSON string containing exactly one action object, with NO MARKDOWN BLOCKS and NO EXPLANATION TEXT.
Valid actions:
1. {"action": "edit", "path": "path/relative/to/root.ts", "content": "full replacement content"}
2. {"action": "verify", "command": "npm run test:run"}
3. {"action": "stop", "reason": "blocker description"}
4. {"action": "complete", "message": "completed the lane goal"}
`;
        
        vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "BeingBijMantra Pilot Copilot Analysis",
            cancellable: false
        }, async (progress) => {
            progress.report({ message: "Consulting LM..." });
            try {
                const responseText = await CopilotAdapter.runDryRunPlan(prompt);
                await AutonomousPilot.handleResponse(responseText, targetLane.id);
            } catch (e: any) {
                vscode.window.showErrorMessage(`Pilot execution failed: ${e.message}`);
            }
        });
    }

    private static fetchActiveBoard(): Promise<any> {
        return new Promise((resolve, reject) => {
            http.get('http://localhost:8000/api/v2/developer-control-plane/active-board', (res) => {
                let data = '';
                res.on('data', chunk => { data += chunk; });
                res.on('end', () => {
                    if (res.statusCode === 200) {
                        try { resolve(JSON.parse(data)); } catch (e) { reject(e); }
                    } else {
                        reject(new Error(`Failed with status ${res.statusCode}`));
                    }
                });
            }).on('error', reject);
        });
    }

    private static async handleResponse(responseText: string, laneId: string) {
        const cleanJSON = responseText.replace(/```json/g, '').replace(/```/g, '').trim();
        let payload: any;
        try {
            payload = JSON.parse(cleanJSON);
        } catch (e) {
            console.error("Malformed JSON from LM:", responseText);
            vscode.window.showErrorMessage("Received malformed execution JSON from LM. Halting.");
            return;
        }

        switch (payload.action) {
            case "edit":
                vscode.window.showInformationMessage(`Pilot proposes an edit to: ${payload.path}. Processing dry-run.`);
                await WorkspaceTools.applyWorkspaceEditDryRun(payload.path, payload.content);
                // Pause and trigger next slice implicitly
                setTimeout(() => AutonomousPilot.startMission(), 3000);
                break;
            case "verify":
                vscode.window.showInformationMessage(`Pilot executing verification: ${payload.command}`);
                const result = await WorkspaceTools.runVerification(payload.command);
                if (vscode.workspace.workspaceFolders) {
                    const logUri = vscode.Uri.joinPath(vscode.workspace.workspaceFolders[0].uri, '.agent/state/latest_verification.log');
                    await vscode.workspace.fs.writeFile(logUri, new TextEncoder().encode(`COMMAND: ${payload.command}\n\nRESULT:\n${result}`));
                }
                vscode.window.showInformationMessage(`Verification complete. Triggering next slice.`);
                setTimeout(() => AutonomousPilot.startMission(), 3000);
                break;
            case "stop":
                vscode.window.showWarningMessage(`Pilot triggered stop condition: ${payload.reason}`);
                break;
            case "complete":
                vscode.window.showInformationMessage(`Pilot completed lane. Writing closeout receipt.`);
                await AutonomousPilot.writeCloseoutReceipt(laneId, payload.message);
                
                // Multi-Lane Recursion: Wait and poll for next active lane
                vscode.window.showInformationMessage(`Checking for next active lane...`);
                setTimeout(() => AutonomousPilot.startMission(), 5000);
                break;
            default:
                vscode.window.showErrorMessage(`Unknown action requested by LM: ${payload.action}`);
        }
    }

    private static async writeCloseoutReceipt(laneId: string, summary: string) {
        if (!vscode.workspace.workspaceFolders || vscode.workspace.workspaceFolders.length === 0) {
            return;
        }
        const rootUri = vscode.workspace.workspaceFolders[0].uri;
        const receiptUri = vscode.Uri.joinPath(rootUri, `.agent/state/closeout-receipts/lane_${laneId}_receipt.json`);
        
        const payload = {
            lane_id: laneId,
            status: "verifiable-complete",
            summary: summary,
            completed_at: new Date().toISOString()
        };

        try {
            await vscode.workspace.fs.writeFile(receiptUri, new TextEncoder().encode(JSON.stringify(payload, null, 2)));
        } catch(e) {
            console.error("Failed to write closeout receipt", e);
        }
    }
}
