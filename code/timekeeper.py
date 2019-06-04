import time

class TimeKeeper:
    def __init__(self):
        self.catchup()

    def advance_by(self, interval):
        current_time = time.time()
        if current_time < self.current_time + interval:
            time.sleep(current_time - self.current_time + interval)
        self.current_time = max(self.current_time + interval, current_time)

    def catchup(self):
        self.current_time = time.time()
