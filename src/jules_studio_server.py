import os
import sys
import json
import time
import numpy as np
import torch
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
import io

# NEURAL FIX (Monkey Patch for PyTorch/Gymnasium compatibility)
import torch.nn as nn
original_lstm_init = nn.LSTM.__init__
def patched_lstm_init(self, input_size, hidden_size, *args, **kwargs):
    return original_lstm_init(self, int(input_size), int(hidden_size), *args, **kwargs)
nn.LSTM.__init__ = patched_lstm_init

# PATH SETUP
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(ROOT_DIR, "src"))
sys.path.append(os.path.join(ROOT_DIR, "engine"))

from sb3_contrib import RecurrentPPO
from oeko_core.envs.oeko_env import OekoEnv
from wrappers import OekoActionBuilderWrapper
from mcts_planner import SovereignMCTS

# GLOBALS
MODEL_PATH = os.path.join(ROOT_DIR, "brain", "sota_recurrent_champion.zip")
GLOBAL_MODEL = None

PROMPT_BOOSTS = {
    "people": 5, # Quality of Life
    "green": 1,  # Sanitation
    "economy": 2, # Production
    "learn": 4,   # Education
    "nature": 1,  # Sanitation proxy
    "stability": 3 # QoL/Stability proxy
}

class XAILogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.logs = []
    def emit(self, record):
        self.logs.append(self.format(record))

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    pass

class JulesStudioHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.path = '/index.html'
        
        try:
            file_path = os.path.join(ROOT_DIR, "src", "jules_studio_web", self.path.lstrip('/'))
            if not os.path.exists(file_path):
                self.send_error(404, "File not found")
                return

            with open(file_path, 'rb') as f:
                self.send_response(200)
                if file_path.endswith(".html"): self.send_header("Content-type", "text/html")
                elif file_path.endswith(".css"): self.send_header("Content-type", "text/css")
                elif file_path.endswith(".js"): self.send_header("Content-type", "application/javascript")
                self.end_headers()
                self.wfile.write(f.read())
        except Exception as e:
            self.send_error(500, str(e))

    def do_POST(self):
        if self.path == '/api/run':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            params = json.loads(post_data)
            
            prompt = params.get("prompt", "").lower()
            sovereign_mode = params.get("sovereign_mode", True)
            
            results = self.run_simulation(prompt, sovereign_mode)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(results).encode())

    def run_simulation(self, prompt, sovereign_mode):
        global GLOBAL_MODEL
        if GLOBAL_MODEL is None:
            print("[SERVER] Loading Model...")
            GLOBAL_MODEL = RecurrentPPO.load(MODEL_PATH)

        # Setup Logging Capture
        xai_handler = XAILogHandler()
        xai_handler.setFormatter(logging.Formatter('%(message)s'))
        mcts_logger = logging.getLogger("MCTS")
        mcts_logger.setLevel(logging.INFO)
        mcts_logger.addHandler(xai_handler)

        def run_env(is_sovereign, prompt_text=""):
            env = OekoEnv()
            wrapped = OekoActionBuilderWrapper(env)
            
            # Boost logic
            boost_id = None
            for key, val in PROMPT_BOOSTS.items():
                if key in prompt_text:
                    boost_id = val
                    break
            
            planner = SovereignMCTS(GLOBAL_MODEL, num_simulations=100, sovereign_mode=is_sovereign)
            
            trajectory = []
            logs_by_step = []
            
            obs, _ = wrapped.reset()
            trajectory.append(env.unwrapped.V.tolist())
            
            for r in range(30):
                step_logs_start = len(xai_handler.logs)
                
                # We use a simplified step for high speed in the studio
                # but still use the planner for the "Next Round" decision
                action = planner.search(wrapped)
                
                # If prompt boost is active and we are in Sovereign mode, try to apply it
                if is_sovereign and boost_id is not None:
                    mask = wrapped.valid_action_mask()
                    if mask[boost_id] and np.random.random() < 0.5:
                        action = boost_id # Override with prompt preference 50% of time if valid

                obs, reward, terminated, truncated, info = wrapped.step(action)
                
                # If we moved to next round (action 0), record state
                if action == 0 or terminated:
                    trajectory.append(env.unwrapped.V.tolist())
                
                step_logs_end = len(xai_handler.logs)
                logs_by_step.append(xai_handler.logs[step_logs_start:step_logs_end])
                
                if terminated: break
            
            return trajectory, logs_by_step

        print(f"[SERVER] Running Sovereign Simulation (Prompt: {prompt})...")
        traj_sov, logs_sov = run_env(sovereign_mode, prompt)
        
        print(f"[SERVER] Running Paper Comparison...")
        traj_paper, _ = run_env(False, "") # No prompt for paper baseline
        
        # Cleanup
        mcts_logger.removeHandler(xai_handler)
        
        return {
            "trajectory": traj_sov,
            "paper_trajectory": traj_paper,
            "logs": logs_sov
        }

def run_server(port=8000):
    server_address = ('', port)
    httpd = ThreadedHTTPServer(server_address, JulesStudioHandler)
    print(f"JULES STUDIO SERVER STARTED ON PORT {port}")
    httpd.serve_forever()

if __name__ == "__main__":
    run_server()
