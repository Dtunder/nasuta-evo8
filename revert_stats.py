import re

for filename in ["src/xai_multiseed.py", "src/mcts_planner.py", "src/SOVEREIGN_JULES_TESTER.py"]:
    with open(filename, "r") as f:
        content = f.read()

    # Revert to original wrapper fix

    original = """
_orig_statistics_step = RecordEpisodeStatistics.step
def _patched_statistics_step(self, action):
    obs, reward, terminated, truncated, info = self.env.step(action)
    self.episode_returns += reward
    self.episode_lengths += 1
    if terminated or truncated:
        if self._stats_key in info:
            info.pop(self._stats_key, None)  # Prevent AssertionError collision
        episode_time_length = round(time.perf_counter() - self.episode_start_time, 6)
        info[self._stats_key] = {
            "r": self.episode_returns,
            "l": self.episode_lengths,
            "t": episode_time_length,
        }
        self.time_queue.append(episode_time_length)
        self.return_queue.append(self.episode_returns)
        self.length_queue.append(self.episode_lengths)
        self.episode_count += 1
        self.episode_start_time = time.perf_counter()
    return obs, reward, terminated, truncated, info
RecordEpisodeStatistics.step = _patched_statistics_step
"""

    content = re.sub(r'_orig_statistics_step = RecordEpisodeStatistics\.step.*?RecordEpisodeStatistics\.step = _patched_statistics_step', original.strip(), content, flags=re.DOTALL)

    with open(filename, "w") as f:
        f.write(content)
