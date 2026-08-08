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
- Under `Request header`, find `Authorization:Bearer abcd...1234`. `abcd...1234` is your `ss_token`. Do not include the word `Bearer`.
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

## Deployment
The uploader is one long running process. It opens no ports, serves no pages, writes no files and needs no database. It wakes every `uploader_interval` minutes, reads from Sisensing and posts to Nightscout. Anything that can keep a small Python process alive will run it, so pick whichever of the following suits the hardware you already have.

* **API secret and token are passed as Environment Variables.** If you have security concerns, please stop using this script or fork this repository to make improvements. (Docker swarm mode may be required to use secrets.)

Keep your credentials in a file rather than on the command line, so they do not end up in your shell history:

```
cp .env.example .env
chmod 600 .env
```

Then fill in `.env`. The same file works for Docker, Docker Compose and systemd.

### Option 1. Docker
Image: https://hub.docker.com/r/imlovinit1019/nightscout-sisensingcgm-uploader

```
docker run -d \
  --name nightscout-sisensingcgm-uploader \
  --restart unless-stopped \
  --env-file .env \
  imlovinit1019/nightscout-sisensingcgm-uploader:latest
```

Follow it with `docker logs -f nightscout-sisensingcgm-uploader`. A healthy run prints the last entry date, the Sisensing response status and how many entries were uploaded.

Published tags are `latest`, `2.0`, `1.1` and `1.0`, all built for `linux/amd64`. On an arm host such as a Raspberry Pi, build the image yourself with `docker build -t nightscout-sisensingcgm-uploader .` and run that, or use Option 3.

### Option 2. Docker Compose
`docker-compose.yml` in this repository is ready to use once `.env` exists.

```
docker compose up -d
docker compose logs -f
```

It pulls the published image, restarts unless you stop it, and reads `.env`. To run your own changes instead, swap the `image:` line for `build: .` as noted in the file.

### Option 3. Portainer
`docker-compose-portainer.yml` is the Compose file adapted for a Portainer stack. Go to Stacks, Add stack, Web editor, paste it in, then supply the four required values under Environment variables, either one at a time or with `Load variables from .env file` using a filled in copy of `.env.example`.

Portainer substitutes those values into the `${...}` entries when it deploys and leaves the stack definition as written, so your token and API secret are not stored in the compose file itself.

Use that file rather than `docker-compose.yml`, which reads `env_file: .env`. A stack defined in the browser has no such file beside it.

If a required variable is missing, the container exits with `ss_url required. Pass it as an Environment Variable.` and the restart policy will keep retrying, so check the stack logs if it will not stay up.

### Option 4. Python directly
The only dependency is `urllib3`. Python 3.10 or newer is required, as the script uses structural pattern matching.

```
git clone https://github.com/ImLovinIt/nightscout-sisensingcgm-uploader.git
cd nightscout-sisensingcgm-uploader
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
set -a; . ./.env; set +a
python -u package/main.py
```

To keep it running after you log out, on a Raspberry Pi or any systemd machine, save this as `/etc/systemd/system/sisensing-uploader.service`, adjusting the user and paths:

```
[Unit]
Description=Nightscout Sisensing CGM Uploader
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/opt/nightscout-sisensingcgm-uploader
EnvironmentFile=/opt/nightscout-sisensingcgm-uploader/.env
ExecStart=/opt/nightscout-sisensingcgm-uploader/.venv/bin/python -u package/main.py
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
```

Then `sudo systemctl enable --now sisensing-uploader`, and read the output with `journalctl -u sisensing-uploader -f`.

### Option 5. Managed container hosts
Northflank, Fly.io, Railway, Koyeb and similar platforms will run the image, as will the Container Manager on a Synology NAS or the Docker plugin on unRAID.

Two things to watch for:

- Deploy it as a **worker or background service**, not a web service. The uploader listens on no port, so a web service plan may fail its health checks or idle the container to sleep.
- The published image is amd64 only, so either choose an amd64 machine type or point the platform at this repository and let it build.

Set the environment variables through the platform's own secrets or variables UI rather than baking them into an image.
