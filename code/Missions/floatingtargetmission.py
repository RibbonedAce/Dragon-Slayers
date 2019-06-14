from Missions.mission import Mission
import math



class FloatingTargetMission(Mission):

    def __init__(self):
        self.total_time = 0
        self.ticks_on = 1
        self.ticks_off = 1
        self.state = "rising"

    def chat_command_init(self, shoot_agent, move_agent, params):
      shoot_agent.commands.append((shoot_agent.agent, "chat /kill @e[type=!player]", 0))
      shoot_agent.commands.append((shoot_agent.agent, "hotbar.1 1", 0))
      shoot_agent.commands.append((shoot_agent.agent, "hotbar.1 0", 0))
      move_agent.commands.append((move_agent.agent, "chat /gamemode 3", 0))
      move_agent.commands.append((move_agent.agent, "jump 1", 0))
      move_agent.commands.append((move_agent.agent, "jump 0", params[2]))
      move_agent.commands.append((move_agent.agent, "chat /gamemode 1", params[2]))



    def ai_step(self, move_agent, target_transform):
        self.total_time += 1
        tick = self.total_time % (self.ticks_off + self.ticks_on)

        if move_agent.transform['y'] < 10:
            self.state = "rising"
        elif move_agent.transform['y'] > 40:
            self.state = "falling"

        if tick < self.ticks_on:
            if self.state == "rising":
                move_agent.agent.sendCommand("jump 1")
                move_agent.agent.sendCommand("crouch 0")
            elif self.state == "falling":
                move_agent.agent.sendCommand("crouch 1")
                move_agent.agent.sendCommand("jump 0")
        else:
            move_agent.agent.sendCommand("crouch 0")
            move_agent.agent.sendCommand("jump 0")            

    
