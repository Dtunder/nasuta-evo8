import os
import sys
import json
import subprocess
import time
import shutil

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TASKS_JSON = os.path.join(ROOT_DIR, "tasks.json")

def load_tasks():
    if not os.path.exists(TASKS_JSON):
        # Create a default template if none exists
        default_tasks = [
            {
                "id": 1,
                "task": "Beispiel-Task: Fuege einen ausfuehrlichen Kommentar in src/xai_logger.py ein.",
                "status": "pending",
                "agent": "gemini1",
                "attempts": 0,
                "max_attempts": 3,
                "validation_cmd": "python src/xai_runner.py",
                "error_logs": []
            }
        ]
        with open(TASKS_JSON, 'w') as f:
            json.dump(default_tasks, f, indent=4)
        return default_tasks
        
    with open(TASKS_JSON, 'r') as f:
        return json.load(f)

def save_tasks(tasks):
    with open(TASKS_JSON, 'w') as f:
        json.dump(tasks, f, indent=4)

def run_agent_cmd(agent, task_desc):
    """Launches the specific agent command and blocks until completion."""
    print(f"\n[Orchestrator] Starte Agent '{agent}' fuer Task...")
    print(f"[Orchestrator] Prompt: {task_desc}")
    sys.stdout.flush()
    
    # Construct command
    if agent in ["gemini1", "gemini2", "gemini3", "gemini4", "gemini5"]:
        # Standard power-prompt for the multi-account Gemini CLI
        cmd = [
            agent, 
            "-p", f"Fuer das lokale Repository: {task_desc}. Bearbeite die Quelldateien direkt und behebe eventuelle Fehler.",
            "--approval-mode", "auto_edit", 
            "--skip-trust"
        ]
    elif agent == "jules":
        # Check if jules_delegator.py exists, fallback to standard jules command if not
        delegator_path = os.path.join(ROOT_DIR, "jules_delegator.py")
        if os.path.exists(delegator_path):
            cmd = ["python", delegator_path, "--task", task_desc]
        else:
            cmd = ["jules", "-p", task_desc, "--approval-mode", "auto_edit"]
    else:
        # Fallback to standard gemini CLI
        cmd = [
            "gemini", 
            "-p", task_desc, 
            "--approval-mode", "auto_edit", 
            "--skip-trust"
        ]
        
    print(f"[Orchestrator] Fuehre aus: {' '.join(cmd)}")
    sys.stdout.flush()
    
    # Run process
    process = subprocess.Popen(
        cmd, 
        cwd=ROOT_DIR, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT, 
        text=True, 
        shell=True
    )
    
    # Stream stdout/stderr in real-time
    output_lines = []
    while True:
        line = process.stdout.readline()
        if not line and process.poll() is not None:
            break
        if line:
            clean_line = line.strip()
            print(f"[{agent}] {clean_line}")
            sys.stdout.flush()
            output_lines.append(line)
            
    rc = process.poll()
    full_output = "".join(output_lines)
    return rc, full_output

def run_validation(validation_cmd):
    """Executes the validation command to verify correctness of changes."""
    print(f"\n[Orchestrator] Starte Validierung: {validation_cmd}")
    sys.stdout.flush()
    
    process = subprocess.Popen(
        validation_cmd, 
        cwd=ROOT_DIR, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT, 
        text=True, 
        shell=True
    )
    
    output_lines = []
    while True:
        line = process.stdout.readline()
        if not line and process.poll() is not None:
            break
        if line:
            print(f"[Validation] {line.strip()}")
            sys.stdout.flush()
            output_lines.append(line)
            
    rc = process.poll()
    return rc, "".join(output_lines)

