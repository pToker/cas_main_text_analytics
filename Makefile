.PHONY: reset-db

reset-db:
	@echo "⚠️  Resetting sync_state, labels, emails..."
	python scripts/reset_db.py
