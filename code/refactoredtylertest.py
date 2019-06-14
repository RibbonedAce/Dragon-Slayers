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
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from Missions.staticflyingtarget import StaticFlyingTargetMission
from Missions.xstrafingtargetmission import XStrafingTargetMission
from Missions.simplifiedxstrafingmission import SimplifiedXStrafingMission
from Missions.enemymission import EnemyMission
from Missions.groundtargetmission import GroundTargetMission
from Missions.staticstandingtarget import StaticStandingTargetMission
from Missions.floatingtargetmission import FloatingTargetMission
from malmo_agent import MalmoAgent
from graphing import Graphing
from fileio import FileIO
from dataset import DataSet
from timekeeper import TimeKeeper
import pickle
import os.path

class Target():

    def __init__(self):
        self.transform = None
        self.id = None

def load_grid(agent):
    global world_state
    
    wait_time = 0
    keeper = TimeKeeper()
    while wait_time < 10:
        #sys.stdout.write(".")
        
        world_state = agent.getWorldState()
        if not world_state.is_mission_running:
            return None
        if len(world_state.errors) > 0:
            raise AssertionError('Could not load grid.')

        if world_state.number_of_observations_since_last_state > 0 and \
           json.loads(world_state.observations[-1].text):
            result = json.loads(world_state.observations[-1].text)
            result["time"] = time.time()
            return result

        keeper.advance_by(0.05)
        wait_time += 0.05

def find_mob_by_name(mobs, name, new=False):
    for m in mobs:
        if m["name"] == name:
            return m
    return None
def find_entity_by_id(entities, id):
    if id is None:
        return None
    for entity in entities:
        if entity["id"] == id:
            return entity

def sleep_until(desired_time):
    current_time = time.time()
    if current_time <= desired_time:
        time.sleep(desired_time - current_time)

def get_target(obs, target):
    #Get existing target
    new_transform = find_entity_by_id(obs["Mobs"],target.id)
    if new_transform is None:
        #Acquire new target
        target.transform = my_mission.get_target(obs["Mobs"])
        target.id = target.transform["id"] if (target.transform is not None) else None
    else:
        update_target_transform(target, new_transform)
        target.id = target.transform["id"]
    return target

def update_target_transform(target, transform):
    has_prev = "prevTime" in target.transform
    if has_prev:
        # Append past data
        target.transform["prevX"].append(target.transform["x"])
        if len(target.transform["prevX"]) > 4:
            target.transform["prevX"].pop(0)
        target.transform["prevY"].append(target.transform["y"])
        if len(target.transform["prevY"]) > 4:
            target.transform["prevY"].pop(0)
        target.transform["prevZ"].append(target.transform["z"])
        if len(target.transform["prevZ"]) > 4:
            target.transform["prevZ"].pop(0)
        target.transform["prevTime"].append(target.transform["time"])
        if len(target.transform["prevTime"]) > 4:
            target.transform["prevTime"].pop(0)
        
    else:
        # Create past data if none exists
        target.transform = {}
        target.transform["prevX"] = []
        target.transform["prevY"] = []
        target.transform["prevZ"] = []
        target.transform["prevTime"] = []

    # Apply stats not found in normal transforms
    old_transform = target.transform
    target.transform = transform
    target.transform["prevX"] = old_transform["prevX"]
    target.transform["prevY"] = old_transform["prevY"]
    target.transform["prevZ"] = old_transform["prevZ"]
    target.transform["prevTime"] = old_transform["prevTime"]
    target.transform["time"] = time.time()

    # Calculate velocity
    if has_prev:
        target.transform["motionX"] = (target.transform["x"] - target.transform["prevX"][0]) / (target.transform["time"] - target.transform["prevTime"][0])
        target.transform["motionY"] = (target.transform["y"] - target.transform["prevY"][0]) / (target.transform["time"] - target.transform["prevTime"][0])
        target.transform["motionZ"] = (target.transform["z"] - target.transform["prevZ"][0]) / (target.transform["time"] - target.transform["prevTime"][0])


