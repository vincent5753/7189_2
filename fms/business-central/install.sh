cd showcase
sudo bash build.sh
sudo bash start.sh
sudo docker ps 
sudo docker run -p 8180:8080 -d --name kie-server --link drools-wb:kie-wb jboss/kie-server-showcase:latest
