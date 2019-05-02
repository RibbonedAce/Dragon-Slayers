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
    return str(random.randrange(-20, 20)), str(random.randrange(20, 40))


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

        if abs(yaw_diff) < 0.001 and abs(pitch_diff) < 0.001:
            break;
            
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

def look_angle(xorigin, zorigin, xtarget, ztarget):
    return math.degrees(math.atan2(ztarget-zorigin, xtarget-xorigin))

def get_first_shot(distance):
    lower_bound = 0
    lower_angle = 0
    upper_bound = 1000
    upper_angle = 45
    
    for key in good_shots.keys():
        if key < distance and key > lower_bound:
            lower_bound = key
            lower_angle = good_shots[key]
        elif key > distance and key < upper_bound:
            upper_bound = key
            upper_angle = good_shots[key]

    interp = (distance - lower_bound) / (upper_bound - lower_bound)
    return lower_angle*(1-interp) + upper_angle*interp

def get_next_shot(prev_angle, error, step_size):
    bound_angle = prev_angle
    
    if error < 0:
        bound_angle = 45
        for value in good_shots.values():
            if value > prev_angle and value < bound_angle:
                bound_angle = value
        
    elif error > 0:
        bound_angle = 0
        for value in good_shots.values():
            if value < prev_angle and value > bound_angle:
                bound_angle = value

    return prev_angle*(1-step_size) + bound_angle*step_size

good_shots = {}

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

commands = []

for retry in range(max_retries):
    try:
        shoot_agent.startMission( my_mission, my_clients, my_mission_record, 0, "")
        move_agent.startMission( my_mission, my_clients, my_mission_record, 1, "")
        break
    except RuntimeError as e:
        if retry == max_retries - 1:
            print("Error starting mission", e)
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

#for i in range(0,10,2):
    #commands.append((move_agent, "strafe 1", i))
    #commands.append((move_agent, "strafe -1", i+1))

# Loop until mission ends:
total_time = 0
shoot_cycle = 0
record_cycle = 10
step_size = 1
error = 0
angle = 0
while world_state.is_mission_running:
    #sys.stdout.write(".")
    time.sleep(0.1)
    total_time += 0.1
    process_commands(total_time)

    if total_time >= shoot_cycle:
        shoot_cycle += 11.2
        
        last_obs = load_grid(move_agent, world_state)
        print(last_obs)
        last_angle = angle
        player_loc = find_mob_by_name(last_obs["Mobs"], "Slayer")
        target_loc = find_mob_by_name(last_obs["Mobs"], "Mover")
        distance = (abs(player_loc["x"] - target_loc["x"]) ** 2 + abs(player_loc["z"] - target_loc["z"] ** 2)) ** 0.5
        angle = 0
        if total_time < 1:
            angle = get_first_shot(distance)
        else:
            angle = get_next_shot(last_angle, error, step_size)
        set_yaw_and_pitch(shoot_agent, None, -angle)
        commands.append((shoot_agent, "use 1", total_time + 0))
        commands.append((shoot_agent, "use 0", total_time + 1.2))

    if total_time >= record_cycle:
        record_cycle += 11.2
        #last_obs = load_grid(shoot_agent, world_state)
        #player = find_mob_by_name(last_obs["Mobs"], "Slayer")
        #target = find_mob_by_name(last_obs["Mobs"], "Mover")
        #print(target["x"]-player["x"], target["z"]-player["z"], look_angle(player["x"], player["z"], target["x"], target["z"]))

        last_obs = load_grid(move_agent, world_state)
        error = 0
        arrow = find_mob_by_name(last_obs["Mobs"], "Arrow")
        if not arrow:
            if find_mob_by_name(last_obs["Mobs"], "Mover")["life"] < 20:
                good_shots[distance] = angle
            else:
                error = 100
        else:
            error = arrow["z"] - target_loc["z"]
        print("Error:", error)
        commands.append((shoot_agent, "chat /kill @e[type=!player]", total_time + 0))
        step_size *= 0.8
        

print()
print("Mission ended")
# Mission has ended.
