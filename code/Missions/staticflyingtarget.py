from Missions.mission import Mission
import math



class StaticFlyingTargetMission(Mission):

    def chat_command_init(self, shoot_agent, move_agent, params):
      shoot_agent.commands.append((shoot_agent.agent, "chat /kill @e[type=!player]", 0))
      shoot_agent.commands.append((shoot_agent.agent, "hotbar.1 1", 0))
      shoot_agent.commands.append((shoot_agent.agent, "hotbar.1 0", 0))
      move_agent.commands.append((move_agent.agent, "chat /gamemode 3", 0))
      move_agent.commands.append((move_agent.agent, "jump 1", 0))
      move_agent.commands.append((move_agent.agent, "jump 0", params[2]))
      move_agent.commands.append((move_agent.agent, "chat /gamemode 1", params[2]))
