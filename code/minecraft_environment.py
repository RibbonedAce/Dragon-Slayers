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
                  <FlatWorldGenerator></FlatWorldGenerator>
                  <DrawingDecorator>
                    <DrawSphere x="-27" y="70" z="0" radius="30" type="air"/>
                  </DrawingDecorator>
                  <ServerQuitFromTimeUp timeLimitMs="13000"/>
                  <ServerQuitWhenAnyAgentFinishes/>
                </ServerHandlers>
              </ServerSection>

              <AgentSection mode="Survival">
                <Name>CS175AwesomeMazeBot</Name>
                <AgentStart>
                    <Placement x="0.5" y="5.0" z="0.5" yaw="0"/>
                    <Inventory>
                        <InventoryItem slot="0" type="bow"/>
                        <InventoryItem slot="1" type="arrow" quantity="64"/>
                    </Inventory>
                </AgentStart>
                <AgentHandlers>
                    <ContinuousMovementCommands turnSpeedDegs="100"/>
                    <MissionQuitCommands/>
                    <ObservationFromNearbyEntities> 
                        <Range name="Mobs" xrange="1000" yrange="1" zrange="1000" update_frequency="1"/>
                    </ObservationFromNearbyEntities>
                    <ChatCommands/>
                </AgentHandlers>
              </AgentSection>
            </Mission>'''

#Observation reference--because I keep forgetting
'''
{'Mobs': [
    {'yaw': 0.0, 
    'x': 0.5, 
    'y': 56.0, 
    'z': 0.5, 
    'pitch': 0.0, 
    'id': '001683dc-7e7f-3a15-8fd2-b95a1c27a483', 
    'motionX': 0.0, 
    'motionY': -0.0784000015258789, 
    'motionZ': 0.0, 
    'life': 20.0, 
    'name': 'CS175AwesomeMazeBot'}, 

    {'yaw': 0.0, 
    'x': 0.5, 
    'y': 56.0, 
    'z': 50.5, 
    'pitch': 0.0, 
    'id': '48bf7eef-2d20-4c06-8d08-c2a4671e5565', 
    'motionX': 0.0, 
    'motionY': -0.07527135, 
    'motionZ': 0.0, 
    'life': 19.0, 
    'name': 'Zombie'}]}
