from subprocess import run
import os
from pymongo import MongoClient

import config

client = MongoClient()
db = client[config.MONGO_DATABASE]
sources_collection = db[config.MONGO_COLLECTION_SOURCES]

for source in sources_collection.find({'newest_xls_local': {'$exists': 1}}):
    print("Processing source %s..." % source['_id'])

    csv_file_pattern = source['newest_xls_local'].split('/')[-1].split('.')[0] + '-%s.csv'
    csv_directory = config.csv_directory(source['_id'])
    os.mkdir(csv_directory)
    run([
        "ssconvert",
        "--export-file-per-sheet",
        source['newest_xls_local'],
        os.path.join(csv_directory, "%s.csv")
    ])

    # some XLS contain a 'cover' sheet with no relevant information, exported as `Text.csv`
    try:
        os.unlink(os.path.join(csv_directory, "Text.csv"))
    except FileNotFoundError:
        pass

    sources_collection.update({'_id': source['_id']}, {'$set': {'newest_xls_local_csv_directory': csv_directory}})
