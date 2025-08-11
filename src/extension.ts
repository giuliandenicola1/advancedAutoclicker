// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from 'vscode';

// This method is called when your extension is activated
// Your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {
	console.log('Copilot Auto Continue extension is active!');

	// Register the Hello World command (for test/demo)
	const disposable = vscode.commands.registerCommand('copilot-auto-continue.helloWorld', () => {
		vscode.window.showInformationMessage('Hello World from Copilot Auto Continue!');
	});
	context.subscriptions.push(disposable);

	// Get allowed prompts from configuration
	function getAllowedPrompts(): string[] {
		return vscode.workspace.getConfiguration().get<string[]>('copilotAutoContinue.allowedPrompts', []);
	}

	// Listen to terminal output (only if API is available)
	const onDidWriteTerminalData = (vscode.window as any).onDidWriteTerminalData;
	if (typeof onDidWriteTerminalData === 'function') {
		context.subscriptions.push(
			onDidWriteTerminalData((e: { data: string }) => {
				const allowedPrompts = getAllowedPrompts();
				for (const prompt of allowedPrompts) {
					if (e.data && e.data.includes(prompt)) {
						vscode.window.showInformationMessage(`Detected allowed prompt: "${prompt}". (Would auto-continue Copilot Chat here.)`);
						// TODO: Programmatically trigger Copilot Chat 'Continue' button if possible
						break;
					}
				}
			})
		);
	} else {
		console.warn('onDidWriteTerminalData API is not available in this version of VS Code.');
	}
}

// This method is called when your extension is deactivated
export function deactivate() {}
