import sys
import json
from pathlib import Path

def print_header(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def unconfigure_antigravity():
    hooks_file = Path.home() / ".gemini" / "config" / "hooks.json"
    if not hooks_file.exists():
        print("ℹ️ Antigravity: No global hooks.json found.")
        return

    try:
        data = json.loads(hooks_file.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"⚠️ Antigravity: Could not parse {hooks_file}: {e}")
        return

    if "discord-remote-gate" in data:
        del data["discord-remote-gate"]
        hooks_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        print(f"✅ Antigravity: Removed discord-remote-gate hook from {hooks_file}")
    else:
        print("ℹ️ Antigravity: discord-remote-gate hook was not found.")

def unconfigure_claude_code():
    settings_file = Path.home() / ".claude" / "settings.json"
    if not settings_file.exists():
        print("ℹ️ Claude Code: No settings.json found.")
        return

    try:
        data = json.loads(settings_file.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"⚠️ Claude Code: Could not parse {settings_file}: {e}")
        return

    hooks = data.get("hooks", {})
    if "PermissionRequest" in hooks:
        # Filter out discord_hub or client.py references
        original_count = len(hooks["PermissionRequest"])
        hooks["PermissionRequest"] = [
            h for h in hooks["PermissionRequest"]
            if not any("client.py" in str(hk.get("command", "")) for hk in h.get("hooks", []))
        ]
        
        if not hooks["PermissionRequest"]:
            del hooks["PermissionRequest"]
        if not hooks:
            del data["hooks"]

        settings_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        print(f"✅ Claude Code: Removed Discord hooks from {settings_file}")
    else:
        print("ℹ️ Claude Code: No Discord PermissionRequest hooks found.")

def unconfigure_codex():
    print("ℹ️ Codex / Custom Agents: 'codex_helper.py' requires no global hooks to clean.")

def remove_env():
    env_file = Path(__file__).resolve().parent / ".env"
    if env_file.exists():
        confirm = input("Would you like to delete your local .env configuration file? (y/n) [n]: ").strip().lower()
        if confirm in ("y", "yes"):
            env_file.unlink()
            print("✅ Deleted .env configuration file.")

def main():
    print("\n" + "#" * 60)
    print("      🗑️  DISCORD AGENT GATE UNINSTALLER")
    print("#" * 60)
    print("This will remove Discord Gate hooks from Antigravity, Claude Code & Codex.")

    print_header("Removing Agent Hooks")
    unconfigure_antigravity()
    unconfigure_claude_code()
    unconfigure_codex()

    print_header("Local Settings")
    remove_env()

    print_header("Uninstall Complete! ✨")
    print("All agent hooks and settings have been cleanly removed.")
    print("Your agents will now use their default standard terminal prompts.\n")

if __name__ == "__main__":
    main()
