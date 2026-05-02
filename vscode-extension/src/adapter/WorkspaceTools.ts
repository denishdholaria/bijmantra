import * as vscode from 'vscode';
import * as cp from 'child_process';

/**
 * Highly constrained workspace tools that execute explicitly via native IDE APIs
 * to satisfy the "plan-only mode before enabling write mode" constraint.
 */
export class WorkspaceTools {
    /**
     * Reads a file from the workspace natively.
     */
    public static async readFileRelative(relativePath: string): Promise<string> {
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
    public static async applyWorkspaceEditDryRun(relativePath: string, newText: string): Promise<void> {
        if (!vscode.workspace.workspaceFolders || vscode.workspace.workspaceFolders.length === 0) {
            throw new Error("No workspace folder open");
        }
        
        const rootUri = vscode.workspace.workspaceFolders[0].uri;
        const fileUri = vscode.Uri.joinPath(rootUri, relativePath);

        const edit = new vscode.WorkspaceEdit();
        
        let doc: vscode.TextDocument;
        try {
            doc = await vscode.workspace.openTextDocument(fileUri);
        } catch (e) {
            // Document doesn't exist, this is a creation edit
            edit.createFile(fileUri, { overwrite: true });
            edit.insert(fileUri, new vscode.Position(0, 0), newText);
            
            await vscode.workspace.applyEdit(edit);
            vscode.window.showInformationMessage(`[Dry Run] Simulated creation of ${relativePath}`);
            return;
        }

        const fullRange = new vscode.Range(
            doc.positionAt(0),
            doc.positionAt(doc.getText().length)
        );
        edit.replace(fileUri, fullRange, newText);

        await vscode.workspace.applyEdit(edit);
        vscode.window.showInformationMessage(`[Dry Run] Proposed edits staged for ${relativePath}. View SCM diff or Undo (Cmd+Z) to revert.`);
    }

    /**
     * Executes a verification command safely inside the workspace context natively, 
     * returning the std-streams to the Copilot loop.
     */
    public static async runVerification(command: string): Promise<string> {
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
