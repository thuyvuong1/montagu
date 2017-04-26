# Montagu
## Prerequisites
* Docker (including Docker Compose)
* A way of running Bash scripts (e.g. on Windows install Cygwin, Git Bash, or similar)

## Deploy
To deploy Montagu run `./run.sh`

This will deploy the database, the API, and the Modelling groups Contribution Portal.

Open `http://localhost:8081` in a browser to view the portal.

## Demo
For demonstration purposes, you can then run (in another terminal) `./insert-test-data.sh` to put a couple of fake touchstones with some fake responsibilities in. The password is "changeme".
