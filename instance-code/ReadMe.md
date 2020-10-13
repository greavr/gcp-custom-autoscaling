# Runs a local web server on port :8080

This code is bootstrapped from a GCS bucket zip file and run in the image. \
\
The code to run the software is:\
```
apt-get install python3-pip unzip supervisor -y
pip3 install -r requirements.txt
python3 main.py
```

This is controlled via [supervisor](http://supervisord.org/), with a custom config of:
```
cat <<EOF >  /etc/supervisor/conf.d/sessions.conf
[program:sessions]
command=python3 main.py 2&>1
directory = /session   
autostart=true
autorestart=true
stderr_logfile=/var/log/long.err.log
stdout_logfile=/var/log/long.out.log
EOF

supervisorctl update
```

This ensures the site runs at reboot \ 

## Permissions Required
- None

Full bootstrap code can be found in the [startup_script.sh](../artifacts/startup_script.sh) in the [artifacts folder](../artifacts)


