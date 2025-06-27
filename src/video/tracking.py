import cv2
import logging

from src.libs.shared_memory import SharedMemory
from src.video.capture import VideoCapturing
from src.video.send import VideoSending

def norm_error(error, max_value): 
    return max(min(error / max_value, 1), -1)

class VideoTracking():
    def __init__(self, shmem: SharedMemory):
        self.shmem = shmem

        self.capture = VideoCapturing(shmem)
        self.sending = VideoSending(shmem)

        self.tracker: cv2.Tracker | None = None
        self.roi_size = 50
        self.init_roi = None
        self.target_roi = None
        self.is_tracking = False
        self.error = (0, 0)
        self.frame_param = (0, 0)

    def to_draw_border(self, frame, p1, p2, length=5, thickness=1, color=(0, 255, 51)):
        # top left corner
        cv2.line(frame, p1, (p1[0] + length, p1[1]), color, thickness)
        cv2.line(frame, p1, (p1[0], p1[1] + length), color, thickness)
        # top right corner
        cv2.line(frame, (p2[0], p1[1]), (p2[0] - length, p1[1]), color, thickness)
        cv2.line(frame, (p2[0], p1[1]), (p2[0], p1[1] + length), color, thickness)
        # bottom left corner
        cv2.line(frame, (p1[0], p2[1]), (p1[0] + length, p2[1]), color, thickness)
        cv2.line(frame, (p1[0], p2[1]), (p1[0], p2[1] - length), color, thickness)
        # bottom right corner
        cv2.line(frame, p2, (p2[0] - length, p2[1]), color, thickness)
        cv2.line(frame, p2, (p2[0], p2[1] - length), color, thickness)

    def init_track(self, frame):
        self.tracker = cv2.TrackerCSRT.create()
        self.tracker.init(frame, self.init_roi)
        self.is_tracking = True
        self.is_retarget = False

    def calculate_error(self, frame):
        height, width, _ = frame.shape
        self.frame_param = (height, width)
        (x, y, w, h) = self.target_roi
        target_point = (x + w // 2, y + h // 2)
        error_x = width // 2 - target_point[0]
        error_y = height // 2 - target_point[1]
        norm_error_x = norm_error(error_x, width / 2)
        norm_error_y = norm_error(error_y, height / 2)
        self.error = (norm_error_x, norm_error_y)

    def on_track(self, frame):
        try:
            if not self.init_roi:
                return
            
            if not self.is_tracking:
                self.init_track(frame)
            
            (success, box) = self.tracker.update(frame)

            if not success: 
                raise Exception("lost target")
            
            (x, y, w, h) = [int(v) for v in box]
            self.target_roi = (x, y, w, h)
            self.calculate_error(frame)
            self.to_draw_border(frame, (x, y), (x + w, y + h), 5, 3, (0, 255, 51))
        except Exception as err:
            logging.error(f"TRACKER: {err}")         
            self.target_roi = None
            self.init_roi = None
            self.is_tracking = False
            self.error = (0, 0)
    
    def update_client_param(self):
        new_init_roi = self.shmem.read_data("client_init_roi")
        new_roi_size = self.shmem.read_data("client_roi_size")
        new_is_retarget = self.shmem.read_data("client_is_retarget")
        
        if new_init_roi == False and new_roi_size:
            print("Reset ROI")
            self.init_roi = None
            self.target_roi = None
            self.is_tracking = False
            self.error = (0, 0)

        if new_init_roi and new_roi_size:
            self.init_roi = new_init_roi
            self.roi_size = new_roi_size
            self.target_roi = None
            self.is_tracking = False

        if new_is_retarget and new_roi_size and self.target_roi and self.is_tracking:
            self.roi_size = new_roi_size
            (x, y, w, h) = self.target_roi
            new_x = x + w // 2 - self.roi_size // 2
            new_y = y + h // 2 - self.roi_size // 2
            self.init_roi = (new_x, new_y, self.roi_size, self.roi_size)
            self.target_roi = None
            self.is_tracking = False
        
        self.shmem.write_data("client_init_roi")
        self.shmem.write_data("client_roi_size")
        self.shmem.write_data("client_is_retarget")
        
    def send_feedback(self):
        feedback = {
            "target_roi": self.target_roi,
            "is_tracking": self.is_tracking,
            "error": self.error,
            "frame_param": self.frame_param
        }

        for attr, value in feedback.items():
            self.shmem.write_data(attr, value)

    def next_iteration(self, frame):
        self.update_client_param()
        self.on_track(frame)
        self.send_feedback()

    def listen(self):
        while(True):
            if not self.shmem.is_in_frame():
                continue

            frame = self.shmem.get_in_frame()
            self.next_iteration(frame)
            self.shmem.put_out_frame(frame)

    def listen_3in1(self):
        cap = self.capture.connect_camera()

        if not cap:
            logging.error("TRACKER: no camera! Tracking is impossible!")
            return

        while(True):
            ret, frame = cap.read()
            if not ret:
                continue

            self.next_iteration(frame)
            self.sending.send_frame(frame)

    def start(self):
        self.listen_3in1()
