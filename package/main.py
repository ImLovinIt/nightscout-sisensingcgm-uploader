from setup import *
from module import *
import json
import sched,time



def main():
# get last entry date
    try:
        ns_last_date = get_last_entry_date(ns_header)
        if ns_last_date == "":
             ns_last_date=0
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

    # adjust scheduler to match Sisensing upload time pattern
    time_at_now = round(datetime.datetime.now().timestamp()) #timestamp
    #print(datetime.datetime.fromtimestamp(time_at_now))

    time_ss_mod = (ns_last_date/1000)%(uploader_interval*60)
    #print(time_ss_mod)

    time_next_run = time_at_now - time_at_now%(uploader_interval*60) + uploader_interval*60 + time_ss_mod
    print("Next run scheduled:", datetime.datetime.fromtimestamp(time_next_run))

    time_next_run_delay = time_next_run - time_at_now
    #print(time_next_run_delay)

    # add task to scheduler
    scheduler.enter(time_next_run_delay, 1, main)

# scheduler to run periodically
scheduler = sched.scheduler(time.time, time.sleep)
scheduler.enter(0, 1, main)
scheduler.run()