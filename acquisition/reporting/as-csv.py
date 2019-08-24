from pymongo import MongoClient

import config

client = MongoClient()
db = client[config.MONGO_DATABASE]
countries_collection = db[config.MONGO_COLLECTION_COUNTRIES]

minerals = []
for country in countries_collection.find():
    minerals.extend(country['minerals'])

minerals = list(dict.fromkeys(minerals))  # deduplicate

print("country;" + ";".join(minerals) + ";")  # empty leading column for country as label, trailing ';'

for country in countries_collection.find():
    line = country['_id'] + ';'
    for mineral in minerals:
        line += "%.5f;" % country.get('values', {}).get(mineral, 0)
    print(line)
