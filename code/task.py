from pybrain.rl.environments.task import Task

class MinecraftTask(Task):

    def setScaling(self, sensor_limits, actor_limits):
        """ Expects scaling lists of 2-tuples - e.g. [(-3.14, 3.14), (0, 1), (-0.001, 0.001)] -
            one tuple per parameter, giving min and max for that parameter. The functions
            normalize and denormalize scale the parameters between -1 and 1 and vice versa.
            To disable this feature, use 'None'. """
        self.sensor_limits = sensor_limits
        self.actor_limits = actor_limits

    def performAction(self, action):
        """ A filtered mapping towards performAction of the underlying environment. """
        if self.actor_limits:
            action = self.denormalize(action)
        self.env.performAction(action)

    def getObservation(self):
        """ A filtered mapping to getSensors of the underlying environment. """
        sensors = self.env.getSensors()
        if self.sensor_limits:
            sensors = self.normalize(sensors)
        return sensors

    def getReward(self):
        """ Compute and return the current reward (i.e. corresponding to the last action performed) """
        #return abstractMethod()
        pass

   