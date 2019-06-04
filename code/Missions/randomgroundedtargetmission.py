
from Missions.mission import Mission
import math
import random




class RandomGroundedTargetMission(Mission):

    def __init__(self):
        self.direction = 1
        self.speed = random.random()

    
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
       