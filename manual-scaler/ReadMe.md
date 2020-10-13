This function disables autoscaling by disabling the autoscaling cron-scheduler. This is for set periods of time.

## Env Vars:
`mig_name` - Name of the managed instance group (mig) \
`mig_region` - Region of the mig \

## Running the CF
```
export GCP_PROJECT='rg-autoscaler'
export mig_name='testing-mig'
export mig_region='us-west2'
pip3 install -r manual-scaler/requirements.txt --upgrade
python3 manual-scaler/main.py
```

## URLS:
`/` - Runs the site \
`/set?start={DATETIME}&end={DATETIME}&SIZE{INT}` - Sets the MIG to a static size during set period

## Permissions:
- `cloudscheduler.jobs.pause`
- `cloudscheduler.jobs.list`
- `cloudscheduler.jobs.enable`
- `cloudscheduler.jobs.create`


## Logic
Reads all the 
