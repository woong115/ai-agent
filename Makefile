name := ai-agent-api
tag := dev

test:
	@docker exec -it ai-agent-test pytest -rAvW

build:
	@docker build . -t ${name}:${tag} -f docker/Dockerfile 

up:
	@docker compose up -d

down:
	@docker compose down

logs:
	@docker compose logs -f api

sh:
	@docker exec -it ai-agent-api bash

pdf_to_markdown:
	@docker build . -t ${name}:${tag} -f docker/Dockerfile
	@docker compose up -d
	@docker exec -it ai-agent-api python app/helper/pdf_to_markdown.py

load_vectorstore:
	@docker build . -t ${name}:${tag} -f docker/Dockerfile
	@docker compose up -d
	@docker exec -it ai-agent-api python app/helper/load_vectorstore.py ${type}

dbul:
	@docker compose down
	@docker build . -t ${name}:${tag} -f docker/Dockerfile
	@docker compose up -d
	@docker compose logs -f demo api
