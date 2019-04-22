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
                  <FlatWorldGenerator generatorString="3;7,44*49,73,35:1,159:4,95:13,35:13,159:11,95:10,159:14,159:6,35:6,95:6;12;"/>
                  <DrawingDecorator>
                    <DrawSphere x="-27" y="70" z="0" radius="30" type="air"/>
                  </DrawingDecorator>
                  <ServerQuitFromTimeUp timeLimitMs="5000"/>
                  <ServerQuitWhenAnyAgentFinishes/>
                </ServerHandlers>
              </ServerSection>

              <AgentSection mode="Survival">
                <Name>CS175AwesomeMazeBot</Name>
                <AgentStart>
                    <Placement x="0.5" y="56.0" z="0.5" yaw="0"/>
                    <Inventory>
                        <InventoryItem slot="0" type="bow"/>
                        <InventoryItem slot="1" type="arrow" quantity="64"/>
                    </Inventory>
                </AgentStart>
                <AgentHandlers>
                    <ContinuousMovementCommands turnSpeedDegs="180"/>
                    <AgentQuitFromTouchingBlockType>
                        <Block type="redstone_block"/>
                    </AgentQuitFromTouchingBlockType>
                    <ObservationFromNearbyEntities> 
                        <Range name="Mobs" xrange="10" yrange="1" zrange="10" update_frequency="1"/>
                    </ObservationFromNearbyEntities>
                </AgentHandlers>
              </AgentSection>
            </Mission>'''


def load_grid(world_state):
    while world_state.is_mission_running:
        #sys.stdout.write(".")
        time.sleep(0.1)
        world_state = agent_host.getWorldState()
        if len(world_state.errors) > 0:
            raise AssertionError('Could not load grid.')

        if world_state.number_of_observations_since_last_state > 0:
            return json.loads(world_state.observations[-1].text)

def set_pitch(obs, degrees):
    current_degrees = obs["Mobs"][0]["yaw"]
    diff = degrees - current_degrees
    if diff > 180:
        diff = diff - 360
    turn = diff / 190
    agent_host.sendCommand("turn " + str(turn))

# Create default Malmo objects:
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

my_mission = MalmoPython.MissionSpec(GetMissionXML(), True)
my_mission_record = MalmoPython.MissionRecordSpec()
my_mission.requestVideo(800, 500)
my_mission.setViewpoint(0)
# Attempt to start a mission:
max_retries = 3
my_clients = MalmoPython.ClientPool()
my_clients.add(MalmoPython.ClientInfo('127.0.0.1', 10000)) # add Minecraft machines here as available

for retry in range(max_retries):
    try:
        agent_host.startMission( my_mission, my_clients, my_mission_record, 0, "")
        break
    except RuntimeError as e:
        if retry == max_retries - 1:
            print("Error starting mission", e)
            exit(1)
        else:
            time.sleep(2)

# Loop until mission starts:
print("Waiting for the mission to start ")
world_state = agent_host.getWorldState()
while not world_state.has_mission_begun:
    #sys.stdout.write(".")
    time.sleep(0.1)
    world_state = agent_host.getWorldState()
    for error in world_state.errors:
        print("Error:",error.text)

print()
print("Mission running.")

last_obs = load_grid(world_state)
print(last_obs["Mobs"][0])

agent_host.sendCommand("hotbar.1 1")
agent_host.sendCommand("hotbar.1 0")
agent_host.sendCommand("use 1")
set_pitch(last_obs, 181)
time.sleep(1.2)
agent_host.sendCommand("turn 0")
agent_host.sendCommand("use 0")

# Loop until mission ends:
observed = False
while world_state.is_mission_running:
    #sys.stdout.write(".")
    time.sleep(0.1)
    world_state = agent_host.getWorldState()
    if not observed:
        last_obs = load_grid(world_state)
        print(last_obs["Mobs"][0])
        observed = True
    for error in world_state.errors:
        print("Error:",error.text)


print()
print("Mission ended")
# Mission has ended.
