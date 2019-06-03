try:
    from malmo import MalmoPython
except:
    import MalmoPython
import malmo.minecraftbootstrap

import os
import sys
import time
import json
import random
import math
import numpy as np
from matplotlib import pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from timekeeper import TimeKeeper

def load_grid(agent):
    wait_time = 0
    keeper = TimeKeeper()
    while wait_time < 10:
        #sys.stdout.write(".")
        world_state = agent.getWorldState()
        if not world_state.is_mission_running:
            return None
        if len(world_state.errors) > 0:
            raise AssertionError('Could not load grid.')

        if world_state.number_of_observations_since_last_state > 0 and \
           json.loads(world_state.observations[-1].text):
            result = json.loads(world_state.observations[-1].text)
            result["time"] = int(round(time.time() * 1000))
            return result

        keeper.advance_by(0.05)
        wait_time += 0.05

def find_mob_by_name(mobs, name, new=False):
    for m in mobs:
        if m["name"] == name:
            return m
    return None

def magnitude(vector):
    return np.sqrt(np.sum(vector**2))


def vert_distance(xtarget, ztarget, xsource=0, zsource=0):
    return ((xtarget - xsource)**2 + (ztarget - zsource)**2) ** 0.5

def get_hori_angle(xorigin, zorigin, xtarget, ztarget):
    return math.degrees(math.atan2(xorigin-xtarget, ztarget-zorigin))

def get_angle_between(vector1, vector2):
    prod = np.dot(vector1, vector2)
    mag1 = np.sqrt(np.sum(vector1**2))
    mag2 = np.sqrt(np.sum(vector2**2))
    if mag1 == 0 or mag2 == 0:
        return 0
    return math.degrees(math.acos(prod/(mag1*mag2)))

def vector_from_angle(angle):
    return np.asarray([math.cos(math.radians(angle+180)), 0, math.sin(math.radians(angle))])

def project_vector(vector1, vector2):
    prod = np.dot(vector1, vector2)
    magsq = np.sum(vector2**2)
    return prod/magsq * vector2

def get_closest_point(curve, target):
    '''
    Get closest point on a curve to a target point.
    Curve is a list of points that define a trajectory.
    Returns the closest point on the set of segments created by curve to the target point
    ''' 
    if len(curve) == 0:
        print("Got closest point with empty list")
        return None
    if len(curve) == 1:
        return curve[0][0]
    
    point1, point2 = None, None
    dist1, dist2 = 9999, 9999
    for i in range(len(curve)):
        dist = magnitude(curve[i][0] - target)
        if dist < dist1:
            dist2 = dist1
            point2 = point1
            dist1 = dist
            point1 = curve[i][0]
        elif dist < dist2:
            dist2 = dist
            point2 = curve[i][0]

    if magnitude(point2 - point1) == 0:
        return point1
    
    angle1 = get_angle_between(point2 - point1, target - point1)
    if angle1 > 90:
        return point1
    if get_angle_between(point1 - point2, target - point2) > 90:
        return point2
    angle2 = 180 - 90 - angle1
    side = dist1 * math.sin(math.radians(angle2)) / math.sin(math.radians(90))
    interp = side / magnitude(point2 - point1)
    
    return point1 * interp + point2 * (1 - interp)

