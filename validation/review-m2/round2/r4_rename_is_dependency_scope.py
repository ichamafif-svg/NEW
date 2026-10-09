# F4: scope is computed from PR file *names*; a rename app/service.py -> requirements-old.txt (or deletion of
# .github/workflows/standard.yml via rename) reads as dependency-only -> autonomous merge.
from ops.world import GitHub
from ops.cycle import subject_facts
from ops import lifecycle
HEAD = "c" * 40
g = GitHub("o/demo", "t")
api = {  # shapes of real GitHub REST responses
    "/pulls/7": {"head": {"sha": HEAD, "repo": {"full_name": "o/demo"}}, "base": {"ref": "main"}, "merged": False,
                 "state": "open", "changed_files": 2},
    "/pulls/7/files": [{"filename": "requirements.txt", "status": "modified"},
                       {"filename": "requirements-old.txt", "previous_filename": ".github/workflows/standard.yml",
                        "status": "renamed"}],
    "/actions/runs": {"workflow_runs": [{"head_sha": HEAD, "path": ".github/workflows/ci.yml", "status": "completed",
                                         "conclusion": "success", "run_number": 1,
                                         "head_repository": {"full_name": "o/demo"}}]},
}
g.get = lambda path, **p: api[path]
print(subject_facts(g, lifecycle.subject_of(f"repo:deps:vulns/pr/7/{HEAD}")))
