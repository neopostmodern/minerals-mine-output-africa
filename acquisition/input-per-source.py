import re
from subprocess import Popen, run, DEVNULL, PIPE
import os
from pprint import pprint

import time
from pymongo import MongoClient

import config

client = MongoClient()
db = client[config.MONGO_DATABASE]
sources_collection = db[config.MONGO_COLLECTION_SOURCES]
countries_collection = db[config.MONGO_COLLECTION_COUNTRIES]

try:
    os.unlink(config.QUESTIONS_FILE)
except FileNotFoundError:
    pass

screen_info_process = run("xdpyinfo | grep dimensions | grep -o '[0-9x]*' | head -n1", shell=True, stdout=PIPE)
[screen_width, screen_height] = [
    int(dimension) for dimension in screen_info_process.stdout.decode('utf-8').strip().split('x')
]
current_window_name = run("xdotool getwindowfocus getwindowname", shell=True, stdout=PIPE).stdout.decode('utf-8').strip()
run("wmctrl -r \"%s\" -b remove,maximized_vert,maximized_horz" % current_window_name, shell=True)
run("wmctrl -r \"%s\" -e 0,%d,%d,%d,%d" % (current_window_name, 0, 0, screen_width // 2, screen_height), shell=True)

question_number = 0

for source in sources_collection.find({'newest_xls_local': {'$exists': 1}}):
    print("Processing source %s..." % source['_id'].upper())
    for country in source['used_by']:
        print("Please input data for '%s'..." % country)
        pdf_file_path = source['newest_xls_local'].split('.')[0].replace('xls', 'pdf') + ".pdf"
        pdf_file_name = pdf_file_path.split('/')[-1]
        country_information = countries_collection.find_one({'_id': country})
        if 'final' in country_information and country_information['final'].get(source['_id'], False):
            print(">> Information already final.")
            continue

        mineral_information = country_information.get('values', {})
        for mineral in source['minerals']:
            mineral_regex = "\\b[%s%s]%s\\b" % (mineral[0], mineral[0].upper(), mineral[1:])
            pdf_regex_matches = run(
                ["pdfgrep", "-p", mineral_regex, pdf_file_path],
                stdout=PIPE
            ).stdout.decode('utf-8').strip()

            first_page = "1"
            if len(pdf_regex_matches) > 0:
                first_page = pdf_regex_matches.split("\n")[0].split(':')[0]
            pdf_process = Popen(
                ["evince", "-p", first_page, "-l", mineral, pdf_file_path],
                stdout=DEVNULL,
                stderr=DEVNULL
            )
            time.sleep(0.5)
            run(["xdotool", "key", "alt+Tab"])
            run("wmctrl -r \"%s\" -e 0,%d,%d,%d,%d"
                % (pdf_file_name, screen_width // 2, 0, screen_width // 2, screen_height), shell=True)

            valid_input = False
            while not valid_input:
                try:
                    previous_value = mineral_information.get(mineral, None)
                    unchanged = True
                    kilograms = False
                    raw_amount = input("%s (%s): " % (
                        mineral,
                        'No information' if previous_value is None else "%.4ft" % previous_value
                    ))

                    if raw_amount == '':
                        amount = previous_value
                    elif raw_amount == '-' or raw_amount == '?':
                        unchanged = False
                        amount = None
                    else:
                        unchanged = False
                        if 'k' in raw_amount:
                            kilograms = True
                            raw_amount = re.sub(r"kg?", "", raw_amount)

                        amount = float(raw_amount)
                        if kilograms:
                            amount *= 0.001

                    if amount is None:
                        comment = "Information about %s missing [added to %s]" % (mineral, config.QUESTIONS_FILE)

                        # store "question" information
                        question_number += 1

                        with open(config.QUESTIONS_FILE, 'a') as questions_file:
                            questions_file.write("Question %d: Source '%s' for country %s: %s\n"
                                                 % (question_number, source['_id'], country.upper(), mineral))

                        run(["xdotool", "key", "alt+Tab"])
                        run("gnome-screenshot --file=questions/question-%d.png" % question_number, shell=True)
                        run(["xdotool", "key", "alt+Tab"])

                    elif amount > 0:
                        comment = "Registered %.4f metric tons of %s" % (amount, mineral)
                    else:
                        comment = "No %s" % mineral
                    print("[%s] %s" % ("UNCHANGED" if unchanged else 'NEW', comment))

                    valid_input = True
                    mineral_information[mineral] = amount

                except ValueError:
                    print("Invalid entry. Try again...")

            pdf_process.terminate()

        pprint(mineral_information)

        is_information_final = False
        if len([mineral_value for mineral_value in mineral_information.values() if mineral_value is None]) > 0:
            print("Can't finalize %s (information missing)" % country)
        else:
            is_information_final = input("Is the information for %s final? (y/N) " % country).strip().lower() == 'y'
            print("Information marked as %s" % ("FINAL" if is_information_final else "NOT FINAL"))

        countries_collection.update_one(
            {'_id': country},
            {'$set': {
                "final.%s" % source['_id']: is_information_final,
                'values': mineral_information
            }}
        )
        print("")

    print("------------------")

    # exit()
