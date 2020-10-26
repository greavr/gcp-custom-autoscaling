This function enables advanced scheduling tooling. This runs of a docker image. The Terraform script provided uses my default image but this is a variable you can change. Terraform is not designed to push out a Docker images, but below is the code for this. 


## Env Vars:
`mig_name` - Name of the managed instance group (mig) \
`mig_region` - Region of the mig \
`GCP_PROJECT` - Auto set value for GCP project \
`mig_size_cf` - HTTPS target of the MIG CF \
`autoscaler_cf` - HTTPS target for the default Autoscaler \
`autoscaler_cf_id` - ID of the Cloud Function autoscaler

## Running the CF locally
```
export GCP_PROJECT='rg-stateful-autoscaler'
export mig_name='testing-mig'
export mig_region='us-west2'
export mig_size_cf='https://us-west2-rg-stateful-autoscaler.cloudfunctions.net/set-mig'
export autoscaler_cf='https://us-west2-rg-stateful-autoscaler.cloudfunctions.net/my_autoscaler'
pip3 install -r manual-scaler-controller/code/requirements.txt --upgrade
python3 manual-scaler-controller/code/main.py
```

## URLS & Parameters:
`/` - Runs the site \

## Docker Parametes
Build the docker image \
`docker build -t gcr.io/rgreaves-sandbox/manual-scaler manual-scaler-controller/.` \
Then run the image with:  
`export GOOGLE_APPLICATION_CREDENTIALS=~/key.json` - Where ~/key.json is the service account key used for local testing \
`docker run -ti -p 8080:8080 --env-file manual-scaler-controller/env.list -v $GOOGLE_APPLICATION_CREDENTIALS:/tmp/key.json:ro  gcr.io/rgreaves-sandbox/manual-scaler` \
Then push this to docker registry with: \
`docker push gcr.io/rgreaves-sandbox/manual-scaler`


## Permissions:
- `cloudscheduler.jobs.pause`
- `cloudscheduler.jobs.list`
- `cloudscheduler.jobs.enable`
- `cloudscheduler.jobs.create`



## Logic
Reads all the existing Schedules and enables the pause / stopping.
