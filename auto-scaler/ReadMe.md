## Running the CF Code Locally
```
export GCP_PROJECT='rg-stateful-autoscaler'
export mig_region='us-west2'
export mig_name='testing-mig'
export upper_session_count=15
pip3 install -r auto-scaler/requirements.txt --upgrade
python3 auto-scaler/main.py
```

## Env Vars:
`mig_name` - Name of the managed instance group (mig) \
`mig_region` - Region of the mig \
`upper_session_count` - max num of sessions per node \

## checks:
`/` - returns list of all servers and session counts 

## Permissions:
- `compute.instanceGroupManagers.get`
- `compute.instanceGroupManagers.update`
- `compute.instances.get`
- `datastore.entities.create`
- `datastore.entities.update`
- `logging.logEntries.create`
- `monitoring.timeSeries.create`