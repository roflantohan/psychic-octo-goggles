import cv2
from src.libs.shared_memory import SharedMemory

class VideoCapturing():
    def __init__(self, shmem: SharedMemory):
        self.shmem = shmem
        self.cam_methond = self.shmem.read_config("cam_method")
        self.cam_path = self.shmem.read_config("cam_path")
        self.cam_enc = self.shmem.read_config("cam_enc")
        self.cam_width = self.shmem.read_config("cam_width")
        self.cam_height = self.shmem.read_config("cam_height")
        self.conn_str = self.shmem.read_config("gst_pipeline")
        self.cap = None
        self.enc_str = ""

    def connect_camera(self):
        if self.conn_str:
            return cv2.VideoCapture(self.conn_str, cv2.CAP_GSTREAMER)
        
        if self.cam_enc == "h264":
            self.enc_str = "rtph264depay ! h264parse ! avdec_h264"
        elif self.cam_enc == "h265":
            self.enc_str = "rtph265depay ! h265parse ! avdec_h265"
        else:
            return

        self.conn_str = (
            f'rtspsrc location={self.cam_path} latency=0 ! queue ! '
            f'{self.enc_str} ! videoconvert ! videoscale ! '
            f'video/x-raw,width={self.cam_width},height={self.cam_height},format=BGR ! '
            f'appsink drop=1'
        )
        return cv2.VideoCapture(self.conn_str, cv2.CAP_GSTREAMER)
    
    def start(self):
        self.cap = self.connect_camera()

        if not self.cap:
            return

        while True:
            ret, frame = self.cap.read()

            if not ret:
                continue

            self.shmem.put_in_frame(frame)
