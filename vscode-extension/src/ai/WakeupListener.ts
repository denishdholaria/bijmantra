import * as vscode from 'vscode';

export class WakeupListener {
    public static activate(context: vscode.ExtensionContext) {
        if (!vscode.workspace.workspaceFolders || vscode.workspace.workspaceFolders.length === 0) {
            return;
        }
        
        const rootUri = vscode.workspace.workspaceFolders[0].uri;
        const relativePattern = new vscode.RelativePattern(rootUri, '.agent/state/wakeup.json');
        
        const watcher = vscode.workspace.createFileSystemWatcher(relativePattern, false, false, false);

        const handleWakeup = async (uri: vscode.Uri) => {
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
                } else if (payload.urgency === 'warning') {
                    vscode.window.showWarningMessage(promptMsg);
                } else {
                    vscode.window.showInformationMessage(promptMsg);
                }

                // Delete file to acknowledge
                await vscode.workspace.fs.delete(uri, { useTrash: false });

            } catch (e) {
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
        }, () => {});
    }
}
