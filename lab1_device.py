# LAB 1 - Simulated CoreIOT device (paho-mqtt 2.x)
# Exercise 2: sends temperature, humidity and light every 3 s
# Exercise 4: answers RPC calls of the LED, PUMP and FAN switches
import json
import random
import time

import paho.mqtt.client as mqtt

BROKER = "app.coreiot.io"
PORT = 1883
ACCESS_TOKEN = "*****"                # Manage credentials
PERIOD = 3                                      # seconds between messages

state = {"LED": False, "PUMP": False, "FAN": False}   # simulated outputs


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("Connected to CoreIOT")
        client.subscribe("v1/devices/me/rpc/request/+")
    else:
        print("Connection failed:", reason_code)


def on_message(client, userdata, msg):
    request_id = msg.topic.split("/")[-1]
    try:
        req = json.loads(msg.payload)
    except json.JSONDecodeError:
        print("Invalid RPC payload:", msg.payload)
        return
    method, params = req.get("method", ""), req.get("params")
    print("RPC:", method, params)

    result = None
    if method.startswith("getState"):          # getStateLED / PUMP / FAN
        result = state.get(method[len("getState"):])
    elif method.startswith("setState"):        # setStateLED / PUMP / FAN
        name = method[len("setState"):]
        if name in state:
            new_value = bool(params)
            if new_value != state[name]:
                print(f"{name} -> {'ON' if new_value else 'OFF'}")
            state[name] = new_value
            result = new_value
            client.publish("v1/devices/me/attributes",
                           json.dumps({name.lower() + "_state": result}))
    # Reply so the switch widget knows the command succeeded
    client.publish("v1/devices/me/rpc/response/" + request_id,
                   json.dumps(result))


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                     client_id="LAB1_PYTHON_DEVICE")
client.username_pw_set(ACCESS_TOKEN)           # token = username
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, PORT, keepalive=60)
client.loop_start()

try:
    while True:
        data = {"temperature": round(random.uniform(25, 35), 1),
                "humidity": round(random.uniform(50, 85), 1),
                "light": random.randint(0, 1000)}
        client.publish("v1/devices/me/telemetry", json.dumps(data), qos=1)
        print("Sent:", data)
        time.sleep(PERIOD)
except KeyboardInterrupt:
    print("Stopping...")
finally:
    client.loop_stop()
    client.disconnect()
