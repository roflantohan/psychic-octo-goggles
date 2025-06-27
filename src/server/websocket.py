import websockets
import asyncio
import json

from src.libs.shared_memory import SharedMemory

class WebSocketServer():
    def __init__(self, shmem: SharedMemory):
        self.shmem = shmem
        self.HOST = "0.0.0.0"
        self.PORT = 3030
        self.TIMEOUT = 0.1

        self.connected_clients = set()
        self.client_ip = None

        self.system_headers = [
            "is_tracking", 
            "target_roi", 
            "error", 
            "is_autopilot",
            "flight_mode",
            "course", 
            "altitude", 
            "heading", 
            "air_speed", 
            "ground_speed", 
            "vertical_speed", 
            "throttle_level",
        ]
        self.client_headers = [
            "init_roi", 
            "roi_size", 
            "flight_mode", 
            "is_retarget",
        ]

    def create_heartbeat(self):
        msg = dict()
        for name in self.system_headers:
            msg[name] = self.shmem.read_data(name)
        return json.dumps(msg)
    
    def on_message(self, msg: str):
        try:
            data: dict = json.loads(msg)
            for name in self.client_headers:
                self.shmem.write_data(f"client_{name}", data.get(name))
        except:
            return
        
    def on_client(self):
        self.shmem.write_data("client_ip", self.client_ip)

    async def on_connection(self, websocket, path):
        self.connected_clients.add(websocket)
        self.client_ip = websocket.remote_address[0]
        self.on_client()
        try:
            async for message in websocket:
                self.on_message(message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.connected_clients.remove(websocket)
            self.on_client()

    async def broadcast(self):
        while True:
            msg = self.create_heartbeat()
            websockets.broadcast(self.connected_clients, msg)
            await asyncio.sleep(self.TIMEOUT)

    async def start(self):
        server = websockets.serve(self.on_connection, self.HOST, self.PORT)
        await asyncio.gather(server, self.broadcast())
