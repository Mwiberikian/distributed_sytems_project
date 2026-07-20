import requests
import concurrent.futures
import matplotlib.pyplot as plt
from collections import Counter

URL = "http://localhost:5000/home"
NUM_REQUESTS = 10000

def make_request(_):
    try:
        r = requests.get(URL, timeout=5)
        return r.json().get("message", "")
    except Exception:
        return None

def main():
    print("Sending requests to /rep to confirm N=3...")
    print(requests.get("http://localhost:5000/rep").json())

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        for res in executor.map(make_request, range(NUM_REQUESTS)):
            results.append(res)

    counts = Counter(results)
    print(counts)

    labels = list(counts.keys())
    values = list(counts.values())

    plt.figure(figsize=(8, 5))
    plt.bar(labels, values)
    plt.xlabel("Server")
    plt.ylabel("Requests handled")
    plt.title("A-1: Request distribution across N=3 servers (10,000 requests)")
    plt.savefig("analysis/plots/a1_bar_chart.png")
    print("Saved chart to analysis/plots/a1_bar_chart.png")

if __name__ == "__main__":
    main()
