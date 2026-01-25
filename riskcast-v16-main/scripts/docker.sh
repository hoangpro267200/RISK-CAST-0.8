#!/bin/bash
# =============================================================================
# RISKCAST - Docker Helper Scripts
# =============================================================================
# Collection of useful Docker commands for managing RiskCast

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# =============================================================================
# Production Commands
# =============================================================================

prod_build() {
    log_info "Building production images..."
    docker-compose build --no-cache
}

prod_up() {
    log_info "Starting production services..."
    docker-compose up -d
    log_info "Services started. Check logs with: docker-compose logs -f"
}

prod_down() {
    log_info "Stopping production services..."
    docker-compose down
}

prod_restart() {
    log_info "Restarting production services..."
    docker-compose restart
}

prod_logs() {
    docker-compose logs -f "$@"
}

prod_ps() {
    docker-compose ps
}

prod_migrate() {
    log_info "Running database migrations..."
    docker-compose exec api alembic upgrade head
}

prod_shell() {
    log_info "Opening shell in API container..."
    docker-compose exec api /bin/bash
}

prod_db_shell() {
    log_info "Opening PostgreSQL shell..."
    docker-compose exec postgres psql -U riskcast -d riskcast
}

# =============================================================================
# Development Commands
# =============================================================================

dev_build() {
    log_info "Building development images..."
    docker-compose -f docker-compose.dev.yml build --no-cache
}

dev_up() {
    log_info "Starting development services..."
    docker-compose -f docker-compose.dev.yml up -d
    log_info "Development environment ready!"
    log_info "  API:              http://localhost:8000"
    log_info "  API Docs:         http://localhost:8000/docs"
    log_info "  Adminer:          http://localhost:8080"
    log_info "  Redis Commander:  http://localhost:8081"
    log_info "  Mailhog:          http://localhost:8025"
}

dev_down() {
    log_info "Stopping development services..."
    docker-compose -f docker-compose.dev.yml down
}

dev_restart() {
    log_info "Restarting development services..."
    docker-compose -f docker-compose.dev.yml restart
}

dev_logs() {
    docker-compose -f docker-compose.dev.yml logs -f "$@"
}

dev_shell() {
    log_info "Opening shell in development API container..."
    docker-compose -f docker-compose.dev.yml exec api /bin/bash
}

dev_test() {
    log_info "Running tests in development container..."
    docker-compose -f docker-compose.dev.yml exec api pytest tests/ -v "$@"
}

dev_migrate() {
    log_info "Running database migrations in development..."
    docker-compose -f docker-compose.dev.yml exec api alembic upgrade head
}

dev_db_reset() {
    log_warn "This will destroy all data in the development database!"
    read -p "Are you sure? (yes/no): " confirm
    if [ "$confirm" = "yes" ]; then
        log_info "Resetting development database..."
        docker-compose -f docker-compose.dev.yml down -v
        docker-compose -f docker-compose.dev.yml up -d postgres redis
        sleep 5
        docker-compose -f docker-compose.dev.yml up -d api
        docker-compose -f docker-compose.dev.yml exec api alembic upgrade head
        log_info "Database reset complete"
    else
        log_info "Cancelled"
    fi
}

# =============================================================================
# Maintenance Commands
# =============================================================================

cleanup() {
    log_info "Cleaning up Docker resources..."
    docker system prune -f
    log_info "Cleanup complete"
}

cleanup_all() {
    log_warn "This will remove all unused Docker resources including volumes!"
    read -p "Are you sure? (yes/no): " confirm
    if [ "$confirm" = "yes" ]; then
        docker system prune -af --volumes
        log_info "All cleanup complete"
    else
        log_info "Cancelled"
    fi
}

backup_db() {
    log_info "Creating database backup..."
    timestamp=$(date +%Y%m%d_%H%M%S)
    backup_file="backup_${timestamp}.sql"
    docker-compose exec -T postgres pg_dump -U riskcast -d riskcast > "$backup_file"
    log_info "Backup created: $backup_file"
}

restore_db() {
    if [ -z "$1" ]; then
        log_error "Usage: $0 restore-db <backup_file.sql>"
        exit 1
    fi
    log_warn "This will overwrite the current database!"
    read -p "Are you sure? (yes/no): " confirm
    if [ "$confirm" = "yes" ]; then
        log_info "Restoring database from $1..."
        docker-compose exec -T postgres psql -U riskcast -d riskcast < "$1"
        log_info "Database restored"
    else
        log_info "Cancelled"
    fi
}

health_check() {
    log_info "Checking service health..."
    echo ""
    echo "API Health:"
    curl -f http://localhost:8000/health/live || echo "API not responding"
    echo ""
    echo ""
    echo "Docker Services:"
    docker-compose ps
}

# =============================================================================
# Main
# =============================================================================

case "${1:-}" in
    # Production
    "build")
        prod_build
        ;;
    "up")
        prod_up
        ;;
    "down")
        prod_down
        ;;
    "restart")
        prod_restart
        ;;
    "logs")
        shift
        prod_logs "$@"
        ;;
    "ps")
        prod_ps
        ;;
    "migrate")
        prod_migrate
        ;;
    "shell")
        prod_shell
        ;;
    "db-shell")
        prod_db_shell
        ;;
    
    # Development
    "dev-build")
        dev_build
        ;;
    "dev-up")
        dev_up
        ;;
    "dev-down")
        dev_down
        ;;
    "dev-restart")
        dev_restart
        ;;
    "dev-logs")
        shift
        dev_logs "$@"
        ;;
    "dev-shell")
        dev_shell
        ;;
    "dev-test")
        shift
        dev_test "$@"
        ;;
    "dev-migrate")
        dev_migrate
        ;;
    "dev-db-reset")
        dev_db_reset
        ;;
    
    # Maintenance
    "cleanup")
        cleanup
        ;;
    "cleanup-all")
        cleanup_all
        ;;
    "backup-db")
        backup_db
        ;;
    "restore-db")
        shift
        restore_db "$@"
        ;;
    "health")
        health_check
        ;;
    
    *)
        echo "RISKCAST Docker Helper"
        echo ""
        echo "Production Commands:"
        echo "  build              Build production images"
        echo "  up                 Start production services"
        echo "  down               Stop production services"
        echo "  restart            Restart production services"
        echo "  logs [service]     View logs (optional: specific service)"
        echo "  ps                 List running services"
        echo "  migrate            Run database migrations"
        echo "  shell              Open shell in API container"
        echo "  db-shell           Open PostgreSQL shell"
        echo ""
        echo "Development Commands:"
        echo "  dev-build          Build development images"
        echo "  dev-up             Start development services"
        echo "  dev-down           Stop development services"
        echo "  dev-restart        Restart development services"
        echo "  dev-logs [service] View development logs"
        echo "  dev-shell          Open shell in development container"
        echo "  dev-test [args]    Run tests in development container"
        echo "  dev-migrate        Run migrations in development"
        echo "  dev-db-reset       Reset development database (destructive!)"
        echo ""
        echo "Maintenance Commands:"
        echo "  cleanup            Clean up unused Docker resources"
        echo "  cleanup-all        Clean up all Docker resources (destructive!)"
        echo "  backup-db          Create database backup"
        echo "  restore-db <file>  Restore database from backup"
        echo "  health             Check service health"
        echo ""
        exit 1
        ;;
esac
