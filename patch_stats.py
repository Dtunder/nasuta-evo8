import re

for filename in ["src/xai_multiseed.py", "src/mcts_planner.py", "src/SOVEREIGN_JULES_TESTER.py"]:
    with open(filename, "r") as f:
        content = f.read()

    # The previous code patched RecordEpisodeStatistics.step to reference `self.episode_start_time`,
    # but the actual implementation in older/newer gymnasium uses `self.episode_start_times` (array).
    # Furthermore, `self._stats_key` is also wrong since we hardcoded "episode".

    content = re.sub(r'self\.episode_start_time(?!\w)', r'self.episode_start_times', content)

    with open(filename, "w") as f:
        f.write(content)
