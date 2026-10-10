"""Read-only repository discovery; presence is never a qualified observation."""
from __future__ import annotations

import subprocess
from fnmatch import fnmatchcase
from pathlib import Path


SOURCES = {
    "ci": (".github/workflows/*", ".gitlab-ci.yml", "Jenkinsfile", "azure-pipelines.yml"),
    "dependencies": ("requirements*.txt", "pyproject.toml", "poetry.lock", "package-lock.json", "pnpm-lock.yaml", "Cargo.lock"),
    "policy": (".standard/law.toml", "policy/*", "policies/*", "**/*.rego", "**/*.cedar"),
    "owners": ("CODEOWNERS", ".github/CODEOWNERS", "docs/adr/*"),
    "infrastructure": ("Dockerfile", "docker-compose*.yml", "**/*.tf", "k8s/*", "helm/*"),
    "observability": ("otel-collector*.yml", "prometheus*.yml", "grafana/*", "datadog.yaml"),
    "security": (".github/dependabot.yml", ".github/workflows/*security*", ".snyk"),
    "sre": ("runbooks/*", "oncall/*", "pagerduty/*", "incident/*"),
}


def discover_repository(path):
    """Inspect tracked path names, not untrusted code or network services."""
    root = Path(path).resolve()
    process = subprocess.run(["git", "-C", str(root), "ls-files", "-z"],
                             capture_output=True, timeout=30, check=True)
    paths = sorted(p.decode("utf-8", "surrogateescape") for p in process.stdout.split(b"\0") if p)
    categories = []
    for name, patterns in SOURCES.items():
        matches = sorted({p for p in paths for pattern in patterns if fnmatchcase(p, pattern)})
        categories.append({"kind": name, "status": "PRESENT_UNQUALIFIED" if matches else "NOT_FOUND",
                           "paths": matches[:100], "truncated": len(matches) > 100})
    return {"format": "standard-discovery/1", "root": str(root), "tracked": len(paths),
            "categories": categories, "authority": "NONE",
            "next": "map_candidates_to_installed_routes_and_qualify_independently"}
