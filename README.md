# Nightscout Sisensing CGM Uploader
Script written in python to periodically upload Sisensing (SiBionics) CGM (CG1) glucose data to Nightscout.

## Update
One phone is all that is needed. The `myself` endpoints listed below return your own device data directly, so there is no second phone and no second mobile number involved.

*Only tested with the Chinese models and API. A Chinese mobile number is required to sign up.

Model Tested:
- A4 (Original. Double packaging)
- A4 2024-05 (Second model. Single packaging)

App Tested:

<img src="https://github.com/user-attachments/assets/3d00d476-090c-4e64-9dbf-d3a9e694c998" width="96">

<em>硅基动感</em>

## Configuration
The script takes the following environment variables.

### Required

| Variable        | Description                                   | Example                                  |
|-----------------|-----------------------------------------------|------------------------------------------|
| `ss_url`        | Sisensing API URL. See Endpoints below.       | see Endpoints                            |
| `ss_token`      | Sisensing API bearer token.                   | abcdefgh-1234-ijkl-5678-mnopqrstuvwx     |
| `ns_url`        | Nightscout host, with scheme. Trailing / optional. | https://nightscout.example.com/     |
| `ns_api_secret` | SHA1 hash of a Nightscout access token.       | 162f14de46149447c3338a8286223de407e3b2fa |

### Optional

| Variable                 | Description                                        | Default |
|--------------------------|----------------------------------------------------|---------|
| `uploader_interval`      | Minutes between polls of Sisensing.                | `5`     |
| `uploader_max_entries`   | Cap on entries per upload. `0` disables the cap.   | `0`     |
| `uploader_all_data`      | Upload every available reading, not just new ones. | `False` |
| `uploader_sensor_events` | Post Sensor Start and Sensor Stop treatments.      | `False` |
| `retries`                | Retries per API request.                           | `10`    |
| `timeout`                | Timeout in seconds per retry.                      | `10`    |

#### Endpoints
Pick the one matching your model:
- A4, 14 days: `https://api.sisensing.com/follow/app/follow/myself/glucose/details/devices`
- 18 months: `https://api.sisensing.com/lite-sense-app/follow/myself/glucose/`

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
- Log in to the Sisensing app on your phone and pair your CGM as usual.
- Install a packet capture app on the same phone. eg. Http traffic capture for iOS. PCAPdroid for andriod.
- Install the required certificate as per the packet capture app instructions.
- Open the Sisensing app while the capture is running.
- Open any captured request to `api.sisensing.com` that returned `200 OK`. There is no need to hunt for a particular address, the same token is sent with all of them.
- Under `Request header`, find `Authorization:Bearer abcd...1234`. `abcd...1234` is your `ss_token`.
- You do not need to find your `ss_url` in the capture. Use the address for your model from Endpoints above.
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
