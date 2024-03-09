#!/bin/bash
set -e
set -x

/sio2/oioioi/wait-for-it.sh -t 60 "db:5432"

compr="True"

[[ "$1" == "--dev" ]] && compr="False"
sed -i "s/DEBUG = True/DEBUG = False/;s/^COMPRESS_OFFLINE.*\$/COMPRESS_OFFLINE = $compr/" /sio2/deployment/settings.py

./manage.py migrate &
if [ "$1" == "--dev" ]; then
    ./manage.py collectstatic --noinput &
else
    ./manage.py compilejsi18n &
    (./manage.py collectstatic --noinput && ./manage.py compress > /dev/null) &
    #sudo /etc/init.d/nginx start &
    caddy start &
fi

wait
exec ./manage.py supervisor --logfile=/sio2/deployment/logs/supervisor.log
