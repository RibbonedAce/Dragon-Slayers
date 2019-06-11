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


def logistic(x):
    '''
    max_val / {1 + e^(-kx)}
    '''
    return 1/(1 + 2.71828**(-7*(x**1-0.5)))

def lerp(low, high, perc):
    return low + perc*(high-low)

def clamp(low, high, value):
    if value < low:
        return low
    if value > high:
        return high
    return value

def clamped_lerp(low, high, perc):
    return clamp(low, high, lerp(low, high, perc))



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
            result["time"] = time.time()
            return result

        keeper.advance_by(0.05)
        wait_time += 0.05

def find_mob_by_name(mobs, name, new=False):
    for m in mobs:
        if m["name"] == name:
            return m
    return None
def find_entity_by_id(entities, id):
    for entity in entities:
        if entity["id"] == id:
            return entity

def find_new_arrow(entities, arrow_set):
    for entity in entities:
        if entity["name"] == "Arrow" and entity["id"] not in arrow_set:
            return entity

def magnitude(vector):
    return np.sqrt(np.sum(vector**2))

def flat_distance(vector):
    #magnitude of (x, 0, z).  Ignore y difference
    return math.sqrt(vector[0]**2 + vector[2]**2)

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
    return math.degrees(math.acos(max(-1, min(prod/(mag1*mag2), 1))))

def vector_from_angle(angle):
    return np.asarray([math.sin(math.radians(angle+180)), 0, math.cos(math.radians(angle))])

def project_vector(vector1, vector2):
    prod = np.dot(vector1, vector2)
    magsq = np.sum(vector2**2)
    return prod/magsq * vector2

def signed_quadratic_features(data, features, include_bias=False):
    result = np.zeros(data.shape)
    for i in range(len(data)):
        to_add = np.zeros(data.shape[1])
        square_indices = [int(j*features - j*(j-1)/2) for j in range(features)]
        to_add[:features] = data[i,:features]
        for j in range(features, data.shape[1]):
            if j-features in square_indices:
                ft = square_indices.index(j-features)
                if data[i,ft] < 0:
                    to_add[j] = -data[i,j]
                else:
                    to_add[j] = data[i,j]
            else:
                to_add[j] = data[i,j]
        result[i,:] = to_add
    return result

def get_closest_point(curve, target):
    '''
    Get closest points based on two lists of locations at times.
    Curve is a list of points that define a trajectory.
    Target is a list of points that define the target location.
    Returns the 2 closest points on the list of segments at a given time.
    ''' 
    
    if len(curve) == 0 or len(target) == 0:
        return None

    point1, point2 = curve[0][0], target[0][0]
    min_distance = magnitude(point1 - point2)
    for i in range(1, len(curve)):
        dist = magnitude(curve[i][0] - target[i][0])
        if dist < min_distance:
            point1, point2 = curve[i][0], target[i][0]
            min_distance = dist

    return point1, point2

