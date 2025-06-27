import asyncio
from multiprocessing import Process

from src.libs.config_loader import ConfigLoader
from src.server.websocket import WebSocketServer
from src.video.tracking import VideoTracking
from src.autopilot.uav_control import UAVControl

from src.libs.shared_memory import SharedMemory

if __name__ == "__main__":
    shmem = SharedMemory()
    ConfigLoader("config.json", shmem).load()

    processes = [
        Process(target=UAVControl(shmem).start),
        Process(target=VideoTracking(shmem).start),
    ]

    for p in processes: p.start()
        
    asyncio.run(WebSocketServer(shmem).start())

    for p in processes: p.terminate()
        


