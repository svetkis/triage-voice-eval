.PHONY: install test example-shopco example-multi-persona

install:
	pip install -e ".[dev,examples]"

test:
	pytest -v

example-shopco:
	python -m examples.shopco_eval.run_eval

example-multi-persona:
	python -m examples.multi_persona.run_eval
