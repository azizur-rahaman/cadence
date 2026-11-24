# ==============================================================================
# Cadence (Level 10) — Operations & Verification Makefile
# ==============================================================================

SHELL := /bin/bash
.DEFAULT_GOAL := help

APP_NOW ?= 2026-11-11T15:00:00Z

BOLD   := \033[1m
GREEN  := \033[32m
YELLOW := \033[33m
CYAN   := \033[36m
RESET  := \033[0m

.PHONY: help up down restart logs status seed report lint typecheck test test-e2e verify ports

help:
	@echo ""
	@echo -e "${BOLD}${GREEN}==============================================================${RESET}"
	@echo -e "${BOLD}${GREEN}          Cadence (Level 10) — Monorepo Operations            ${RESET}"
	@echo -e "${BOLD}${GREEN}==============================================================${RESET}"
	@echo ""
	@echo -e "${BOLD}Docker Compose Stack:${RESET}"
	@echo -e "  ${CYAN}make up${RESET}         Build & start Postgres, API (:8000) and Web (:3000)"
	@echo -e "  ${CYAN}make down${RESET}       Stop containers (add -v manually to wipe DB volume)"
	@echo -e "  ${CYAN}make restart${RESET}    Restart all stack containers"
	@echo -e "  ${CYAN}make status${RESET}     Show container health status"
	@echo -e "  ${CYAN}make logs${RESET}       Follow container logs"
	@echo ""
	@echo -e "${BOLD}Data & Rules Report:${RESET}"
	@echo -e "  ${CYAN}make seed${RESET}       Run idempotent seed loader"
	@echo -e "  ${CYAN}make report${RESET}     Print rules_report JSON for APP_NOW"
	@echo ""
	@echo -e "${BOLD}Verification & Quality Gates:${RESET}"
	@echo -e "  ${CYAN}make lint${RESET}       Run ruff static checks on apps/api"
	@echo -e "  ${CYAN}make typecheck${RESET}  Run TypeScript strict compiler check (tsc --noEmit)"
	@echo -e "  ${CYAN}make test${RESET}       Run automated test suite unattended (frozen clock)"
	@echo -e "  ${CYAN}make test-e2e${RESET}   Run two-browser Playwright E2E suite against live stack"
	@echo -e "  ${CYAN}make verify${RESET}     Compulsory pre-PR gate (lint + typecheck + test)"
	@echo -e "  ${CYAN}make ports${RESET}      Check listening status of ports 3000, 8000, 5432"
	@echo ""

up:
	@docker compose up --build -d
	@echo -e "${GREEN}==> Stack is up: Web http://localhost:3000 | API http://localhost:8000/docs${RESET}"

down:
	@docker compose down

restart:
	@docker compose down
	@docker compose up --build -d

logs:
	@docker compose logs -f

status:
	@docker compose ps

seed:
	@docker compose run --rm -e APP_NOW=$(APP_NOW) -e CLOCK_MODE=frozen api python -m app.cli.seed

report:
	@docker compose run --rm -T -e APP_NOW=$(APP_NOW) -e CLOCK_MODE=frozen api python -m app.cli.report

lint:
	@echo -e "${CYAN}==> Running ruff lint on apps/api...${RESET}"
	@docker compose run --rm --no-deps api ruff check app tests

typecheck:
	@echo -e "${CYAN}==> Running TypeScript typecheck on apps/web...${RESET}"
	@cd apps/web && npm run typecheck

test:
	@echo -e "${CYAN}==> Running pytest suite (frozen clock: $(APP_NOW))...${RESET}"
	@docker compose run --rm -e APP_NOW=$(APP_NOW) -e CLOCK_MODE=frozen api pytest -v

test-e2e:
	@echo -e "${CYAN}==> Running two-browser Playwright E2E suite...${RESET}"
	@cd e2e && npm test

verify: lint typecheck test
	@echo -e "${GREEN}==> make verify PASSED (0 errors)${RESET}"

ports:
	@echo -e "${BOLD}Port Status:${RESET}"
	@for port in 3000 8000 5432; do \
		pid=$$(lsof -sTCP:LISTEN -ti :$$port 2>/dev/null | head -n 1); \
		if [ -n "$$pid" ]; then \
			echo -e "  Port $$port: ${GREEN}IN USE${RESET} (PID $$pid)"; \
		else \
			echo -e "  Port $$port: ${YELLOW}FREE${RESET}"; \
		fi \
	done
