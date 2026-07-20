import requests
import concurrent.futures
import matplotlib.pyplot as plt

NUM_REQUESTS = 10000
BASE_URL = "http://localhost:5000"

def make_request(_):
    try:
        requests.get(f"{BASE_URL}/home", timeout=5)
        return True
    except Exception:
        return False

def set_replica_count(target_n):
    current = requests.get(f"{BASE_URL}/rep").json()["message"]["N"]
    if target_n > current:
        requests.post(f"{BASE_URL}/add", json={"n": target_n - current, "hostnames": []})
    elif target_n < current:
        requests.delete(f"{BASE_URL}/rm", json={"n": current - target_n, "hostnames": []})

def main():
    ns = [2, 3, 4, 5, 6]
    avg_loads = []

    for n in ns:
        set_replica_count(n)
        print(f"N={n}, sending {NUM_REQUESTS} requests...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
            list(executor.map(make_request, range(NUM_REQUESTS)))
        avg_loads.append(NUM_REQUESTS / n)

    plt.figure(figsize=(8, 5))
    plt.plot(ns, avg_loads, marker='o')
    plt.xlabel("N (number of servers)")
    plt.ylabel("Average load per server")
    plt.title("A-2: Average load vs N")
    plt.savefig("analysis/plots/a2_line_chart.png")
    print("Saved chart to analysis/plots/a2_line_chart.png")

if __name__ == "__main__":
    main()
