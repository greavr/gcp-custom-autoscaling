## Install TF
Source
`https://learn.hashicorp.com/tutorials/terraform/install-cli`

```
curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -
sudo apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
sudo apt-get update && sudo apt-get install terraform
terraform -install-autocomplete
```

## Run TF
```
cd tf/
terraform plan
terraform apply -auto-approve
Then to destroy
terraform destroy -auto-approve`
```

## Running the CF
```
export GCP_PROJECT='rg-autoscaler'
export mig_region='us-west2'
export mig_name='testing-mig'
export upper_session_count=15
pip3 install -r auto-scaler/requirements.txt --upgrade
python3 auto-scaler/main.py
```

## Autoscaling behavior
* Will remove servers with currently 0 sessions
* Will Scale if the average session per server is above `lower_session` limit, calculated like this:\
`ServerAverage = CountOfNoneZeroSessionServers/TotalActiveSessions`
* Will recommend servers which are closest `upper_session` limit without going over ~~*[Next Version]*~~
