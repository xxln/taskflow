# Define patterns for files and directories
CLEAN_FILES = .DS_Store *.pyc
CLEAN_DIRS = .pytest_cache __pycache__ .ipynb_checkpoints
CLEAN_LATEX_FILES = *.aux *.log *.out *.synctex.gz

# Clean up build artifacts, caches, and documentation output
clean:
	@echo "Cleaning up..."
	@echo "--------------------------------"
	# Clean files
	@for pattern in $(CLEAN_FILES); do \
		find . -type f -name "$$pattern" -delete; \
		echo "Deleted $$pattern"; \
	done
	@echo "--------------------------------"

.PHONY: api cli ui

api:
	uv run taskflow-server

cli:
	uv run taskflow $(ARGS)

ui:
	@echo "Open http://127.0.0.1:8765 in your browser after running 'make api'"

	# Clean directories
	@for pattern in $(CLEAN_DIRS); do \
		find . -type d -name "$$pattern" -exec rm -rf {} +; \
		echo "Deleted $$pattern"; \
	done
	@echo "--------------------------------"
