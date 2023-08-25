PYTHON=python3.11

# TODO: might be nice to have a non threading setting
TEST_CONTEXT=export TEST_ENV=True &&

ENV_DIR=.env_$(PYTHON)
IN_ENV=. $(ENV_DIR)/bin/activate &&

env: $(ENV_DIR)

setup:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install virtualenv
	$(PYTHON) -m virtualenv -p $(PYTHON) $(ENV_DIR)
	$(IN_ENV) $(PYTHON) -m pip install --upgrade -r requirements.txt
	$(IN_ENV) $(PYTHON) -m pip install --editable .

test_requirements:
	$(IN_ENV) $(PYTHON) -m pip install --upgrade -r test_requirements.txt

upload_pip: test build_dist
	twine upload --repository via dist/*

build_dist: setup
	rm -fr dist/
	$(IN_ENV) python setup.py sdist bdist_wheel

build: setup

quick_build:
	$(IN_ENV) $(PYTHON) -m pip install --editable .

test: build test_requirements quick_test

quick_test:
	$(IN_ENV) $(TEST_CONTEXT) coverage run -m pytest
	$(IN_ENV) coverage report -m --skip-empty --include="src/*"

ci_test: build test_requirements ci_quick_test

ci_quick_test:
	$(IN_ENV) $(TEST_CONTEXT) IS_ACTION=True coverage run -m pytest
	$(IN_ENV) coverage report -m --skip-empty --include="src/*"




local_setup:
	@echo "Running Make rule local_setup..."
	$(PYTHON) -m venv $(ENV_DIR)
	$(IN_ENV) python -m pip install --upgrade pip
	$(IN_ENV) python -m pip install --upgrade -r requirements.txt

local_run:
	$(IN_ENV) $(PYTHON) -m pip install --editable .
	@echo "Running Make rule local_run..."
	$(IN_ENV) uvicorn src.via.api.main:app --reload --log-level trace

local_docker_run:
	docker compose up --build

production_setup:
	@echo "Running Make rule production_setup..."

production_run:
	@echo "Running Make rule production_run..."
	uvicorn via.api.main:app --proxy-headers --host 0.0.0.0 --port 8000 --reload

reingest_journeys:
	echo "TODO"
