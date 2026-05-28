import re

for filename in ["src/xai_multiseed.py", "src/mcts_planner.py", "src/SOVEREIGN_JULES_TESTER.py"]:
    with open(filename, "r") as f:
        content = f.read()

    # Change round(..., 6) to np.round(..., 6)
    content = content.replace("round(time.perf_counter() - self.episode_start_times, 6)", "np.round(time.perf_counter() - self.episode_start_times, 6)")

    with open(filename, "w") as f:
        f.write(content)
