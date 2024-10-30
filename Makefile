RUN=docker compose run --rm sso
all:
	docker compose build

run:
	docker compose up

ms:
	$(RUN) alembic revision --autogenerate

# merge-migrations:
# migration_count := $(shell $(RUN) alembic heads | wc -l)
# ifeq ($(shell expr $(migration_count) \> 1), 1)
# 	$(RUN) alembic merge heads
# else
# 	$(RUN) alembic revision --autogenerate
# endif

migrate:
	$(RUN) alembic upgrade head

shell:
	$(RUN) /bin/bash

seed-dashboard:
	$(RUN) python3 seed_dashboard.py -u=${USERID} -o=${ORGID} -c=${CONSULTANTID}

fmt:
	$(RUN) poetry run black .
	$(RUN) poetry run isort . --profile black

lint:
	$(RUN) poetry run black . --check
	$(RUN) poetry run isort . -c --profile black

test:
	$(RUN) poetry run pytest -x -vvv --pdb

report:
	$(RUN) poetry run pytest -x --pdb

report-fail:
	$(RUN) poetry run pytest --cov-report term --cov-fail-under=90