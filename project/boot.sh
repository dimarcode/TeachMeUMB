#!/bin/bash
flask db upgrade
flask seed-db
exec gunicorn -b :5000 --access-logfile - --error-logfile - teachmeumb:app