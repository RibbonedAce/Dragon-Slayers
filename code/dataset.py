

class DataSet():

    def __init__(self, horizontal_shots=[[],[]], vertical_shots=[[],[]]):
        self.hori_shots = horizontal_shots
        self.vert_shots = vertical_shots

    def empty(self):
        return self.hori_shots == [[], []] or self.vert_shots == [[], []]



    def clear_horizontal_static_shots(self):
        #Hori_shots append (horz_angle_between shooter and target, distance to target, target's tangential velocity, aiming_yaw)
        for i in reversed(range(len(self.hori_shots[1]))):
            if(abs(self.hori_shots[1][2]) < 0.1):
                self.hori_shots[1].pop(i)

    def clear_vertical_static_shots(self):
        #Vert shots do not have velocity yet
        for i in reversed(range(len(self.vert_shots[1]))):
            if(abs(self.vert_shots[1][2]) < 0.1):
                self.vert_shots[1].pop(i)

    def clear_horizontal_leading_shots(self):
        #Hori_shots append (horz_angle_between shooter and target, distance to target, target's tangential velocity, aiming_yaw)
        for i in reversed(range(len(self.hori_shots[1]))):
            if(abs(self.hori_shots[1][2]) >= 0.1):
                self.hori_shots[1].pop(i)
    
    def clear_vertical_leading_shots(self):
        #Vert shots do not have velocity yet
        for i in reversed(range(len(self.vert_shots[1]))):
            if(abs(self.vert_shots[1][2]) >= 0.1):
                self.vert_shots[1].pop(i)

    
