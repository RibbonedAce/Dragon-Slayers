try:
    from malmo import MalmoPython
except:
    import MalmoPython

import os
import sys
import time
import json
import math
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
                    <ChatCommands/>
                    <ContinuousMovementCommands turnSpeedDegs="10000"/>
                    <AgentQuitFromTouchingBlockType>
                        <Block type="redstone_block"/>
                    </AgentQuitFromTouchingBlockType>
                    <ObservationFromNearbyEntities> 
                        <Range name="Mobs" xrange="10000" yrange="10000" zrange="10000" update_frequency="1"/>
                    </ObservationFromNearbyEntities>
                </AgentHandlers>
              </AgentSection>
            </Mission>'''

class Entity:

    def __init__(self,entity_xml):
        self.name = entity_xml['name']
        self.id = entity_xml['id']
        self.pitch = entity_xml['pitch']
        self.yaw = entity_xml['yaw']
        self.position = (entity_xml['x'],entity_xml['y'],entity_xml['z'])
        self.velocity = (entity_xml['motionX'],entity_xml['motionY'],entity_xml['motionZ'])

    def distance_from(self,other):
        return math.sqrt((self.position[0]-other.position[0])**2 + (self.position[2]-other.position[2])**2)


def get_player(obs, player_name):
    if len(obs.observations) == 0:
        return None
    for entity_xml in json.loads(obs.observations[0].text)["Mobs"]:
        if entity_xml['name'] == player_name:
            return Entity(entity_xml)
    return None

def get_entities(obs):
    if len(obs.observations) == 0:
        return None
    result = []
    for entity_xml in json.loads(obs.observations[0].text)["Mobs"]:
        result.append(Entity(entity_xml))
    return result

def get_closest_entity(obs, player, types_to_find):
    entity_list = get_entities(obs)
    min_distance = 10000000
    closest = None
    for entity in entity_list:
        if entity.name in types_to_find:
            dist = entity.distance_from(player)
            if dist < min_distance:
                min_distance = dist
                closest = entity
    return closest
            
            
def angvel(target, current, scale):
    '''Use sigmoid function to choose a delta that will help smoothly steer from current angle to target angle.'''
    delta = target - current
    while delta < -180:
        delta += 360
    while delta > 180:
        delta -= 360
    return 2.0/(1.0 + math.exp(-delta/scale)) - 1.0

def pointTo(agent_host, ob, target_pitch, target_yaw, threshold):
    '''Steer towards the target pitch/yaw, return True when within the given tolerance threshold.'''
    pitch = ob.get(u'Pitch', 0)
    yaw = ob.get(u'Yaw', 0)
    delta_yaw = angvel(target_yaw, yaw, 50.0)
    delta_pitch = angvel(target_pitch, pitch, 50.0)
    agent_host.sendCommand("turn " + str(delta_yaw))    
    agent_host.sendCommand("pitch " + str(delta_pitch))
    if abs(pitch-target_pitch) + abs(yaw-target_yaw) < threshold:
        agent_host.sendCommand("turn 0")
        agent_host.sendCommand("pitch 0")
        return True
    return False

def calcYawAndPitchToMob(target, x, y, z, target_height):
    dx = target.x - x
    dz = target.z - z
    yaw = -180 * math.atan2(dx, dz) / math.pi
    distance = math.sqrt(dx * dx + dz * dz)
    pitch = math.atan2(((y + 1.625) - (target.y + target_height * 0.9)), distance) * 180.0 / math.pi
    return yaw, pitch
    
def load_grid(world_state):
    while world_state.is_mission_running:
        #sys.stdout.write(".")
        time.sleep(0.1)
        world_state = agent_host.getWorldState()
        if len(world_state.errors) > 0:
            raise AssertionError('Could not load grid.')

        if world_state.number_of_observations_since_last_state > 0:
            return json.loads(world_state.observations[-1].text)


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
agent_host.sendCommand("hotbar.1 1")
agent_host.sendCommand("hotbar.1 0")
agent_host.sendCommand("use 1")
agent_host.sendCommand("chat /summon Spider 10 56 10")
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
    player = get_player(world_state,'CS175AwesomeMazeBot')
    closest_entity = get_closest_entity(world_state, player, ['Spider','Arrow'])
    print(closest_entity.name + ": " + str(closest_entity.position))
    if not observed:
        last_obs = load_grid(world_state)
        print(last_obs["Mobs"][0])
        observed = True
    for error in world_state.errors:
        print("Error:",error.text)


print()
print("Mission ended")
# Mission has ended.

