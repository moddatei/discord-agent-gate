# 🛡️ Discord Agent Gate

> **Control your AI Coding Agents from your phone!**  
> Approve commands, decline risky actions, or provide custom instructions via Discord interactive buttons when you're away from your PC.

Works with **Google Antigravity (AGY)**, **Claude Code**, **OpenAI Codex**, and custom CLI agents.

---

## ✨ Features

- 📱 **Remote Approvals from Mobile**: Accept (`✅`) or Decline (`❌`) tool runs directly inside Discord.
- 💬 **Interactive Modals**: Type custom feedback or alternative prompts from Discord that get sent right back to the agent.
- 🌐 **Universal Support**: One lightweight background daemon handles Antigravity, Claude Code, Codex, and terminal tools.
- ⚡ **Zero Port Forwarding Needed**: Discord bot connects outbound via WebSocket (works behind NAT, firewalls, and VPNs).
- 🎨 **Rich Embeds**: Syntax-highlighted code blocks, tool names, workspace paths, and automatic timeout handling.

---

## 📸 How It Looks on Discord

```
┌─────────────────────────────────────────────────────────────┐
│ 🛡️ Confirmation: ANTIGRAVITY                                │
│ Tool / Operation: run_command                               │
│ Workspace: /home/user/my-project                            │
│                                                             │
│ Command / Arguments:                                        │
│ ```yaml                                                     │
│ CommandLine: npm run build && git push origin main          │
│ ```                                                         │
│                                                             │
│ [✅ Approve]      [❌ Decline]      [💬 Send Feedback]       │
└─────────────────────────────────────────────────────────────┘
```

When you tap **`[💬 Send Feedback]`**, a Discord modal pops up asking for instructions (e.g. *"Run tests first, don't push to main"*), and routes it back into the agent loop!

---

## 🚀 Quickstart (3 Minutes)

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/yourusername/discord-agent-gate.git
cd discord-agent-gate
pip install -r requirements.txt
```

### 2. Create a Discord Bot
1. Go to the [Discord Developer Portal](https://discord.com/developers/applications).
2. Click **New Application**, name it (e.g. `Agent Approver`).
3. Go to the **Bot** tab:
   - Click **Reset Token** to copy your **Bot Token**.
4. Go to **OAuth2 > URL Generator**:
   - Scopes: `bot`, `applications.commands`
   - Bot Permissions: `Send Messages`, `Embed Links`, `Read Message History`
5. Open the generated URL in your browser to invite the bot to your private Discord server.
6. Enable **Developer Mode** in Discord (`User Settings > Advanced > Developer Mode`).
7. Right-click your desired channel and click **Copy Channel ID**.

### 3. Run the Interactive Installer
```bash
python install.py
```
The wizard will:
- Prompt for your Bot Token & Channel ID.
- Test your Discord connection.
- **Auto-configure hooks** for Google Antigravity and Claude Code!

### 4. Start the Background Daemon
```bash
python daemon.py
```

---

## 🛠️ Manual Hook Configuration

If you prefer to configure your agents manually:

### Google Antigravity (AGY)
Add to `.agents/hooks.json` or `~/.gemini/config/hooks.json`:
```json
{
  "discord-remote-gate": {
    "PreToolUse": [
      {
        "matcher": "ask_question|run_command",
        "hooks": [
          {
            "type": "command",
            "command": "python /path/to/discord-agent-gate/client.py --agent antigravity"
          }
        ]
      }
    ]
  }
}
```

#### Sensitivity Matcher Options:
- `"ask_question|run_command"` *(Recommended)*: Pings Discord only on interactive questions/forms and terminal commands. Normal file editing remains silent.
- `"ask_question"`: Pings Discord only when the agent explicitly asks a multiple-choice question or confirmation form.
- `"run_command"`: Pings Discord only when terminal commands are about to execute.
- `"run_command|write_to_file|replace_file_content"`: Full gate on all file edits and commands.

### Claude Code
Add to `~/.claude/settings.json`:
```json
{
  "hooks": {
    "PermissionRequest": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "python /path/to/discord-agent-gate/client.py --agent claude"
          }
        ]
      }
    ]
  }
}
```

---

## 🗑️ Uninstallation

If you ever want to remove Discord Agent Gate and restore your agents to their default terminal behavior, just run:

```bash
python uninstall.py
```

This cleanly removes the hook configurations from Antigravity (`hooks.json`) and Claude Code (`settings.json`) without affecting any of your other custom configurations.

---

## 🔄 Running the Daemon in the Background

### Option A: Using PM2 (Recommended)
```bash
npm install -g pm2
pm2 start daemon.py --name "discord-agent-gate" --interpreter python
pm2 save
pm2 startup
```

### Option B: Using systemd (Linux)
Create `/etc/systemd/system/discord-agent-gate.service`:
```ini
[Unit]
Description=Discord Agent Gate Daemon
After=network.target

[Service]
Type=simple
User=yourusername
WorkingDirectory=/path/to/discord-agent-gate
ExecStart=/usr/bin/python3 /path/to/discord-agent-gate/daemon.py
Restart=always

[Install]
WantedBy=multi-user.target
```
Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now discord-agent-gate
```

### Option C: Windows Startup (Task Scheduler or Background)
Create a batch file `start_gate.bat`:
```bat
@echo off
python C:\path\to\discord-agent-gate\daemon.py
```
Place a shortcut in `shell:startup`.

---

## 🔒 Security Best Practices
- Keep your Discord channel private (accessible only to you).
- Never commit your `.env` file containing your Discord Bot Token to GitHub.
- Set a reasonable `TIMEOUT_SECONDS` (default: 5 minutes) to automatically reject expired requests.

---

## 📄 License
MIT License. Free for personal and commercial use.