class MalmoAgent():

    def __init__(self, name, agent, pitch, yaw, vert_step_size, hori_step_size, model=None, data_set=None):
        self.name = name
        self.agent = agent
        self.pitch = pitch
        self.yaw = yaw
        self._obs = None
        self.transform = None
        self.commands = []
        self.total_time = 0
        self.vert_step_size = vert_step_size
        self.hori_step_size = hori_step_size
        self.desired_pitch = pitch
        self.desired_yaw = yaw
        self.last_shot = 0
        #Data set encapsulates hori_shots and vert_shots
        self.data_set = data_set
        self.hori_errors = []
        self.vert_errors = []
        self.vert_angle_step = 0
        self.model = model

    def step(self, obs):
        #Run this once a tick
        if(obs is not None):
            self.set_obs(obs)
        self.total_time += 1
        self.process_commands(self.total_time)

    def reset(self):
        #Reset the time for commands
        self.total_time = 0
        self.comands = []
        
    def set_obs(self, obs):
        if not obs:
            return
        self._obs = obs
        for entity in self._obs["Mobs"]:
            if entity["name"] == self.name:
                self.transform = entity

            
    def fill_inventory(self):
        result = ""
        for i in range(36):
            result += "<InventoryItem slot=\"" + str(i) + "\" type=\"bow\" quantity=\"1\"/>\n"
        return result

    def get_first_vert_shot(self, distance, elevation):
        array = np.asarray(self.data_set.vert_shots[0] + self.data_set.vert_shots[1])
        if array.shape[0] > 100:
            if elevation > distance:
                array = array[array[:,-1] > 45]
            else:
                array = array[array[:,-1] <= 45]
        if self.vert_angle_step >= 45:
            poly = PolynomialFeatures(2, include_bias=False).fit(array[:,:-1])
            self.model = LinearRegression().fit(poly.transform(array[:,:-1]), array[:,-1])
            return min(self.model.predict(poly.transform([[distance, elevation]]))[0], 89.9)

        self.vert_angle_step += 3
        return self.vert_angle_step


    def get_next_vert_shot(self, prev_angle, error, step_size):
        bound_angle = prev_angle    
        if error < 0:
            bound_angle = 90
        elif error > 0:
            bound_angle = 0
        return prev_angle*(1-step_size) + bound_angle*step_size

    def get_first_hori_shot(self, angle, distance, x_velocity):
        array = np.asarray(self.data_set.hori_shots[0] + self.data_set.hori_shots[1])
        if array.shape[0] > 100:
            poly = PolynomialFeatures(2, include_bias=False).fit(array[:,:-1])
            self.model = LinearRegression().fit(poly.transform(array[:,:-1]), array[:,-1])
            return self.model.predict(poly.transform([[angle, distance, x_velocity]]))[0]
        
        return random.randrange(-180, 180)

    def get_next_hori_shot(self, prev_angle, error, step_size):
        result = prev_angle - error
        return ((result + 180) % 360) - 180

    def set_yaw_and_pitch(self, desiredYaw=None, desiredPitch=None, timeLimit=2):
        if desiredYaw == None and desiredPitch == None:
            return
        
        i = 1
        total_sleep = 0
        
        while True:
            self.set_obs(load_grid(self.agent))

            current_yaw = self.transform["yaw"]
            current_pitch = self.transform["pitch"]
            
            yaw_diff = 0
            if desiredYaw != None:
                yaw_diff = desiredYaw - current_yaw
            pitch_diff = 0
            if desiredPitch != None:
                pitch_diff = desiredPitch - current_pitch

            if (abs(yaw_diff) < 0.001 and abs(pitch_diff) < 0.001):
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
            sleep_time = max(yaw_sleep, pitch_sleep, 0.001)
            actual_sleep = min(timeLimit - total_sleep, sleep_time)
            total_sleep += actual_sleep

            self.agent.sendCommand("turn " + str(i * yaw_multiplier * yaw_sleep / sleep_time))
            self.agent.sendCommand("pitch " + str(i * pitch_multiplier * pitch_sleep / sleep_time))
            time.sleep(actual_sleep)
            self.agent.sendCommand("turn 0")
            self.agent.sendCommand("pitch 0")            
            if total_sleep >= timeLimit:
                break
                
            i *= 0.5
            
        if (total_sleep < timeLimit):
            time.sleep(timeLimit - total_sleep)
        return timeLimit
    

    def process_commands(self, mission_elapsed_time):
        for command in self.commands:
            if command[2] <= mission_elapsed_time:
                self.commands.remove(command)
                command[0].sendCommand(command[1])


    def shoot_at_target(self, target_transform):
        '''
        Aims and shoots at target point

        '''
        
        if not self._obs:
            return
        distance = vert_distance(target_transform["x"], target_transform["z"], self.transform["x"], self.transform["z"])
        elevation = target_transform["y"] - self.transform["y"]
        obs_angle = get_hori_angle(self.transform["x"], self.transform["z"], target_transform["x"], target_transform["z"])
        x_velocity = project_vector(np.asarray([target_transform["motionX"], target_transform["motionY"], target_transform["motionZ"]]), vector_from_angle(self.transform["yaw"]))[0]
        self.agent.sendCommand("use 1")
        
        #if self.total_time < 30 or len(self.vert_shots[0] + self.vert_shots[1]) > 5:
        self.desired_pitch = self.get_first_vert_shot(distance, elevation+1)
        #else:
            #self.desired_pitch = self.get_next_vert_shot(self.desired_pitch, self.vert_errors[-1], self.vert_step_size)
            #self.vert_step_size *= 0.8
            
        #if self.total_time < 30 or len(self.hori_shots[0] + self.hori_shots[1]) > 5:
        self.desired_yaw = self.get_first_hori_shot(obs_angle, distance, x_velocity)
        #else:
            #self.desired_yaw = self.get_next_hori_shot(self.desired_yaw, self.hori_errors[-1], self.hori_step_size)
            #self.vert_step_size *= 0.8

        self.last_shot = time.time()
        self.set_yaw_and_pitch(self.desired_yaw, -self.desired_pitch)
        self.agent.sendCommand("use 0")
        time.sleep(0.1)

    def record_data(self, target_transform, other=None):
        if not other:
            other = self
        
        ticks_to_wait = 50
        keeper = TimeKeeper()
        
        data = []
        while ticks_to_wait > 0:
            #Begin charging new arrow
            self.agent.sendCommand("use 1")
            other.set_obs(load_grid(other.agent))
            if not other._obs:
                return
            arrow = find_mob_by_name(other._obs["Mobs"], "Arrow")
            if arrow:
                data.append((np.asarray([arrow["x"], arrow["y"], arrow["z"]]), other._obs["time"]))
            ticks_to_wait -= 1
            keeper.advance_by(0.05)

        vert_error = 0
        hori_error = 0
        if len(data) > 0:
            target_loc = np.asarray([target_transform["x"], target_transform["y"], target_transform["z"]])
            abs_velocity = np.asarray([target_transform["motionX"], target_transform["motionY"], target_transform["motionZ"]])
            target_velocity = project_vector(abs_velocity, vector_from_angle(self.transform["yaw"]))
            closest_point = get_closest_point(data, target_loc)
            for i in range(len(data)):
                if self.desired_pitch < 85 and (i == 0 or not np.array_equal(data[i][0], data[i-1][0])):
                    self.data_set.vert_shots[1].append([magnitude(data[i][0][::2] - np.asarray([self.transform["x"], self.transform["z"]])), data[i][0][1] - self.transform["y"], self.desired_pitch])
                    pred_location = data[i][0] - abs_velocity*(data[i][1]-self.last_shot)/1000
                    self.data_set.hori_shots[1].append([get_hori_angle(self.transform["x"], self.transform["z"], pred_location[0], pred_location[2]), \
                                               magnitude(data[i][0][::2] - np.asarray([self.transform["x"], self.transform["z"]])), target_velocity[0], self.desired_yaw])
                if i > 1 and get_angle_between(data[i][0] - data[i-1][0], data[i-1][0] - data[i-2][0]) > 45:
                    break
            self.vert_error = closest_point[1] - target_loc[1]
            self.hori_error = get_hori_angle(self.transform["x"], self.transform["z"], closest_point[0], closest_point[2]) - \
                        get_hori_angle(self.transform["x"], self.transform["z"], target_loc[0], target_loc[2])
            self.hori_error = ((self.hori_error + 180) % 360) - 180

            self.vert_errors.append(vert_error)
            self.hori_errors.append(hori_error)
            self.commands.append((self.agent, "chat /kill @e[type=!player]", self.total_time + 0))

        return -((vert_error**2 + hori_error**2)**0.5)

