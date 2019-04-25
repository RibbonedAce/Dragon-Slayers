from pybrain.rl.learners.directsearch.enac import ENAC

class MineCraftENAC(ENAC):
    """ Episodic Natural Actor-Critic. See J. Peters "Natural Actor-Critic", 2005.
        Estimates natural gradient with regression of log likelihoods to rewards.
    """
    #Nothing to implement here either, I think
    """
    def learn(self):
         calls the gradient calculation function and executes a step in direction
            of the gradient, scaled with a small learning rate alpha. 
        assert self.dataset != None
        assert self.module != None

        # calculate the gradient with the specific function from subclass
        gradient = self.calculateGradient()

        # scale gradient if it has too large values
        if max(gradient) > 1000:
            gradient = gradient / max(gradient) * 1000

        # update the parameters of the module
        p = self.gd(gradient.flatten())
        self.network._setParameters(p)
        self.network.reset()

    def explore(self, state, action):
        # forward pass of exploration
        explorative = ExploringLearner.explore(self, state, action)

        # backward pass through network and store derivs
        self.network.backward()
        self.loglh.appendLinked(self.network.derivs.copy())

        return explorative



    """