
from scipy import *
import sys, time
from pybrain.rl.environments.mazes import Maze, MDPMazeTask
from pybrain.rl.learners.valuebased import ActionValueTable
from pybrain.rl.agents import LearningAgent
from pybrain.rl.learners import NFQ
from pybrain.rl.experiments import Experiment
from pybrain.rl.environments import Task
import random
import matplotlib.pyplot as plt
import pickle
import os.path
import numpy as np

from agent import MinecraftAgent
from environment import MinecraftEnvironment
from controller import MineCraftActionValueNetwork
from experiment import MinecraftExperiment
from task import MinecraftTask


OUTPUTFILE = "TrainedAIParams"
SAVE = True
LOAD = True
DISPLAY_NETWORK_OUTPUT = True
NUM_INPUTS = 2
NUM_OUTPUTS = 21

def join_to_base_path(rel_path):
    try:
        base_path = sys._MEI
    except:
        base_path = os.path.abspath(".")
    return base_path

def load_params(file_name,network):
    current_path = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(current_path,file_name)
    print("Loading AI neural network from: " + file_path)
    if os.path.getsize(file_path) <= 0:
        return
    file = open(file_path,'r')
    net = pickle.load(file)
    
def save_params(file_name,network):
    current_path = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(current_path,file_name)
    print("Saving AI neural network to: " + file_path)
    file = open(file_path,'w')
    pickle.dump(network, file)



if __name__ == "__main__":
    environment = MinecraftEnvironment()
    controller = MineCraftActionValueNetwork(NUM_INPUTS,NUM_OUTPUTS)
    learner = NFQ()
    agent = MinecraftAgent(controller, learner)
    task = MinecraftTask(environment)
    experiment = MinecraftExperiment(task, agent)
    num_episodes = 1000
    i = 0
    try:
        if LOAD:
            load_params(OUTPUTFILE,controller)
                
        while i < num_episodes:
            experiment.doInteractions(1)
            i += 1
            agent.learn()

    except KeyboardInterrupt:
        pass

    if SAVE:
        save_params(OUTPUTFILE,controller)

    
