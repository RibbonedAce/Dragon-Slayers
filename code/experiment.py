from pybrain.rl.experiments.episodic import EpisodicExperiment

class MinecraftExperiment(EpisodicExperiment):


    def doEpisodes(self, number = 1):
        """ Do one episode, and return the rewards of each step as a list. """
        if self.doOptimization:
            self.optimizer.maxEvaluations += number
            self.optimizer.learn()
        else:
            all_rewards = []
            for dummy in range(number):
                self.agent.newEpisode()
                rewards = []
                self.stepid = 0
                self.task.reset()
                while not self.task.isFinished():
                    r = self._oneInteraction()
                    rewards.append(r)
                all_rewards.append(rewards)

            return all_rewards
