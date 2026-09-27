# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "requests",
# ]
# ///

import os
import sys
import json
import subprocess
import requests

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
MODEL_ID = os.environ.get("MODEL_ID", "google/gemini-2.5-flash")

def get_skill_content():
    skill_path = os.path.join(os.path.dirname(__file__), "..", "SKILL.md")
    with open(skill_path, "r", encoding="utf-8") as f:
        return f.read()

def execute_bash_command(cmd: str) -> str:
    print(f"\n[AGENT EXECUTES TOOL] $ {cmd}")
    try:
        # Prepend uv path if needed
        env = os.environ.copy()
        env["PATH"] = f"{os.path.expanduser('~/.local/bin')}:{env.get('PATH', '')}"
        
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=45,
            env=env
        )
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        
        output = stdout
        if stderr:
            output += f"\n[stderr]: {stderr}"
        if result.returncode != 0:
            output += f"\n[exit code {result.returncode}]"
            
        print(f"[TOOL OUTPUT PREVIEW]: {output[:300]}..." if len(output) > 300 else f"[TOOL OUTPUT]: {output}")
        return output
    except Exception as e:
        err = f"Execution failed: {e}"
        print(f"[TOOL ERROR]: {err}")
        return err

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Execute a bash command in the terminal from the skill directory. Use this to run scripts like `uv run scripts/resolve_articles.py`, `uv run scripts/fetch_pageviews.py`, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The command line string to run."
                    }
                },
                "required": ["command"]
            }
        }
    }
]

def run_agent_simulation(user_prompt: str, max_turns: int = 12):
    skill_md = get_skill_content()
    
    system_prompt = (
        "You are an AI Product Analyst agent equipped with the following Agent Skill:\n\n"
        f"{skill_md}\n\n"
        "Your task is to answer the user's research request following the workflow described in SKILL.md. "
        "Use the bash tool to invoke the provided python scripts directly from the current directory (e.g., `uv run scripts/...`). "
        "Base your final conclusions strictly on data returned by the scripts. "
        "Once scripts have been run and data analyzed, deliver a comprehensive, structured response in Ukrainian directly addressing the product question."
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    if not OPENROUTER_API_KEY:
        print("Error: OPENROUTER_API_KEY environment variable is not set. Run: export OPENROUTER_API_KEY=your_key")
        return None

    print(f"\n==================================================")
    print(f"STARTING SIMULATION WITH MODEL: {MODEL_ID}")
    print(f"USER PROMPT: {user_prompt}")
    print(f"==================================================")
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    for turn in range(max_turns):
        print(f"\n--- Turn {turn + 1}/{max_turns} ---")
        
        payload = {
            "model": MODEL_ID,
            "messages": messages,
            "tools": TOOLS,
            "temperature": 0.2
        }
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"API Error {response.status_code}: {response.text}")
            break
            
        res_data = response.json()
        choice = res_data["choices"][0]
        message = choice["message"]
        
        messages.append(message)
        
        content = message.get("content")
        tool_calls = message.get("tool_calls")
        
        if content:
            print(f"\n[AGENT THOUGHT / MESSAGE]:\n{content}")
            
        if not tool_calls:
            print("\n[AGENT FINISHED WORKFLOW]")
            return content
            
        for tool_call in tool_calls:
            call_id = tool_call.get("id")
            func_name = tool_call.get("function", {}).get("name")
            args_str = tool_call.get("function", {}).get("arguments", "{}")
            
            try:
                args = json.loads(args_str)
            except Exception:
                args = {"command": args_str}
                
            if func_name == "bash":
                cmd = args.get("command", "")
                result_output = execute_bash_command(cmd)
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": result_output
                })

    print("\nReached max turns without full completion.")
    return None

if __name__ == "__main__":
    test_query = (
        "Ми думаємо додати курс з астрономії до освітнього застосунку. "
        "Чи зростає інтерес до цієї теми в україномовній Wikipedia, і наскільки цьому зростанню можна довіряти?"
    )
    if len(sys.argv) > 1:
        test_query = " ".join(sys.argv[1:])
        
    run_agent_simulation(test_query)
