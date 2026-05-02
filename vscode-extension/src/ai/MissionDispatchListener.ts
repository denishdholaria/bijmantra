import * as vscode from 'vscode';
import { CopilotAdapter } from '../adapter/CopilotAdapter';
import { WorkspaceTools } from '../adapter/WorkspaceTools';

/**
 * MissionDispatchListener — watches .agent/state/mission-dispatch.json
 * 
 * When OpenClaw (the receptionist) dispatches a mission, this listener
 * picks it up and executes it through Copilot (the strong model).
 * Results are written back to .agent/state/mission-result.json for
 * the watchdog to consume.
 * 
 * Protocol:
 *   OpenClaw writes mission-dispatch.json (status: "dispatched")
 *   This listener reads it, marks it "in-progress", runs via Copilot
 *   On completion, writes mission-result.json and deletes the dispatch
 */
export class MissionDispatchListener {
    private static isExecuting = false;
    private static currentJobId: string | null = null;
    private static iterationCount = 0;
    private static maxIterations = 50; // Safety cap per mission

    public static activate(context: vscode.ExtensionContext) {
        if (!vscode.workspace.workspaceFolders || vscode.workspace.workspaceFolders.length === 0) {
            return;
        }

        const rootUri = vscode.workspace.workspaceFolders[0].uri;
        const pattern = new vscode.RelativePattern(rootUri, '.agent/state/mission-dispatch.json');
        const watcher = vscode.workspace.createFileSystemWatcher(pattern, false, false, false);

        const handleDispatch = async (uri: vscode.Uri) => {
            if (MissionDispatchListener.isExecuting) {
                console.log('[MissionBridge] Already executing a mission, ignoring new dispatch signal');
                return;
            }

            try {
                const raw = await vscode.workspace.fs.readFile(uri);
                const dispatch = JSON.parse(new TextDecoder().decode(raw));

                if (dispatch.status !== 'dispatched') {
                    return; // Already picked up or completed
                }

                // Mark as in-progress so the watchdog knows we picked it up
                dispatch.status = 'in-progress';
                dispatch.picked_up_at = new Date().toISOString();
                await vscode.workspace.fs.writeFile(uri, new TextEncoder().encode(JSON.stringify(dispatch, null, 2)));

                await MissionDispatchListener.executeMission(dispatch);
            } catch (e) {
                console.error('[MissionBridge] Failed to handle dispatch:', e);
            }
        };

        watcher.onDidCreate(handleDispatch);
        watcher.onDidChange(handleDispatch);
        context.subscriptions.push(watcher);

        // Check on boot for an existing dispatch
        const dispatchUri = vscode.Uri.joinPath(rootUri, '.agent/state/mission-dispatch.json');
        vscode.workspace.fs.stat(dispatchUri).then(() => handleDispatch(dispatchUri), () => {});
    }

    private static async executeMission(dispatch: any) {
        const jobId = dispatch.job_id || 'unknown';
        MissionDispatchListener.isExecuting = true;
        MissionDispatchListener.currentJobId = jobId;
        MissionDispatchListener.iterationCount = 0;

        vscode.window.showInformationMessage(`[Chloe → IDE] Mission received: ${dispatch.title || jobId}`);

        try {
            // Check Copilot availability first
            const availability = await CopilotAdapter.checkAvailability();
            if (!availability.available) {
                await MissionDispatchListener.writeResult(jobId, 'failed', `Copilot not available: ${availability.reason}`, []);
                return;
            }

            await MissionDispatchListener.runMissionLoop(dispatch);
        } catch (e: any) {
            await MissionDispatchListener.writeResult(jobId, 'failed', `Mission execution error: ${e.message}`, []);
        } finally {
            MissionDispatchListener.isExecuting = false;
            MissionDispatchListener.currentJobId = null;
            MissionDispatchListener.iterationCount = 0;

            // Clean up the dispatch file
            MissionDispatchListener.deleteDispatchFile();
        }
    }

