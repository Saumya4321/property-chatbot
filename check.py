import json
from collections import Counter

data = json.load(open("wasalt.json", encoding="utf-8"))
print(len(data), "listings")
print(Counter(x["purpose"] for x in data))
print(Counter(x["city"] for x in data))
print(Counter(x["property_type"] for x in data))

matches = [x["title"] for x in data
           if x["purpose"] == "rent" and x["city"] == "Jeddah" and x["bedrooms"] == 2]
print(len(matches), "two-bedroom rentals in Jeddah:", matches)