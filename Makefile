init:
	pip install -r requirements.txt

test:
	python -m unittest discover

bench:
	python -m resch.evaluation.benchmark

.PHONY: init test bench
