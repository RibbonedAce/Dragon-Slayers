
from scipy import *
import sys, time
from pybrain.rl.environments.mazes import Maze, MDPMazeTask
from pybrain.rl.learners.valuebased import ActionValueTable
from pybrain.rl.agents import LearningAgent
from pybrain.rl.learners import Q, SARSA
from pybrain.rl.experiments import Experiment
from pybrain.rl.environments import Task
import pylab
import random
import matplotlib.pyplot as plt
import pickle
import os.path
import numpy as np

from agent import MinecraftAgent
from environment import MinecraftEnvironment
from controller import MineCraftENAC
from experiment import MinecraftExperiment
from task import MinecraftTask


def join_to_base_path(rel_path):
    try:
        base_path = sys._MEI
    except:
        base_path = os.path.abspath(".")
    return base_path

def load_params(file_name,action_value_table):
    #current_path = os.path.dirname(os.path.realpath(__file__))
    #file_path = os.path.join(current_path,file_name)
    file_path = join_to_base_path(file_name)
    if os.path.getsize(file_path) <= 0:
        return

    file = open(file_path,'rb')
    #controller._setParameters(pickle.load(file))
    #print("Loading: " + str(controller.params))
    
def save_params(file_name,action_value_table):
    #current_path = os.path.dirname(os.path.realpath(__file__))
    file_path = join_to_base_path(file_name)
    file = open(file_path,'wb')
    #pickle.dump(controller.params,file)
    #print("Saving: " + str(controller.params))

if __name__ == "__main__":
    pass
