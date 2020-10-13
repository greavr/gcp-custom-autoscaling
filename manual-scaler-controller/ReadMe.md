This function enables advanced scheduling tooling

## Env Vars:
`mig_name` - Name of the managed instance group (mig) \
`mig_region` - Region of the mig \
`GCP_PROJECT` - Auto set value for GCP project \
`mig_size_cf` - HTTPS target of the MIG CF
`autoscaler_cf` - HTTPS target for the default LB

## Running the CF locally
```
export GCP_PROJECT='rg-autoscaler'
export mig_name='testing-mig'
export mig_region='us-west2'
export mig_size_cf='https://us-west2-rg-autoscaler.cloudfunctions.net/set-mig'
export autoscaler_cf='https://us-west2-rg-autoscaler.cloudfunctions.net/my_autoscaler'
pip3 install -r manual-scaler-controller/code/requirements.txt --upgrade
python3 manual-scaler-controller/code/main.py
```

## URLS & Parameters:
`/` - Runs the site \

## Permissions:
- `cloudscheduler.jobs.pause`
- `cloudscheduler.jobs.list`
- `cloudscheduler.jobs.enable`
- `cloudscheduler.jobs.create`



## Logic
Reads all the existing Schedules and enables the pause / stopping.
