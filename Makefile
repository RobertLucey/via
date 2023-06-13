PYTHON=python3.10

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
	$(IN_ENV) $(TEST_CONTEXT) nose2




local_setup:
	@echo "Running Make rule local_setup..."
	$(PYTHON) -m venv $(ENV_DIR)
	$(IN_ENV) python -m pip install --upgrade pip
	$(IN_ENV) python -m pip install --upgrade -r requirements.txt

local_run:
	@echo "Running Make rule local_run..."
	$(IN_ENV) uvicorn src.via.main:app --reload

local_docker_run:
	docker compose up --build

local_push_journey:
	@echo "POST /push_journey:"
	@curl \
		-X POST \
		-H "accept: application/json" \
		-H "Content-Type: application/json" \
		-d @resources/full.json \
		http://127.0.0.1:8000/push_journey
	@echo

	@echo "Done."

local_pull_journey:
	@echo "GET /get_journey:"
	@curl \
		-X GET \
		http://127.0.0.1:8000/get_journey
	@echo

	@echo "Done."

local_get_geojson:
	@echo "GET /get_geojson:"
	@curl \
		-X GET \
		http://127.0.0.1:8000/get_geojson?earliest_time=2021-01&latest_time=2023-12
	@echo

	@echo "Done."

production_setup:
	@echo "Running Make rule production_setup..."

production_run:
	@echo "Running Make rule production_run..."
	uvicorn via.main:app --proxy-headers --host 0.0.0.0 --port 8000 --reload


remote_push_journey:
	@echo "POST /push_journey:"
	@curl \
		-X POST \
		-H "accept: application/json" \
		-H "Content-Type: application/json" \
		-d @resources/full.json \
		https://test-via-api.randombits.host/push_journey
	@echo

	@echo "Done."
