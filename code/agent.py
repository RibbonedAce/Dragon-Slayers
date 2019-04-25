from pybrain.rl.agents.logging import LoggingAgent

class MinecraftAgent(LoggingAgent):

   

    def integrateObservation(self, obs):
        """Step 1: store the observation received in a temporary variable until action is called and
        reward is given. """
        self.lastobs = obs
        self.lastaction = None
        self.lastreward = None


    def getAction(self):
        """Step 2: store the action in a temporary variable until reward is given. """
        assert self.lastobs != None
        assert self.lastaction == None
        assert self.lastreward == None

        # implement getAction in subclass and set self.lastaction


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


    def newEpisode(self):
        """ Indicate the beginning of a new episode in the training cycle. """
        if self.logging:
            self.history.newSequence()


    def reset(self):
        """ Clear the history of the agent. """
        self.lastobs = None
        self.lastaction = None
        self.lastreward = None

        self.history.clear()