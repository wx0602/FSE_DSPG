#!/bin/bash
mvn clean install
docker-compose down
sudo docker-compose up -d --build --force-recreate
sudo docker stop jjdz7-drony_app_1
sleep 10
sudo docker start jjdz7-drony_app_1