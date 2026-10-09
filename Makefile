.PHONY: check budget test manifest
check: budget test
manifest:
	python3 tools/release_manifest.py
budget:
	python3 tools/check_tcb.py
test:
	python3 tests/test_kernel.py
	python3 tests/test_effects.py
	python3 tests/test_accountability.py
	python3 tests/test_robustness.py
	python3 tests/test_isolation.py
	python3 tests/test_review.py
	python3 tests/test_floor.py
	python3 tests/test_language.py
	python3 tests/test_merge_regressions.py
	python3 tests/test_v0.py
	python3 tests/test_floors.py
	python3 tests/test_v6.py
	python3 tests/test_maintenance.py
	python3 tests/test_budget_classification.py
	python3 tests/test_root_causes.py
	python3 tests/test_m2.py
	python3 tests/test_compliance.py
	python3 tests/test_ops.py
