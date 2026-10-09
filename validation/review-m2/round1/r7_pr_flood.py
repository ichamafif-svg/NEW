"""R7 (new): Client.pages raises once a listing exceeds its cap; pulls() caps at 1000 open PRs. 1000 open PRs by
anyone (filtering by author happens after the listing) make pull_facts, hence cmd_scan's PR facts and read-back,
and cmd_repair abort on every cycle."""
from ops.gh import Client, GitHubError
from ops import scan

c = Client("o/demo", "t")
c.get = lambda path, **p: [{"number": i, "user": {"login": "spam"}, "base": {"ref": "main"},
                            "head": {"ref": "x", "sha": "0" * 40, "repo": None}} for i in range(100)]
try:
    scan.pull_facts(c, "standard-agent[bot]")
    print("pull_facts ok")
except GitHubError as exc:
    print("pull_facts raised:", exc)
