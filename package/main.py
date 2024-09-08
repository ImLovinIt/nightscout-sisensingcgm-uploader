from setup import *
from module import *
import requests # pip install
import json
import sched,time



def main():
# get last entry date
    try:
        ns_last_date = get_last_entry_date(ns_header)
    except Exception as error:
            print("Error requesting from Nightscout:", error)

    # get Sisensing data
    try:
        ss_data = get_ss_entries(ss_header)
    except Exception as error:
        print("Error requesting from Sisensing:", error)

    # load test data
    # with open('package/test.json', encoding="utf8") as f:
    #     ss_data = json.load(f)

    # process Sisensing data and upload to Nightscout
    try:
        # add code to verify ns_last_date
        process_json_data(ss_data,ns_last_date)
    except Exception as error:
        print("Error reading direction:", error)

    # add task to scheduler
    scheduler.enter(uploader_interval*60, 1, main)

# scheduler to run periodically
scheduler = sched.scheduler(time.time, time.sleep)
scheduler.enter(0, 1, main)
scheduler.run()