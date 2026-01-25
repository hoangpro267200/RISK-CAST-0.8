# Makefile for Database Migrations

.PHONY: help migration-check migration-create migration-up migration-down backup

help:
	@echo "Database Migration Commands:"
	@echo "  make migration-check     - Check migration status"
	@echo "  make migration-create    - Create new migration"
	@echo "  make migration-up        - Run migrations"
	@echo "  make migration-down      - Rollback migration"
	@echo "  make backup              - Create database backup"
	@echo "  make migration-history   - Show migration history"

migration-check:
	python scripts/db/check_migrations.py

migration-create:
	@read -p "Migration message: " msg; \
	python scripts/db/create_migration.py "$$msg"

migration-up:
	python scripts/db/migrate.py

migration-down:
	@read -p "Target revision: " rev; \
	python scripts/db/rollback.py --target "$$rev"

backup:
	python scripts/db/backup.py

migration-history:
	python scripts/db/rollback.py --history

migration-dry-run:
	python scripts/db/migrate.py --dry-run
