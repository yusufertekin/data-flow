#!/bin/sh

python3 wait_for_it.py
sleep 2
echo ===Migrating===
django-admin migrate
echo ===Running Server===
django-admin runserver 0.0.0.0:8000
