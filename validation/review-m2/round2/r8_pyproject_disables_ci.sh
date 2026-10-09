# F5b: a "dependency-scope" pyproject.toml turns the CI that judges it green without running a test.
set -e; d=$(mktemp -d); cp -r /tmp/claude-0/nosec/m2/demo/. $d; cd $d; rm -rf .pytest_cache */__pycache__
echo 'def test_broken(): assert False' > tests/test_broken.py
python3 -m pytest -q -p no:cacheprovider >/dev/null 2>&1 && echo "before: exit 0" || echo "before: exit $?"
printf '[tool.pytest.ini_options]\naddopts = "--collect-only -q"\n' > pyproject.toml
python3 -m pytest -q -p no:cacheprovider >/dev/null 2>&1; echo "after pyproject.toml: exit $?"
