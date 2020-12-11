import signal
import os
import time
import websocket
import logging
import numpy as np
import json

import tensorflow as tf

from datetime import datetime
from opcua import  Client

logger = logging.getLogger(__name__)

buff = list()

def on_message(ws, message):
    print(message)        
    
def on_error(ws, error):
    print(error)

def on_close(ws):
    print("### closed ###")

def on_open(ws):
    print("### opened ###")

# Connect to Websocket server
ws = websocket.WebSocket()
ws.connect("ws://192.168.9.238:8100/",on_message = on_message, on_error = on_error, on_close = on_close)
ws.on_open = on_open

ws.send('python')

# Connection with PLC using opcua protocol
url = "opc.tcp://192.168.3.21:5519"
client = Client(url)
client.connect()
D900 = client.get_node("ns=2;s=LP.F1.L1.PRS.TRASM.Data.D902")

pid = os.getpid()
g_recv_count = 0
val = 0
check_time = 0

array_size = 200
send_interval = 50

def logging_time(original_fn):
    def wrapper_fn(*args, **kwargs):
        start_time = datetime.now()
        result = original_fn(*args, **kwargs)
        end_time = datetime.now()
        print("Working time[{}]: string at {} , during {} sec".format(original_fn.__name__, start_time.strftime("%H:%M:%S.%f"), end_time-start_time))
        return result
    return wrapper_fn

# @logging_time
def collection_handler(signum, frame):
    global g_recv_count, buff, client, val, check_time
    if val == 0:
        check_time = time.time()

    cur_time = time.time()
    if cur_time - check_time <= 0.0102:
        val = D900.get_value()
    
    buff.append(val)
    if len(buff)>=array_size:
        g_recv_count += 1
    check_time = cur_time
    # print("test {0:04d}, cur_time - check_time : {1:.4f}, val : {2:.1f}".format(g_recv_count%1000, cur_time - check_time, val))

def classification_handler(signum, frame):
    global buff
    x = buff[:]
    r = model.predict(np.array(x).reshape(1, array_size,1))
    r_np = np.round(r[0])

    result = {
        "device_operation" : int(r_np[1]),
        "device_error" : int(r_np[0]),
        "time" : str(time.time()),
        "data" : str(x)
    }
    # print(result)

    ws.send(json.dumps(result))
    ack_text = ws.recv()
    if ack_text == 'closed':
        os.system('kill -9 ' + str(pid))

if __name__ == '__main__':
    # Load Model
    model= tf.keras.models.load_model("ShinShin")
    model.summary()

    # Receive data (10ms intervals)
    signal.signal(signal.SIGALRM, collection_handler)
    signal.setitimer(signal.ITIMER_REAL, 1, 0.01)

    while True:
        try:
            time.sleep(0.001)

            if len(buff)>=array_size:
                if g_recv_count > send_interval:
                    g_recv_count = 0
                    last_index = array_size * -1 - 1
                    buff = buff[last_index:-1]

                    signal.signal(signal.SIGUSR1, classification_handler)
                    os.kill(os.getpid(), signal.SIGUSR1)            
        except KeyboardInterrupt:
            signal.alarm(0)
            break
