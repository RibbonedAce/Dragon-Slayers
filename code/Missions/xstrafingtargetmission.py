
from Missions.mission import Mission
import random


class XStrafingTargetMission(Mission):

    def __init__(self):
        self.direction = 1
        self.speed = random.random()

   
    def chat_command_init(self,shoot_agent, move_agent, params):
        shoot_agent.commands.append((shoot_agent.agent, "chat /kill @e[type=!player]", 0))
        shoot_agent.commands.append((shoot_agent.agent, "hotbar.1 1", 0))
        shoot_agent.commands.append((shoot_agent.agent, "hotbar.1 0", 0))
        move_agent.commands.append((move_agent.agent, "strafe " + str(self.direction*self.speed), 0))


    def ai_step(self, move_agent):
        self.toggle_direction(move_agent)

    def toggle_direction(self, move_agent):
        self.direction *= -1
        move_agent.commands.append((move_agent.agent, "strafe " + str(self.direction*self.speed), 0))
