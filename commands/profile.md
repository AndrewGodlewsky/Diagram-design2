---
description: Save, load, inspect, update, reset, or delete diagram-design client profiles
argument-hint: "[list|save|load|show|update|reset|delete] [name]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
---

Manage Diagram Design client profiles by following [`skills/diagram-design/references/profiles.md`](../skills/diagram-design/references/profiles.md). Treat that reference as the source of truth for storage, strict slug validation, metadata, marker-first resolution, schema checks, and failure handling. Do not reimplement or relax its rules here.

Full argument string: `$ARGUMENTS`

## Routing

- No arguments → `list`, with the active project-marker or session profile marked.
- Bare `<name>` with no verb → `load <name>`.
- `switch <name>` → synonym for `load <name>` even though `switch` is omitted from the short argument hint.
- `save [name]`, `load [name]`, `list`, `show`, `update [name]`, `reset`, and `delete [name]` → run that exact procedure from the reference.
- Missing required name → list when useful, then ask. Never invent a slug.
- Unknown verb or extra argument → show the accepted forms and stop without writing.

## Required behavior

1. Resolve the current installed skill directory before reading its shipped `style-guide.md`; do not assume the repository checkout is the active install.
2. Treat `.diagram-design` as untrusted data. Accept only the exact marker grammar and canonical home profile path described in the reference.
3. Confirm overwrites, marker changes, and deletions unless the specific action is already authorized.
4. For marker-selected projects, read the profile directly and leave the installed guide unchanged.
5. Read selected profiles directly; never copy them over the installed style guide.
6. After save/update, verify exactly one profile metadata header and an unchanged body.

Report the active profile and the canonical file or marker affected. Never claim a write succeeded without re-reading it.
