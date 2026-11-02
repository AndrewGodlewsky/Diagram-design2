# Privacy Policy

This distribution of Diagram Design is maintained by [AndrewGodlewsky](https://github.com/AndrewGodlewsky/Diagram-design2), based on the original skill by LittleMight (Cathryn Lavery). This policy covers this repository's plugin and skill in every host it is installed in, including ChatGPT, Codex, and Claude Code.

Effective 2026-11-01.

Diagram Design is a set of instructions, HTML templates, and small local scripts that run inside the AI agent you install it in. It has no server, no accounts, no analytics, and no telemetry. The maintainer does not receive any data from your use of it.

## Personal data collected

The maintainer collects no personal data through Diagram Design.

When you use it, the plugin works with what you give your agent: a description of the diagram you want, files you ask it to redraw (draw.io, Mermaid, or Excalidraw), and, if you ask for brand onboarding, local brand files or pasted tokens. The skill's helper scripts process files locally. Your agent may still send prompts and file contents to its model provider, including when its tools run on your computer. The plugin does not ask for payment details, health data, government identifiers, passwords, or other sensitive data, and it does not need any.

## How data is used

The skill uses the content you provide to produce the diagram you asked for: to choose a diagram type, lay it out, apply your brand colors and fonts, and write the static HTML or SVG file. The maintainer does not collect it for advertising, profiling, or training. Your agent provider's handling of that content is governed by its own policies and your account settings.

## Who receives data

- **Your AI agent's provider.** Your prompts and files are processed by the agent you use (for example OpenAI for ChatGPT and Codex) under that provider's own privacy policy. Diagram Design does not change how your agent handles data.
- **External resources.** Authoring uses supplied local files or pasted values. Generated files and SVG exports use installed fonts and generic fallbacks, without scripts, remote stylesheets, font downloads, or other network resources.
- **The maintainer.** Nothing. There is no server to send data to.

## Data retention

The maintainer retains no data, because it receives none. Diagrams you generate and brand profiles you save (in `~/.diagram-design/profiles/`) are kept wherever your agent runs until you delete them. With a local agent that is your computer. With a hosted agent such as ChatGPT, the files live in your provider's workspace and follow that provider's retention and deletion rules. Your agent provider retains data under its own policies.

## Your controls

- Delete generated diagrams and saved profiles at any time. With a local agent they are ordinary files on your computer; with a hosted agent, use your provider's controls to delete the files or the conversation that holds them.
- Use the defaults, supply exact local brand paths, or paste tokens. The skill does not discover branding by browsing websites or scanning your home directory.
- Review generated static files and saved profiles; local output checks are available without a browser or network connection.
- Uninstall the plugin at any time from your agent.

## Changes and contact

Changes to this policy are published here with a new effective date, and the full history is in this repository's git log. Ask questions in [GitHub issues](https://github.com/AndrewGodlewsky/Diagram-design2/issues). Report security problems privately, as described in [SECURITY.md](SECURITY.md).
