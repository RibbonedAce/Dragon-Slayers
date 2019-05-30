try:
    from malmo import MalmoPython
except:
    import MalmoPython
import malmo.minecraftbootstrap

import os
import sys
import time
import json
import random
import math
import numpy as np
from matplotlib import pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures

class Mission():

    '''
    Example:
        example = Mission()
        mission = example.get_mission_xml()
        agent = example.one_agent_init()
        for i in range(50):
            example.load_solo_mission(mission, agent)
            example.chat_command_init()
                ...
                    ...
    '''
    def get_mission_xml(self, params):
        #implemented in children
        pass

    def chat_command_init(self, params):
        #implemented in children
        pass

    def one_agent_init(self):
        agent = MalmoPython.AgentHost()
        try:
            agent.parse( sys.argv )
        except RuntimeError as e:
            print('ERROR:',e)
            print(agent.getUsage())
            exit(1)
        if agent.receivedArgument("help"):
            print(agent.getUsage())
            exit(0)
        return agent

    def two_agent_init(self):
        # Create default Malmo objects:
        agent1 = MalmoPython.AgentHost()
        agent2 = MalmoPython.AgentHost()
        try:
            agent1.parse(sys.argv)
            agent2.parse(sys.argv)
        except RuntimeError as e:
            print('ERROR:',e)
            print(agent1.getUsage())
            print(agent2.getUsage())
            exit(1)
        if agent1.receivedArgument("help"):
            print(agent1.getUsage())
            exit(0)
        if agent2.receivedArgument("help"):
            print(agent2.getUsage())
            exit(0)
        return (agent1,agent2)

    def load_duo_mission(self, mission, agents):
        #agen
        mission_record = MalmoPython.MissionRecordSpec()
        mission.setViewpoint(0)
        # Attempt to start a mission:
        max_retries = 25
        #Quit out of currently running mission
        agents[0].sendCommand("quit")
        clients = MalmoPython.ClientPool()
        clients.add(MalmoPython.ClientInfo('127.0.0.1', 10001))
        clients.add(MalmoPython.ClientInfo('127.0.0.1', 10002))
            
        for retry in range(max_retries):
            try:
                agents[0].startMission( mission, clients, mission_record, 0, "")
                break
            except RuntimeError as e:
                print("Error starting mission", e)
                if retry == max_retries - 1:
                    exit(1)
                else:
                    time.sleep(2)

        for retry in range(max_retries):
            try:
                agents[1].startMission( mission, clients, mission_record, 1, "")
                break
            except RuntimeError as e:
                print("Error starting mission", e)
                if retry == max_retries - 1:
                    exit(1)
                else:
                    time.sleep(2)

        # Loop until mission starts:
        print("Waiting for the mission to start ")
        world_state = agents[0].getWorldState()
        while not world_state.has_mission_begun:
            #sys.stdout.write(".")
            time.sleep(0.1)
            world_state = agents[0].getWorldState()
            for error in world_state.errors:
                print("Error:",error.text)

        print()
        print("Mission running.")

    def load_solo_mission(self, mission, agent):
        mission_record = MalmoPython.MissionRecordSpec()
        mission.setViewpoint(0)
        

        clients = MalmoPython.ClientPool()
        clients.add(MalmoPython.ClientInfo('127.0.0.1', 10000)) # add Minecraft machines here as available
        #Quit from existing mission
        max_retries = 25
        #Quit out of currently running mission
        agent.sendCommand("quit")
        # Attempt to start a mission:
        for retry in range(max_retries):
            try:
                agent.startMission( mission, clients, mission_record, 0, "")
                break
            except RuntimeError as e:
                if retry == max_retries - 1:
                    print("Failed to start mission.")
                    exit(1)
                else:
                    time.sleep(2)

        # Loop until mission starts:
        print("Waiting for the mission to start ")
        world_state = agent.getWorldState()
        while not world_state.has_mission_begun:
            #sys.stdout.write(".")
            time.sleep(0.1)
            world_state = agent.getWorldState()
            for error in world_state.errors:
                print("Error:",error.text)

        print()
        print("Mission running.")


    def ai_step(self, move_agent):
        pass








