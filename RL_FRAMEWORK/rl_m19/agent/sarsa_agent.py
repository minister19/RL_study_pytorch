import numpy as np
import pandas as pd
import random
from itertools import count
from .base_agent import BaseAgent


class SarsaAgent(BaseAgent):
    def __init__(self, config):
        super().__init__(config)
        self.actions = range(self.config.actions_dim)
        self.q_table = pd.DataFrame(columns=self.actions, dtype=np.float32)
        self.select_action_counter = 0

    def __check_state_exist(self, state):
        if state not in self.q_table.index:
            # append new state to q table
            new_state_row = pd.Series(
                np.zeros(self.config.actions_dim),
                index=self.actions,
                name=state,
            )
            self.q_table = self.q_table.append(new_state_row)

    def select_action(self, state):
        # convert tensor to string, number
        state = self.tensor2str(state.cpu())

        # record unknown state
        self.__check_state_exist(state)

        sample = random.random()
        eps = self.eps_fn(self.select_action_counter)
        self.select_action_counter += 1
        if sample < eps:
            # some actions may have the same value, randomly choose on in these actions
            state_action = self.q_table.loc[state, :]
            best_actions = state_action[state_action == max(state_action)].index
            action = random.choice(best_actions)
        else:
            action = random.choice(self.actions)
        return action

    def learn(self, state, action, reward, next_state):
        # convert tensor to string, number
        state = self.tensor2str(state.cpu())
        real_reward = self.tensor2number(reward.cpu())
        if real_reward > 0:
            reward = 1
        elif real_reward == 0:
            reward = 0
        else:
            reward = -1
        next_state = self.tensor2str(next_state.cpu())

        # record unknown state
        self.__check_state_exist(next_state)

        q_predict = self.q_table.loc[state, action]
        if next_state != None:
            # next state is not terminal
            q_target = reward + self.config.GAMMA * self.q_table.loc[next_state, :].max()
        else:
            # next state is terminal
            q_target = reward
        self.q_table.loc[state, action] += self.config.LR * (q_target - q_predict)

    def episode_learn(self, i_episode):
        state = self.config.env.reset()

        for t in count():
            # self.config.env.render()

            # take action, observe
            action = self.select_action(state)
            next_state, reward, done, info = self.config.env.step(action)

            if done or t >= self.config.episode_lifespan:
                # print(self.q_table)
                self.config.env.render()
                self.episode_t.append(t)
                # self.config.plotter.plot_list_ndarray(self.episode_t)
                break
            else:
                # learn
                self.learn(state, action, reward, next_state)

                # update state
                state = next_state

    def episodes_learn(self):
        for i_episode in range(self.config.episodes):
            self.episode_learn(i_episode)