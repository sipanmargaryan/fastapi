#!/bin/bash
alembic upgrade head
python3 fill_countries.py
python3 add_super_admin.py
exec "$@"