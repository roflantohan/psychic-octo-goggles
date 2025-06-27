import math
import time

from src.libs.shared_memory import SharedMemory
from src.autopilot.pid_controller import PIDController
from src.autopilot.ardupilot import ArduPilotBase

def scale_error(norm_error, limits: tuple, revert = False): 
    result = norm_error * (limits[1] - limits[0]) / 2
    return result * (-1 if revert else 1)

class UAVControl(ArduPilotBase):
    
    def __init__(self, shmem: SharedMemory):
        ArduPilotBase.__init__(self)
        self.shmem = shmem

        # self.path = "/dev/ttyACM0" # RPi USB 3.0 Up port
        # self.path = "/dev/ttyAMA10"(0) # RPi UART(GPIO) port
        # self.path = "/dev/tty.usbmodem1301"(3) # MacOS M2 USB-C port
        # self.path = "tcp:192.168.0.105:5763" # SITL TCP port

        self.path: str = self.shmem.read_config("uav_path")
        self.baud: int = self.shmem.read_config("uav_baud")
        self.auto_mode: str = self.shmem.read_config("uav_automode")

        self.timeout: int = self.shmem.read_config("uav_timeout")
        self.delta_lost: int = self.shmem.read_config("uav_delta_lost")
        self.course_lost: tuple = tuple(self.shmem.read_config("uav_course_lost"))

        self.limit_roll: list = self.shmem.read_config("limit_roll")
        self.limit_pitch: list = self.shmem.read_config("limit_pitch")
        self.limit_yaw: list = self.shmem.read_config("limit_yaw")
        self.limit_throttle: float = self.shmem.read_config("limit_throttle")

        self.revert_roll: bool = self.shmem.read_config("revert_roll")
        self.revert_pitch: bool = self.shmem.read_config("revert_pitch")
        self.revert_yaw: bool = self.shmem.read_config("revert_yaw")

        self.pid_param_roll: list = self.shmem.read_config("pid_roll")
        self.pid_param_pitch: list = self.shmem.read_config("pid_pitch")
        self.pid_param_yaw: list = self.shmem.read_config("pid_yaw")

        self.pid_roll = PIDController(self.pid_param_roll)
        self.pid_pitch = PIDController(self.pid_param_pitch)
        self.pid_yaw = PIDController(self.pid_param_yaw)

        self.is_tracking = False
        self.is_autopilot = False
        self.error = (0, 0)
        self.course = self.course_lost
        self.last_time_aim = 0

    def update_drone_param(self):
        self.get_flight_mode()
        self.get_attitude()
        self.get_vfr_hud()
        self.is_autopilot = self.flight_mode == self.auto_mode

    def reset_PID(self):
        self.pid_roll.reset()
        self.pid_pitch.reset()
        self.pid_yaw.reset()
        self.course = self.course_lost

    def update_PID(self):
        self.pid_roll.update(self.error[0], self.timeout)
        self.pid_pitch.update(self.error[1], self.timeout)
        self.pid_yaw.update(self.error[0], self.timeout)

    def set_direction(self, reset_flag = False):
        if reset_flag:
            (roll, pitch, yaw, thrust) = self.course_lost
            self.set_attitude_target(roll, pitch, yaw, thrust)
            self.reset_PID()

        roll_correction = scale_error(self.pid_roll.get(), self.limit_roll, self.revert_roll)
        pitch_correction = scale_error(self.pid_pitch.get(), self.limit_pitch, self.revert_pitch)
        yaw_correction = scale_error(self.pid_yaw.get(), self.limit_yaw, self.revert_yaw)

        new_roll = math.radians(roll_correction)
        new_yaw = math.radians(yaw_correction)
        new_pitch = math.radians(max(min(self.pitch * (180 / math.pi) + pitch_correction, self.limit_pitch[1]), self.limit_pitch[0]))

        self.course = (math.degrees(new_roll), math.degrees(new_pitch), math.degrees(new_yaw), self.limit_throttle)

        if self.is_autopilot and self.master:
            self.set_attitude_target(new_roll, new_pitch, new_yaw, self.limit_throttle)

    def update_shared_param(self):
        self.error = self.shmem.read_data("error")
        is_tracking = self.shmem.read_data("is_tracking")
        self.is_tracking = is_tracking if self.is_tracking != is_tracking else self.is_tracking
        flight_mode = self.shmem.read_data("client_flight_mode")
        if flight_mode and self.flight_mode != flight_mode:
            self.set_flight_mode(flight_mode)

        self.shmem.write_data("client_flight_mode")

    def send_feedback(self):
        feedback = {
            "is_autopilot": self.is_autopilot, 
            "flight_mode":  self.flight_mode, 
            "course": self.course,
            "altitude": self.altitude,
            "heading": self.heading,
            "air_speed": self.air_speed,
            "ground_speed": self.ground_speed,
            "vertical_speed": self.vertical_speed,
            "throttle_level": self.throttle_lvl
        }

        for attr, value in feedback.items():
            self.shmem.write_data(attr, value)

    def start(self):
        self.connect_drone(self.path, self.baud)

        while True:
            self.update_shared_param()
            self.update_drone_param()
            
            if self.is_tracking:
                self.last_time_aim = time.time()
                self.update_PID()
                self.set_direction()
            elif self.is_autopilot:
                delta_t = time.time() - self.last_time_aim
                reset = True if delta_t > self.delta_lost else False
                self.set_direction(reset)

            self.send_feedback()
