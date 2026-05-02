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
exports.ControlPlanePanel = void 0;
const vscode = __importStar(require("vscode"));
const auth_1 = require("./auth");
class ControlPlanePanel {
    static currentPanel;
    _panel;
    _disposables = [];
    constructor(panel) {
        this._panel = panel;
        this._panel.onDidDispose(() => this.dispose(), null, this._disposables);
        this._update();
    }
    static createOrShow() {
        const column = vscode.window.activeTextEditor
            ? vscode.window.activeTextEditor.viewColumn
            : undefined;
        if (ControlPlanePanel.currentPanel) {
            ControlPlanePanel.currentPanel._panel.reveal(column);
            return;
        }
        const panel = vscode.window.createWebviewPanel('bijmantraBoard', 'Developer Control Plane', column || vscode.ViewColumn.One, {
            enableScripts: true,
            retainContextWhenHidden: true,
        });
        ControlPlanePanel.currentPanel = new ControlPlanePanel(panel);
    }
    dispose() {
        ControlPlanePanel.currentPanel = undefined;
        this._panel.dispose();
        while (this._disposables.length) {
            const x = this._disposables.pop();
            if (x) {
                x.dispose();
            }
        }
    }
    _update() {
        const webview = this._panel.webview;
        this._panel.title = 'BijMantra Active Board';
        webview.html = this._getHtmlForWebview(webview);
    }
    _getHtmlForWebview(webview) {
        const token = (0, auth_1.getRuntimeAuthToken)() || "";
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Developer Control Plane</title>
    <style>
        body { font-family: var(--vscode-font-family); color: var(--vscode-editor-foreground); background-color: var(--vscode-editor-background); padding: 20px; }
        h1 { font-size: 1.5em; border-bottom: 1px solid var(--vscode-widget-border); padding-bottom: 10px; }
        pre { background: var(--vscode-textCodeBlock-background); padding: 15px; border-radius: 5px; overflow-x: auto; white-space: pre-wrap; }
        .status { padding: 5px 10px; margin-bottom: 20px; border-radius: 3px; display: inline-block; background-color: var(--vscode-button-background); color: var(--vscode-button-foreground); }
    </style>
</head>
<body>
    <h1>BijMantra Developer Master Board</h1>
    <div class="status" id="indicator">Connecting to control plane...</div>
    <button onclick="fetchBoard()">Refresh</button>
    <pre id="output">Waiting for data...</pre>

    <script>
        const authToken = "${token}";

        async function fetchBoard() {
            const indicator = document.getElementById('indicator');
            const output = document.getElementById('output');
            
            indicator.textContent = "Fetching active board...";
            
            try {
                const response = await fetch('http://localhost:8000/api/v2/developer-control-plane/active-board', {
                    headers: {
                        'Accept': 'application/json',
                        ...(authToken ? {'Authorization': 'Bearer ' + authToken} : {})
                    }
                });

                if (!response.ok) {
                    throw new Error('HTTP error: ' + response.status);
                }

                const data = await response.json();
                output.textContent = JSON.stringify(data, null, 2);
                indicator.textContent = "Connected (Live)";
                indicator.style.backgroundColor = "green";
            } catch (err) {
                output.textContent = err.toString();
                indicator.textContent = "Offline / Error";
                indicator.style.backgroundColor = "red";
            }
        }

        fetchBoard();
    </script>
</body>
</html>`;
    }
}
exports.ControlPlanePanel = ControlPlanePanel;
//# sourceMappingURL=panel.js.map