AIMING = 0
SHOOT = 1
class ArrowTracker():

    def __init__(self, malmo_agent, arrow_id, stored_data, aim_data):
        self.malmo_agent = malmo_agent
        self.arrow_id = arrow_id
        self.track_duration = 50
        self.delete_me = False
        self.target_data = []
        self.arrow_data = []
        self.stored_data = stored_data
        self.aim_data = aim_data
        self.count = 0

    def step(self, target_transform, obs):
        if self.track_duration > 0:
            self.track_duration -= 1
            self.track_arrow(target_transform, obs)
        else:
            self.delete_me = True
            self.malmo_agent.analyze_arrow_trajectory(target_transform, self.arrow_data, self.target_data, self.stored_data, self.aim_data)

    def track_arrow(self,target_transform, obs):
        '''
        This function is run once per tick.
        Add the current position of the arrow to a list, if it is different from the
        previous position.
        '''
        arrow = find_entity_by_id(obs["Mobs"], self.arrow_id)
        self.target_data.append((np.asarray([target_transform["x"], target_transform["y"], target_transform["z"]]), obs["time"]))
        #if arrow found
        if arrow:
            #get arrow location
            arrow_vec = np.asarray([arrow["x"], arrow["y"], arrow["z"]])
            #if first arrow data or different from previous arrow data
            #avoid appending duplicate adjacent data
            
            if len(self.arrow_data) == 0 or not np.array_equal(arrow_vec,self.arrow_data[-1][0]):
                self.arrow_data.append((arrow_vec, obs["time"]))
        return None

  
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
        self.stored_data = []
        #Data set encapsulates hori_shots and vert_shots
        self.data_set = data_set
        self.hori_errors = []
        self.vert_errors = []
        self.model = model

        #Decide if we need to get data for vertical shots
        if self.data_set and not self.data_set.empty():
            vert_shots = np.asarray(self.data_set.vert_shots[0] + self.data_set.vert_shots[1])[:,2]
            max_angle = np.max(vert_shots)
            min_angle = np.min(vert_shots)
            self.vert_angle_step = 45 if max_angle - min_angle > 40 else -3
        else:
            self.vert_angle_step = 0

        #shooter parameters
        self.reset_shoot_loop()

    def reset_shoot_loop(self):
        self.min_aim_duration = 20
        self.max_record_duration = 50 #ticks
        self.shoot_state = AIMING
        self.aim_timer = 0
        self.shoot_timer = 0
        self.aim_on_target_ticks = 0
        self.end_mission = False
      
        self.listen_for_new_arrow = False
        self.arrow_ids = set()
        self.arrow_trackers = []
        self.aim_data = []

        #Scales turning speed
        self.turn_speed_multiplier = (1/360)* 2

    def step(self, obs):
        #Run this once a tick
        if(obs is not None):
            self.set_obs(obs)
        self.total_time += 1
        self.process_commands(self.total_time)


    def shooter_step(self, shooter_obs, move_agent, target_transform):
        '''
        This function:
        1. calls step()
        2. aims at targets
        3. shoots when aiming at target
        4. finds id of nearly fired arrows
        5. calls the step function of all arrow trackers
              -arrow trackers call record_data()
        6. returns whether a new shot has started
        '''
        
        result = False
        self.step(shooter_obs)
        #Abort if no target to aim at/record data for
        if target_transform is None:
            return None
        self.aim_data.append((self.transform["yaw"], -self.transform["pitch"], time.time()))
        mover_obs = move_agent._obs

        #aims over max_aim_duration many ticks
        if self.shoot_state == AIMING:
            if self.aim_timer < self.min_aim_duration:
                if self.aim_timer == 0:
                    #Calculate desired aim once at start of aiming loop
                    #aim_iteration is used to calculate rotation speed
                    self.agent.sendCommand("use 1")
                    result = True
                    self.desired_yaw, self.desired_pitch = self.calculate_desired_aim(target_transform)
                    
                self.aim_timer += 1
                aiming_complete = self.aim_step(self.desired_yaw, self.desired_pitch)
                
            else:
                self.aim_timer = 0
                self.aim_on_target_ticks = 0
                self.shoot_state = SHOOT

        #Shoot if done aiming
        if self.shoot_state == SHOOT:
            self.agent.sendCommand("use 0")
            self.stored_data = self.current_data
            self.stored_data[2] = self.transform["yaw"]
            if self.shoot_timer < 2:
                self.shoot_timer += 1
            else:
                self.shoot_timer = 0
                self.shoot_state = AIMING
                self.listen_for_new_arrow = True
                self.vert_angle_step = min(45, self.vert_angle_step + 3)

        #Find newly fired arrows
        if self.listen_for_new_arrow:
            #An arrow has just been shot, so look through the observations and find it
            arrow = find_new_arrow(mover_obs["Mobs"],self.arrow_ids)
            if arrow != None:
                #add to set and stop listening for arrows
                self.arrow_ids.add(arrow["id"])
                self.arrow_trackers.append(ArrowTracker(self,arrow["id"], self.stored_data, self.aim_data))
                self.listen_for_new_arrow = False
                self.aim_data = []
                
        #Track positions of all arrows in flight
        self.track_arrows_step(mover_obs,target_transform)
        return result


    def calculate_desired_aim(self, target_transform):
        distance = vert_distance(target_transform["x"], target_transform["z"], self.transform["x"], self.transform["z"])
        elevation = target_transform["y"] - self.transform["y"]
        obs_angle = ((get_hori_angle(self.transform["x"], self.transform["z"], target_transform["x"], target_transform["z"]) + 180) % 360) - 180
        rel_angle = ((obs_angle - self.transform["yaw"] + 180) % 360) - 180
        x_angle = ((obs_angle + 180 + 90) % 360) - 180
        x_velocity = project_vector(np.asarray([target_transform["motionX"], target_transform["motionY"], target_transform["motionZ"]]), vector_from_angle(x_angle))
        x_velocity = math.copysign(magnitude(x_velocity), math.cos(math.radians(get_angle_between(vector_from_angle(x_angle), x_velocity))))
        z_velocity = project_vector(np.asarray([target_transform["motionX"], target_transform["motionY"], target_transform["motionZ"]]), vector_from_angle(obs_angle))
        z_velocity = math.copysign(magnitude(z_velocity), math.cos(math.radians(get_angle_between(vector_from_angle(obs_angle), z_velocity))))
        #set desired pitch
        delta_pitch = self.get_first_vert_shot(distance, elevation+1)
        #set desired yaw
        delta_yaw = self.get_first_hori_shot(rel_angle, distance, x_velocity, z_velocity)

        #Store some data points now to use for future data points
        self.current_data = [x_velocity, z_velocity, self.transform["yaw"]]
        return (((self.transform["yaw"] + delta_yaw + 180) % 360) - 180,-delta_pitch)

    def aim_step(self, desiredYaw, desiredPitch):
        '''
        Set pitch and yaw movement for a single tick.
        Returns true if aiming is complete
        '''
        if desiredYaw == None and desiredPitch == None:
            return
        
        #Get current yaw and pitch
        current_yaw = self.transform["yaw"]
        current_pitch = self.transform["pitch"]
        #Calculate difference in yaw and pitch to desired angle
        yaw_diff = 0
        if desiredYaw != None:
            yaw_diff = desiredYaw - current_yaw
        pitch_diff = 0
        if desiredPitch != None:
            pitch_diff = desiredPitch - current_pitch

        #If aiming at the right angle, return true
        allowable_deviation = 0.2 #degrees
        '''
        The curve from [0,1] is modified by exponentiating the value.
        This adjusts speeds when near 0 or near 1.
        '''
      
        if abs(yaw_diff) < allowable_deviation:
            self.agent.sendCommand("turn 0")
        else:
            #set aim direction
            yaw_multiplier = 1
            while yaw_diff > 180:
                yaw_diff = yaw_diff - 360
            while(yaw_diff < -180):
                yaw_diff = yaw_diff + 360
            yaw_multiplier = -1 if yaw_diff < 0 else 1
            self.agent.sendCommand("turn " + str(yaw_multiplier * abs(yaw_diff) * self.turn_speed_multiplier))

        if abs(pitch_diff) < allowable_deviation:
            self.agent.sendCommand("pitch 0")
        else:
            #set aim direction
            pitch_multiplier = -1 if pitch_diff < 0 else 1
            self.agent.sendCommand("pitch " + str( pitch_multiplier * abs(pitch_diff) * self.turn_speed_multiplier))



        
        if (abs(yaw_diff) < allowable_deviation and abs(pitch_diff) < allowable_deviation):
            #Aim is good when the aim has been on the target angle for two consecutive ticks.
            #This is to counteract times when aim is correct but current look velocity
            #is too high so it throws off the aim before the stop command is issued
            if self.aim_on_target_ticks >= 3:
                    return True   
            else:
                self.aim_on_target_ticks += 1
                return False

                
        
          
        #Aim not yet finished, return false and keep iterating
        self.aim_on_target_ticks = 0
        return False

    def track_arrows_step(self,mover_obs, target_transform):
        #Iterate through arrow trackers
        for tracker in self.arrow_trackers:
            tracker.step(target_transform, mover_obs)
        #Delete any completed trackers
        for i in reversed(range(len(self.arrow_trackers))):
            if self.arrow_trackers[i].delete_me:
                self.arrow_trackers.pop(i)

    def analyze_arrow_trajectory(self, target_transform, data, target_data, obs, aim_data):        
        player_loc = np.asarray([self.transform["x"], self.transform["y"], self.transform["z"]])
        pred_velocity = obs[0] * vector_from_angle(((obs[2] + 180 + 90) % 360) - 180) + obs[1] * vector_from_angle(obs[2])
        
        vert_error = 0
        hori_error = 0
        if len(data) > 0:
            #data_preds = []
            last_distance_from_player = 0
            current_distance_from_player = 0

            #Count the number of instances where distance to arrow decreases
            reverse_ticks = 0
            
            for i in range(len(data)):
                if self.desired_pitch < 85 and (i == 0 or not np.array_equal(data[i][0], data[i-1][0])):
                    d_elevation = data[i][0][1] - player_loc[1]
                    pred_location = data[i][0] - pred_velocity*(data[i][1]-aim_data[0][2])
                    #data_preds.append(pred_location)
                    d_distance = magnitude(pred_location[::2] - np.asarray([self.transform["x"], self.transform["z"]]))
                    #get arrow position distance from shooter.  Ignore y-difference
                    current_distance_from_player = flat_distance(data[i][0]-player_loc)

                    #Arrow hits if arrow's distance from player decreases.  Arrow's should strictly move away from the player's shooting position if they do not hit anyone
                    if i > 1 and current_distance_from_player < last_distance_from_player:
                        reverse_ticks += 1

                    #Update previous position
                    last_distance_from_player = current_distance_from_player
                    d_angle = ((get_hori_angle(player_loc[0], player_loc[2], pred_location[0], pred_location[2]) - aim_data[0][0] + 180) % 360) - 180
                    self.data_set.vert_shots[1].append([d_distance, d_elevation, aim_data[-1][1]])
                    self.data_set.hori_shots[1].append([d_angle, d_distance, obs[0], obs[1], obs[2] - aim_data[0][0]])
    
                #get arrow position distance from shooter.  Ignore y-difference
                current_distance_from_player = flat_distance(data[i][0]-player_loc)

                #Arrow hits if arrow's distance from player decreases.  Arrow's should strictly move away from the player's shooting position if they do not hit anyone
                if i > 1 and current_distance_from_player < last_distance_from_player:
                    reverse_ticks += 1

                #Update previous position
                last_distance_from_player = current_distance_from_player

            #Append errors depending on how close the arrow got
            print(self.data_set.hori_shots[1][-1])
            closest_point, target_loc = get_closest_point(data, target_data)
            vert_error = closest_point[1] - target_loc[1]
            hori_error = get_hori_angle(self.transform["x"], self.transform["z"], closest_point[0], closest_point[2]) - \
                        get_hori_angle(self.transform["x"], self.transform["z"], target_loc[0], target_loc[2])
            hori_error = ((hori_error + 180) % 360) - 180

            self.vert_errors.append(vert_error)
            self.hori_errors.append(hori_error)
            #An arrow hits the target if it has moved backward for more than 2 ticks
            #(Arrows that hit nothing decrease in distance for 1-2 ticks)
            if reverse_ticks > 2:
                pass
                #self.end_mission = True

        return -((vert_error**2 + hori_error**2)**0.5)
    

    def reset(self):
        #Reset the time for commands
        self.total_time = 0
        self.comands = []
        self._obs = None
        
    def set_obs(self, obs):
        if not obs:
            return
        has_prev = True if self._obs else False
        self._obs = obs
        has_prev = self.transform is not None
        for entity in self._obs["Mobs"]:
            if entity["name"] == self.name:
                if has_prev:
                    # Append past data
                    self.transform["prevX"].append(self.transform["x"])
                    if len(self.transform["prevX"]) > 4:
                        self.transform["prevX"].pop(0)
                    self.transform["prevY"].append(self.transform["y"])
                    if len(self.transform["prevY"]) > 4:
                        self.transform["prevY"].pop(0)
                    self.transform["prevZ"].append(self.transform["z"])
                    if len(self.transform["prevZ"]) > 4:
                        self.transform["prevZ"].pop(0)
                    self.transform["prevTime"].append(self.transform["time"])
                    if len(self.transform["prevTime"]) > 4:
                        self.transform["prevTime"].pop(0)
                    
                else:
                    # Create past data if none exists
                    self.transform = {}
                    self.transform["prevX"] = []
                    self.transform["prevY"] = []
                    self.transform["prevZ"] = []
                    self.transform["prevTime"] = []

                # Apply stats not found in normal transforms
                old_transform = self.transform
                self.transform = entity
                self.transform["prevX"] = old_transform["prevX"]
                self.transform["prevY"] = old_transform["prevY"]
                self.transform["prevZ"] = old_transform["prevZ"]
                self.transform["prevTime"] = old_transform["prevTime"]
                self.transform["time"] = self._obs["time"]

                # Calculate velocity
                if has_prev:
                    self.transform["motionX"] = (self.transform["x"] - self.transform["prevX"][0]) / (self.transform["time"] - self.transform["prevTime"][0])
                    self.transform["motionY"] = (self.transform["y"] - self.transform["prevY"][0]) / (self.transform["time"] - self.transform["prevTime"][0])
                    self.transform["motionZ"] = (self.transform["z"] - self.transform["prevZ"][0]) / (self.transform["time"] - self.transform["prevTime"][0])
                    

    def get_first_vert_shot(self, distance, elevation):
        array = np.asarray(self.data_set.vert_shots[0] + self.data_set.vert_shots[1])
        if array.shape[0] > 100:
            if elevation > distance:
                array = array[array[:,-1] > 45]
            else:
                array = array[array[:,-1] <= 45]
            if self.vert_angle_step >= 45:
                poly = PolynomialFeatures(3, include_bias=False).fit(array[:,:-1])
                self.model = LinearRegression().fit(poly.transform(array[:,:-1]), array[:,-1])
                return min(self.model.predict(poly.transform([[distance, elevation]]))[0], 89.9)

        return self.vert_angle_step


    def get_next_vert_shot(self, prev_angle, error, step_size):
        bound_angle = prev_angle    
        if error < 0:
            bound_angle = 90
        elif error > 0:
            bound_angle = 0
        return prev_angle*(1-step_size) + bound_angle*step_size

    def get_first_hori_shot(self, angle, distance, x_velocity, z_velocity):
        array = np.asarray(self.data_set.hori_shots[0] + self.data_set.hori_shots[1])
        if array.shape[0] > 100:
            poly = PolynomialFeatures(2, include_bias=False).fit(array[:,:-1])
            self.model = LinearRegression().fit(signed_quadratic_features(poly.transform(array[:,:-1]), 4), array[:,-1])
            return min(max(-180, self.model.predict(signed_quadratic_features(poly.transform([[angle, distance, x_velocity, z_velocity]]), 4))[0]), 180)
        
        return random.randrange(-180, 180)

    def get_next_hori_shot(self, prev_angle, error, step_size):
        result = prev_angle - error
        return ((result + 180) % 360) - 180


    def process_commands(self, mission_elapsed_time):
        for command in self.commands:
            if command[2] <= mission_elapsed_time:
                self.commands.remove(command)
                command[0].sendCommand(command[1])

