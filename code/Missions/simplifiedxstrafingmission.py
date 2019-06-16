

from Missions.mission import Mission
import random
import math

def fill_inventory():
    result = ""
    for i in range(36):
        result += "<InventoryItem slot=\"" + str(i) + "\" type=\"bow\" quantity=\"1\"/>\n"
    return result

class SimplifiedXStrafingMission(Mission):

    def __init__(self):
        self.direction = 1

    def get_mission_xml(self, params):
        #override params
        param = (5,12)
        angle = ((math.atan2(params[0],-params[1]) * 180 / 3.14159))
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
                  <ServerQuitFromTimeUp timeLimitMs="15000"/>
                </ServerHandlers>
              </ServerSection>

              <AgentSection mode="Creative">
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
                    <MissionQuitCommands/>
                </AgentHandlers>
              </AgentSection>
              
              <AgentSection mode="Survival">
                <Name>Mover</Name>
                <AgentStart>
                    <Placement x="'''+str(params[0])+'''" y="4" z="'''+str(params[1])+'''" yaw="'''+str(angle)+'''"/>
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
                    <MissionQuitCommands/>
                </AgentHandlers>
              </AgentSection>
            </Mission>'''
   
    def chat_command_init(self,shoot_agent, move_agent, params):
        shoot_agent.commands.append((shoot_agent.agent, "chat /kill @e[type=!player]", 0))
        shoot_agent.commands.append((shoot_agent.agent, "hotbar.1 1", 0))
        shoot_agent.commands.append((shoot_agent.agent, "hotbar.1 0", 0))
        move_agent.commands.append((move_agent.agent, "strafe 0.5", 0))


    def ai_step(self, move_agent, target_transform):
        pass
