try:
    from malmo import MalmoPython
except:
    import MalmoPython

import os
import sys
import time
import json

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
                  <FlatWorldGenerator/>
                  <ServerQuitFromTimeUp timeLimitMs="10000"/>
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
                        <Range name="Mobs" xrange="1000" yrange="1" zrange="1000" update_frequency="1"/>
                    </ObservationFromNearbyEntities>
                    <ChatCommands/>
                </AgentHandlers>
              </AgentSection>
              
              <AgentSection mode="Survival">
                <Name>Mover</Name>
                <AgentStart>
                    <Placement x="-1.5" y="4.0" z="10.5" yaw="180"/>
                </AgentStart>
                <AgentHandlers>
                    <ContinuousMovementCommands turnSpeedDegs="900"/>
                    <ChatCommands/>
                </AgentHandlers>
              </AgentSection>
            </Mission>'''


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
        obs = load_grid(world_state)
        current_yaw = obs["Mobs"][0]["yaw"]
        current_pitch = obs["Mobs"][0]["pitch"]
        
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
    return False

def process_commands(time):
    for command in commands:
        if command[2] <= time:
            commands.remove(command)
            command[0].sendCommand(command[1])            

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
my_clients.add(MalmoPython.ClientInfo('127.0.0.1', 10000))
my_clients.add(MalmoPython.ClientInfo('127.0.0.1', 10001))

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

commands.append((shoot_agent, "hotbar.1 1", 0))
commands.append((shoot_agent, "hotbar.1 0", 0))
commands.append((shoot_agent, "use 1", 0))
commands.append((shoot_agent, "use 0", 1.2))
commands.append((shoot_agent, "chat /kill @e[type=!player]", 3.2))

for i in range(0,10,2):
    commands.append((move_agent, "strafe 1", i))
    commands.append((move_agent, "strafe -1", i+1))

# Loop until mission ends:
total_time = 0
recorded = False
while world_state.is_mission_running:
    #sys.stdout.write(".")
    time.sleep(0.1)
    process_commands(total_time)
    
    if not recorded and total_time >= 3.2:
        recorded = True
        last_obs = load_grid(shoot_agent, world_state)
        arrow = find_mob_by_name(last_obs["Mobs"], "Arrow")
        if not arrow:
            print("Hit target!")
        else:
            mob = find_mob_by_name(last_obs["Mobs"], "Mover")
            print("Missed by", (abs(arrow["x"] - mob["x"]) ** 2 + abs(arrow["z"] - mob["z"] ** 2)) ** 0.5)

    total_time += 0.1

print()
print("Mission ended")
# Mission has ended.
