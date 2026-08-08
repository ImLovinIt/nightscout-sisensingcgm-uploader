from setup import *
from module import *
import datetime
import json
import sched,time


# Align the next run with the Sisensing upload pattern. Sisensing publishes every
# uploader_interval minutes, and ns_last_date shows where in that window its
# uploads land, so aim for the same offset plus a short sync delay.
def get_next_run_delay(ns_last_date):
    time_at_now = round(datetime.datetime.now().timestamp())
    #print(datetime.datetime.fromtimestamp(time_at_now))

    time_ss_mod = (ns_last_date/1000)%(uploader_interval*60)
    #print(time_ss_mod)

    time_delay = 15 # seconds delay to allow data sync on server

    #print(time_at_now%(uploader_interval*60),time_ss_mod)

    if time_at_now%(uploader_interval*60) >= time_ss_mod:
        time_next_run = time_at_now - time_at_now%(uploader_interval*60) + uploader_interval*60 + time_ss_mod + time_delay
    else:
        time_next_run = time_at_now - time_at_now%(uploader_interval*60) + time_ss_mod + time_delay

    time_next_run_delay = time_next_run - time_at_now
    #print(time_next_run_delay)

    # never schedule in the past, that would spin the scheduler
    if time_next_run_delay <= 0:
        time_next_run_delay += uploader_interval*60
        time_next_run = time_at_now + time_next_run_delay

    print("Next run scheduled:", datetime.datetime.fromtimestamp(time_next_run), "(local time)")
    return time_next_run_delay


def main():
    # the scheduler maths below needs a number, so start from a safe default
    ns_last_date = 0

    try:
        # get last entry date
        try:
            last_date = get_last_entry_date(ns_header)
            if isinstance(last_date, (int, float)):
                ns_last_date = last_date
            else:
                print("No usable last entry date. Treating it as 0.")
        except Exception as error:
            print("Error requesting from Nightscout:", error)

        # get Sisensing data
        ss_data = None
        try:
            ss_data = get_ss_entries(ss_header)
        except Exception as error:
            print("Error requesting from Sisensing:", error)

        # load test data
        # with open('package/test.json', encoding="utf8") as f:
        #     ss_data = json.load(f)

        # process Sisensing data and upload to Nightscout
        if ss_data is None:
            print("Skipping upload. No usable Sisensing response this run.")
        else:
            try:
                process_json_data(ss_data,ns_last_date)
            except Exception as error:
                print("Error processing glucose data:", error)

            # sensor treatments are optional and must never cost a glucose upload
            if uploader_sensor_events:
                try:
                    process_sensor_events(ss_data,ns_header)
                except Exception as error:
                    print("Error processing sensor events:", error)

    except Exception as error:
        print("Unexpected error during run:", error)

    finally:
        # always re-arm the scheduler, otherwise one bad run ends the process
        try:
            delay = get_next_run_delay(ns_last_date)
        except Exception as error:
            print("Error scheduling next run:", error)
            delay = uploader_interval*60
        scheduler.enter(delay, 1, main)

# scheduler to run periodically
scheduler = sched.scheduler(time.time, time.sleep)

if __name__ == "__main__":
    scheduler.enter(0, 1, main)
    scheduler.run()
