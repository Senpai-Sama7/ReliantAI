PYTHON ?= python3
VENV ?= .venv
PIP := $(VENV)/bin/pip
PY := $(VENV)/bin/python

.PHONY: venv install init-db ranker dashboard test run lint clean download-models

venv:
	$(PYTHON) -m venv $(VENV)

install: venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

init-db:
	$(PY) lead_queue.py init

ranker:
	$(PY) market/census_ranker.py --config market/target_verticals.json

dashboard:
	$(PY) -m uvicorn dashboard_app:app --host 127.0.0.1 --port 8888 --reload

run:
	$(PY) orchestrator.py $(URL)

test:
	$(PY) -m pytest -q

lint:
	$(PY) -m py_compile orchestrator.py lead_queue.py dashboard_app.py market/census_ranker.py

clean:
	rm -rf .pytest_cache

download-models:
	$(PY) -m spacy download en_core_web_trf
