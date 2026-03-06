up:
	docker-compose up --build -d

down:
	docker-compose down

logs:
	docker-compose logs -f backend worker

test:
	docker-compose exec backend pytest tests/ -v

migrate:
	docker-compose exec backend alembic upgrade head

shell:
	docker-compose exec backend python
