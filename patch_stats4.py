import re

for filename in ["src/xai_multiseed.py", "src/mcts_planner.py", "src/SOVEREIGN_JULES_TESTER.py"]:
    with open(filename, "r") as f:
        content = f.read()

    # The issue is that the code in evo9-bugfix-base was relying on a specific version of gym/gymnasium or our custom wrapper.
    # The error "RecordEpisodeStatistics.__init__() got an unexpected keyword argument 'buffer_length'" was from gymcts passing buffer_length.
    # We replaced it with deque_size.
    # But then we got "_stats_key is prohibited" because older gym didn't have _stats_key. It used "episode".
    # And then we had "OekoEnv object has no attribute time_queue" or "episode_start_time" because those were added in the patch but they don't exist on OekoEnv.
    # The real issue is that the monkey patch was written for a very specific gymnasium version (probably 0.28.1 which has deque_size, or older gym).

    # Let's fix the monkey patch in xai_multiseed.py to work with whatever gymnasium 0.28.1 has.

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
        if hasattr(self, 'is_vector_env') and self.is_vector_env:
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

    content = re.sub(r'_orig_statistics_step = RecordEpisodeStatistics\.step.*?RecordEpisodeStatistics\.step = _patched_statistics_step', new_patch.strip(), content, flags=re.DOTALL)

    with open(filename, "w") as f:
        f.write(content)
