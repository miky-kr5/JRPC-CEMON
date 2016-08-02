#! /bin/sh

python service.py 8080 DATABASE &
python service.py 8081 LINK &
python service.py 8082 ROUTER &
python service.py 8083 APP &
python service.py 8084 SERVER &
