"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
const panel_1 = require("./panel");
const WorkspaceTools_1 = require("./adapter/WorkspaceTools");
const CopilotAdapter_1 = require("./adapter/CopilotAdapter");
const AutonomousPilot_1 = require("./ai/AutonomousPilot");
const WakeupListener_1 = require("./ai/WakeupListener");
const MissionDispatchListener_1 = require("./ai/MissionDispatchListener");
function activate(context) {
    console.log('BeingBijMantra extension is now active');
    // --- IDE Presence Heartbeat ---
    if (vscode.workspace.workspaceFolders && vscode.workspace.workspaceFolders.length > 0) {
        const rootUri = vscode.workspace.workspaceFolders[0].uri;
        const presenceUri = vscode.Uri.joinPath(rootUri, '.agent/state/ide-presence.json');
        const updatePresence = async (isOpen) => {
            try {
                const payload = {
                    is_vscode_open: isOpen,
                    timestamp: new Date().toISOString()
                };
                await vscode.workspace.fs.writeFile(presenceUri, new TextEncoder().encode(JSON.stringify(payload, null, 2)));
            }
            catch (e) {
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
        WakeupListener_1.WakeupListener.activate(context);
        // --- Mission Dispatch Listener (OpenClaw → Copilot bridge) ---
        MissionDispatchListener_1.MissionDispatchListener.activate(context);
    }
    const disposableBoard = vscode.commands.registerCommand('beingbijmantra.openDeveloperBoard', () => {
        panel_1.ControlPlanePanel.createOrShow();
    });
    const disposableTestCopilot = vscode.commands.registerCommand('beingbijmantra.testCopilot', async () => {
        vscode.window.showInformationMessage("Checking Copilot Availability...");
        try {
            const result = await CopilotAdapter_1.CopilotAdapter.checkAvailability();
            if (!result.available) {
                vscode.window.showErrorMessage(`Copilot not available: ${result.reason}`);
                return;
            }
            vscode.window.showInformationMessage("Copilot is connected! Running a dry-run test payload...");
            // Hardcoded test objective
            const res = await CopilotAdapter_1.CopilotAdapter.runDryRunPlan("State a cheerful 1-sentence hello world message.");
            await WorkspaceTools_1.WorkspaceTools.applyWorkspaceEditDryRun('.agent/state/copilot-handshake-test.json', JSON.stringify({
                status: "success",
                handshakeData: res,
                timestamp: new Date().toISOString()
            }, null, 2));
        }
        catch (e) {
            vscode.window.showErrorMessage(`Copilot test failed: ${e.message}`);
        }
    });
    const disposableStartPilot = vscode.commands.registerCommand('beingbijmantra.startAutonomousPilot', () => {
        AutonomousPilot_1.AutonomousPilot.startMission();
    });
    context.subscriptions.push(disposableBoard, disposableTestCopilot, disposableStartPilot);
}
function deactivate() { }
//# sourceMappingURL=extension.js.map