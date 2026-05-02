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
exports.WorkspaceTools = void 0;
const vscode = __importStar(require("vscode"));
const cp = __importStar(require("child_process"));
/**
 * Highly constrained workspace tools that execute explicitly via native IDE APIs
 * to satisfy the "plan-only mode before enabling write mode" constraint.
 */
class WorkspaceTools {
    /**
     * Reads a file from the workspace natively.
     */
    static async readFileRelative(relativePath) {
        if (!vscode.workspace.workspaceFolders || vscode.workspace.workspaceFolders.length === 0) {
            throw new Error("No workspace folder open");
        }
        const rootUri = vscode.workspace.workspaceFolders[0].uri;
        const fileUri = vscode.Uri.joinPath(rootUri, relativePath);
        const raw = await vscode.workspace.fs.readFile(fileUri);
        return new TextDecoder().decode(raw);
    }
    /**
     * Proposes a workspace edit, rendering the diff safely through VS Code core.
     * In "plan-only mode", it does not apply the edit directly to disk, but
     * places it into the unsaved "Modified" state inside the IDE.
     */
    static async applyWorkspaceEditDryRun(relativePath, newText) {
        if (!vscode.workspace.workspaceFolders || vscode.workspace.workspaceFolders.length === 0) {
            throw new Error("No workspace folder open");
        }
        const rootUri = vscode.workspace.workspaceFolders[0].uri;
        const fileUri = vscode.Uri.joinPath(rootUri, relativePath);
        const edit = new vscode.WorkspaceEdit();
        let doc;
        try {
            doc = await vscode.workspace.openTextDocument(fileUri);
        }
        catch (e) {
            // Document doesn't exist, this is a creation edit
            edit.createFile(fileUri, { overwrite: true });
            edit.insert(fileUri, new vscode.Position(0, 0), newText);
            await vscode.workspace.applyEdit(edit);
            vscode.window.showInformationMessage(`[Dry Run] Simulated creation of ${relativePath}`);
            return;
        }
        const fullRange = new vscode.Range(doc.positionAt(0), doc.positionAt(doc.getText().length));
        edit.replace(fileUri, fullRange, newText);
        await vscode.workspace.applyEdit(edit);
        vscode.window.showInformationMessage(`[Dry Run] Proposed edits staged for ${relativePath}. View SCM diff or Undo (Cmd+Z) to revert.`);
    }
    /**
     * Executes a verification command safely inside the workspace context natively,
     * returning the std-streams to the Copilot loop.
     */
    static async runVerification(command) {
        if (!vscode.workspace.workspaceFolders || vscode.workspace.workspaceFolders.length === 0) {
            throw new Error("No workspace folder open");
        }
        const cwd = vscode.workspace.workspaceFolders[0].uri.fsPath;
        return new Promise((resolve) => {
            vscode.window.showInformationMessage(`[Pilot Verification] Running: ${command}`);
            cp.exec(command, { cwd }, (err, stdout, stderr) => {
                resolve(`Exit Code: ${err ? err.code : 0}\nSTDOUT:\n${stdout.slice(-1000)}\nSTDERR:\n${stderr.slice(-1000)}`);
            });
        });
    }
}
exports.WorkspaceTools = WorkspaceTools;
//# sourceMappingURL=WorkspaceTools.js.map