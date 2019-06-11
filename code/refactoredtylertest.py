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
from malmo_agent import MalmoAgent
from graphing import Graphing
from fileio import FileIO
from dataset import DataSet
from timekeeper import TimeKeeper
import pickle
import os.path


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

# Launch the clients
malmo.minecraftbootstrap.launch_minecraft([10001, 10002])

# Create default Malmo objects:
graphing = False
my_mission = SimplifiedXStrafingMission()
agents = my_mission.two_agent_init()
iterations = 20
vert_step_size = 0.5
hori_step_size = 0.5

#Load model from file
model = FileIO.get_model()
data_set = FileIO.get_data_set()
shoot_agent = MalmoAgent("Slayer",agents[0],0,0,vert_step_size,hori_step_size,model, data_set)
move_agent = MalmoAgent("Mover",agents[1],0,0,vert_step_size,hori_step_size,None, None)

try:
    for i in range(iterations):
        time.sleep(1)
        params = (random.randint(10, 30)*random.randrange(-1, 2, 2), random.randint(10, 30)*random.randrange(-1, 2, 2), random.randint(10, 30))
        mission = MalmoPython.MissionSpec(my_mission.get_mission_xml(params), True)
        my_mission.load_duo_mission(mission, agents)
        shoot_agent.reset()
        move_agent.reset()
        
        # Loop until mission ends:
        record_cycle = 86
        total_time = 0
        keeper = TimeKeeper()
        
        my_mission.chat_command_init(shoot_agent,move_agent,params)
        shoot_agent.agent.sendCommand("use 1")
        
        world_state = shoot_agent.agent.peekWorldState()
        shoot_agent.reset_shoot_loop()
        target = None
        target_id = None
        while world_state.is_mission_running:
            shooter_obs = load_grid(shoot_agent.agent)
            mover_obs = load_grid(move_agent.agent)
            if not shooter_obs or not mover_obs:
                break
            move_agent.step(mover_obs)
           
            #get target
            if mover_obs is not None:
                target_transform = find_entity_by_id(mover_obs["Mobs"],target_id)
                if target_id is None or target_transform is None:
                    target_transform = my_mission.get_target(mover_obs["Mobs"])
                    if target_transform is not None:
                        target_id = target_transform["id"]

            #Run shooter ticks if target exists
            #agent step
            if shoot_agent.shooter_step(shooter_obs, move_agent, target_transform):
                #Change mover direction
                if not isinstance(my_mission,EnemyMission):
                    my_mission.ai_step(move_agent, target_transform)
            if isinstance(my_mission,EnemyMission):
                my_mission.ai_step(move_agent, target_transform)
        
            
            #If shoot agent hits target, end mission early
            if shoot_agent.end_mission:
                shoot_agent.reset_shoot_loop()
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
#Save model to file
FileIO.save_data("model",model)
FileIO.save_data("dataset",data_set)
# Graph results
if graphing:
    Graphing.FitData(data_set.hori_shots[0] + data_set.hori_shots[1])
    #Graphing.RegressionLine()
    Graphing.HorizontalDataGraph()
    Graphing.HorizontalPredictionGraph()
    Graphing.FitData(data_set.vert_shots[0] + data_set.vert_shots[1])
    Graphing.FitErrors(shoot_agent.vert_errors, shoot_agent.hori_errors)
    Graphing.DataGraph()
    Graphing.PredictionGraph()
    Graphing.ErrorGraph()
    Graphing.AccuracyGraph()
