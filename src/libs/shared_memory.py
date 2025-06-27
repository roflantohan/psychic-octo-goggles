from multiprocessing import Manager

class SharedMemory:
    def __init__(self):
        manager = Manager()
        self.config = manager.dict()
        self.shared = manager.dict()
        self.in_queue = manager.Queue(maxsize=120)
        self.out_queue = manager.Queue(maxsize=120)

    def write_config(self, param, value = None):
        self.config[param] = value
    
    def read_config(self, param):
        return self.config.get(param, None)

    def write_data(self, param, value = None):
        self.shared[param] = value
    
    def read_data(self, param):
        return self.shared.get(param, None)

    def put_in_frame(self, frame):
        return self.in_queue.put(frame)

    def get_in_frame(self):    
        return self.in_queue.get()
    
    def is_in_frame(self):
        return bool(self.in_queue.qsize())
    
    def put_out_frame(self, frame):
        return self.out_queue.put(frame)

    def get_out_frame(self):    
        return self.out_queue.get()
    
    def is_out_frame(self):
        return bool(self.out_queue.qsize())
