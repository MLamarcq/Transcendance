USERNAME :=$(shell whoami)

all: 
	sudo mkdir -p /home/$(USERNAME)/data/database
	sudo mkdir -p /home/$(USERNAME)/data/backend
	sudo docker-compose -f docker-compose.yml build --no-cache;
	sudo docker-compose -f docker-compose.yml up -d

logs:
	sudo docker logs backend
	sudo docker logs database

clean:
	sudo docker container stop database
	sudo docker container stop backend
	sudo docker network rm transcendance

fclean: clean
	sudo rm -rf /home/$(USERNAME)/data/database/*
	sudo rm -rf /home/$(USERNAME)/data/backend/*
	sudo docker system prune -af

re: fclean all

.Phony: all logs clean fclean