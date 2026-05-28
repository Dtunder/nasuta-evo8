import re

with open("src/mcts_planner.py", "r") as f:
    content = f.read()

# Add a failsafe loop counter for the while not d_done and rounds_played < 50
new_while = """
        loop_counter = 0
        while not d_done and rounds_played < 50 and loop_counter < 1000:  # safety cap for rollout simulations
            loop_counter += 1
"""
content = re.sub(r'while not d_done and rounds_played < 50:\s*# safety cap for rollout simulations', new_while.strip(), content)

with open("src/mcts_planner.py", "w") as f:
    f.write(content)
