import logging
import time
from pymavlink import mavutil, mavextra

class ArduPilotBase():
    def __init__(self):
        self.master = None
        self.flight_mode = None
        self.roll = 0
        self.pitch = 0
        self.yaw = 0
        self.altitude = 0
        self.air_speed = 0 
        self.ground_speed = 0
        self.vertical_speed = 0
        self.heading = 0
        self.throttle_lvl = 0
    
    def is_connect(self):
        return bool(self.master)
    
    def connect_drone(self, path, baud = 115200):
        if not path: return
            
        try:
            self.master = mavutil.mavlink_connection(path, baud)
            self.master.wait_heartbeat()
        except Exception as err:
            logging.error(f"AUTOPILOT: connection error: {err}")
            time.sleep(10)
            return self.connect_drone(path, baud)
        
    def get_attitude(self):
        if not self.is_connect(): return

        attitude = self.master.recv_match(type='ATTITUDE', blocking=False)

        if not attitude: return
        
        self.roll = attitude.roll
        self.pitch = attitude.pitch 
        self.yaw = attitude.yaw

    def get_flight_mode(self):
        if not self.is_connect(): return
        
        msg = self.master.recv_match(type='HEARTBEAT', blocking=False)

        if not msg: return

        if self.flight_mode != self.master.flightmode:
            self.flight_mode = self.master.flightmode

    def get_vfr_hud(self):
        if not self.is_connect(): return
            
        hud = self.master.recv_match(type='VFR_HUD', blocking=False)

        if not hud: return
            
        self.altitude = hud.alt
        self.air_speed = hud.airspeed
        self.ground_speed = hud.groundspeed
        self.heading = hud.heading
        self.vertical_speed = hud.climb 
        self.throttle_lvl = hud.throttle

    def set_flight_mode(self, mode):
        if self.is_connect(): self.master.set_mode(mode)

    def set_attitude_target(self, roll, pitch, yaw, thrust):
        if not self.is_connect(): return
            
        self.master.mav.set_attitude_target_send(
            0,
            self.master.target_system,
            self.master.target_component,
            0b00000000,
            mavextra.euler_to_quat([roll, pitch, yaw]),
            0, 0, 0,
            thrust
        )
