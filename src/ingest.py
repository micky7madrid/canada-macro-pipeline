import requests

SERIES_ID = "V39079"
BASE = "https://www.bankofcanada.ca/valet"

# Part 1: ask the API what this series is, so we know we have the right one
info = requests.get(f"{BASE}/series/{SERIES_ID}/json", timeout=30).json()
print("Series:", info["seriesDetails"]["label"])

# Part 2: ask for the 10 most recent values
resp = requests.get(
    f"{BASE}/observations/{SERIES_ID}/json",
    params={"recent": 10},
    timeout=30,
)
resp.raise_for_status()
data = resp.json()

# Part 3: print each date and value
for row in data["observations"]:
    print(row["d"], row[SERIES_ID]["v"])