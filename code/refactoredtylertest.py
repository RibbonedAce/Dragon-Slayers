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
from Missions.staticflyingtarget import StaticFlyingTargetMission
from malmo_agent import MalmoAgent

def load_grid(agent):
    global world_state
    
    wait_time = 0

    while wait_time < 10:
        #sys.stdout.write(".")
        time.sleep(0.05)
        wait_time += 0.05
        world_state = agent.getWorldState()
        if not world_state.is_mission_running:
            return None
        if len(world_state.errors) > 0:
            raise AssertionError('Could not load grid.')

        if world_state.number_of_observations_since_last_state > 0 and \
           json.loads(world_state.observations[-1].text):
            return json.loads(world_state.observations[-1].text)

def find_mob_by_name(mobs, name, new=False):
    for m in mobs:
        if m["name"] == name:
            return m
    return None

# Launch the clients
malmo.minecraftbootstrap.launch_minecraft([10001, 10002])

# Create default Malmo objects:
my_mission = StaticFlyingTargetMission()
agents = my_mission.two_agent_init()
iterations = 3
for i in range(iterations):
    params = (random.randint(10, 30)*random.randrange(-1, 2, 2), random.randint(10, 20), random.randint(10, 30)*random.randrange(-1, 2, 2))
    mission = my_mission.get_mission_xml(params)
    my_mission.load_duo_mission(mission,agents,params)
    my_mission.chat_command_init(agents[0],agents[1],params)
    
    # Loop until mission ends:
    shoot_cycle = 20
    record_cycle = 46
    total_time = 0
    vert_step_size = 0.5
    hori_step_size = 0.5
    

    shoot_agent = MalmoAgent("Slayer",agents[0],0,0,vert_step_size,hori_step_size)
    move_agent = MalmoAgent("Mover",agents[1],0,0,vert_step_size,hori_step_size)

    world_state = shoot_agent.peekWorldState()
    while world_state.is_mission_running:
        obs = load_grid(world_state)
        time.sleep(0.05)
        total_time += 1
        shoot_agent.step()
        move_agent.step()

        if total_time >= shoot_cycle:
            shoot_cycle += 30
            shoot_agent.shoot_at_target(find_mob_by_name(obs["Mobs"],"Mover"))

        if total_time >= record_cycle:
            record_cycle += 30
            reward = shoot_agent.record_data(find_mob_by_name(obs["Mobs"],"Mover"))

    print()
    print("Mission ended")
    # Mission has ended.


