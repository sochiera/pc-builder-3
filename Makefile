.PHONY: run smoke ci hardware

run:
	python3 app.py

smoke:
	python3 -m unittest -v test_app.py

ci: smoke

hardware: smoke
