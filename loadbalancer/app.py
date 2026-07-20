from flask import Flask, jsonify, request
import requests
import random
import string
import threading
import time
import docker as docker_sdk
from consistent_hash import ConsistentHashMap

app = Flask(__name__)
client = docker_sdk.from_env()

IMAGE_NAME = "server-image"
NETWORK_NAME = "net1"
N_DEFAULT = 3

chm = ConsistentHashMap(M=512, K=9)
replicas = []          # list of hostnames
server_num_map = {}    # hostname -> numeric id used for hashing
next_num = [0]


def random_hostname():
    return "S" + ''.join(random.choices(string.digits, k=4))


def spawn_container(hostname):
    num = next_num[0]
    next_num[0] += 1
    server_num_map[hostname] = num
    client.containers.run(
        IMAGE_NAME,
        name=hostname,
        environment={"SERVER_ID": hostname},
        network=NETWORK_NAME,
        detach=True
    )
    chm.add_server(hostname, num)
    replicas.append(hostname)


def remove_container(hostname):
    try:
        c = client.containers.get(hostname)
        c.stop()
        c.remove()
    except Exception as e:
        print(f"Error removing {hostname}: {e}")
    chm.remove_server(hostname)
    if hostname in replicas:
        replicas.remove(hostname)


def heartbeat_check():
    while True:
        time.sleep(5)
        for hostname in list(replicas):
            try:
                r = requests.get(f"http://{hostname}:5000/heartbeat", timeout=2)
                if r.status_code != 200:
                    raise Exception("bad status")
            except Exception:
                print(f"{hostname} is down, replacing...")
                remove_container(hostname)
                new_host = random_hostname()
                spawn_container(new_host)


@app.route('/rep', methods=['GET'])
def rep():
    return jsonify({
        "message": {"N": len(replicas), "replicas": replicas},
        "status": "successful"
    }), 200


@app.route('/add', methods=['POST'])
def add():
    data = request.get_json()
    n = data.get("n", 0)
    hostnames = data.get("hostnames", [])

    if len(hostnames) > n:
        return jsonify({
            "message": "<Error> Length of hostname list is more than newly added instances",
            "status": "failure"
        }), 400

    for h in hostnames:
        spawn_container(h)
    for _ in range(n - len(hostnames)):
        spawn_container(random_hostname())

    return jsonify({
        "message": {"N": len(replicas), "replicas": replicas},
        "status": "successful"
    }), 200


@app.route('/rm', methods=['DELETE'])
def rm():
    data = request.get_json()
    n = data.get("n", 0)
    hostnames = data.get("hostnames", [])

    if len(hostnames) > n:
        return jsonify({
            "message": "<Error> Length of hostname list is more than removable instances",
            "status": "failure"
        }), 400

    for h in hostnames:
        remove_container(h)

    remaining_to_remove = n - len(hostnames)
    for _ in range(remaining_to_remove):
        if replicas:
            victim = random.choice(replicas)
            remove_container(victim)

    return jsonify({
        "message": {"N": len(replicas), "replicas": replicas},
        "status": "successful"
    }), 200


@app.route('/<path:path>', methods=['GET'])
def route_request(path):
    if path not in ["home"]:
        return jsonify({
            "message": f"<Error> '/{path}' endpoint does not exist in server replicas",
            "status": "failure"
        }), 400

    request_id = random.randint(100000, 999999)
    hostname = chm.get_server(request_id)

    if hostname is None:
        return jsonify({"message": "<Error> No servers available", "status": "failure"}), 500

    try:
        r = requests.get(f"http://{hostname}:5000/{path}", timeout=3)
        return r.json(), r.status_code
    except Exception as e:
        return jsonify({"message": f"<Error> {str(e)}", "status": "failure"}), 500


def initial_setup():
    for _ in range(N_DEFAULT):
        spawn_container(random_hostname())


if __name__ == '__main__':
    initial_setup()
    t = threading.Thread(target=heartbeat_check, daemon=True)
    t.start()
    app.run(host='0.0.0.0', port=5000)
