import urllib.request, urllib.error
import os.path
from pymongo import MongoClient

import config

client = MongoClient()
db = client[config.MONGO_DATABASE]
sources_collection = db[config.MONGO_COLLECTION_SOURCES]

for source in sources_collection.find():
    print("Processing %s..." % source['_id'])
    if len(source['xls']) == 0:
        print("No XLS data available.")
        continue
    newest_xls = source['xls'][-1]
    print(newest_xls)
    source_url = config.USGS_BASE_URL + newest_xls['url'][2:]
    file_name = os.path.join(
        config.LOCAL_FILE_ROOT,
        config.XLS_DIRECTORY,
        source['_id'] + '-' + newest_xls['year'] + '.' + newest_xls['url'].split('.')[-1]
    )

    try:
        urllib.request.urlretrieve(source_url, file_name)

        sources_collection.update({'_id': source['_id']}, {'$set': {'newest_xls_local': file_name}})

    except urllib.error.URLError as error:
        print("Failed to download %s" % source_url, error)


