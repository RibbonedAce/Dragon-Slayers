from pybrain.rl.learners.valuebased.interface import ActionValueNetwork
from scipy import argmax, array, r_, asarray, where
import numpy as np
from random import choice

class MineCraftActionValueNetwork(ActionValueNetwork):
    """ A network that approximates action values for continuous state /
        discrete action RL environments. To receive the maximum action
        for a given state, a forward pass is executed for all discrete
        actions, and the maximal action is returned. This network is used
        for the NFQ algorithm. """
    def getMaxAction(self, state):
        """ Return the action with the maximal value for the given state. """
        print("GETMAXACTION")
        print("STATE: "+ str(state))
        actions = self.getActionValues(state)
        print("output of neural net: " + str(actions))
        max_index = argmax(actions)
        print("max action index: " + str(max_index))
        print("max action-value: " + str(np.amax(actions)))
        return argmax(actions)
    
    
    def getUnexploredAction(self,state,value=1.0,default=[0]):
        #state is environment
        '''
        Return an action with a value equal to the given one
        '''
        ''''
        values = self.params.reshape(self.numRows, self.numColumns)[int(state), :].flatten()
        action = where(values == value)[0]
        if default[0] in action or len(action) == 0:
            return default[0]
        
        action = choice(action)
        return action

        '''
        pass