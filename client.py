import sys
import json
import argparse
import urllib.request
import urllib.error
from pathlib import Path

# Try to read port from config or fallback
try:
    import config
    LOCAL_PORT = config.LOCAL_PORT
    TIMEOUT = config.TIMEOUT_SECONDS + 15
except Exception:
    LOCAL_PORT = 9876
    TIMEOUT = 315

def parse_args():
    parser = argparse.ArgumentParser(description="Universal Discord Approval Client for AI Agents")
    parser.add_argument("--agent", choices=["antigravity", "claude", "codex", "generic"], default="generic",
                        help="Target AI agent type")
    return parser.parse_args()

def extract_payload(agent_type: str, raw_data: dict) -> dict:
    tool_name = "Action"
    args_str = ""
    workspace = ""

    if agent_type == "antigravity":
        tool_call = raw_data.get("toolCall", {})
        tool_name = tool_call.get("name", "Tool")
        args = tool_call.get("args", {})
        if tool_name == "ask_question" and "questions" in args:
            lines = []
            for q in args["questions"]:
                lines.append(f"❓ {q.get('question', '')}")
                for opt in q.get("options", []):
                    lines.append(f"  • {opt}")
            args_str = "\n".join(lines)
        elif tool_name == "run_command" and "CommandLine" in args:
            args_str = f"$ {args['CommandLine']}"
        else:
            args_str = json.dumps(args, indent=2)
        workspaces = raw_data.get("workspacePaths", [])
        if workspaces:
            workspace = str(workspaces[0])

    elif agent_type == "claude":
        tool_name = raw_data.get("tool_name", raw_data.get("tool", "Tool"))
        tool_input = raw_data.get("tool_input", raw_data.get("args", {}))
        args_str = json.dumps(tool_input, indent=2)
        workspace = raw_data.get("cwd", "")

    else:  # codex or generic
        tool_name = raw_data.get("name", raw_data.get("tool", "Command"))
        args_str = json.dumps(raw_data.get("args", raw_data), indent=2)

    return {
        "agent": agent_type,
        "tool": tool_name,
        "args": args_str,
        "workspace": workspace
    }

def format_output(agent_type: str, daemon_response: dict, raw_data: dict) -> dict:
    decision = daemon_response.get("decision", "deny")
    reason = daemon_response.get("reason", "")

    if agent_type == "claude":
        return {
            "behavior": "allow" if decision == "allow" else "deny",
            "message": reason
        }
    elif agent_type == "antigravity":
        output = {
            "decision": decision,  # "allow" | "deny"
            "reason": reason
        }
        if decision == "allow":
            tool_call = raw_data.get("toolCall", {})
            name = tool_call.get("name", "")
            args = tool_call.get("args", {})
            overrides = []
            if name == "run_command" and "CommandLine" in args:
                cmd = args["CommandLine"].strip()
                overrides.append(f"command({cmd})")
                base_cmd = cmd.split()[0] if cmd.split() else ""
                if base_cmd:
                    overrides.append(f"command({base_cmd})")
                overrides.append("command(*)")
            elif name in ("write_to_file", "replace_file_content") and "TargetFile" in args:
                target_file = args["TargetFile"]
                overrides.append(f"file_write({target_file})")
                overrides.append("file_write(*)")
            elif name:
                overrides.append(f"{name}(*)")
                overrides.append("*")
            if overrides:
                output["permissionOverrides"] = overrides
        return output
    else:
        return {
            "decision": decision,
            "reason": reason
        }

def main():
    args = parse_args()

    # Read stdin from agent hook
    raw_input = ""
    try:
        raw_input = sys.stdin.read()
        raw_data = json.loads(raw_input) if raw_input.strip() else {}
    except Exception:
        raw_data = {"raw": raw_input}

    payload = extract_payload(args.agent, raw_data)

    # Communicate with local background daemon
    url = f"http://127.0.0.1:{LOCAL_PORT}/ask"
    req_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=req_bytes, headers={"Content-Type": "application/json"})

    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            daemon_res = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError:
        # Daemon is offline -> fallback safely
        daemon_res = {
            "decision": "ask",
            "reason": "Discord Bridge Daemon is not running. Falling back to local terminal prompt."
        }
    except Exception as e:
        daemon_res = {
            "decision": "deny",
            "reason": f"Bridge error: {str(e)}"
        }

    output = format_output(args.agent, daemon_res, raw_data)
    print(json.dumps(output))

if __name__ == "__main__":
    main()
