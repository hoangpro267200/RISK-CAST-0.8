#!/bin/bash
# =============================================================================
# Kubernetes Deployment Helper Script
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed"
        exit 1
    fi
    
    if ! command -v kustomize &> /dev/null; then
        log_error "kustomize is not installed"
        exit 1
    fi
    
    log_info "Prerequisites OK"
}

# Deploy to environment
deploy() {
    local env=$1
    
    if [[ -z "$env" ]]; then
        log_error "Environment not specified"
        echo "Usage: $0 deploy <development|staging|production>"
        exit 1
    fi
    
    log_info "Deploying to ${env}..."
    
    # Validate overlay exists
    if [[ ! -d "k8s/overlays/${env}" ]]; then
        log_error "Overlay directory k8s/overlays/${env} does not exist"
        exit 1
    fi
    
    # Build and apply
    kustomize build k8s/overlays/${env} | kubectl apply -f -
    
    log_info "Deployment to ${env} complete"
}

# View manifest without applying
view() {
    local env=$1
    
    if [[ -z "$env" ]]; then
        log_error "Environment not specified"
        echo "Usage: $0 view <development|staging|production>"
        exit 1
    fi
    
    kustomize build k8s/overlays/${env}
}

# Check deployment status
status() {
    local env=$1
    local namespace="riskcast"
    
    if [[ "$env" == "production" ]]; then
        namespace="riskcast-prod"
    elif [[ "$env" == "staging" ]]; then
        namespace="riskcast-staging"
    elif [[ "$env" == "development" ]]; then
        namespace="riskcast-dev"
    fi
    
    log_info "Checking status in namespace: ${namespace}"
    
    echo ""
    log_info "Deployments:"
    kubectl get deployments -n ${namespace}
    
    echo ""
    log_info "Pods:"
    kubectl get pods -n ${namespace}
    
    echo ""
    log_info "Services:"
    kubectl get services -n ${namespace}
    
    echo ""
    log_info "Ingress:"
    kubectl get ingress -n ${namespace}
    
    echo ""
    log_info "HPA:"
    kubectl get hpa -n ${namespace}
}

# Rollback deployment
rollback() {
    local env=$1
    local deployment=$2
    local namespace="riskcast"
    
    if [[ "$env" == "production" ]]; then
        namespace="riskcast-prod"
    elif [[ "$env" == "staging" ]]; then
        namespace="riskcast-staging"
    elif [[ "$env" == "development" ]]; then
        namespace="riskcast-dev"
    fi
    
    if [[ -z "$deployment" ]]; then
        deployment="prod-riskcast-api"
    fi
    
    log_warn "Rolling back ${deployment} in ${namespace}"
    kubectl rollout undo deployment/${deployment} -n ${namespace}
    
    log_info "Rollback initiated"
}

# Get logs
logs() {
    local env=$1
    local component=$2
    local namespace="riskcast"
    
    if [[ "$env" == "production" ]]; then
        namespace="riskcast-prod"
    elif [[ "$env" == "staging" ]]; then
        namespace="riskcast-staging"
    elif [[ "$env" == "development" ]]; then
        namespace="riskcast-dev"
    fi
    
    if [[ -z "$component" ]]; then
        component="api"
    fi
    
    log_info "Fetching logs for ${component} in ${namespace}"
    
    kubectl logs -f -l app.kubernetes.io/name=riskcast-${component} -n ${namespace}
}

# Scale deployment
scale() {
    local env=$1
    local replicas=$2
    local namespace="riskcast"
    
    if [[ "$env" == "production" ]]; then
        namespace="riskcast-prod"
    elif [[ "$env" == "staging" ]]; then
        namespace="riskcast-staging"
    elif [[ "$env" == "development" ]]; then
        namespace="riskcast-dev"
    fi
    
    if [[ -z "$replicas" ]]; then
        log_error "Replicas count not specified"
        echo "Usage: $0 scale <env> <replicas>"
        exit 1
    fi
    
    log_info "Scaling API to ${replicas} replicas in ${namespace}"
    kubectl scale deployment/prod-riskcast-api --replicas=${replicas} -n ${namespace}
}

# Delete deployment
delete() {
    local env=$1
    local namespace="riskcast"
    
    if [[ "$env" == "production" ]]; then
        namespace="riskcast-prod"
        log_warn "⚠️  WARNING: You are about to delete PRODUCTION environment!"
        read -p "Type 'DELETE PRODUCTION' to confirm: " confirm
        if [[ "$confirm" != "DELETE PRODUCTION" ]]; then
            log_info "Cancelled"
            exit 0
        fi
    elif [[ "$env" == "staging" ]]; then
        namespace="riskcast-staging"
    elif [[ "$env" == "development" ]]; then
        namespace="riskcast-dev"
    fi
    
    log_warn "Deleting all resources in ${namespace}"
    kubectl delete namespace ${namespace}
    
    log_info "Deletion complete"
}

# Main
case "${1:-}" in
    "deploy")
        check_prerequisites
        deploy "$2"
        ;;
    "view")
        check_prerequisites
        view "$2"
        ;;
    "status")
        status "$2"
        ;;
    "rollback")
        rollback "$2" "$3"
        ;;
    "logs")
        logs "$2" "$3"
        ;;
    "scale")
        scale "$2" "$3"
        ;;
    "delete")
        delete "$2"
        ;;
    *)
        echo "RISKCAST Kubernetes Deployment Helper"
        echo ""
        echo "Usage: $0 <command> [options]"
        echo ""
        echo "Commands:"
        echo "  deploy <env>           Deploy to environment (development|staging|production)"
        echo "  view <env>             View generated manifests without applying"
        echo "  status <env>           Check deployment status"
        echo "  rollback <env> [name]  Rollback deployment"
        echo "  logs <env> [component] View logs (component: api|worker)"
        echo "  scale <env> <replicas> Scale deployment"
        echo "  delete <env>           Delete environment (DESTRUCTIVE!)"
        echo ""
        echo "Examples:"
        echo "  $0 deploy production"
        echo "  $0 status production"
        echo "  $0 logs production api"
        echo "  $0 scale production 10"
        echo ""
        exit 1
        ;;
esac
