try:
    from malmo import MalmoPython
except:
    import MalmoPython
import numpy as np

import os
import sys
import gym
from gym import spaces
import time
import json
from gym.utils import seeding
def GetMissionXML():
    return '''<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
            <Mission xmlns="http://ProjectMalmo.microsoft.com" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">

              <About>
                <Summary>Hello world!</Summary>
              </About>

            <ServerSection>
              <ServerInitialConditions>
                <Time>
                    <StartTime>1000</StartTime>
                    <AllowPassageOfTime>false</AllowPassageOfTime>
                </Time>
                <Weather>clear</Weather>
              </ServerInitialConditions>
              <ServerHandlers>
                  <FlatWorldGenerator generatorString="3;7,44*49,73,35:1,159:4,95:13,35:13,159:11,95:10,159:14,159:6,35:6,95:6;12;"/>
                  <DrawingDecorator>
                    <DrawSphere x="-27" y="70" z="0" radius="30" type="air"/>
                  </DrawingDecorator>
                  <ServerQuitFromTimeUp timeLimitMs="60000"/>
                  <ServerQuitWhenAnyAgentFinishes/>
                </ServerHandlers>
              </ServerSection>

              <AgentSection mode="Survival">
                <Name>CS175AwesomeMazeBot</Name>
                <AgentStart>
                    <Placement x="0.5" y="56.0" z="0.5" yaw="0"/>
                    <Inventory>
                        <InventoryItem slot="0" type="bow"/>
                        <InventoryItem slot="1" type="arrow" quantity="64"/>
                    </Inventory>
                </AgentStart>
                <AgentHandlers>
                    <ContinuousMovementCommands turnSpeedDegs="900"/>
                    <AgentQuitFromTouchingBlockType>
                        <Block type="redstone_block"/>
                    </AgentQuitFromTouchingBlockType>
                    <ObservationFromNearbyEntities> 
                        <Range name="Mobs" xrange="1000" yrange="1" zrange="1000" update_frequency="1"/>
                    </ObservationFromNearbyEntities>
                    <ChatCommands/>
                </AgentHandlers>
              </AgentSection>
            </Mission>'''

def load_grid(world_state):
    while world_state.is_mission_running:
        #sys.stdout.write(".")
        time.sleep(0.1)
        world_state = agent_host.getWorldState()
        if len(world_state.errors) > 0:
            raise AssertionError('Could not load grid.')

        if world_state.number_of_observations_since_last_state > 0:
            return json.loads(world_state.observations[-1].text)

class MinecraftEnvironment(gym.Env):
    """Hotter Colder
    The goal of hotter colder is to guess closer to a randomly selected number
    After each step the agent receives an observation of:
    0 - No guess yet submitted (only after reset)
    1 - Guess is lower than the target
    2 - Guess is equal to the target
    3 - Guess is higher than the target
    The rewards is calculated as:
    (min(action, self.number) + self.range) / (max(action, self.number) + self.range)
    Ideally an agent will be able to recognise the 'scent' of a higher reward and
    increase the rate in which is guesses in that direction until the reward reaches
    its maximum
    """
    
    def __init__(self):
        self.frame_width = 800
        self.frame_height = 500
        self.bow_charge_duration = 1.2
        self.agent = self.initialize_agent()
        self._action_set = [(-1, -1), (-1, 0), (-1, 1), (-0.5, -0.5), (-0.5, 0), (-0.5, 0.5),
              (-0.1, -0.1), (-0.1, 0), (-0.1, 0.1), (0, -1), (0, -0.5), (0, -0.1),
              (0, 0.1), (0, 0.5), (0, 1), (0.1, -0.1), (0.1, 0), (0.1, 0.1),
              (0.5, -0.5), (0.5, 0), (0.5, 0.5), (1, -1), (1, 0), (1, 1)]

        self.action_space = spaces.Discrete(len(self._action_set))

        self.observation_space = spaces.Discrete(4)
        self.total_reward = 0
        self.reward_since_last_obs = 0
        #self.seed()
        self.obs = None
        self.time = time.time()
        self.shoot_timer = 0
        self.reset()


   

    def step(self, action):
        print("step")
        assert self.action_space.contains(action)
        self.obs = self.agent.getWorldState()

        #get time since last step
        self.delta_time = int(round(time.time() * 1000)) - self.time

        #get pitch and yaw of new action
        pitch = self._action_set[action][0]
        yaw = self._action_set[action][1]
        print("turn: " + str(yaw) + ", pitch: " + str(pitch))

        #set agent's turning rates
        self.agent.sendCommand("turn " + str(yaw))
        self.agent.sendCommand("pitch " + str(pitch))
        
        #get reward since last frame
        #reward = ((min(action, self.number) + self.bounds) / (max(action, self.number) + self.bounds)) ** 2


        #shoot loop
        self.shoot_timer += self.delta_time
        if(self.shoot_timer > 1.2*1000):
            #release RMB
            self.agent.sendCommand("use 0")
            self.shoot_timer = 0
        else:
            #hold RMB
            self.agent.sendCommand("use 1")
        

        #update current time
        self.time = int(round(time.time() * 1000))

        #return reward since last step
        return None

    def reset(self):
        


        my_mission = MalmoPython.MissionSpec(GetMissionXML(), True)
        my_mission_record = MalmoPython.MissionRecordSpec()
        my_mission.requestVideo(self.frame_width, self.frame_height)
        my_mission.setViewpoint(1)
        # Attempt to start a mission:
        max_retries = 3
        my_clients = MalmoPython.ClientPool()
        my_clients.add(MalmoPython.ClientInfo('127.0.0.1', 10000)) # add Minecraft machines here as available

        print("Starting mission...")
        for retry in range(max_retries):
            try:
                self.agent.startMission( my_mission, my_clients, my_mission_record, 0, "")
                break
            except RuntimeError as e:
                if retry == max_retries - 1:
                    exit(1)
                else:
                    time.sleep(2)

        # Loop until mission starts:
        self.obs = self.agent.getWorldState()
        print("Waiting for mission to start")
        while not self.obs.has_mission_begun:
            #sys.stdout.write(".")
            time.sleep(0.1)
            self.obs = self.agent.getWorldState()
            for error in self.obs.errors:
                print("Error:",error.text)



        self.agent.sendCommand("chat /kill @e[type=!player]")
        self.agent.sendCommand("chat /summon zombie ~0 ~0 ~50")
        
        #arrow = find_mob_by_name(last_obs["Mobs"], "Arrow")
        #mob = find_mob_by_name(last_obs["Mobs"], "Zombie")
        #print("Distance:", (abs(arrow["x"] - mob["x"]) ** 2 + abs(arrow["z"] - mob["z"] ** 2)) ** 0.5)

        # Loop until mission ends:
        
        # Mission has ended.






        print("reset ended")
        return self.obs

    def initialize_agent(self):
        agent_host = MalmoPython.AgentHost()
        try:
            agent_host.parse( sys.argv )
        except RuntimeError as e:
            print('ERROR:',e)
            print(agent_host.getUsage())
            exit(1)
        if agent_host.receivedArgument("help"):
            print(agent_host.getUsage())
            exit(0)
        return agent_host

    

if __name__ == "__main__":
    env = MinecraftEnvironment()

    while(True):
        time.sleep(1)
        env.step(9)













