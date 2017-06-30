import numpy as np
import io
from PIL import Image
import threading, time
import asyncio
import datetime
import random
import websockets

class WebSocketThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True
        self.lock = threading.Lock()
        self.data = None
        
    async def send_updates(self, websocket, path):
        while True:
            with self.lock:
                data = self.data
                self.data = None
            if data is None:
                asyncio.sleep(0.03)
                continue
            img = Image.fromarray(data, 'RGB')
            f = io.BytesIO()
            img.save(f, format='png')
            f.seek(0)
            await websocket.send(f.read())
            await asyncio.sleep(0.01)

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        start_server = websockets.serve(self.send_updates, '127.0.0.1', 12345)
        loop.run_until_complete(start_server)
        loop.run_forever()

    def set_data(self, data):
        with self.lock:
            self.data = data


thread = WebSocketThread()
thread.start()


for i in range(100):
    d = np.random.normal(size=(10, 10, 3), loc=128, scale=20).astype('ubyte')
    thread.set_data(d)
    time.sleep(0.5)

thread.join()
