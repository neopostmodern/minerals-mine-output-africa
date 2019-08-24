from bs4 import BeautifulSoup, NavigableString
import re
import argparse

from pymongo import MongoClient

import config

parser = argparse.ArgumentParser()
parser.add_argument(
    "-f",
    "--override",
    action="store_true",
    help="Drop databases before creating country and sources structure"
)
arguments = parser.parse_args()

client = MongoClient()
db = client[config.MONGO_DATABASE]
countries_collection = db[config.MONGO_COLLECTION_COUNTRIES]
sources_collection = db[config.MONGO_COLLECTION_SOURCES]


def normalize_file_type(file_type):
    return 'xls' if file_type == 'xlsx' else file_type


def normalize_country_name(country_string):
    # convert name to lowercase
    # remove newlines in HTML source
    # remove "and" (oxford commas -> last item in the list)
    # remove "the" (necessary because source is inconsistent)
    # strip whitespace before and after
    # remove redundant whitespace between words
    country_names = country_string\
        .lower()\
        .replace('\n', '')\
        .replace('and ', '')\
        .replace('the ', '')\
        .strip()
    return re.sub('\s+', ' ', country_names)


def unified_country_identifier(country):
    return country.replace(' ', '-').replace("'", '-')


def unified_countries_identifier(countries):
    return "_".join([unified_country_identifier(country) for country in countries])


def find_next_country(any_soup):
    for sibling in any_soup.next_siblings:
        if sibling.name == 'p':
            parse_country(sibling)
            return


def parse_country(country_soup):
    if 'see' in country_soup.text.lower():  # this country is listed as a synonym
        print("--- Synonym: %s" % country_soup.text.strip())
        find_next_country(country_soup)
        return

    data_sheets_soup = None
    for sibling in country_soup.next_siblings:
        if sibling.name == 'ul':
            data_sheets_soup = sibling
            break

    assert data_sheets_soup is not None, "Data sheets sibling mustn't be 'None'"

    original_country_name = country_soup.find('b').text
    country_name = normalize_country_name(original_country_name)
    print("Processing %s..." % country_name)

    sources = []
    for data_sheets_group in data_sheets_soup:
        if data_sheets_group.name == 'li':
            countries = None
            for industry_name in data_sheets_group.children:
                if type(industry_name) is NavigableString:
                    if 'of' in industry_name:
                        countries_string = industry_name[industry_name.index('of')+2:]
                        if '(' in countries_string:
                            countries_string = countries_string[
                                               countries_string.index('(')+1:countries_string.index(')')
                                               ]
                        country_name_list = countries_string.split(', ') \
                            if ',' in countries_string \
                            else countries_string.split('and ')
                        countries = [normalize_country_name(country) for country in country_name_list]
                        break

            if countries is not None:  # todo: we might lose some data here
                countries_identifier = unified_countries_identifier(countries)

                sources.append(countries_identifier)

                if sources_collection.find_one({'_id': countries_identifier}) is not None:
                    sources_collection.update_one({'_id': countries_identifier}, {'$push': {'used_by': country_name}})
                else:
                    data_sources = {'pdf': [], 'xls': []}
                    for data_link in data_sheets_group.find_all('a'):
                        url = data_link['href']
                        file_type = normalize_file_type(url.split('.')[-1])
                        if file_type in ['xls', 'pdf']:
                            data_sources[file_type].append({'url': url, 'year': data_link.text })

                    sources_collection.insert({
                        '_id': countries_identifier,
                        'xls': data_sources['xls'],
                        'pdf': data_sources['pdf'],
                        'used_by': [country_name]
                    })
            # print(data_sheets_group.prettify())

    countries_collection.insert({
        "_id": country_name,
        "name": original_country_name,
        "sources": sources,
        "minerals": []  # to be filled by another script
    })

    print("Complete. [%s]" % country_name)

    if country_name != 'zimbabwe':  # Zimbambwe is the last country in the list
        find_next_country(data_sheets_soup)


if arguments.override:
    sources_collection.remove({}, multi=True)
    countries_collection.remove({}, multi=True)

with open(config.HTML_FILE_NAME, 'r') as html_file:
    soup = BeautifulSoup(html_file, "lxml")
    country_paragraph = soup.find('a', {'name': 'ag'}).parent
    parse_country(country_paragraph)


