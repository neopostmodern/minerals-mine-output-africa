import os
import re
import mmap
from pymongo import MongoClient

import config

client = MongoClient()
db = client[config.MONGO_DATABASE]
sources_collection = db[config.MONGO_COLLECTION_SOURCES]
countries_collection = db[config.MONGO_COLLECTION_COUNTRIES]

minerals_regex = re.compile(bytes("(%s)" % "|".join(config.MINERALS), 'utf-8'), re.IGNORECASE | re.MULTILINE)

for source in sources_collection.find({'newest_xls_local_csv_directory': {'$exists': 1}}):
    print("Processing source %s..." % source['_id'])
    for table in os.listdir(source['newest_xls_local_csv_directory']):
        print("  └ %s..." % table)
        with open(os.path.join(source['newest_xls_local_csv_directory'], table), 'rb', 0) as file, \
                mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as file_mmap:
            mineral_matches = [mineral.decode('utf-8').lower() for mineral in minerals_regex.findall(file_mmap)]
            mineral_matches = list(dict.fromkeys(mineral_matches))  # deduplicate
            print('   ', mineral_matches)
            sources_collection.update_one(
                {'_id': source['_id']},
                {'$set': {'minerals': mineral_matches}}
            )
            countries_collection.update_many(
                {'_id': {'$in': source['used_by']}},
                {'$addToSet': {'minerals': {'$each': mineral_matches}}}
            )
