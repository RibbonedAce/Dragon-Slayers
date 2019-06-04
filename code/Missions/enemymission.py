


from Missions.mission import Mission
import random
import math




class EnemyMission(Mission):

    def __init__(self):
        self.enemy_types = ["Spider", "Ghast", "Blaze", "Creeper", "Cow", "Pig", "Chicken", "Golem"]

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
            </Mission>'''
    
    def chat_command_init(self,shoot_agent, move_agent, params):
        shoot_agent.commands.append((shoot_agent, "chat /kill @e[type=!player]", 0))
        shoot_agent.commands.append((shoot_agent, "hotbar.1 1", 0))
        shoot_agent.commands.append((shoot_agent, "hotbar.1 0", 0))
        enemy = random.choice(self.enemy_types)
        spawn_loc = (params[0],params[1])
        shoot_agent.commands.append((shoot_agent, "chat /summon {} ~{} ~0 ~{}".format(enemy, spawn_loc[0],spawn_loc[1]), 0))
