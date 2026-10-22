# Makefile — reportesTekon (reg.tekon-rl.cl)
# Producción: `make deploy` en el VPS. Desarrollo local: `make dev`.

COMPOSE     ?= docker compose
DOMAIN      ?= reg2.tekon-rl.cl
BRANCH      ?= main
BACKUP_DIR  ?= backups
BACKUP_KEEP ?= 20

# ── Desarrollo local ──────────────────────────────────────────────────────────
# Puerto opcional: `make dev PORT=8005` (default 8001)
PORT ?= 8001

dev:
	python3 manage.py migrate
	python3 manage.py runserver $(PORT)

css:
	cd theme/static_src && npm run build

css-watch:
	cd theme/static_src && npm run start

check:
	python3 manage.py check

# ── Producción ────────────────────────────────────────────────────────────────
# Respaldo (no fatal) → git pull → rebuild + up → espera healthcheck.
deploy:
	@[ -f .env ] || { echo "Error: no se encontró .env"; exit 1; }
	@echo "━━━ Desplegando reg.tekon-rl.cl ($(DOMAIN)) ━━━"
	@echo "▶ Respaldando la base de datos..."
	@$(MAKE) --no-print-directory backup || echo "  ⚠ No se pudo respaldar (¿primer despliegue?); se continúa."
	@echo "▶ Actualizando código ($(BRANCH))..."
	git pull origin $(BRANCH)
	@echo "▶ Reconstruyendo contenedores..."
	$(COMPOSE) up -d --build --remove-orphans
	@echo "▶ Esperando a que Django esté saludable..."
	@for i in $$(seq 1 30); do \
		st=$$(docker inspect -f '{{.State.Health.Status}}' django_reg_tekon 2>/dev/null); \
		[ "$$st" = "healthy" ] && { echo "  ✓ django healthy"; break; }; \
		[ $$i -eq 30 ] && { echo "  ⚠ Django no quedó healthy (estado: $$st). Revisa: make logs"; exit 1; }; \
		sleep 5; \
	done
	docker image prune -f >/dev/null
	@echo ""
	@echo "✓ Despliegue completado → https://$(DOMAIN)"

# Respaldo pg_dump comprimido desde el contenedor `db`; conserva los últimos BACKUP_KEEP.
backup:
	@mkdir -p $(BACKUP_DIR)
	@set -a && . ./.env && set +a; \
	f="$(BACKUP_DIR)/db_$$(date +%Y%m%d_%H%M%S).sql.gz"; \
	if $(COMPOSE) exec -T db pg_dump -U "$$POSTGRES_USER" "$$POSTGRES_DB" | gzip > "$$f" && [ -s "$$f" ]; then \
		echo "  ✓ $$f"; \
		ls -t $(BACKUP_DIR)/db_*.sql.gz | tail -n +$$(($(BACKUP_KEEP) + 1)) | xargs -r rm -f --; \
	else \
		rm -f "$$f"; exit 1; \
	fi

# Aplica nginx.conf al host (requiere sudo). Ajusta la ruta si tu nginx usa otra.
nginx:
	sudo cp nginx.conf /etc/nginx/sites-available/$(DOMAIN)
	sudo ln -sf /etc/nginx/sites-available/$(DOMAIN) /etc/nginx/sites-enabled/$(DOMAIN)
	sudo nginx -t && sudo systemctl reload nginx

logs:
	$(COMPOSE) logs -f --tail=100 django

ps:
	$(COMPOSE) ps

restart:
	$(COMPOSE) restart django

down:
	$(COMPOSE) down

# Comandos Django dentro del contenedor
migrate:
	$(COMPOSE) exec django python manage.py migrate

shell:
	$(COMPOSE) exec django python manage.py shell

superuser:
	$(COMPOSE) exec django python manage.py createsuperuser

.PHONY: dev css css-watch check deploy backup nginx logs ps restart down migrate shell superuser
