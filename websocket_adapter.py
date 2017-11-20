import numpy as np
import io
from PIL import Image
import threading, time, itertools
import asyncio
import datetime
import random
import websockets
import json
import sys



class WebSocketAdapter(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.event_callback = None
        self.daemon = True
        self.lock = threading.Lock()
        self.data = None
        self.start()
        
    def set_callback(self, cb):
        self.event_callback = cb
        
    async def send_updates(self, websocket):
        while True:
            with self.lock:
                data = self.data
                self.data = None
            
            if data is None:
                await asyncio.sleep(0.03)
                continue
            
            await websocket.send(data)
            await asyncio.sleep(0.01)

    async def recv_events(self, websocket):
        while True:
            message = await websocket.recv()
            try:
                self.event_callback(message)
            except Exception:
                sys.excepthook(*sys.exc_info())

    async def handler(self, websocket, path):
        tasks = [asyncio.ensure_future(self.send_updates(websocket)),
                 asyncio.ensure_future(self.recv_events(websocket))]
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

        for task in pending:
            task.cancel()
        
    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        start_server = websockets.serve(self.handler, '127.0.0.1', 12345)
        loop.run_until_complete(start_server)
        loop.run_forever()

    def send(self, data):
        with self.lock:
            self.data = data
