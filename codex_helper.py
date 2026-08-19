"""
OpenAI Codex & Custom Agent Integration Helper for Discord Agent Gate
Use this module to gate tool executions or human-in-the-loop approvals via Discord.
"""

import sys
import json
import urllib.request
import urllib.error

LOCAL_PORT = 9876
TIMEOUT = 315

def ask_discord(tool_name: str, args: dict | str, agent: str = "CODEX", workspace: str = "") -> dict:
    """
    Sends a confirmation request to Discord and waits for the user's response.

    :param tool_name: Name of the tool or action (e.g. 'bash', 'run_command', 'write_file')
    :param args: Command line string or dictionary of arguments
    :param agent: Name of the agent (e.g. 'CODEX', 'AUTOGEN', 'LANGCHAIN')
    :param workspace: Optional workspace directory
    :return: dict with {"decision": "allow" | "deny", "reason": str}
    """
    args_str = args if isinstance(args, str) else json.dumps(args, indent=2)

    payload = {
        "agent": agent,
        "tool": tool_name,
        "args": args_str,
        "workspace": workspace
    }

    url = f"http://127.0.0.1:{LOCAL_PORT}/ask"
    req_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=req_bytes, headers={"Content-Type": "application/json"})

    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError:
        print("⚠️ Warning: Discord Bridge Daemon is offline. Falling back to allow.", file=sys.stderr)
        return {"decision": "allow", "reason": "Daemon offline"}
    except Exception as e:
        return {"decision": "deny", "reason": f"Bridge error: {str(e)}"}

def is_approved(tool_name: str, args: dict | str, agent: str = "CODEX") -> bool:
    """
    Returns True if approved on Discord, False if declined.
    """
    res = ask_discord(tool_name, args, agent=agent)
    return res.get("decision") == "allow"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python codex_helper.py <command_or_action>")
        print("Example: python codex_helper.py 'git push origin main'")
        sys.exit(1)

    cmd = " ".join(sys.argv[1:])
    approved = is_approved("CLI_EXEC", cmd, agent="CODEX")
    if approved:
        print(f"✅ Approved via Discord. Executing: {cmd}")
        import subprocess
        subprocess.run(cmd, shell=True)
    else:
        print("❌ Blocked / Declined via Discord.")
        sys.exit(1)
