# Nightscout Sisensing CGM Uploader
Script written in python to periodically upload Sisensing (SiBionics) CGM (CG1) glucose data to Nightscout.

## V2 Update
It looks like Sisensing has changed the bearer token verification. I can no longer keep a valid token after retrieving the token from the follower phone and logging back into the master phone with the same mobile number.
The current solution is to have two Chinese phone numbers log in each master phone and follower phone. This will change the API address with each URL having a unique follower ID assigned to it.

*Only tested with the Chinese models and API. A Chinese mobile number is required to sign up.

Model Tested:
- A4 (Original. Double packaging)
- A4 2024-05 (Second model. Single packaging)

App Tested:

<img src="https://github.com/user-attachments/assets/3d00d476-090c-4e64-9dbf-d3a9e694c998" width="96">

<em>硅基动感</em>

## Configuration
The script takes the following environment variables
| Variable                 | Description                                                                                                                | Example                                  | Required |
|--------------------------|----------------------------------------------------------------------------------------------------------------------------|------------------------------------------|----------|
| ss_url                   | Sisensing API URL with a unique user/follower ID                                            | https://api.sisensing.com/follow/app/follow/1234567890/glucose https://api.sisensing.com/lite-sense-app/follow/info?followId=1234567890                               |   X      |
| ss_token                 | Sisensing API Bearer Token                                                                                                 | abcdefgh-1234-ijkl-5678-mnopqrstuvwx     | X        |
| ns_url                   | Hostname of the Nightscout instance with http:// or https:// and end with /                                                | https://nightscout.azurewebsites.net/    | X        |
| ns_api_secret            | SHA1 Hash of Nightscout access toke                                                                                        | 162f14de46149447c3338a8286223de407e3b2fa | X        |
| uploader_interval        | The time interval of requesting values from Sisensing. Default to 5 mins as Sisensing CGM only uploads every 5 mins.       | 5                                        |          |
| uploader_max_entries     | Maximum number of entries to upload everytime. 0 to disable.                                                               | 0                                        |          |
| uploader_all_data        | Upload all available data.                                                                                                 | False                                    |          |
| uploader_sensor_events   | Post `Sensor Start` and `Sensor Stop` treatments alongside glucose entries. Off by default.                                 | False                                    |          |
| retries                  | Number of retries for API request. Default to 10.                                                                          | 10                                       |          |
| timeout                  | Timeout for each retry. Default to 10.                                                                                     | 10                                       |          |

## Sensor treatments
Set `uploader_sensor_events` to `True` to have the uploader record the sensor session in Nightscout as well as the readings.

- `Sensor Start` is posted at `deviceEnableTime`, the sensor activation reported by Sisensing.
- `Sensor Stop` is posted at `latestGlucoseTime`, the final reading, once Sisensing reports the sensor as no longer running (`deviceStatus` other than `1`). The response carries no explicit stop time, and readings can continue for a few hours past the scheduled 14 day end, so the last reading is used rather than the schedule.

Both are posted with `enteredBy` set to the uploader, and are skipped when Nightscout already holds that event at that time. Nightscout also upserts treatments on event type plus timestamp, so a repeat post overwrites rather than duplicates.

Note that Nightscout's Sensor Age (SAGE) pill reads `Sensor Start` and `Sensor Change` only, and warns on Dexcom style thresholds by default. For a 14 day sensor, set `SAGE_INFO`, `SAGE_WARN` and `SAGE_URGENT` on your Nightscout instance to roughly `312`, `332` and `334` hours.

## IMPORTANT for Azure free tier users
Enable `server side retry` to prevent rate-limiting errors for Azure Cosmos DB for MongoDB operations. Follow link below for details.
https://learn.microsoft.com/en-us/azure/cosmos-db/mongodb/prevent-rate-limiting-errors  

## Obtain Sisensing API Bearer Token
- Use your main phone to log in with the first phone number and select the master device mode to read data from CGM.
- Use your spare phone to log in with the second phone number and select follower mode to retrieve history data stored on the server.
- Install a packet capture app on your spare phone. eg. Http traffic capture for iOS. PCAPdroid for andriod.
- Install the required certificate as per the packet capture app instructions.
- Scan Sisensing app on your spare phone.
- Find an entry with API address that looks like this `https://api.sisensing.com/follow/app/follow/1234567890/glucose` for A4 (14 days) models or `https://api.sisensing.com/lite-sense-app/follow/info?followId=1234567890` for the 18 months model. This is your `ss_url`.
- Under `Response` json file, you should see a list of glucose entries. Congrats. You find the correct one.
- Under `Request header`, find `Authorization:Bearer abcd...1234`. `abcd...1234` is your `ss_token`.
- If Sisensing app is reinstalled or logged in on another device with the same phone number, you may need to repeat the above step.

## Hashing Nightscout API token
`ns_api_secret`  must be a SHA1 hash of an Access Token from Nightscout (Add new subject first in Nightscout's Admin Tools if required), e.g. your Access Token for a subject named Sisensing might be `sisensing-123456789abcde`.

Obtain your hash with
```
echo -n "sisensing-123456789abcde" | sha1sum | cut -d ' ' -f 1
```
(use shasum instead of sha1sum on Mac)

which will print the hash (40 characters in length):
```
14c779d01a34ad1337ab59c2168e31b141eb2de6
```
You might also use an online tool to generate your hash, e.g. https://codebeautify.org/sha1-hash-generator

Credit to https://github.com/timoschlueter/nightscout-librelink-up

## Deployment - Docker

Docker Hub
https://hub.docker.com/r/imlovinit1019/nightscout-sisensingcgm-uploader

* **API secret and token are passed as Environment Variables.** If you have security concerns, please stop using this script or fork this repository to make improvements. (Docker swarm mode may be required to use secrets.)