'''
BOW_DAMAGE = 10
class MinecraftEnvironment(gym.Env):
    
    def __init__(self):
        self.valid_targets = {"Zombie", "Spider", "Skeleton", "Cow"}
        self.frame_width = 400
        self.frame_height = 250
        self.bow_charge_duration = 1.2
        self._action_set = [(-1, -1), (-1, 0), (-1, 1), (-0.5, -0.5), (-0.5, 0), (-0.5, 0.5),
              (-0.1, -0.1), (-0.1, 0), (-0.1, 0.1), (0, -1), (0, -0.5), (0, -0.1),
              (0, 0.1), (0, 0.5), (0, 1), (0.1, -0.1), (0.1, 0), (0.1, 0.1),
              (0.5, -0.5), (0.5, 0), (0.5, 0.5), (1, -1), (1, 0), (1, 1)]

        #action_space--[0,24] because number of actions
        self.action_space = spaces.Discrete(len(self._action_set))

        #observation space--frame width*frame height
        self.observation_space = spaces.Box(low=0, high=255, shape=(self.frame_height, self.frame_width, 3), dtype=np.uint8)
        #total reward during mission
        self.total_reward = 0
        #get reward obtained from the last time step() is called
        self.reward_since_last_obs = 0
        #self.seed()
        self.world_state = None
        self.last_mob_healths = {}
        self.time = time.time()
        self.shoot_timer = 0
        self.shot_count = 0
        #total elapsed time
        self.mission_time = 0

        #current episode index
        self.episode_index = 0

        #parse mission xml
        self.initialize_mission()
        #build client
        self.initialize_client()
        #build agent
        self.agent = self.initialize_agent()
        #self.reset()



   

    def step(self, action):
        '''
        Sets the agent's pitch and yaw rate values until step() is called again.
        Checks if any targets have lost HP since the last time this was called.
        Returns reward gained from the last time step() was called.
        +1 if enemy was damaged, 0 otherwise.
        Enemies shouldn't be losing health outside of player's arrows hitting them
        '''
        assert self.action_space.contains(action)

        self.world_state = self.agent.getWorldState()
        #get time since last step
        delta_time = int(round(time.time() * 1000)) - self.time

        #get pitch and yaw of new action
        pitch = self._action_set[action][0]
        yaw = self._action_set[action][1]
        #print("turn: " + str(yaw) + ", pitch: " + str(pitch))

        #set agent's turning rates
        self.agent.sendCommand("turn " + str(yaw))
        self.agent.sendCommand("pitch " + str(pitch))


        #calculate reward since last step()
        #self.world_sttate.num obs is frequently zero and it emptied whenever it isn't
        reward = 0
        if(self.world_state.number_of_observations_since_last_state > 0):
            self.obs = self.get_obs(self.world_state)
            mob_healths = self.get_mob_healths(self.obs,self.valid_targets)
            reward = self.calculate_reward(mob_healths,self.last_mob_healths)
            self.last_mob_healths = mob_healths

        #shoot loop
        self.shoot_timer += delta_time
        if(self.shoot_timer > 1.2*1000):
            #release RMB
            self.agent.sendCommand("use 0")
            self.shoot_timer = 0
            self.shot_count += 1
        else:
            #hold RMB
            self.agent.sendCommand("use 1")
        

        #update variables
        self.time = int(round(time.time() * 1000))
        self.mission_time += delta_time

        #Get screen pixels
        screen_frame = self.get_frame()
        assert screen_frame is not None
        #return observation (sceen data), reward of this step(), whether this episode is done, additional info
        return screen_frame, reward, self.shot_count > 5, {"enemies_hurt": reward}

    def reset(self):
        '''
        Loads a malmo mission to give a clean reset of the environment
        '''
        self.reward_since_last_obs = 0
        self.time = time.time()
        self.shoot_timer = 0
        self.last_mob_healths = {}
        self.mission_time = 0
        self.shot_count = 0



        self.initialize_mission()
        self.initialize_client()
        #Quit from existing mission
        self.agent.sendCommand("quit")
        max_retries = 3

        # Attempt to start a mission:
        for retry in range(max_retries):
            try:
                self.agent.startMission( self.mission, self.clients, self.mission_record, 0, "iteration " + str(self.episode_index))
                break
            except RuntimeError as e:
                if retry == max_retries - 1:
                    print("Failed to start mission.")
                    exit(1)
                else:
                    time.sleep(2)

        # Loop until mission starts:
        self.world_state = self.agent.getWorldState()
        while not self.world_state.has_mission_begun:
            #sys.stdout.write(".")
            time.sleep(0.1)
            self.world_state = self.agent.getWorldState()
            for error in self.world_state.errors:
                print("Error:",error.text)



        self.agent.sendCommand("chat /kill @e[type=!player]")
        time.sleep(0.5)
        self.agent.sendCommand("chat /summon cow ~0 ~0 ~3")
        self.agent.sendCommand("chat /summon cow ~0 ~0 ~-3")

        

        self.time = time.time()
        self.episode_index += 1

        screen_frame = self.get_frame()
        self.world_state = self.agent.getWorldState()
        assert screen_frame is not None

        return screen_frame

    def get_mob_healths(self, obs, valid_targets):
        '''
        Builds dict of <id, life> for enemies in valid_targets
        '''
        if(obs is None):
            return {}
        mob_health_dict = {}
        for entity in obs["Mobs"]:
            if entity["name"] in valid_targets and int(entity["life"] > 0):
                mob_health_dict[entity["id"]] = int(entity["life"])
        return mob_health_dict

    def calculate_reward(self, current_mob_healths, last_mob_healths):
        '''
            Reward = # of enemies damaged since last step(), or +1 per enemy hit
            This does not know which enemies were hit by bows--it tracks how many
            enemies were damaged since last step(), so any other damage sources
            will be falsely reported as arrow hits.
            We do not know how many times the enemy was hit since the last step, so an enemy being damaged twice in quick
            succession will only count as one hit.  This should not be a problem because we are shooting a fully charged bow.
        '''
        damaged_enemies = 0
        
        total_damage = 0 #this is not used, but it's a possible reward structure so might as well track it
        for id in last_mob_healths.keys():
            if id in current_mob_healths.keys() and current_mob_healths[id] < last_mob_healths[id]:
                #enemy is in both dicts and has less life now than last step()
                damaged_enemies += 1
                total_damage = last_mob_healths[id] - current_mob_healths[id]
            elif id not in current_mob_healths.keys() and last_mob_healths[id] <= BOW_DAMAGE:
                #enemy was present in last step(), but not in current step()
                #If they were one hit away from death, I assume they were killed by an arrow
                #This assumption should remain true 
                damaged_enemies += 1
        return damaged_enemies

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

    def initialize_mission(self):
        self.mission = MalmoPython.MissionSpec(GetMissionXML(), True)
        self.mission_record = MalmoPython.MissionRecordSpec()
        self.mission.requestVideo(self.frame_width, self.frame_height)
        self.mission.setViewpoint(0)
        

    def initialize_client(self):
        self.clients = MalmoPython.ClientPool()
        self.clients.add(MalmoPython.ClientInfo('127.0.0.1', 10000)) # add Minecraft machines here as available

    def get_obs(self,world_state):
        if len(world_state.errors) > 0:
            raise AssertionError('Could not load grid.')

        if world_state.number_of_observations_since_last_state > 0 and \
            json.loads(world_state.observations[-1].text):
            return json.loads(world_state.observations[-1].text)

    def render(self, img):
        from gym.envs.classic_control import rendering
        viewer = rendering.SimpleImageViewer()
        viewer.imshow(img)
        time.sleep(1)
        return viewer.isopen

    def get_frame(self):
        screen_frame = None
        #If, by some chance, there is no video frame available, wait until it is available
        #Returning null for observation is kind of a fatal error for dqn
        while(screen_frame is None):
            if self.world_state.number_of_video_frames_since_last_state > 0:
                time_stamped_frame = self.world_state.video_frames[-1]
                #Reshaped to the correct format for keras-rl
                screen_frame = np.reshape(time_stamped_frame.pixels,(time_stamped_frame.height,time_stamped_frame.width,time_stamped_frame.channels))
            else:
                #print("waiting for frame")
                time.sleep(0.1)
                self.world_state = self.agent.getWorldState()
        return screen_frame
    

if __name__ == "__main__":
    env = MinecraftEnvironment()
    env.reset()

    time.sleep(3)
    env.reset()













