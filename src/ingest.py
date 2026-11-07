import requests
BASE = "https://www.bankofcanada.ca/valet"

def fetch_series(series_id,recent=300):
    info = requests.get(f"{BASE}/series/{series_id}/json",timeout=30)
    info.raise_for_status()
    details = info.json()["seriesDetails"]

    resp = requests.get(f"{BASE}/observations/{series_id}/json",params={"recent": recent},timeout=30)
    resp.raise_for_status()
    observations = resp.json()["observations"]
    return details,observations

if __name__ == "__main__":
    details, obs = fetch_series("V39079", recent=10)
    print("Series:", details["label"])
    for row in obs:
        print(row["d"], row["V39079"]["v"])