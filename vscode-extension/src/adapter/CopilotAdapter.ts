import * as vscode from 'vscode';

export class CopilotAdapter {
    /**
     * Checks if the Copilot Language Model is available and ready for inference.
     */
    public static async checkAvailability(): Promise<{ available: boolean; reason?: string }> {
        try {
            const models = await vscode.lm.selectChatModels({ vendor: 'copilot' });
            if (models.length === 0) {
                return { available: false, reason: "Copilot model family not found or not active." };
            }
            return { available: true };
        } catch (error) {
            return { available: false, reason: String(error) };
        }
    }

    /**
     * Sends a simple pre-flight prompt to the active language model.
     * Throws if no model is available.
     */
    public static async runDryRunPlan(prompt: string): Promise<string> {
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
        } catch (err: any) {
            if (err instanceof vscode.LanguageModelError) {
                throw new Error(`Copilot Language Model Error: ${err.message}. Ensure Copilot Chat is installed and authorized.`);
            }
            throw err;
        }
    }
}
