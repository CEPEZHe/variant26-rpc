.PHONY: install repl server test coverage

install:
	python3 -m pip install -r requirements.txt

repl:
	PYTHONPATH=src python3 src/repl.py

server:
	PYTHONPATH=src python3 src/server.py

test:
	PYTHONPATH=src pytest -q

coverage:
	PYTHONPATH=src coverage run --branch -m pytest -q tests/test_mbt.py
	coverage report -m
