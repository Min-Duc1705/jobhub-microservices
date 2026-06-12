import json

log_path = r"C:\Users\ACER\.gemini\antigravity\brain\d4150590-3c4e-4983-b1eb-92134b87127d\.system_generated\logs\transcript.jsonl"

def search():
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        print(f"Total steps in log: {len(lines)}")
        
        matches = []
        for line in lines:
            step = json.loads(line)
            content = step.get("content", "")
            tool_calls = step.get("tool_calls", [])
            tool_str = json.dumps(tool_calls)
            
            # Look for running commands
            is_match = False
            for tc in tool_calls:
                if tc.get('name') == 'run_command':
                    cmd = tc.get('args', {}).get('CommandLine', '')
                    if any(x in cmd.lower() for x in ['docker', 'git', 'python', 'logs']):
                        is_match = True
            
            if is_match:
                matches.append(step)
                
        print(f"Found {len(matches)} matching command steps:")
        for step in matches[-40:]: # show last 40 matching steps
            print(f"\n--- Step {step.get('step_index')} ({step.get('type')}) ---")
            for tc in step.get('tool_calls', []):
                print(f"  Cmd: {tc.get('args', {}).get('CommandLine')}")
            # print first 200 chars of stdout/output if available
            # but wait, the next line in the jsonl contains the output (type: GENERIC or RUN_COMMAND result)
            
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    search()
