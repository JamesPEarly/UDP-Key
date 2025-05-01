import socket
import threading
import time
from pynput import keyboard

# Keys and their associated source and destination info
KEY_NETWORK_MAPPING = {
    'w': {'src_port': 6001, 'dst_ip': '192.168.1.1', 'dst_port': 5001},
    'a': {'src_port': 6002, 'dst_ip': '192.168.1.1', 'dst_port': 5001},
    's': {'src_port': 6003, 'dst_ip': '192.168.1.1', 'dst_port': 5001},
    'd': {'src_port': 6004, 'dst_ip': '192.168.1.1', 'dst_port': 5001},
    'space': {'src_port': 6005, 'dst_ip': '192.168.1.1', 'dst_port': 5001},
}

# Track which keys are being held
active_keys = {}
key_press_times = {}

lock = threading.Lock()

def build_message(key):
    with lock:
        press_time = key_press_times.get(key)
    if press_time is not None:
        duration = time.time() - press_time
    else:
        duration = 0.0
    return f"{key}: {duration:.2f} seconds".encode()

def send_packets(key, src_port, dst_ip, dst_port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', src_port))
    print(f"[{key}] Sending thread started: {src_port} -> {dst_ip}:{dst_port}")

    while True:
        with lock:
            is_active = active_keys.get(key, False)
        if is_active:
            message = build_message(key)
            sock.sendto(message, (dst_ip, dst_port))
            print(f"[{key}] Sent: {message.decode()}")
            time.sleep(0.1)  # every 100ms
        else:
            time.sleep(0.01)

def on_press(key):
    try:
        k = key.char
    except AttributeError:
        k = str(key).split('.')[-1]

    if k in KEY_NETWORK_MAPPING:
        with lock:
            if not active_keys.get(k, False):
                key_press_times[k] = time.time()
            active_keys[k] = True

def on_release(key):
    try:
        k = key.char
    except AttributeError:
        k = str(key).split('.')[-1]

    if k in KEY_NETWORK_MAPPING:
        with lock:
            active_keys[k] = False
            key_press_times[k] = None  # clear the time when key is released

def start_listener():
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

if __name__ == "__main__":
    with lock:
        for key in KEY_NETWORK_MAPPING:
            active_keys[key] = False
            key_press_times[key] = None

    # Start sending threads
    for key, netinfo in KEY_NETWORK_MAPPING.items():
        threading.Thread(
            target=send_packets,
            args=(key, netinfo['src_port'], netinfo['dst_ip'], netinfo['dst_port']),
            daemon=True
        ).start()

    # Start keyboard listener
    start_listener()
