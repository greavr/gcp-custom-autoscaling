This function manually sets the MIG size.

It is to be called by Cron Task

## Env Vars:
`GCP_PROJECT` - Auto set value for GCP project

## Running the CF locally
```
export GCP_PROJECT='rg-autoscaler'
pip3 install -r Manual-Scaler-set-mig/requirements.txt --upgrade
python3 Manual-Scaler-set-mig/main.py
```

## URLS & Parameters:
`/` - Returns Error \
`/?IGM={STRING}&Region={GCP-REGION}&NewSize={INT}` - Updates the schedule for 

## Permissions:
- `compute.instanceGroupManagers.get`
- `compute.instanceGroupManagers.update`

## Testing the request
```curl -X POST https://us-west2-rg-autoscaler.cloudfunctions.net/set-mig -H "Content-Type:application/json"  -d '{"IGM":"testing-mig","Region" : "us-west2", "NewSize" : 10}'```
