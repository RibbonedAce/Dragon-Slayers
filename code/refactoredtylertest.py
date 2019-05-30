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
from malmo_agent import MalmoAgent
from graphing import Graphing

def load_grid(agent):
    global world_state
    
    wait_time = 0

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
            result["time"] = int(round(time.time() * 1000))
            return result

        time.sleep(0.05)
        wait_time += 0.05

def find_mob_by_name(mobs, name, new=False):
    for m in mobs:
        if m["name"] == name:
            return m
    return None

def sleep_until(desired_time):
    current_time = time.time()
    if current_time <= desired_time:
        time.sleep(desired_time - current_time)

# Launch the clients
malmo.minecraftbootstrap.launch_minecraft([10001, 10002])

# Create default Malmo objects:
my_mission = StaticFlyingTargetMission()
agents = my_mission.two_agent_init()
iterations = 5
for i in range(iterations):
    params = (random.randint(10, 50)*random.randrange(-1, 2, 2), random.randint(10, 30), random.randint(10, 50)*random.randrange(-1, 2, 2))
    mission = MalmoPython.MissionSpec(my_mission.get_mission_xml(params), True)
    my_mission.load_duo_mission(mission, agents)
    
    # Loop until mission ends:
    shoot_cycle = 50
    record_cycle = 86
    total_time = 0
    real_time = time.time()
    vert_step_size = 0.5
    hori_step_size = 0.5
    
    shoot_agent = MalmoAgent("Slayer",agents[0],0,0,vert_step_size,hori_step_size)
    move_agent = MalmoAgent("Mover",agents[1],0,0,vert_step_size,hori_step_size)
    my_mission.chat_command_init(shoot_agent,move_agent,params)
    
    world_state = shoot_agent.agent.peekWorldState()
    while world_state.is_mission_running:
        obs = load_grid(move_agent.agent)
        if not obs:
            break
        
        shoot_agent.step(obs)
        move_agent.step(obs)
        total_time += 1
        sleep_until(real_time + 0.05)
        real_time += 0.05

        if total_time >= shoot_cycle:
            shoot_cycle += 30
            shoot_agent.shoot_at_target(find_mob_by_name(obs["Mobs"],"Mover"))
            reward = shoot_agent.record_data(find_mob_by_name(obs["Mobs"],"Mover"))
            real_time = time.time()
            
    print()
    print("Mission ended")
    # Mission has ended.

# Graph results
Graphing.FitData(shoot_agent.vert_shots[0] + shoot_agent.vert_shots[1])
Graphing.FitErrors(shoot_agent.vert_errors, shoot_agent.hori_errors)
Graphing.DataGraph()
Graphing.PredictionGraph()
Graphing.ErrorGraph()
Graphing.AccuracyGraph()

