This function disables autoscaling by disabling the autoscaling cron-scheduler. This is for set periods of time.

## Env Vars:
`mig_name` - Name of the managed instance group (mig) \
`mig_region` - Region of the mig \
`GCP_PROJECT` - Auto set value for GCP project

## Running the CF locally
```
export GCP_PROJECT='rg-autoscaler'
export mig_name='testing-mig'
export mig_region='us-west2'
pip3 install -r manual-scaler/requirements.txt --upgrade
python3 manual-scaler/main.py
```

## URLS & Parameters:
`/` - Runs the site \
`/?cron={DATETIME}` - Updates the schedule for 

## Permissions:
- `cloudscheduler.jobs.pause`
- `cloudscheduler.jobs.list`
- `cloudscheduler.jobs.enable`
- `cloudscheduler.jobs.create`


## Logic
Reads all the existing Schedules and enables the pause / stopping.
