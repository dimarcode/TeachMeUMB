#!/bin/bash
flask db migrate -m "migrate on update"
flask db upgrade
flask seed-db
exec gunicorn -b :5000 --access-logfile - --error-logfile - teachmeumb:app