# Launch the clients
malmo.minecraftbootstrap.launch_minecraft([10001, 10002])

# Create default Malmo objects:
graphing = True

mission_type = sys.argv[1] if len(sys.argv) > 1 else "enemymission"
my_mission = StaticFlyingTargetMission()
if mission_type.lower() == "enemymission":
    my_mission = EnemyMission()
elif mission_type.lower() == "staticflyingmission":
    my_mission = StaticFlyingTargetMission()
elif mission_type.lower() == "simplifiedxstrafingmission":
    my_mission = SimplifiedXStrafingMission()
elif mission_type.lower() == "groundtargetmission":
    my_mission = GroundTargetMission()
elif mission_type.lower() == "staticstandingmission":
    my_mission = StaticStandingTargetMission()
elif mission_type.lower() == "floatingtargetmission":
    my_mission = FloatingTargetMission()

agents = my_mission.two_agent_init()
iterations = 20
vert_step_size = 0.5
hori_step_size = 0.5

#Load model from file
data_set = FileIO.get_data_set()
shoot_agent = MalmoAgent("Slayer",agents[0],0,0,vert_step_size,hori_step_size, data_set)
move_agent = MalmoAgent("Mover",agents[1],0,0,vert_step_size,hori_step_size, data_set)

try:
    for i in range(iterations):
        time.sleep(1)
        params = (random.randint(30, 50)*random.randrange(-1, 2, 2), random.randint(30, 50)*random.randrange(-1, 2, 2), random.randint(10, 20))
        mission = MalmoPython.MissionSpec(my_mission.get_mission_xml(params), True)
        my_mission.load_duo_mission(mission, agents)
        shoot_agent.reset()
        shoot_agent.reset_shoot_loop()
        move_agent.reset()
        
        # Loop until mission ends:
        record_cycle = 86
        total_time = 0
        keeper = TimeKeeper()
        
        my_mission.chat_command_init(shoot_agent,move_agent,params)
        shoot_agent.agent.sendCommand("use 1")
        
        world_state = shoot_agent.agent.peekWorldState()
        shoot_agent.reset_shoot_loop()
        target = Target()
        first_target_found = False
        initial_delay = 5
        while world_state.is_mission_running:
            
            shooter_obs = load_grid(shoot_agent.agent)
            mover_obs = load_grid(move_agent.agent)
            if not shooter_obs or not mover_obs:
                break
            move_agent.step(mover_obs)
          
            #get target
            target = get_target(mover_obs, target)
            if target.transform is not None:
                first_target_found = True  
            if target.transform is None and first_target_found:
                #End mission early if no enemies remaining
                break

            #Run shooter ticks if target exists
            #agent step
            if initial_delay > 0:
                initial_delay -= 1
            else:
                if shoot_agent.shooter_step(shooter_obs, move_agent, target):
                    #Change mover direction
                    my_mission.ai_toggle(move_agent, target.transform)
            
            my_mission.ai_step(move_agent, target.transform)
        
            
            #If shoot agent hits target, end mission early
            if shoot_agent.end_mission:
                print("Ending mission early...")
                break
            keeper.advance_by(0.05)
            
        print()
        print("Mission ended")
            # Mission has ended.
except KeyboardInterrupt:
    shoot_agent.agent.sendCommand("quit")
    move_agent.agent.sendCommand("quit")
    pass
#Save dataset to file
FileIO.save_data("dataset",data_set)
# Graph results
if graphing:
    Graphing.FitData(data_set.hori_leading)
    Graphing.PredictionGraph([10,None,0], "Horizontal Aim Compensation", "x_velocity", "Degrees adjusted")
    Graphing.FitData(data_set.hori_shots)

    Graphing.FitData(data_set.vert_shots)
    Graphing.FitErrors(shoot_agent.vert_errors, shoot_agent.hori_errors)
    Graphing.DataGraph()
    Graphing.PredictionGraph([None, None], "Angle prediction", "Distance", "Elevation")
    Graphing.ErrorGraph()
    Graphing.AccuracyGraph()
