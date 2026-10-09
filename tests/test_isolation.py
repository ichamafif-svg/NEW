"""Actual confinement of the health reducer and durable pin failure probes."""
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixture import T0, World, raises, run, digest
from tcb import SQLitePins


def confined(source):
    root = str(Path(__file__).resolve().parents[1])
    script = (f"import sys; sys.path.insert(0, {root!r}); import os, socket, subprocess; "
              "from tcb.sandbox import lock_down; lock_down(); " + source)
    return subprocess.run([sys.executable, '-I', '-B', '-c', script], capture_output=True, timeout=10)


def test_health_confinement_blocks_credentials_network_processes_and_parent_memory():
    w = World()
    secret = w.tmp / 'provider-credential'
    secret.write_text('must-stay-with-the-port')
    for source in (f"open({str(secret)!r}).read()", f"open({str(secret)!r}, 'w').write('tampered')",
                   "socket.socket()", "subprocess.run(['/usr/bin/true'])",
                   f"open('/proc/{os.getpid()}/mem', 'rb').read(1)"):
        result = confined(source)
        assert result.returncode != 0 and b'PermissionError' in result.stderr, result.stderr
    assert secret.read_text() == 'must-stay-with-the-port'


def test_live_health_worker_receives_no_provider_environment():
    from unittest.mock import patch
    from tcb.sandbox import StreamWorker
    import subprocess
    seen = []
    original = subprocess.Popen
    def launch(*args, **kw):
        seen.append(kw['env'])
        return original(*args, **kw)
    with patch.dict(os.environ, {'TCB_TEST_PROVIDER_SECRET': 'not-for-health'}):
        with patch('tcb.sandbox.subprocess.Popen', side_effect=launch):
            w = World()
            assert w.journal.health()['state'] == 'IN_PROGRESS'
            assert 'TCB_TEST_PROVIDER_SECRET' not in seen[-1]
            pid = w.journal.auditor._worker.child.pid
            assert w.journal.health()['state'] == 'IN_PROGRESS'
            assert w.journal.auditor._worker.child.pid == pid
            w.journal.close()


def test_durable_pins_reopen_and_reject_fork_domain_and_silent_recreation():
    w = World()
    retained = w.pins.load()
    reopened = SQLitePins(w.pins.path)
    assert reopened.load() == retained
    with raises(ValueError, 'another ledger'):
        reopened.bind(digest({'other': 'ledger'}))
    with raises(ValueError, 'regression or fork'):
        reopened.retain({**retained[0], 'head': digest({'fork': 1})})
    with raises(FileExistsError, '.'):
        SQLitePins(w.pins.path, create=True)
    w.pins.path.unlink()
    with raises(FileNotFoundError, 'silently recreated'):
        SQLitePins(w.pins.path)


if __name__ == '__main__':
    run(globals())
