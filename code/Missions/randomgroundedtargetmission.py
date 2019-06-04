
from Missions.mission import Mission
import random


def fill_inventory():
    result = ""
    for i in range(36):
        result += "<InventoryItem slot=\"" + str(i) + "\" type=\"bow\" quantity=\"1\"/>\n"
    return result

class RandomGroundedTargetMission(Mission):

    def __init__(self):
        self.direction = 1
        self.speed = random.random()

    def get_mission_xml(self, params):
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
                    <MissionQuitCommands/>
                    <InventoryCommands/>
                </AgentHandlers>
              </AgentSection>
              
              <AgentSection mode="Survival">
                <Name>Mover</Name>
                <AgentStart>
                    <Placement x="'''+str(params[0])+'''" y="4" z="'''+str(params[1])+'''" yaw="180"/>
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
    
    def chat_command_init(self,shoot_agent, move_agent, params):
      shoot_agent.commands.append((shoot_agent, "chat /kill @e[type=!player]", 0))
      shoot_agent.commands.append((shoot_agent, "hotbar.1 1", 0))
      shoot_agent.commands.append((shoot_agent, "hotbar.1 0", 0))



    def ai_step(self, move_agent):
        move_agent.agent.sendCommand("move 0")
        self.set_random_direction(move_agent)
        move_agent.agent.sendCommand("move 1")

    def set_random_direction(self, move_agent):
        desiredYaw = random.random()
        desiredPitch = 0
        i = 1
        total_sleep = 0
        
        while True:
            if not move_agent._obs:
                return total_sleep

            current_yaw = move_agent.transform["yaw"]
            current_pitch = move_agent.transform["pitch"]
            
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
            
            move_agent.agent.sendCommand("turn " + str(i * yaw_multiplier * yaw_sleep / sleep_time))
            move_agent.agent.sendCommand("pitch " + str(i * pitch_multiplier * pitch_sleep / sleep_time))
            time.sleep(sleep_time)
            move_agent.agent.sendCommand("turn 0")
            move_agent.agent.sendCommand("pitch 0")
                
            i *= 0.2
            if total_sleep > 1:
                return 
       