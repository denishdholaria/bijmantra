import * as fs from 'fs';
import * as path from 'path';
import * as vscode from 'vscode';

export function getRuntimeAuthToken(): string | null {
    const workspaceFolders = vscode.workspace.workspaceFolders;
    if (!workspaceFolders || workspaceFolders.length === 0) {
        return null;
    }

    const repoRoot = workspaceFolders[0].uri.fsPath;
    const authProfilesPath = path.join(repoRoot, '.agent', 'state', 'auth-profiles.json');

    try {
        if (fs.existsSync(authProfilesPath)) {
            const rawData = fs.readFileSync(authProfilesPath, 'utf8');
            const data = JSON.parse(rawData);
            return data.profiles?.default?.token || null;
        }
    } catch (e) {
        console.error("Failed to parse auth-profiles.json", e);
    }

    return null;
}