def run_loop():
    print("====================================================")
    print("      AUTONOMOUS MULTI-AGENT SWARM ORCHESTRATOR     ")
    print("====================================================")
    print(f"Workspace: {ROOT_DIR}")
    print(f"Task Queue: {TASKS_JSON}\n")
    sys.stdout.flush()
    
    while True:
        tasks = load_tasks()
        
        # Find next pending task
        active_task = None
        for t in tasks:
            if t["status"] == "pending":
                active_task = t
                break
                
        if not active_task:
            print("\n[Orchestrator] Keine 'pending' Tasks in der Warteschlange. Warte 10s...")
            sys.stdout.flush()
            time.sleep(10)
            continue
            
        print(f"\n>>> Bearbeite Task #{active_task['id']}: '{active_task['task']}'")
        sys.stdout.flush()
        
        # Lock task status
        active_task["status"] = "running"
        save_tasks(tasks)
        
        agent = active_task.get("agent", "gemini1")
        task_desc = active_task["task"]
        
        # 1. Run the AI agent
        rc_agent, output_agent = run_agent_cmd(agent, task_desc)
        
        # Reload tasks in case queue was modified during execution
        tasks = load_tasks()
        active_task = next(t for t in tasks if t["id"] == active_task["id"])
        
        if rc_agent != 0:
            print(f"\n[Orchestrator] Agent '{agent}' schlug mit Exit-Code {rc_agent} fehl.")
            active_task["attempts"] += 1
            active_task["error_logs"].append(f"Agent failed to execute (rc={rc_agent}). Output:\n{output_agent[:500]}")
            
            if active_task["attempts"] >= active_task.get("max_attempts", 3):
                active_task["status"] = "failed"
                print(f"[Orchestrator] Task #{active_task['id']} endgueltig FEHLGESCHLAGEN.")
            else:
                active_task["status"] = "pending"
                print(f"[Orchestrator] Versuche Task #{active_task['id']} erneut...")
                
            save_tasks(tasks)
            continue
            
        # 2. Run validation if specified
        val_cmd = active_task.get("validation_cmd")
        if not val_cmd:
            # If no validation command, assume success
            print("[Orchestrator] Keine Validierung definiert. Task als abgeschlossen markiert.")
            active_task["status"] = "completed"
            save_tasks(tasks)
            continue
            
        rc_val, output_val = run_validation(val_cmd)
        
        # Reload and sync
        tasks = load_tasks()
        active_task = next(t for t in tasks if t["id"] == active_task["id"])
        
        if rc_val == 0:
            print(f"\n[Orchestrator] Validation ERFOLGREICH fuer Task #{active_task['id']}!")
            active_task["status"] = "completed"
            save_tasks(tasks)
        else:
            print(f"\n[Orchestrator] Validation FEHLGESCHLAGEN fuer Task #{active_task['id']} (rc={rc_val})!")
            active_task["attempts"] += 1
            active_task["error_logs"].append(f"Validation failed (rc={rc_val}). Output:\n{output_val}")
            
            if active_task["attempts"] >= active_task.get("max_attempts", 3):
                active_task["status"] = "failed"
                print(f"[Orchestrator] Task #{active_task['id']} endgueltig FEHLGESCHLAGEN (Validierung kollabiert).")
            else:
                # SELF-HEALING: Modify the task prompt to pass the error back to the agent!
                print(f"[Orchestrator] Triggere Self-Healing. Fehler-Feedback an {agent}...")
                feedback = (
                    f"Bei deinem letzten Versuch, die Aufgabe '{task_desc}' zu loesen, "
                    f"trat ein Validierungsfehler auf. Hier ist der Fehlerausgabebildschirm:\n\n"
                    f"```\n{output_val}\n```\n\n"
                    f"Bitte korrigiere deinen Code, um diesen Fehler zu beheben."
                )
                active_task["task"] = feedback
                active_task["status"] = "pending"
                
            save_tasks(tasks)
            
        # Small cooldown between tasks
        time.sleep(2)

if __name__ == "__main__":
    try:
        run_loop()
    except KeyboardInterrupt:
        print("\n[Orchestrator] Beendet durch User.")
