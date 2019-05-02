from pybrain.rl.agents.learning import LearningAgent

class MinecraftAgent(LearningAgent):
    """ LearningAgent has a module, a learner, that modifies the module, and an explorer,
        which perturbs the actions. It can have learning enabled or disabled and can be
        used continuously or with episodes.
    """
    def integrateObservation(self, obs):
        """Step 1: store the observation received in a temporary variable until action is called and
        reward is given. """
        self.lastobs = obs
        self.lastaction = None
        self.lastreward = None

    def giveReward(self, r):
        """Step 3: store observation, action and reward in the history dataset. """
        # step 3: assume that state and action have been set
        assert self.lastobs != None
        assert self.lastaction != None
        assert self.lastreward == None

        self.lastreward = r

        # store state, action and reward in dataset if logging is enabled
        if self.logging:
            self.history.addSample(self.lastobs, self.lastaction, self.lastreward)

    

    def getAction(self):
        """ Activate the module with the last observation, add the exploration from
            the explorer object and store the result as last action. """

        LearningAgent.getAction(self)

        self.lastaction = self.module.activate(self.lastobs)

        if self.learning:
            self.lastaction = self.learner.explore(self.lastobs, self.lastaction)

        return self.lastaction


    def reset(self):
        """ Clear the history of the agent and resets the module and learner. """
        LearningAgent.reset(self)
        self.module.reset()
        if self.learning:
            self.learner.reset()


  