from pybrain.rl.environments.environment import Environment
try:
    from malmo import MalmoPython
except:
    import MalmoPython

import os
import sys
import time
import json
import random
import math

def GetMissionXML():
    params = get_mission_randoms()
    
    return '''<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
            <Mission xmlns="http://ProjectMalmo.microsoft.com" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">

            <About>
                <Summary>Shoot the Target</Summary>
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
                <FlatWorldGenerator/>
                <ServerQuitFromTimeUp timeLimitMs="180000"/>
                </ServerHandlers>
            </ServerSection>

            <AgentSection mode="Survival">
                <Name>Slayer</Name>
                <AgentStart>
                    <Placement x="0.5" y="4.0" z="0.5" yaw="0"/>
                    <Inventory>
                        <InventoryItem slot="0" type="bow"/>
                        <InventoryItem slot="1" type="arrow" quantity="64"/>
                    </Inventory>
                </AgentStart>
                <AgentHandlers>
                    <ContinuousMovementCommands turnSpeedDegs="900"/>
                    <ObservationFromNearbyEntities> 
                        <Range name="Mobs" xrange="10000" yrange="1" zrange="10000" update_frequency="1"/>
                    </ObservationFromNearbyEntities>
                    <ChatCommands/>
                </AgentHandlers>
            </AgentSection>
            
            <AgentSection mode="Survival">
                <Name>Mover</Name>
                <AgentStart>
                    <Placement x="0.5" y="4.0" z="'''+params[1]+'''" yaw="180"/>
                    <Inventory>
                        '''+fill_inventory()+'''
                    </Inventory>
                </AgentStart>
                <AgentHandlers>
                    <ContinuousMovementCommands turnSpeedDegs="900"/>
                    <ObservationFromNearbyEntities> 
                        <Range name="Mobs" xrange="10000" yrange="1" zrange="10000" update_frequency="1"/>
                    </ObservationFromNearbyEntities>
                    <ChatCommands/>
                </AgentHandlers>
            </AgentSection>
            </Mission>'''

def get_mission_randoms():
    return str(random.randrange(-20, 20)), str(random.randrange(10, 20))

def fill_inventory():
    result = ""
    for i in range(36):
        result += "<InventoryItem slot=\"" + str(i) + "\" type=\"bow\" quantity=\"1\"/>\n"
    return result

def load_grid(agent, world_state):
    while world_state.is_mission_running:
        #sys.stdout.write(".")
        time.sleep(0.1)
        world_state = agent.getWorldState()
        if len(world_state.errors) > 0:
            raise AssertionError('Could not load grid.')

        if world_state.number_of_observations_since_last_state > 0:
            return json.loads(world_state.observations[-1].text)


