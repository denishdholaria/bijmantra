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
exports.CopilotAdapter = void 0;
const vscode = __importStar(require("vscode"));
class CopilotAdapter {
    /**
     * Checks if the Copilot Language Model is available and ready for inference.
     */
    static async checkAvailability() {
        try {
            const models = await vscode.lm.selectChatModels({ vendor: 'copilot' });
            if (models.length === 0) {
                return { available: false, reason: "Copilot model family not found or not active." };
            }
            return { available: true };
        }
        catch (error) {
            return { available: false, reason: String(error) };
        }
    }
    /**
     * Sends a simple pre-flight prompt to the active language model.
     * Throws if no model is available.
     */
    static async runDryRunPlan(prompt) {
        const models = await vscode.lm.selectChatModels({ vendor: 'copilot' });
        if (models.length === 0) {
            throw new Error("No Copilot language models available.");
        }
        // Picking the first available model
        const chatModel = models[0];
        const messages = [
            vscode.LanguageModelChatMessage.User(prompt)
        ];
        try {
            const chatResponse = await chatModel.sendRequest(messages, {}, new vscode.CancellationTokenSource().token);
            let result = "";
            for await (const chunk of chatResponse.text) {
                result += chunk;
            }
            return result;
        }
        catch (err) {
            if (err instanceof vscode.LanguageModelError) {
                throw new Error(`Copilot Language Model Error: ${err.message}. Ensure Copilot Chat is installed and authorized.`);
            }
            throw err;
        }
    }
}
exports.CopilotAdapter = CopilotAdapter;
//# sourceMappingURL=CopilotAdapter.js.map