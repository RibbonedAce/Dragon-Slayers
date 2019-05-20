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

wall_length = 40
x_start = .5
y_start = 4
z_start = 20.5
mover_start = 0

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
                  <FlatWorldGenerator></FlatWorldGenerator>
                  <ServerQuitFromTimeUp timeLimitMs="180000"/>
                </ServerHandlers>
              </ServerSection>

              <AgentSection mode="Survival">
                <Name>Slayer</Name>
                <AgentStart>
                    <Placement x="0.5" y="4" z="0.5" yaw="0"/>
                    <Inventory>
                        <InventoryItem slot="0" type="bow"/>
                        <InventoryItem slot="1" type="arrow" quantity="64"/>
                    </Inventory>
                </AgentStart>
                <AgentHandlers>
                    <ContinuousMovementCommands turnSpeedDegs="900"/>
                    <InventoryCommands/>
                    <ObservationFromNearbyEntities> 
                        <Range name="Mobs" xrange="10000" yrange="1" zrange="10000" update_frequency="1"/>
                    </ObservationFromNearbyEntities>
                    <ChatCommands/>
                </AgentHandlers>
              </AgentSection>
              
              <AgentSection mode="Creative">
                <Name>Mover</Name>
                <AgentStart>
                    <Placement x="'''+str(x_start)+'''" y="'''+str(y_start)+'''" z="'''+str(z_start)+'''" yaw="180"/>
                    <Inventory>
                        '''+fill_inventory()+'''
                    </Inventory>
                </AgentStart>
                <AgentHandlers>
                    <ContinuousMovementCommands turnSpeedDegs="900"/>
                    <ObservationFromNearbyEntities> 
                        <Range name="Mobs" xrange="10000" yrange="10000" zrange="10000" update_frequency="1"/>
                    </ObservationFromNearbyEntities>
                    <ChatCommands/>
                </AgentHandlers>
              </AgentSection>
            </Mission>'''

def get_mission_randoms():
    return str(random.randrange(-40, 40)), str(random.randrange(-40, 40))

def generateWall():
    global mover_start

    # general wall specs for draw line
    length = wall_length
    half = length/2
    x1 = int(x_start - half)
    x2 = int(x_start + half -.5)
    z = int(z_start + 12)

    result = ""
    # create front wall
    for line_num in range(length):
        y = y_start + line_num
        z_bw = z+1 # z coordinate for the back wall
        result += "<DrawLine x1=\""+str(x1)+"\" y1=\""+str(y)+"\" z1=\""+str(z)+ \
                    "\" x2=\""+str(x2)+"\" y2=\""+str(y)+"\" z2=\""+str(z)+ \
                    "\" type=\"dirt\"/>\n"
        result += "<DrawLine x1=\""+str(x1)+"\" y1=\""+str(y)+"\" z1=\""+str(z_bw)+ \
                    "\" x2=\""+str(x2)+"\" y2=\""+str(y)+"\" z2=\""+str(z_bw)+ \
                    "\" type=\"dirt\"/>\n"

    # create random hole values for the target
    target_x = random.randint(x1+1,x2-1) # +1/-1 to keep from being on edge of wall
    target_y1 = random.randint(5,2+length) # 5/2+ to keep from being on edge of wall
    target_y2 = target_y1-1

    # block 1
    result += "<DrawLine x1=\""+str(target_x)+"\" y1=\""+str(target_y1)+"\" z1=\""+str(z)+ \
                    "\" x2=\""+str(target_x)+"\" y2=\""+str(target_y1)+"\" z2=\""+str(z)+ \
                    "\" type=\"air\"/>\n"
    # block 2
    result += "<DrawLine x1=\""+str(target_x)+"\" y1=\""+str(target_y2)+"\" z1=\""+str(z)+ \
                    "\" x2=\""+str(target_x)+"\" y2=\""+str(target_y2)+"\" z2=\""+str(z)+ \
                    "\" type=\"air\"/>\n"

    mover_start = "<Placement x=\""+str(target_x+.5)+"\" y=\""+str(target_y2)+"\" z=\""+str(z)+ \
                    "\" yaw=\"180\"/>"
    #print(result)
    return result

def fill_inventory():
    result = ""
    for i in range(36):
        result += "<InventoryItem slot=\"" + str(i) + "\" type=\"bow\" quantity=\"1\"/>\n"
    return result

def load_grid(agent, world_state):
    wait_time = 0

    while wait_time < 10:
        #sys.stdout.write(".")
        time.sleep(0.1)
        wait_time += 0.1
        world_state = agent.getWorldState()
        if len(world_state.errors) > 0:
            raise AssertionError('Could not load grid.')

        if world_state.number_of_observations_since_last_state > 0 and \
           json.loads(world_state.observations[-1].text):
            return json.loads(world_state.observations[-1].text)

def set_yaw_and_pitch(agent, yaw=None, pitch=None):
    if yaw == None and pitch == None:
        return
    
    i = 1
    total_sleep = 0
    
    while True:
        obs = load_grid(agent, world_state)
        stats = find_mob_by_name(obs["Mobs"], "Slayer")
        current_yaw = stats["yaw"]
        current_pitch = stats["pitch"]
        
        yaw_diff = 0
        if yaw != None:
            yaw_diff = yaw - current_yaw
        pitch_diff = 0
        if pitch != None:
            pitch_diff = pitch - current_pitch

        if (abs(yaw_diff) < 0.001 and abs(pitch_diff) < 0.001) or total_sleep > 5:
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
        sleep_time = min(3.0, max(yaw_sleep, pitch_sleep, 0.1))
        total_sleep += sleep_time
        
        agent.sendCommand("turn " + str(i * yaw_multiplier * yaw_sleep / sleep_time))
        agent.sendCommand("pitch " + str(i * pitch_multiplier * pitch_sleep / sleep_time))
        time.sleep(sleep_time)
        agent.sendCommand("turn 0")
        agent.sendCommand("pitch 0")
            
        i *= 0.2
        
    if (total_sleep < 1.3):
        time.sleep(1.3 - total_sleep)
    return max(1.3, total_sleep)

def find_mob_by_name(mobs, name, new=False):
    for m in mobs:
        if m["name"] == name:
            return m
    return None

def process_commands(time):
    remove = []
    for command in commands:
        if command[2] <= time:
            print(time, ":", command[1])
            remove.append(command)
            command[0].sendCommand(command[1])
    for command in remove:
        commands.remove(command)

def vert_distance(xtarget, ztarget, xsource=0, zsource=0):
    return ((xtarget - xsource)**2 + (ztarget - zsource)**2) ** 0.5
    
def get_hori_angle(xorigin, zorigin, xtarget, ztarget):
    return math.degrees(math.atan2(xorigin-xtarget, ztarget-zorigin))

def get_first_vert_shot(distance, elevation):
    array = np.asarray(vert_shots[0] + vert_shots[1])
    if array.shape[0] > 5:
        if elevation > distance:
            array = array[array[:,1] > array[:,0]]
        else:
            array = array[array[:,1] <= array[:,0]]
    if array.shape[0] > 5:
        poly = PolynomialFeatures(2).fit(array[:,0].reshape(-1, 1))
        predictor = LinearRegression().fit(np.concatenate((poly.transform(array[:,0].reshape(-1, 1)), array[:,1].reshape(-1, 1)), axis=1), array[:,-1])
        return min(predictor.predict(np.concatenate((poly.transform(np.asarray([[distance]])), np.asarray([[elevation]])), axis=1))[0], 89.9)
    
    lower_bound = 0
    lower_angle = 0
    upper_bound = 1000
    upper_angle = 90
    
    for i in range(array.shape[0]):
        ratio = array[i,0] / array[i,1]
        if ratio < distance / elevation and ratio > lower_bound:
            lower_bound = ratio
            lower_angle = array[i,-1]
        elif ratio > distance / elevation and ratio < upper_bound:
            upper_bound = ratio
            upper_angle = array[i,-1]

    interp = (distance / elevation - lower_bound) / (upper_bound - lower_bound)
    return lower_angle*(1-interp) + upper_angle*interp

def get_next_vert_shot(prev_angle, error, step_size):
    bound_angle = prev_angle    
    if error < 0:
        bound_angle = 90
    elif error > 0:
        bound_angle = 0
    return prev_angle*(1-step_size) + bound_angle*step_size

def get_first_hori_shot(angle):
    array = np.asarray(hori_shots[0] + hori_shots[1])
    if array.shape[0] > 5:
        predictor = LinearRegression().fit(array[:,0].reshape(-1, 1), array[:,1])
        return predictor.predict(np.asarray([[angle]]))[0]
    
    lower_angle = -179
    upper_angle = 179
    
    for i in range(array.shape[0]):
        if array[i,0] < angle and array[i,0] > lower_angle:
            lower_angle = array[i,1]
        elif array[i,0] > angle and array[i,0] < upper_angle:
            upper_angle = array[i,1]

    interp = (angle - lower_angle) / (upper_angle - lower_angle)
    return lower_angle*(1-interp) + upper_angle*interp

def get_next_hori_shot(prev_angle, error, step_size):
    bound_angle = prev_angle
    if error < 0:
        bound_angle = 179
    elif error > 0:
        bound_angle = -179
    return prev_angle*(1-step_size) + bound_angle*step_size

def shoot_at_target():
    global vert_angle
    global hori_angle
    global total_time
    global commands
    global distance
    global elevation
    global obs_angle
    global mover_pos
    global mover_life
    global vert_step_size
    global hori_step_size
    
    last_obs = load_grid(move_agent, world_state)
    player_loc = find_mob_by_name(last_obs["Mobs"], "Slayer")
    target_loc = find_mob_by_name(last_obs["Mobs"], "Mover")
    distance = vert_distance(target_loc["x"], target_loc["z"], player_loc["x"], player_loc["z"])
    elevation = target_loc["y"] - player_loc["y"]
    obs_angle = get_hori_angle(player_loc["x"], player_loc["z"], target_loc["x"], target_loc["z"])
    vert_angle = 0
    hori_angle = 0
    mover_pos = [target_loc["x"], target_loc["z"]]
    mover_life = target_loc["life"]
    
    if total_time < 1 or len(vert_shots[0] + vert_shots[1]) > 5:
        vert_angle = get_first_vert_shot(distance, elevation)
    else:
        vert_angle = get_next_vert_shot(vert_angle, vert_error, vert_step_size)
        vert_step_size *= 0.8
        
    if total_time < 1 or len(hori_shots[0] + hori_shots[1]) > 5:
        hori_angle = get_first_hori_shot(obs_angle)
    else:
        hori_angle = get_next_hori_shot(hori_angle, hori_error, hori_step_size)
        hori_step_size *= 0.8
        
    set_yaw_and_pitch(shoot_agent, hori_angle, -vert_angle)
    commands.append((shoot_agent, "use 1", total_time + 0))
    commands.append((shoot_agent, "use 0", total_time + 13))

def record_data(record_time):
    global vert_error
    global hori_error
    global total_time
    global commands
    global mover_pos
    global mover_life
    
    curr_time = 0
    data = []
    while curr_time < record_time:
        curr_time += 0.1
        time.sleep(0.1)
        last_obs = load_grid(move_agent, world_state)
        arrow = find_mob_by_name(last_obs["Mobs"], "Arrow")
        if arrow and (len(data) == 0 or (arrow["x"], arrow["y"], arrow["z"]) != data[-1]):
            data.append((arrow["x"], arrow["y"], arrow["z"]))

    print(data)
    commands.append((shoot_agent, "chat /kill @e[type=!player]", total_time + 0))
    return -((vert_error**2 + hori_error**2)**0.5)

vert_shots = [[], []]
hori_shots = [[], []]

# Launch the clients
malmo.minecraftbootstrap.launch_minecraft([10001, 10002])

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

iterations = 3
for i in range(iterations):
    my_mission = MalmoPython.MissionSpec(GetMissionXML(), True)
    my_mission_record = MalmoPython.MissionRecordSpec()
    my_mission.setViewpoint(0)
    # Attempt to start a mission:
    max_retries = 25
    my_clients = MalmoPython.ClientPool()
    my_clients.add(MalmoPython.ClientInfo('127.0.0.1', 10001))
    my_clients.add(MalmoPython.ClientInfo('127.0.0.1', 10002))
    
    commands = []
    
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
    world_state = shoot_agent.getWorldState()
    while not world_state.has_mission_begun:
        #sys.stdout.write(".")
        time.sleep(0.1)
        world_state = shoot_agent.getWorldState()
        for error in world_state.errors:
            print("Error:",error.text)

    print()
    print("Mission running.")

    commands.append((shoot_agent, "chat /kill @e[type=!player]", 0))
    commands.append((shoot_agent, "hotbar.1 1", 0))
    commands.append((shoot_agent, "hotbar.1 0", 0))
    commands.append((move_agent, "chat /gamemode 3", 0))
    commands.append((move_agent, "jump 1", 0))
    commands.append((move_agent, "jump 0", 10))
    commands.append((move_agent, "chat /gamemode 1", 10))

    #for i in range(0,10,2):
        #commands.append((move_agent, "strafe 1", i))
        #commands.append((move_agent, "strafe -1", i+1))

    # Loop until mission ends:
    shoot_cycle = 20
    record_cycle = 33
    total_time = 0
    vert_step_size = 1
    hori_step_size = 1
    vert_error = 0
    hori_error = 0
    distance = 0
    elevation = 0
    obs_angle = 0
    mover_pos = [0, 0]
    mover_life = 10
    while world_state.is_mission_running:
        #sys.stdout.write(".")
        time.sleep(0.1)
        total_time += 1
        process_commands(total_time)

        if total_time >= shoot_cycle:
            shoot_cycle += 14
            shoot_at_target()

        if total_time >= record_cycle:
            record_cycle += 14
            reward = record_data(5)

        world_state = shoot_agent.getWorldState()

    print()
    print("Mission ended")
    # Mission has ended.

'''good_array = np.asarray(shots[0])
bad_array = np.asarray(shots[1])
total_array = np.asarray(shots[0] + shots[1])
poly = PolynomialFeatures(2, include_bias=False).fit(total_array[:,0].reshape(-1, 1))
predictor = LinearRegression().fit(poly.transform(total_array[:,0].reshape(-1, 1)), total_array[:,1])
x = np.linspace(0, total_array[:,0].max(), 1000).reshape(-1, 1)
plt.plot(x, predictor.predict(poly.transform(x)))
plt.scatter(good_array[:,0], good_array[:,1], c="g")
plt.scatter(bad_array[:,0], bad_array[:,1], c="r")
plt.show()'''