class MinecraftEnvironment(Environment):
    shoot_cycle = 0
    record_cycle = 10
    total_time = 0
    step_size = 1
    error = 0
    angle = 0
    reward = 0
    distance = 0
    directions = [(-1, -1), (-1, 0), (-1, 1), (-0.5, -0.5), (-0.5, 0), (-0.5, 0.5),
                    (-0.1, -0.1), (-0.1, 0), (-0.1, 0.1), (0, -1), (0, -0.5), (0, -0.1),
                    (0, 0.1), (0, 0.5), (0, 1), (0.1, -0.1), (0.1, 0), (0.1, 0.1),
                    (0.5, -0.5), (0.5, 0), (0.5, 0.5), (1, -1), (1, 0), (1, 1)]

    commands = []
    good_shots = {}
    world_state = None
    shoot_agent = None
    move_agent = None
    loop_interval = 0.1

    def __init__(self,record_delay=5):
        self.record_cycle = record_delay
        
    def set_yaw_and_pitch(self,agent, yaw=None, pitch=None):
        if yaw == None and pitch == None:
            return
        
        i = 1
        total_sleep = 0
        
        while True:
            obs = load_grid(agent, self.world_state)
            stats = self.find_mob_by_name(obs["Mobs"], "Slayer")
            current_yaw = stats["yaw"]
            current_pitch = stats["pitch"]
            
            yaw_diff = 0
            if yaw != None:
                yaw_diff = yaw - current_yaw
            pitch_diff = 0
            if pitch != None:
                pitch_diff = pitch - current_pitch

            if abs(yaw_diff) < 0.001 and abs(pitch_diff) < 0.001:
                break
                
            yaw_multiplier = 1
            pitch_multiplier = 1
            if yaw_diff > 180:
                yaw_diff = yaw_diff - 360
            if yaw_diff < 0:
                yaw_multiplier = -1
            if pitch_diff < 0:
                pitch_multiplier = -1
                
            yaw_sleep = abs(yaw_diff) / (i * 900)
            pitch_sleep = abs(pitch_diff) / (i * 900)
            sleep_time = max(yaw_sleep, pitch_sleep)
            total_sleep += sleep_time
            
            agent.sendCommand("turn " + str(i * yaw_multiplier * yaw_sleep / sleep_time))
            agent.sendCommand("pitch " + str(i * pitch_multiplier * pitch_sleep / sleep_time))
            time.sleep(sleep_time)
            agent.sendCommand("turn 0")
            agent.sendCommand("pitch 0")
                
            i *= 0.2
            
        if (total_sleep < 1.2):
            time.sleep(1.2 - total_sleep)
        return max(1.2, total_sleep)

    def find_mob_by_name(self,mobs, name, new=False):
        for m in mobs:
            if m["name"] == name:
                return m
        return None

    def process_commands(self,time):
        for command in self.commands:
            if command[2] <= time:
                self.commands.remove(command)
                command[0].sendCommand(command[1])

    def look_angle(self,xorigin, zorigin, xtarget, ztarget):
        return math.degrees(math.atan2(xorigin-xtarget, ztarget-zorigin))

    def get_first_shot(self,distance):
        lower_bound = 0
        lower_angle = 0
        upper_bound = 1000
        upper_angle = 45
        
        for key in self.good_shots.keys():
            if key < distance and key > lower_bound:
                lower_bound = key
                lower_angle = self.good_shots[key]
            elif key > distance and key < upper_bound:
                upper_bound = key
                upper_angle = self.good_shots[key]

        interp = (distance - lower_bound) / (upper_bound - lower_bound)
        return lower_angle*(1-interp) + upper_angle*interp

    def get_next_shot(self,prev_angle, error, step_size):
        bound_angle = prev_angle
        
        if error < 0:
            bound_angle = 45
            for value in self.good_shots.values():
                if value > prev_angle and value < bound_angle:
                    bound_angle = value
            
        elif error > 0:
            bound_angle = 0
            for value in self.good_shots.values():
                if value < prev_angle and value > bound_angle:
                    bound_angle = value

        return prev_angle*(1-step_size) + bound_angle*step_size

    def shoot_at_target(self):
       
        
        last_obs = load_grid(self.move_agent, self.world_state)
        last_angle = self.angle
        player_loc = self.find_mob_by_name(last_obs["Mobs"], "Slayer")
        target_loc = self.find_mob_by_name(last_obs["Mobs"], "Mover")
        self.distance = (abs(player_loc["x"] - target_loc["x"]) ** 2 + abs(player_loc["z"] - target_loc["z"] ** 2)) ** 0.5
        angle = 0
        if self.total_time < 1:
            angle = self.get_first_shot(self.distance)
        else:
            angle = self.get_next_shot(last_angle, self.error, self.step_size)
        self.total_time += self.set_yaw_and_pitch(self.shoot_agent, None, -angle)
        self.commands.append((self.shoot_agent, "use 1", self.total_time + 0))
        self.commands.append((self.shoot_agent, "use 0", self.total_time + 1.2))


    def record_data(self):
   
        
        #last_obs = load_grid(shoot_agent, world_state)
        #player = find_mob_by_name(last_obs["Mobs"], "Slayer")
        #target = find_mob_by_name(last_obs["Mobs"], "Mover")
        #angle = look_angle(player["x"], player["z"], target["x"], target["z"])
        #set_yaw_and_pitch(shoot_agent, angle, None)

        last_obs = load_grid(self.move_agent, self.world_state)
        error = 0
        arrow = self.find_mob_by_name(last_obs["Mobs"], "Arrow")
        target_loc = self.find_mob_by_name(last_obs["Mobs"], "Mover")
        if not arrow:
            if self.find_mob_by_name(last_obs["Mobs"], "Mover")["life"] < 20:
                self.good_shots[self.distance] = self.angle
            else:
                error = 100
        else:
            error = arrow["z"] - target_loc["z"]
        print("Error:", error)
        self.commands.append((self.shoot_agent, "chat /kill @e[type=!player]", self.total_time + 0))
        self.step_size *= 0.8

        if error == 0:
            return 100
        else:
            return -abs(error)
    def getSensors(self):
        """ the currently visible state of the world (the observation may be
            stochastic - repeated calls returning different values)

            :rtype: by default, this is assumed to be a numpy array of doubles
            :note: This function is abstract and has to be implemented.
        """
        return [1,1]

    def currentReward(self):
        return self.reward

    def performAction(self, action):
        """ perform an action on the world that changes it's internal state (maybe
            stochastically).
            :key action: an action that should be executed in the Environment.
            :type action: by default, this is assumed to be a numpy array of doubles
            :note: This function is abstract and has to be implemented.
        """
       
        return self.reward

    def set_look_velocity(self, velocity):
        self.shoot_agent.sendCommand("pitch " + str(velocity[0]))
        self.shoot_agent.sendCommand("yaw " + str(velocity[1]))

    def run(self):

        # Create default Malmo objects:
        shoot_agent = MalmoPython.AgentHost()
        move_agent = MalmoPython.AgentHost()
        try:
            shoot_agent.parse(sys.argv)
            move_agent.parse(sys.argv)
        except RuntimeError as e:
            print('ERROR:',e)
            print(shoot_agent.getUsage())
            print(move_agent.getUsage())
            exit(1)
        if shoot_agent.receivedArgument("help"):
            print(shoot_agent.getUsage())
            exit(0)
        if move_agent.receivedArgument("help"):
            print(move_agent.getUsage())
            exit(0)

        my_mission = MalmoPython.MissionSpec(GetMissionXML(), True)
        my_mission_record = MalmoPython.MissionRecordSpec()
        my_mission.setViewpoint(0)
        # Attempt to start a mission:
        max_retries = 3
        my_clients = MalmoPython.ClientPool()
        my_clients.add(MalmoPython.ClientInfo('127.0.0.1', 10001))
        my_clients.add(MalmoPython.ClientInfo('127.0.0.1', 10002))

        

        for retry in range(max_retries):
            try:
                shoot_agent.startMission( my_mission, my_clients, my_mission_record, 0, "")
                break
            except RuntimeError as e:
                print("Error starting mission", e)
                if retry == max_retries - 1:
                    exit(1)
                else:
                    time.sleep(2)

        for retry in range(max_retries):
            try:
                move_agent.startMission( my_mission, my_clients, my_mission_record, 1, "")
                break
            except RuntimeError as e:
                print("Error starting mission", e)
                if retry == max_retries - 1:
                    exit(1)
                else:
                    time.sleep(2)

        # Loop until mission starts:
        print("Waiting for the mission to start ")
        self.world_state = shoot_agent.getWorldState()
        while not self.world_state.has_mission_begun:
            #sys.stdout.write(".")
            time.sleep(0.1)
            world_state = shoot_agent.getWorldState()
            for error in world_state.errors:
                print("Error:",error.text)

        print()
        print("Mission running.")

        self.commands.append((shoot_agent, "chat /kill @e[type=!player]", 0))
        self.commands.append((shoot_agent, "hotbar.1 1", 0))
        self.commands.append((shoot_agent, "hotbar.1 0", 0))

    def step(self):

        #for i in range(0,10,2):
            #commands.append((move_agent, "strafe 1", i))
            #commands.append((move_agent, "strafe -1", i+1))

        # Loop until mission ends:

        if self.world_state.is_mission_running:
            #sys.stdout.write(".")
            time.sleep(self.loop_interval)
            self.total_time += self.loop_interval
            self.process_commands(self.total_time)

            if self.total_time >= self.shoot_cycle:
                self.shoot_cycle += 11.2
                self.shoot_at_target()

            if self.total_time >= self.record_cycle:
                self.record_cycle += 11.2
                self.reward = self.record_data()
        else:
            print()
            print("Mission ended")
        # Mission has ended


    