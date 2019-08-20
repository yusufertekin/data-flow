"""To prevent docker race condition, this test the database port and
exits when it is open.
"""
import socket
import time
import dj_database_url

service_name = 'Postgres'
port = 5432
ip = dj_database_url.config()['HOST']

while True:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((ip, port))
    if result == 0:
        print("{0} port is open! Bye!".format(service_name))
        break
    else:
        print("{0} port is not open! I'll check it soon!".format(service_name))
        time.sleep(3)
