import cv2
from src.libs.shared_memory import SharedMemory

class VideoSending():
    def __init__(self, shmem: SharedMemory):
        self.shmem = shmem
        self.PORT = 6000
        self.host = None
        self.out = None
    
    def create_stream(self, host, port, w, h, fps = 30):
        gst_pipeline = (
            f'appsrc ! videoconvert ! x264enc speed-preset=ultrafast tune=zerolatency ! '
            f'rtph264pay ! udpsink host={host} port={port}'
        )
        return cv2.VideoWriter(gst_pipeline, cv2.CAP_GSTREAMER, 0, fps, (w, h), True)   

    def send_frame(self, frame):
        self.update_shared_param()

        if not self.host:
            if self.out:
                self.out.release()
                self.out = None
            return

        if not self.out:
            h, w, _ = frame.shape
            self.out = self.create_stream(self.host, self.PORT, w, h)
        
        self.out.write(frame)

    def start(self):
        while(True):
            if not self.shmem.is_out_frame():
                continue

            frame = self.shmem.get_out_frame()
            self.send_frame(frame)

    def update_shared_param(self):
        client_ip = self.shmem.read_data("client_ip")
        self.host = client_ip if self.host != client_ip else self.host