    private static async runMissionLoop(dispatch: any) {
        const jobId = dispatch.job_id;
        const verificationResults: any[] = [];

        while (MissionDispatchListener.iterationCount < MissionDispatchListener.maxIterations) {
            MissionDispatchListener.iterationCount++;

            // Read previous verification log if it exists
            let previousVerification = "";
            try {
                if (vscode.workspace.workspaceFolders) {
                    const logUri = vscode.Uri.joinPath(
                        vscode.workspace.workspaceFolders[0].uri,
                        '.agent/state/latest_verification.log'
                    );
                    const logData = await vscode.workspace.fs.readFile(logUri);
                    previousVerification = `\nPrevious Verification:\n${new TextDecoder().decode(logData)}\n`;
                }
            } catch (e) {
                // No previous verification
            }

            const prompt = MissionDispatchListener.buildPrompt(dispatch, previousVerification);

            let responseText: string;
            try {
                responseText = await vscode.window.withProgress({
                    location: vscode.ProgressLocation.Notification,
                    title: `[Chloe Mission] ${dispatch.title || jobId}`,
                    cancellable: false
                }, async (progress) => {
                    progress.report({ message: `Iteration ${MissionDispatchListener.iterationCount} — consulting Copilot...` });
                    return await CopilotAdapter.runDryRunPlan(prompt);
                });
            } catch (e: any) {
                await MissionDispatchListener.writeResult(jobId, 'failed', `Copilot error on iteration ${MissionDispatchListener.iterationCount}: ${e.message}`, verificationResults);
                return;
            }

            // Parse the LM response
            const cleanJSON = responseText.replace(/```json/g, '').replace(/```/g, '').trim();
            let action: any;
            try {
                action = JSON.parse(cleanJSON);
            } catch (e) {
                console.error('[MissionBridge] Malformed JSON from Copilot:', responseText);
                // Give it one more chance
                if (MissionDispatchListener.iterationCount >= 3) {
                    await MissionDispatchListener.writeResult(jobId, 'failed', 'Repeated malformed JSON from Copilot', verificationResults);
                    return;
                }
                continue;
            }

            // Handle the action
            switch (action.action) {
                case 'edit':
                    vscode.window.showInformationMessage(`[Mission] Editing: ${action.path}`);
                    await WorkspaceTools.applyWorkspaceEditDryRun(action.path, action.content);
                    // Brief pause before next iteration
                    await MissionDispatchListener.sleep(2000);
                    break;

                case 'verify':
                    vscode.window.showInformationMessage(`[Mission] Verifying: ${action.command}`);
                    const result = await WorkspaceTools.runVerification(action.command);
                    verificationResults.push({
                        iteration: MissionDispatchListener.iterationCount,
                        command: action.command,
                        result: result,
                        timestamp: new Date().toISOString()
                    });

                    // Write verification log for next iteration
                    if (vscode.workspace.workspaceFolders) {
                        const logUri = vscode.Uri.joinPath(
                            vscode.workspace.workspaceFolders[0].uri,
                            '.agent/state/latest_verification.log'
                        );
                        await vscode.workspace.fs.writeFile(logUri, new TextEncoder().encode(
                            `COMMAND: ${action.command}\n\nRESULT:\n${result}`
                        ));
                    }
                    await MissionDispatchListener.sleep(2000);
                    break;

                case 'stop':
                    vscode.window.showWarningMessage(`[Mission] Stopped: ${action.reason}`);
                    await MissionDispatchListener.writeResult(jobId, 'stopped', action.reason, verificationResults);
                    return;

                case 'complete':
                    vscode.window.showInformationMessage(`[Mission] Complete: ${action.message}`);
                    // Run the job's verification commands before declaring success
                    const verifyPassed = await MissionDispatchListener.runJobVerification(dispatch, verificationResults);
                    const finalStatus = verifyPassed ? 'completed' : 'verification-failed';
                    await MissionDispatchListener.writeResult(jobId, finalStatus, action.message, verificationResults);
                    return;

                default:
                    console.warn('[MissionBridge] Unknown action:', action.action);
                    await MissionDispatchListener.sleep(1000);
                    break;
            }
        }

        // Hit iteration cap
        await MissionDispatchListener.writeResult(
            jobId,
            'iteration-limit',
            `Reached ${MissionDispatchListener.maxIterations} iterations without completion`,
            verificationResults
        );
    }

