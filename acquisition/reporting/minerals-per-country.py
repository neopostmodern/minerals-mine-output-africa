from pymongo import MongoClient

import config

client = MongoClient()
db = client[config.MONGO_DATABASE]
sources_collection = db[config.MONGO_COLLECTION_SOURCES]
countries_collection = db[config.MONGO_COLLECTION_COUNTRIES]

for mineral in config.MINERALS:
    print(mineral)
    print([country['name'] for country in countries_collection.find({'minerals': mineral}, {'name': 1, '_id': 0})])
    print()
