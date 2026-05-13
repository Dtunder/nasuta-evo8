import gymnasium as gym

class OekoPerRoundRewardWrapper(gym.Wrapper):
    def __init__(self, env, per_round_reward=1):
        super().__init__(env)
        self.per_round_reward = per_round_reward

    def mod_reward(self):
        if self.env.unwrapped.done and self.env.unwrapped.V[self.env.unwrapped.ROUND] in range(10, 31):
            reward = self.env.unwrapped.balance
        else:
            reward = self.per_round_reward
        return reward

    def step(self, action):
        obs, _, terminated, truncated, info = self.env.step(action)
        reward = self.mod_reward()
        return obs, reward, terminated, truncated, info


class OekoAuxRewardWrapper(gym.Wrapper):
    def __init__(self, env, scaling=1):
        super().__init__(env)
        self.scaling = scaling

    def mod_reward(self):
        if self.env.unwrapped.done and self.env.unwrapped.V[self.env.unwrapped.ROUND] in range(10, 31):
            return self.env.unwrapped.balance
        else:
            production_reward = 14 - abs(15 - self.env.unwrapped.V[self.env.unwrapped.PRODUCTION])
            population_reward = 23 - abs(24 - self.env.unwrapped.V[self.env.unwrapped.POPULATION])
            return self.scaling * (production_reward + population_reward)

    def step(self, action):
        obs, _, terminated, truncated, info = self.env.step(action)
        reward = self.mod_reward()
        return obs, reward, terminated, truncated, info
