"""Running code: the only place Standard executes the repository, and it holds no key.

Rule 5: the instrument is fixed by the base. A commit is tested with main's test suite and test configuration (the
suite, `requirements-dev.txt`, an empty pytest configuration so nothing the commit ships can reconfigure the runner),
against the commit's own code and dependency lock. The universe is the set of tests main's suite defines.

Code under test can lie about itself (exit early, forge a report): a `tests` fact is a necessary signal, never
sufficient ground for autonomy. That is why the law also requires `reproduced` or a signed human review."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from .probes import Measure, verdict


def _sh(cmd, cwd, env=None, timeout=1800):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, env=env)


def run_suite(code: Path, suite: Path) -> Measure:
    """Run `suite`'s tests/ against `code`, in a fresh environment with code's lock and suite's dev requirements."""
    work = Path(tempfile.mkdtemp())
    venv = work / "venv"
    _sh([sys.executable, "-m", "venv", str(venv)], work)
    py = str(venv / "bin" / "python")
    reqs = ["-r", str(code / "requirements.txt")]
    if (suite / "requirements-dev.txt").exists():
        reqs += ["-r", str(suite / "requirements-dev.txt")]
    if _sh([py, "-m", "pip", "install", "-q", *reqs], code).returncode != 0:
        raise RuntimeError("dependencies do not install")
    (work / "pytest.ini").write_text("[pytest]\n")
    report = work / "report.xml"
    env = {"PATH": f"{venv / 'bin'}:/usr/bin:/bin", "PYTHONPATH": str(code), "HOME": str(work)}
    _sh([py, "-m", "pytest", "-c", str(work / "pytest.ini"), "--rootdir", str(code), "-p", "no:cacheprovider",
         "-q", f"--junitxml={report}", str(suite / "tests")], code, env=env)
    if not report.exists():
        raise RuntimeError("no report")
    names, failed = set(), []
    for case in ET.parse(report).iter("testcase"):
        name = f"{case.get('classname', '').rsplit('.', 1)[-1]}::{case.get('name')}"
        if any(child.tag == "skipped" for child in case):
            continue                                       # not run: not covered
        names.add(name)
        if any(child.tag in ("failure", "error") for child in case):
            failed.append(name)
    return Measure(frozenset(), frozenset(names), tuple(failed))


def test_all(main: Path, subjects: dict) -> dict:
    """subjects: resource -> checkout of its head. The universe of every run is the set of tests main defines."""
    out = {"subjects": {}}
    try:
        on_main = run_suite(main, main)
        universe = on_main.covered
        out["main"] = verdict("green", Measure(universe, on_main.covered, on_main.findings))
    except Exception as exc:  # noqa: BLE001
        universe, out["main"] = frozenset(), verdict("green", exc)
    for resource, head in subjects.items():
        try:
            m = run_suite(Path(head), main)
            out["subjects"][resource] = verdict("green", Measure(universe, m.covered & universe, m.findings))
        except Exception as exc:  # noqa: BLE001
            out["subjects"][resource] = verdict("green", exc)
    return out


if __name__ == "__main__":
    print(json.dumps(test_all(Path(sys.argv[1]), json.loads(sys.argv[2]) if len(sys.argv) > 2 else {})))
