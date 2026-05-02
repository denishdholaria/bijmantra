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
exports.WakeupListener = void 0;
const vscode = __importStar(require("vscode"));
class WakeupListener {
    static activate(context) {
        if (!vscode.workspace.workspaceFolders || vscode.workspace.workspaceFolders.length === 0) {
            return;
        }
        const rootUri = vscode.workspace.workspaceFolders[0].uri;
        const relativePattern = new vscode.RelativePattern(rootUri, '.agent/state/wakeup.json');
        const watcher = vscode.workspace.createFileSystemWatcher(relativePattern, false, false, false);
        const handleWakeup = async (uri) => {
            try {
                const raw = await vscode.workspace.fs.readFile(uri);
                const payload = JSON.parse(new TextDecoder().decode(raw));
                const promptMsg = `[Supervisor] ${payload.message}`;
                // Display native alert
                if (payload.urgency === 'error' || payload.urgency === 'critical') {
                    vscode.window.showErrorMessage(promptMsg, "Investigate")
                        .then(choice => {
                        if (choice === "Investigate") {
                            vscode.commands.executeCommand("beingbijmantra.openDeveloperBoard");
                        }
                    });
                }
                else if (payload.urgency === 'warning') {
                    vscode.window.showWarningMessage(promptMsg);
                }
                else {
                    vscode.window.showInformationMessage(promptMsg);
                }
                // Delete file to acknowledge
                await vscode.workspace.fs.delete(uri, { useTrash: false });
            }
            catch (e) {
                // File might have been deleted concurrently or malformed buffer
            }
        };
        // Trigger on creation or manual modification
        watcher.onDidCreate(handleWakeup);
        watcher.onDidChange(handleWakeup);
        context.subscriptions.push(watcher);
        // Check once on boot just in case we woke up to an existing notification
        const manualUri = vscode.Uri.joinPath(rootUri, '.agent/state/wakeup.json');
        vscode.workspace.fs.stat(manualUri).then(() => {
            handleWakeup(manualUri);
        }, () => { });
    }
}
exports.WakeupListener = WakeupListener;
//# sourceMappingURL=WakeupListener.js.map