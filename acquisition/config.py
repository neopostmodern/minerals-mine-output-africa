from os import path

ENTRY_POINT = "https://minerals.usgs.gov/minerals/pubs/country/africa.html"
USGS_BASE_URL = "https://minerals.usgs.gov/minerals/pubs/country/"
HTML_FILE_NAME = "usgs-minerals-africa.html"
MONGO_DATABASE = "usgs-minerals-africa"
MONGO_COLLECTION_COUNTRIES = "countries"
MONGO_COLLECTION_SOURCES = "sources"
LOCAL_FILE_ROOT = path.join(path.realpath(__file__), "data")
XLS_DIRECTORY = "xls"
CSV_DIRECTORY = "csv"
MINERALS = ["cassiterite", "tin", "wolframite", "tungsten", "coltan", "columbium", "tantalum", "gold", "copper", "zinc",
            "bauxite", "platinum", "gallium", "cobalt"]


def csv_directory(source_id):
    return path.join(LOCAL_FILE_ROOT, CSV_DIRECTORY, source_id)
