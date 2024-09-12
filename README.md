# Nightscout Sisensing CGM Uploader
Script written in python to periodically upload Sisensing (SiBionics) CGM (CG1) glucose data to Nightscout.

*Only tested with the Chinese CGM and database. A Chinese mobile number is required for signing up.

## Configuration
The script takes the following environment variables
| Variable                 | Description                                                                                                                | Example                                  | Required |
|--------------------------|----------------------------------------------------------------------------------------------------------------------------|------------------------------------------|----------|
| ss_token                 | Sisensing API Bearer Token                                                                                                 | abcdefgh-1234-ijkl-5678-mnopqrstuvwx     | X        |
| ss_region                | Sisensing Region (CN/EU)                                                                                                   | CN                                       |          |
| ns_url                   | Hostname of the Nightscout instance with http:// or https:// and end with /                                                | https://nightscout.azurewebsites.net/    | X        |
| ns_api_secret            | SHA1 Hash of Nightscout access toke                                                                                        | 162f14de46149447c3338a8286223de407e3b2fa | X        |
| uploader_interval        | The time interval of requesting values from Sisensing. Default to 5 mins as Sisensing CGM only uploads every 5 mins.       | 5                                        |          |
| uploader_max_entries     | Maximum number of entries to upload everytime. 0 to disable.                                                               | 0                                        |          |
| uploader_all_data        | Upload all available data.                                                                                                 | False                                    |          |


## IMPORTANT for Azure free tier users
Enable `server side retry` to prevent rate-limiting errors for Azure Cosmos DB for MongoDB operations. Follow link below for details.
https://learn.microsoft.com/en-us/azure/cosmos-db/mongodb/prevent-rate-limiting-errors  

## Obtain Sisensing API Bearer Token
- Register and run your Sisensing (SiBionics) app on mobile phone first.
- Install a packet capture app on your mobile. eg. Http traffic capture for iOS. PCAPdroid for andriod.
- Install the required certificate per the packet capture app instruction.
- Scan Sisensing app.
- Under `Request header`, find `Authorization:Bearer ...`. "`...`" is your `ss_token`.
- If Sisensing app is reinstalled, you may need to repeat the above step.

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

## Deployment - Docker

Docker Hub
https://hub.docker.com/r/imlovinit1019/nightscout-sisensingcgm-uploader

* **API secret and token are passed as Environment Variables.** If you have security concerns, please stop using this script or fork this repository to make improvements. (Docker swarm mode may be required to use secrets.)


## Credit
Inspired by https://github.com/timoschlueter/nightscout-librelink-up