    private static buildPrompt(dispatch: any, previousVerification: string): string {
        const inputFiles = (dispatch.input_files || []).map((f: string) => `- \`${f}\``).join('\n');
        const criteria = (dispatch.success_criteria || []).map((c: string) => `- ${c}`).join('\n');
        const verifyCommands = (dispatch.verification_commands || []).map((c: string) => `\`${c}\``).join(', ');
        const blockedPaths = (dispatch.blocked_paths || []).map((p: string) => `- ${p}`).join('\n');

        return `You are BeingBijMantra, executing an autonomous mission dispatched by Chloe (the runtime receptionist).

## Mission: ${dispatch.title || dispatch.job_id}
**Objective:** ${dispatch.objective || dispatch.goal}
**Priority:** ${dispatch.priority}
**Iteration:** ${MissionDispatchListener.iterationCount} of ${MissionDispatchListener.maxIterations}

### Input Files (read these first)
${inputFiles || '(none specified — examine the workspace)'}

### Success Criteria
${criteria || '(none specified)'}

### Verification Commands (run these when you think you are done)
${verifyCommands || '(none specified)'}

### Blocked Paths (DO NOT modify these)
${blockedPaths || '(none)'}

${dispatch.notes ? `### Notes\n${dispatch.notes}\n` : ''}
${previousVerification}

## Instructions
Examine the workspace and determine the single immediate next action.
Your response MUST be a raw JSON object with NO markdown blocks and NO explanation.

Valid actions:
1. {"action": "edit", "path": "relative/path.ts", "content": "full file content"}
2. {"action": "verify", "command": "the command to run"}
3. {"action": "stop", "reason": "why you cannot continue"}
4. {"action": "complete", "message": "summary of what was accomplished"}

Rules:
- Work toward the objective incrementally. One edit or one verify per response.
- Read input files before making changes.
- Run verification commands before declaring complete.
- If stuck after 2 attempts at the same problem, use "stop".
- Never modify blocked paths.
`;
    }

    private static async runJobVerification(dispatch: any, results: any[]): Promise<boolean> {
        const commands: string[] = dispatch.verification_commands || [];
        if (commands.length === 0) {
            return true; // No verification commands = pass
        }

        let allPassed = true;
        for (const cmd of commands) {
            vscode.window.showInformationMessage(`[Mission] Final verification: ${cmd}`);
            const result = await WorkspaceTools.runVerification(cmd);
            const passed = !result.includes('Exit Code: 1') && !result.includes('FAILED');
            results.push({
                iteration: 'final-verification',
                command: cmd,
                result: result,
                passed: passed,
                timestamp: new Date().toISOString()
            });
            if (!passed) {
                allPassed = false;
            }
        }
        return allPassed;
    }

    /**
     * Write the mission result for the watchdog to consume.
     * This is the VS Code → OpenClaw feedback path.
     */
    private static async writeResult(
        jobId: string,
        status: string,
        summary: string,
        verificationResults: any[]
    ) {
        if (!vscode.workspace.workspaceFolders || vscode.workspace.workspaceFolders.length === 0) {
            return;
        }

        const rootUri = vscode.workspace.workspaceFolders[0].uri;
        const resultUri = vscode.Uri.joinPath(rootUri, '.agent/state/mission-result.json');

        const payload = {
            version: 1,
            job_id: jobId,
            status: status,
            summary: summary,
            executor: 'vscode-copilot',
            iterations: MissionDispatchListener.iterationCount,
            verification_results: verificationResults,
            started_at: MissionDispatchListener.currentJobId === jobId
                ? new Date().toISOString() : null,
            completed_at: new Date().toISOString()
        };

        await vscode.workspace.fs.writeFile(
            resultUri,
            new TextEncoder().encode(JSON.stringify(payload, null, 2))
        );

        // Also write a closeout receipt in the format the existing system expects
        const receiptUri = vscode.Uri.joinPath(rootUri, `.agent/state/closeout-receipts/${jobId}_receipt.json`);
        const receipt = {
            job_id: jobId,
            lane_id: jobId,
            status: status === 'completed' ? 'verifiable-complete' : status,
            summary: summary,
            executor: 'vscode-copilot',
            completed_at: new Date().toISOString()
        };

        try {
            await vscode.workspace.fs.writeFile(
                receiptUri,
                new TextEncoder().encode(JSON.stringify(receipt, null, 2))
            );
        } catch (e) {
            console.error('[MissionBridge] Failed to write closeout receipt:', e);
        }
    }

    private static deleteDispatchFile() {
        if (!vscode.workspace.workspaceFolders) { return; }
        const rootUri = vscode.workspace.workspaceFolders[0].uri;
        const dispatchUri = vscode.Uri.joinPath(rootUri, '.agent/state/mission-dispatch.json');
        vscode.workspace.fs.delete(dispatchUri, { useTrash: false }).then(() => {}, () => {});
    }

    private static sleep(ms: number): Promise<void> {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}
