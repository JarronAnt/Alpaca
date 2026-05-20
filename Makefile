# Makefile
.PHONY: install test lint format clean build docker

install:
	uv pip install -e ".[dev]"

test:
	pytest -v --cov=alpaca --cov-report=term-missing

lint:
	ruff check src tests
	mypy src

format:
	black src tests
	ruff check --fix src tests

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .mypy_cache htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} +

build:
	uv build

docker:
	docker-compose up --build

run:
	python -m alpaca run --interactive
