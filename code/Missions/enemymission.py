


from Missions.mission import Mission
import random
import math




class EnemyMission(Mission):

    def __init__(self):
        #self.enemy_types = ["Spider", "Ghast", "Blaze", "Creeper", "Cow", "Pig", "Chicken", "Golem"]
        self.enemy_types = ["Horse"]

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
                  <FlatWorldGenerator generatorString="3;1*minecraft:bedrock,2*minecraft:dirt,1*minecraft:obsidian;2;village"></FlatWorldGenerator>
                  <ServerQuitFromTimeUp timeLimitMs="60000"/>
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
                    <Placement x="'''+str(params[0])+'''" y="4" z="'''+str(params[1])+'''" yaw="0" pitch="90"/>
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

        move_agent.commands.append((move_agent.agent, "chat /gamemode 3", 0))
        move_agent.commands.append((move_agent.agent, "jump 1", 0))
        move_agent.commands.append((move_agent.agent, "jump 0", params[2]))
        move_agent.commands.append((move_agent.agent, "chat /gamemode 1", params[2]))

        enemy = random.choice(self.enemy_types)
        spawn_loc = (params[0],params[1])
        shoot_agent.commands.append((shoot_agent.agent, "chat /summon {} ~{} ~0 ~{}".format(enemy, spawn_loc[0],spawn_loc[1]), 0))
        shoot_agent.commands.append((shoot_agent.agent, "chat /summon {} ~{} ~0 ~{}".format(enemy, spawn_loc[0]*1.2,spawn_loc[1]*1.2), 0))
        shoot_agent.commands.append((shoot_agent.agent, "chat /summon {} ~{} ~0 ~{}".format(enemy, spawn_loc[0]*1,spawn_loc[1]*1.4), 0))
        shoot_agent.commands.append((shoot_agent.agent, "chat /summon {} ~{} ~0 ~{}".format(enemy, spawn_loc[0]*1.4,spawn_loc[1]*1), 0))



    def get_target(self, entities):
      for entity in entities:
          if entity["name"] in self.enemy_types:
              return entity
      return None

    def ai_step(self, move_agent, target_transform):
        if move_agent is None or target_transform is None:
            return None
        if move_agent.transform['x'] - target_transform['x'] > 3:
            move_agent.agent.sendCommand("strafe 1")
        elif move_agent.transform['x'] - target_transform['x'] < -3:
            move_agent.agent.sendCommand("strafe -1")
        else:
            move_agent.agent.sendCommand("strafe 0")

        if move_agent.transform['z'] - target_transform['z'] > 3:
            move_agent.agent.sendCommand("move -1")
        elif move_agent.transform['z'] - target_transform['z'] < -3:
            move_agent.agent.sendCommand("move 1")
        else:
            move_agent.agent.sendCommand("move 0")

        