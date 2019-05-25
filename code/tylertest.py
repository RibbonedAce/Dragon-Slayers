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

def GetMissionXML():
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
                  <ServerQuitFromTimeUp timeLimitMs="60000"/>
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
                    <ObservationFromNearbyEntities> 
                        <Range name="Mobs" xrange="10000" yrange="1" zrange="10000" update_frequency="1"/>
                    </ObservationFromNearbyEntities>
                    <ChatCommands/>
                    <InventoryCommands/>
                </AgentHandlers>
              </AgentSection>
              
              <AgentSection mode="Survival">
                <Name>Mover</Name>
                <AgentStart>
                    <Placement x="'''+str(params[0])+'''" y="4" z="'''+str(params[2])+'''" yaw="180"/>
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

def fill_inventory():
    result = ""
    for i in range(36):
        result += "<InventoryItem slot=\"" + str(i) + "\" type=\"bow\" quantity=\"1\"/>\n"
    return result

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

def set_yaw_and_pitch(agent, yaw=None, pitch=None):
    if yaw == None and pitch == None:
        return
    
    i = 1
    total_sleep = 0
    
    while True:
        obs = load_grid(agent)
        if not obs:
            return total_sleep
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
    for command in commands:
        if command[2] <= time:
            commands.remove(command)
            command[0].sendCommand(command[1])

def vert_distance(xtarget, ztarget, xsource=0, zsource=0):
    return ((xtarget - xsource)**2 + (ztarget - zsource)**2) ** 0.5
    
def get_hori_angle(xorigin, zorigin, xtarget, ztarget):
    return math.degrees(math.atan2(xorigin-xtarget, ztarget-zorigin))

def magnitude(vector):
    return np.sqrt(np.sum(vector**2))

def get_angle_between(vector1, vector2):
    prod = np.dot(vector1, vector2)
    mag1 = np.sqrt(np.sum(vector1**2))
    mag2 = np.sqrt(np.sum(vector2**2))
    if mag1 == 0 or mag2 == 0:
        return 0
    return math.degrees(math.acos(prod/(mag1*mag2)))

def get_closest_point(curve, target):
    if len(curve) == 0:
        print("Got closest point with empty list")
        return None
    if len(curve) == 1:
        return curve[0]
    
    point1, point2 = None, None
    dist1, dist2 = 9999, 9999
    for i in range(len(curve)):
        dist = magnitude(curve[i] - target)
        if dist < dist1:
            dist2 = dist1
            point2 = point1
            dist1 = dist
            point1 = curve[i]
        elif dist < dist2:
            dist2 = dist
            point2 = curve[i]

    if magnitude(point2 - point1) == 0:
        return point1
    
    angle1 = get_angle_between(point2 - point1, target - point1)
    if angle1 > 90:
        return point1
    if get_angle_between(point1 - point2, target - point2) > 90:
        return point2
    angle2 = 180 - 90 - angle1
    side = dist1 * math.sin(math.radians(angle2)) / math.sin(math.radians(90))
    interp = side / magnitude(point2 - point1)
    
    return point1 * interp + point2 * (1 - interp)

def get_first_vert_shot(distance, elevation):
    global vert_angle_step
    
    array = np.asarray(vert_shots[0] + vert_shots[1])
    if array.shape[0] > 100:
        if elevation > distance:
            array = array[array[:,-1] > 45]
        else:
            array = array[array[:,-1] <= 45]
    if vert_angle_step >= 45:
        poly = PolynomialFeatures(2, include_bias=False).fit(array[:,:-1])
        predictor = LinearRegression().fit(poly.transform(array[:,:-1]), array[:,-1])
        print(predictor.intercept_, predictor.coef_)
        print(distance, elevation)
        return min(predictor.predict(poly.transform([[distance, elevation]]))[0], 89.9)

    vert_angle_step += 3
    return vert_angle_step

def get_next_vert_shot(prev_angle, error, step_size):
    bound_angle = prev_angle    
    if error < 0:
        bound_angle = 90
    elif error > 0:
        bound_angle = 0
    return prev_angle*(1-step_size) + bound_angle*step_size

def get_first_hori_shot(angle):
    array = np.asarray(hori_shots[0] + hori_shots[1])
    if array.shape[0] > 100:
        predictor = LinearRegression().fit(array[:,0].reshape(-1, 1), array[:,1])
        return predictor.predict(np.asarray([[angle]]))[0]
    
    return random.randrange(-180, 180)

def get_next_hori_shot(prev_angle, error, step_size):
    result = prev_angle - error
    return ((result + 180) % 360) - 180

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
    
    last_obs = load_grid(move_agent)
    if not last_obs:
        return
    player_loc = find_mob_by_name(last_obs["Mobs"], "Slayer")
    target_loc = find_mob_by_name(last_obs["Mobs"], "Mover")
    distance = vert_distance(target_loc["x"], target_loc["z"], player_loc["x"], player_loc["z"])
    elevation = target_loc["y"] - player_loc["y"]
    obs_angle = get_hori_angle(player_loc["x"], player_loc["z"], target_loc["x"], target_loc["z"])
    mover_pos = [target_loc["x"], target_loc["z"]]
    mover_life = target_loc["life"]
    
    if total_time < 30 or len(vert_shots[0] + vert_shots[1]) > 5:
        vert_angle = get_first_vert_shot(distance, elevation+1)
    else:
        vert_angle = get_next_vert_shot(vert_angle, vert_error, vert_step_size)
        vert_step_size *= 0.8
        
    if total_time < 30 or len(hori_shots[0] + hori_shots[1]) > 5:
        hori_angle = get_first_hori_shot(obs_angle)
    else:
        hori_angle = get_next_hori_shot(hori_angle, hori_error, hori_step_size)
        hori_step_size *= 0.8
        
    set_yaw_and_pitch(shoot_agent, hori_angle, -vert_angle)
    commands.append((shoot_agent, "use 1", total_time + 0))
    commands.append((shoot_agent, "use 0", total_time + 26))

