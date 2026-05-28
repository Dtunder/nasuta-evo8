import re

for filename in ["src/xai_multiseed.py", "src/mcts_planner.py", "src/SOVEREIGN_JULES_TESTER.py"]:
    with open(filename, "r") as f:
        content = f.read()

    # The actual RecordEpisodeStatistics implementation doesn't have a time_queue, it seems like we appended to it unnecessarily. Let's just remove that patch and replace it entirely with what was originally in RecordEpisodeStatistics, just modified to avoid the assert.

    # Let's replace the whole _patched_statistics_step

    new_patch = """
_orig_statistics_step = RecordEpisodeStatistics.step
def _patched_statistics_step(self, action):
    obs, reward, terminated, truncated, info = self.env.step(action)
    self.episode_returns += reward
    self.episode_lengths += 1
    dones = np.logical_or(terminated, truncated)
    if np.any(dones):
        if "episode" in info:
            info.pop("episode") # avoid assert
        if "_episode" in info:
            info.pop("_episode")

        info["episode"] = {
            "r": np.where(dones, self.episode_returns, 0.0),
            "l": np.where(dones, self.episode_lengths, 0),
            "t": np.where(dones, np.round(time.perf_counter() - self.episode_start_times, 6), 0.0)
        }
        if self.is_vector_env:
            info["_episode"] = np.where(dones, True, False)

        if hasattr(self, 'return_queue'):
            self.return_queue.extend(self.episode_returns[dones])
        if hasattr(self, 'length_queue'):
            self.length_queue.extend(self.episode_lengths[dones])

        self.episode_count += np.sum(dones)
        self.episode_lengths[dones] = 0
        self.episode_returns[dones] = 0
        self.episode_start_times[dones] = time.perf_counter()

    return obs, reward, terminated, truncated, info
RecordEpisodeStatistics.step = _patched_statistics_step
"""

    # We replace from "def _patched_statistics_step" to "RecordEpisodeStatistics.step = _patched_statistics_step"
    content = re.sub(r'def _patched_statistics_step.*?RecordEpisodeStatistics\.step = _patched_statistics_step', new_patch.strip(), content, flags=re.DOTALL)

    with open(filename, "w") as f:
        f.write(content)
