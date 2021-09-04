#!/bin/bash

if [ ! -f "/config/app.py" ]; then
    cp -f /app/{app.py,stats.sh} /config/
    chmod +x /config/stats.sh 
fi

cd /config
export FLASK_APP=app.py
flask run --host=0.0.0.0
