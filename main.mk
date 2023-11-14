PYTHON_SCRIPT = prod.py
DEST_DIR = ../frontend
GITHUB_REPO = dailyprod/prod

.PHONY: run_script commit_and_push

run_script:
	python $(PYTHON_SCRIPT)

push_update: run_script
	cd $(DEST_DIR)

	git add .
	git commit -m "auto update: $(shell date)"
	git push

# Default target
default: push_update
