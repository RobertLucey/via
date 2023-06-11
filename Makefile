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

production_setup:
	@echo "Running Make rule production_setup..."

production_run:
	@echo "Running Make rule production_run..."
	uvicorn via.main:app --reload

local_query:
	@echo "GET /:"
	@curl http://127.0.0.1:8000
	@echo

	@echo "GET /items/{item_id}:"
	@curl http://127.0.0.1:8000/items/123
	@echo

	@echo "GET /offset_items/:"
	@curl http://127.0.0.1:8000/offset_items?skip=1&limit=2
	@echo

	@echo "POST /items/:"
	@curl http://127.0.0.1:8000/items/123
	@echo

	@echo "POST /items/ (Simulated data packet):"
	@curl \
		-X POST \
		-H "accept: application/json" \
		-H "Content-Type: application/json" \
		-d @resources/basic_packet.json \
		http://127.0.0.1:8000/items/
	@echo

	@echo "Done."
