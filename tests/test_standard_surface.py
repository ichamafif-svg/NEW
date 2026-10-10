"""The agent sees a scoped text projection, never an unsigned local law."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixture import World
from maintenance.constitution import agent_view
from standard.authoring import AuthoringError, load_source, proposal_text
from standard.service import Route, StandardService
from standard.surface import SurfaceError, render_m2, render_overview, render_task


class Surface(unittest.TestCase):
    def test_client_source_is_bounded_and_never_activates_itself(self):
        path = Path(__file__).resolve().parents[1] / "standard/examples/client-law.toml"
        client, effective, pinned = load_source(path)
        self.assertEqual(client["format"], "standard-client/1")
        self.assertIn("service-uptime", {t["id"] for t in effective["targets"]})
        self.assertIn(pinned, proposal_text(path))
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "law.toml"
            bad.write_text(path.read_text().replace('floor', 'fl00r', 1).replace(
                'sha256:78f56b582e01916bef9228fdeabd0c3ebcda40a868a012bfb02c1394590ae3a8',
                'sha256:' + '0' * 64))
            with self.assertRaises(AuthoringError):
                load_source(bad)

    def test_context_is_scoped_and_stale_law_never_renders(self):
        world = World()
        try:
            class Installed:
                def constitutional_view(self):
                    return agent_view(world.kernel, world.state, world.journal.health())
                def qualify_route(self, required): return None
                def admit(self, envelope): raise AssertionError("read-only context")

            cycle = StandardService(Installed(), [Route("scan", "RUN", "repo:*",
                                frozenset({"observe"}), frozenset({"T06"}))]).inspect()
            task = next(t for t in cycle["tasks"] if t["state"] == "READY")
            context = render_task(cycle, task["id"])
            self.assertIn(task["resource"], context)
            self.assertIn(cycle["basis"]["law_digest"], context)
            self.assertNotIn('"targets":', context)
            self.assertIn("standard context --task", render_overview(cycle))
            stale = dict(cycle, basis=dict(cycle["basis"], law_digest="sha256:" + "0" * 64))
            with self.assertRaises(SurfaceError):
                render_task(stale, task["id"])
            m2 = render_m2(Installed().constitutional_view(), "vulns")
            self.assertIn("remediate-autonomous", m2)
            self.assertNotIn("service-uptime", m2)
        finally:
            world.journal.close()


if __name__ == "__main__": unittest.main()
