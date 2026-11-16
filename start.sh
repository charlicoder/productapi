#!/usr/bin/env bash
# Usage: ./start.sh [dev|prod|stop|logs|import <file>|shell] [dev|prod]
set -euo pipefail
cd "$(dirname "$0")"

MODE="${1:-dev}"
DEV=(docker compose -f docker-compose.yml)
PROD=(docker compose -f docker-compose.prod.yml)

case "$MODE" in
  dev)
    [ -f .env ] || echo "⚠ No .env found – using local SQLite. Copy .env.example to .env to set DATABASE_URL."
    echo "▶ Dev server → http://localhost:${PORT:-8765}  (admin: /admin; create a user: ./start.sh createsuperuser)"
    exec "${DEV[@]}" up --build
    ;;
  prod)
    [ -f .env ] || { echo "✖ .env missing (copy .env.example and fill it in)"; exit 1; }
    for v in DJANGO_SECRET_KEY DJANGO_ALLOWED_HOSTS DATABASE_URL; do
      grep -qE "^${v}=.+" .env || { echo "✖ $v must be set in .env"; exit 1; }
    done
    echo "▶ Building and starting production stack"
    "${PROD[@]}" up --build -d
    "${PROD[@]}" ps
    echo "Logs: ./start.sh logs prod"
    ;;
  stop)
    "${DEV[@]}" down 2>/dev/null || true
    "${PROD[@]}" down 2>/dev/null || true
    ;;
  logs)
    [ "${2:-dev}" = "prod" ] && exec "${PROD[@]}" logs -f api || exec "${DEV[@]}" logs -f api
    ;;
  import)   # ./start.sh import sample/products.json [prod]
    f="${2:?usage: ./start.sh import <json file> [dev|prod]}"
    C=("${DEV[@]}"); [ "${3:-dev}" = "prod" ] && C=("${PROD[@]}")
    "${C[@]}" run --rm -v "$PWD:/app" api python manage.py import_products "$f"
    ;;
  createsuperuser)
    exec "${DEV[@]}" run --rm api python manage.py createsuperuser
    ;;
  shell)
    exec "${DEV[@]}" exec api python manage.py shell
    ;;
  *)
    echo "Usage: $0 [dev|prod|stop|logs [dev|prod]|import <file> [dev|prod]|shell|createsuperuser]"; exit 1
    ;;
esac
