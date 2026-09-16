.PHONY: up down build logs seed migrate revision fmt backend-shell db-shell

up:            ## Build and start the whole stack
	docker compose up --build

down:          ## Stop and remove containers
	docker compose down

build:         ## Build images
	docker compose build

logs:          ## Tail all logs
	docker compose logs -f

seed:          ## Load demo data into the demo tenant
	docker compose exec backend python -m app.seed

migrate:       ## Apply DB migrations
	docker compose exec backend alembic upgrade head

revision:      ## Autogenerate a migration: make revision m="message"
	docker compose exec backend alembic revision --autogenerate -m "$(m)"

backend-shell: ## Shell into the backend container
	docker compose exec backend sh

db-shell:      ## psql into the database
	docker compose exec db psql -U fleetos -d fleetos