def record_data():
    global vert_error
    global hori_error
    global total_time
    global commands
    global mover_pos
    global mover_life

    curr_time = 0
    data = []
    while curr_time < 50:
        curr_time += 1
        time.sleep(0.05)
        last_obs = load_grid(move_agent)
        if not last_obs:
            return
        arrow = find_mob_by_name(last_obs["Mobs"], "Arrow")
        if arrow:
            data.append(np.asarray([arrow["x"], arrow["y"], arrow["z"]]))

    vert_error = 0
    hori_error = 0
    if len(data) > 0:
        target_loc = find_mob_by_name(last_obs["Mobs"], "Mover")
        target_loc = np.asarray([target_loc["x"], target_loc["y"], target_loc["z"]])
        player_loc = find_mob_by_name(last_obs["Mobs"], "Slayer")
        closest_point = get_closest_point(data, target_loc)
        for i in range(len(data)):
            if vert_angle < 85 and (i == 0 or not np.array_equal(data[i], data[i-1])):
                vert_shots[1].append([magnitude(data[i][::2] - np.asarray([player_loc["x"], player_loc["z"]])), data[i][1] - player_loc["y"], vert_angle])
                hori_shots[1].append([get_hori_angle(player_loc["x"], player_loc["z"], data[i][0], data[i][2]), hori_angle])
            if i > 1 and get_angle_between(data[i] - data[i-1], data[i-1] - data[i-2]) > 45:
                break
        vert_error = closest_point[1] - target_loc[1]
        hori_error = get_hori_angle(player_loc["x"], player_loc["z"], closest_point[0], closest_point[2]) - \
                     get_hori_angle(player_loc["x"], player_loc["z"], target_loc[0], target_loc[2])
        hori_error = ((hori_error + 180) % 360) - 180

        vert_errors.append(vert_error)
        hori_errors.append(hori_error)
        commands.append((shoot_agent, "chat /kill @e[type=!player]", total_time + 0))

    return -((vert_error**2 + hori_error**2)**0.5)

vert_shots = [[], []]
hori_shots = [[], []]
vert_errors = []
hori_errors = []
vert_angle_step = -3

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

iterations = 5
for i in range(iterations):
    params = (random.randint(10, 50)*random.randrange(-1, 2, 2), random.randint(10, 30), random.randint(10, 50)*random.randrange(-1, 2, 2))
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
    commands.append((move_agent, "jump 0", params[1]))
    commands.append((move_agent, "chat /gamemode 1", params[1]))

    #for i in range(0,10,2):
        #commands.append((move_agent, "strafe 1", i))
        #commands.append((move_agent, "strafe -1", i+1))

    # Loop until mission ends:
    shoot_cycle = 20
    record_cycle = 46
    total_time = 0
    vert_step_size = 0.5
    hori_step_size = 0.5
    vert_error = 0
    hori_error = 0
    distance = 0
    elevation = 0
    obs_angle = 0
    mover_pos = [0, 0]
    mover_life = 10
    while world_state.is_mission_running:
        #sys.stdout.write(".")
        time.sleep(0.05)
        total_time += 1
        process_commands(total_time)

        if total_time >= shoot_cycle:
            shoot_cycle += 30
            shoot_at_target()

        if total_time >= record_cycle:
            record_cycle += 30
            reward = record_data()

    print()
    print("Mission ended")
    # Mission has ended.

# Data Graphing
array = np.asarray(vert_shots[0] + vert_shots[1])
colors = [(min(max(0, 2 - 4*s/45), 1), \
           min(max(0, 2 - abs((4*s-90)/45)), 1), \
           min(max(0, 4*s/45 - 2), 1)) for s in array[:,2]]
plt.scatter(array[:,0], array[:,1], c=colors, alpha=0.5)
plt.title("Vertical Angle Regression Data")
plt.xlabel("Distance")
plt.ylabel("Elevation")
plt.show()

# Prediction Graphing
poly = PolynomialFeatures(2, include_bias=False).fit(array[:,:-1])
predictor = LinearRegression().fit(poly.transform(array[:,:-1]), array[:,-1])
xSpace = np.linspace(0, array[:,0].max(), 100)
ySpace = np.linspace(0, array[:,1].max(), 100)
xx, yy = np.meshgrid(xSpace, ySpace)
zz = np.zeros(xx.shape)
for i in range(xx.shape[0]):
    for j in range(xx.shape[1]):
        zz[i][j] = predictor.predict(poly.transform([[xx[i,j], yy[i,j]]]))[0]
zz.reshape(xx.shape)
cs = plt.contourf(xx, yy, zz, levels=[5*i for i in range(10)])
cbar = plt.colorbar(cs)
cbar.ax.set_ylabel("Vertical angle")
plt.title("Vertical Angle Regression Predictions")
plt.xlabel("Distance")
plt.ylabel("Elevation")
plt.show()

# Error Graphing
total_errors = (np.asarray(vert_errors)**2 + np.asarray(hori_errors)**2)**0.5
plt.scatter(range(total_errors.shape[0]), total_errors)
plt.title("Errors for each shot")
plt.xlabel("Arrow shot")
plt.ylabel("Error")
plt.show()

# Accuracy Graphing
accuracies = []
for i in range(5, len(total_errors)):
    shots = total_errors[i-5:i]
    hit_shots = shots[shots<2]
    accuracies.append(len(hit_shots) / len(shots))
plt.plot(np.arange(5, len(total_errors)), accuracies)
plt.title("Accuracy over last 5 shots")
plt.xlabel("Last shot")
plt.show()
