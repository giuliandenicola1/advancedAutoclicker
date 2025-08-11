# Copilot Auto Continue

This extension automatically clicks 'Continue' in Copilot Chat when specified terminal prompts are detected.

## Features
- Monitors terminal output for user-configurable prompts.
- If a configured prompt is detected, it will (in future) automatically trigger the Copilot Chat 'Continue' action.
- Prompts are configurable via `copilotAutoContinue.allowedPrompts` in your VS Code settings.

## Configuration
Add your allowed prompts in your settings.json:

```
"copilotAutoContinue.allowedPrompts": [
	"Type 'continue' to proceed",
	"Another prompt to match"
]
```

## Limitations
- Currently, the extension only shows a notification when a prompt is detected. Automatic Copilot Chat interaction is planned.

## Requirements
- VS Code 1.87.0 or later.

## Known Issues
- The VS Code API does not yet provide a public way to programmatically click Copilot Chat buttons. This will be implemented as soon as the API allows.

## Release Notes
### 0.0.1
- Initial release: terminal monitoring and prompt detection.

### 1.0.1

Fixed issue #.

### 1.1.0

Added features X, Y, and Z.

---

## Following extension guidelines

Ensure that you've read through the extensions guidelines and follow the best practices for creating your extension.

* [Extension Guidelines](https://code.visualstudio.com/api/references/extension-guidelines)

## Working with Markdown

You can author your README using Visual Studio Code. Here are some useful editor keyboard shortcuts:

* Split the editor (`Cmd+\` on macOS or `Ctrl+\` on Windows and Linux).
* Toggle preview (`Shift+Cmd+V` on macOS or `Shift+Ctrl+V` on Windows and Linux).
* Press `Ctrl+Space` (Windows, Linux, macOS) to see a list of Markdown snippets.

## For more information

* [Visual Studio Code's Markdown Support](http://code.visualstudio.com/docs/languages/markdown)
* [Markdown Syntax Reference](https://help.github.com/articles/markdown-basics/)

**Enjoy!**
