PYTHON := python

.PHONY: migrate upgrade downgrade alembic-init

migrate:
	alembic revision --autogenerate -m "manual revision"

upgrade:
	alembic upgrade head

downgrade:
	alembic downgrade -1

alembic-init:
	alembic init migrations
