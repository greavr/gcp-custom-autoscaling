#!/bin/bash

# Get File Path
source_code_loc=$(curl http://metadata.google.internal/computeMetadata/v1/instance/attributes/source_code_loc -H "Metadata-Flavor: Google")

# Install Dependencies
apt-get install python3-pip unzip supervisor -y

# Download, extract and setup the code
mkdir /session
chmod 777 -R /session
cd /session
gsutil cp $source_code_loc .
unzip code.zip
pip3 install -r requirements.txt

# Set code to run at startup
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
