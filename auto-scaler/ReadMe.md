## Running the CF
```
export GCP_PROJECT='rg-autoscaler'
export mig_region='us-west2'
export mig_name='testing-mig'
export upper_session_count=20
pip3 install -r auto-scaler/requirements.txt --upgrade
python3 auto-scaler/main.py
```

## Env Vars:
`mig_name` - Name of the managed instance group (mig) \
`mig_region` - Region of the mig \
`upper_session_count` - max num of sessions per node \

## checks:
`/` - returns list of all servers and session counts \ 

## Permissions:
- compute.instances.setLabels
