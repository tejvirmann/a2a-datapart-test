.PHONY: help setup test clean run-server run-client

help:
	@echo "A2A EventQueue & TaskUpdater Test Project"
	@echo ""
	@echo "Available commands:"
	@echo "  make setup        - Create venv and install dependencies"
	@echo "  make test         - Run all tests"
	@echo "  make test-proof   - Run proof that enqueue_event works"
	@echo "  make test-diag    - Run diagnostic for common issues"
	@echo "  make run-server   - Start streaming server"
	@echo "  make run-client   - Start streaming client"
	@echo "  make run-executor - Run executor example"
	@echo "  make clean        - Remove cache and temp files"
	@echo ""

setup:
	@echo "Setting up environment..."
	python3 -m venv venv
	. venv/bin/activate && pip install -r requirements.txt
	@echo "✅ Setup complete! Activate with: source venv/bin/activate"

test:
	@echo "Running all tests..."
	@echo ""
	@echo "=== Proof of Concept ==="
	venv/bin/python3 tests/PROOF_QUEUE_WORKS.py
	@echo ""
	@echo "=== Diagnostics ==="
	venv/bin/python3 tests/FINAL_DIAGNOSIS.py
	@echo ""
	@echo "=== Method Tests ==="
	venv/bin/python3 tests/test_enqueue_methods.py
	@echo ""
	@echo "✅ All tests complete!"

test-proof:
	@echo "Running proof that enqueue_event() works..."
	venv/bin/python3 tests/PROOF_QUEUE_WORKS.py

test-diag:
	@echo "Running diagnostics..."
	venv/bin/python3 tests/FINAL_DIAGNOSIS.py

test-methods:
	@echo "Testing enqueue methods..."
	venv/bin/python3 tests/test_enqueue_methods.py

test-simple:
	@echo "Running simple blocking test..."
	venv/bin/python3 tests/simple_blocking_test.py

run-executor:
	@echo "Running executor example..."
	venv/bin/python3 examples/executor_with_taskupdater.py

run-server:
	@echo "Starting streaming server on http://localhost:8000..."
	@echo "Stream endpoint: http://localhost:8000/stream?query=test"
	venv/bin/python3 examples/stream_server.py

run-client:
	@echo "Starting streaming client..."
	venv/bin/python3 examples/stream_client.py

clean:
	@echo "Cleaning up..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Cleanup complete!"

list:
	@echo "Project structure:"
	@echo ""
	@echo "📁 examples/"
	@ls -1 examples/
	@echo ""
	@echo "🧪 tests/"
	@ls -1 tests/
	@echo ""
	@echo "📚 docs/"
	@ls -1 docs/
