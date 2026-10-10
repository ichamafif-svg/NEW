"""Regression scenarios from the external review, including crash and concurrency boundaries."""
import copy
import hashlib
import importlib.util
import json
import shutil
import sqlite3
import struct
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixture import T0, DAY, World, Refused, raises, run, digest
from tcb import EffectPort, NotDispatched, Kernel, Journal
from tcb.canon import canon, parse, CanonError
from tcb.sandbox import StreamWorker, WorkerFault, MAX_REPLY
import bootstrap


def intent(w):
    gid, t = w.grant('agent', ['effect:merge'], ['repo:pr:*'], T0 + 1)
    iid = w.add('intent', 'agent', t, under=gid, op='merge', args={'pr': '42', 'method': 'squash'})
    return gid, t, iid


def test_every_acknowledged_write_pins_and_restored_restrictions_cannot_disappear():
    for kind, fields in [('revoke', None), ('freeze', {'scope': 'repo:pr:*'}), ('veto', None)]:
        w = World()
        gid, t, iid = intent(w)
        guard = w.guard(lambda *_: 'ok')
        guard.issue(iid, t + 1)
        guard.redeem(w.state['token_of'][iid], t + 2)
        pending = w.add('grant', 'alice', w.state['last_at'] + 1, ['alice', 'bob'], holder='agent',
                        actions=['effect:merge'], resources=['repo:pr:*'], conditions=[], not_after=t + DAY)
        old_pin = w.pins.load()
        backup = w.tmp / 'backup.sqlite3'
        shutil.copy2(w.path, backup)
        fields = fields or ({'grant': gid} if kind == 'revoke' else {'proposal': pending})
        w.add(kind, 'carol', w.state['last_at'] + 1, **fields)
        assert w.pins.load() != old_pin
        assert w.pins.load() == [{'size': w.state['size'], 'head': w.state['head']}]
        shutil.copy2(backup, w.path)
        with raises(ValueError, 'retained checkpoint mismatch'):
            w.other_journal().snapshot()
        assert w.journal.health()['state'] == 'FAULT'


def test_pin_failure_before_durability_rolls_back_without_consuming_a_token():
    w = World()
    gid, t, iid = intent(w)
    calls = []
    guard = w.guard(lambda *_: calls.append(1) or 'ok')
    guard.issue(iid, t + 1)
    token = w.state['token_of'][iid]
    before = w.state['size']
    with patch.object(w.pins, 'retain', side_effect=OSError('storage unavailable')):
        with raises(OSError, 'storage unavailable'):
            guard.redeem(token, t + 2)
    assert w.state['size'] == before and f'unredeemed:{token}' in w.state['obligations']
    assert not calls


def test_pin_durable_then_interrupted_commit_blocks_until_exact_tail_repair():
    w = World()
    candidate, _ = w.signed('freeze', 'carol', T0 + 1, scope='repo:pr:*')
    retained = w.pins.retain
    def interrupted(pin):
        retained(pin)
        raise OSError('crash after pin commit')
    with patch.object(w.pins, 'retain', side_effect=interrupted):
        with raises(OSError, 'crash after pin commit'):
            w.journal.append(candidate)
    with raises(ValueError, 'truncated'):
        w.other_journal().snapshot()
    wrong = copy.deepcopy(candidate)
    wrong['prev'] = digest({'wrong': 'tail'})
    with raises(ValueError, 'exactly'):
        w.journal.recover_tail(wrong)
    restored = w.journal.recover_tail(candidate)
    assert 'repo:pr:*' in restored['frozen']
    assert w.other_journal().snapshot()['head'] == restored['head']


def test_real_process_exit_after_pin_commit_preserves_the_restriction_for_recovery():
    w = World()
    candidate, _ = w.signed('freeze', 'carol', T0 + 1, scope='repo:pr:*')
    cfg = {'law': w.law, 'law_pin': digest(w.law), 'code_pin': w.kernel.code_pin,
           'genesis_pin': w.state['domain'], 'journal': str(w.path), 'pins': str(w.pins.path), 'entry': candidate}
    root = str(Path(__file__).resolve().parents[1])
    script = f"import sys;sys.path.insert(0,{root!r})\n" + """import os,json
from tcb import Kernel,Journal,SQLitePins
cfg=json.load(sys.stdin)
pins=SQLitePins(cfg['pins']);retain=pins.retain
def exit_after_commit(pin):
    retain(pin)
    os._exit(93)
pins.retain=exit_after_commit
journal=Journal(cfg['journal'],Kernel(code_pin=cfg['code_pin']),
                genesis_pin=cfg['genesis_pin'],checkpoints=pins)
journal.append(cfg['entry'])
"""
    child = subprocess.run([sys.executable, '-I', '-B', '-c', script], input=canon(cfg), capture_output=True, timeout=10)
    assert child.returncode == 93, child.stderr
    with raises(ValueError, 'truncated'):
        w.other_journal().snapshot()
    assert 'repo:pr:*' in w.journal.recover_tail(candidate)['frozen']


def test_an_unretained_append_is_never_silently_promoted():
    w = World()
    candidate, _ = w.signed('freeze', 'carol', T0 + 1, scope='repo:pr:*')
    old_pin = w.pins.load()
    with sqlite3.connect(w.path) as db:
        db.execute('INSERT INTO entries VALUES (?, ?)', (candidate['seq'], canon(candidate)))
    with raises(ValueError, 'unretained journal tail'):
        w.other_journal().snapshot()
    assert w.pins.load() == old_pin


def test_restriction_between_reservation_and_dispatch_is_rejudged_and_known_failed():
    for kind in ('revoke', 'freeze', 'flag'):
        w = World()
        gid, t, iid = intent(w)
        calls = []
        guard = w.guard(lambda *_: calls.append(1) or 'ok')
        guard.issue(iid, t + 1)
        original = w.journal.effect_gate
        @contextmanager
        def after_restriction():
            fields = {'grant': gid} if kind == 'revoke' else {'scope': 'repo:pr:*'} if kind == 'freeze' else {'intent': iid}
            w.add(kind, 'carol', w.state['last_at'] + 1, **fields)
            with original() as state:
                yield state
        with patch.object(w.journal, 'effect_gate', after_restriction):
            guard.redeem(w.state['token_of'][iid], t + 2)
        assert not calls and w.state['executed'][w.state['token_of'][iid]] == 'failed'
        assert f'reconcile:{iid}' not in w.state['obligations']


def test_a_deferred_provider_wait_never_delays_a_restriction():
    w = World()
    gid, t, iid = intent(w)
    trying, finished = threading.Event(), threading.Event()
    errors, threads, calls = [], [], []
    other = w.other_journal()
    def writer():
        try:
            trying.set()
            def build(state):
                return w.signed('revoke', 'carol', state['last_at'] + 1, state=state, grant=gid)[0]
            other.transact(build)
            finished.set()
        except BaseException as exc:
            errors.append(exc)
    def provider(*args):
        calls.append(args)
        thread = threading.Thread(target=writer)
        threads.append(thread)
        thread.start()
        assert trying.wait(5)
        def wait_for_result():
            assert finished.wait(5), 'a restriction waited for provider completion'
            return 'ok'
        return wait_for_result
    guard = w.guard(provider)
    guard.issue(iid, t + 1)
    guard.redeem(w.state['token_of'][iid], t + 2)
    threads[0].join(5)
    assert finished.is_set() and not errors and len(calls) == 1
    assert gid in w.state['revoked']


def test_dispatch_gate_orders_writes_from_a_separate_process():
    w = World()
    gid, t, iid = intent(w)
    guard = w.guard(lambda *_: 'ok')
    guard.issue(iid, t + 1)
    token = w.state['token_of'][iid]
    w.add('reservation', 'guard', t + 2, token=token)
    candidate, _ = w.signed('freeze', 'carol', t + 3, scope='repo:pr:*')
    cfg = {'law': w.law, 'law_pin': digest(w.law), 'code_pin': w.kernel.code_pin,
           'genesis_pin': w.state['domain'], 'journal': str(w.path), 'pins': str(w.pins.path), 'entry': candidate}
    root = str(Path(__file__).resolve().parents[1])
    script = f"import sys;sys.path.insert(0,{root!r})\n" + """import json
from tcb import Kernel,Journal,SQLitePins
cfg=json.load(sys.stdin)
journal=Journal(cfg['journal'],Kernel(code_pin=cfg['code_pin']),
                genesis_pin=cfg['genesis_pin'],checkpoints=SQLitePins(cfg['pins']))
print('ready',flush=True)
journal.append(cfg['entry'])
"""
    with w.journal.effect_gate() as state:
        w.kernel.judge_dispatch(state, token, 'guard', t + 2)
        child = subprocess.Popen([sys.executable, '-I', '-B', '-c', script], stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        child.stdin.write(canon(cfg));child.stdin.close();child.stdin=None
        import select
        assert select.select([child.stdout], [], [], 5)[0]
        assert child.stdout.readline() == b'ready\n'
        with raises(subprocess.TimeoutExpired, '.'):
            child.wait(timeout=0.1)
    out, err = child.communicate(timeout=10)
    assert child.returncode == 0, err
    assert 'repo:pr:*' in w.state['frozen']


def test_missing_adapter_fails_but_an_adapter_exception_stays_unknown():
    for raises_in_adapter in (False, True):
        w = World()
        gid, t, iid = intent(w)
        guard = w.guard(lambda *_: 'ok')
        if raises_in_adapter:
            def adapter(*args):
                raise NotDispatched('adapter might already have acted')
            guard.effect_port = EffectPort({'merge': adapter})
        else:
            guard.effect_port = EffectPort({'different-operation': lambda *_: 'ok'})
        guard.issue(iid, t + 1)
        guard.redeem(w.state['token_of'][iid], t + 2)
        assert w.state['executed'][w.state['token_of'][iid]] == ('unknown' if raises_in_adapter else 'failed')
        assert (f'reconcile:{iid}' in w.state['obligations']) == raises_in_adapter


def test_provider_receives_a_stable_genesis_bound_reservation_key():
    w = World()
    gid, t, iid = intent(w)
    seen = []
    guard = w.guard(lambda *_: 'ok')
    guard.effect_port = EffectPort({'merge': lambda resource, args, key: seen.append((resource, args, key)) or 'ok'})
    guard.issue(iid, t + 1)
    token = w.state['token_of'][iid]
    guard.redeem(token, t + 2)
    expected = digest({'genesis': w.state['domain'], 'reservation': w.state['reserved'][token]})
    assert seen == [('repo:pr:42', {'pr': '42', 'method': 'squash'}, expected)]
    with raises(Refused, 'OBL.NOT_OPEN'):
        guard.redeem(token, t + 4)
    assert len(seen) == 1


def test_long_health_is_incremental_restarts_and_matches_full_audit():
    from tcb import audit
    w = World()
    for i in range(1, 2001):
        w.add('heartbeat', 'sentinel', T0 + i, seen=0)
    h = w.journal.health()
    assert h['state'] == 'IN_PROGRESS', h
    worker = w.journal.auditor._worker
    pid = worker.child.pid
    frames = []
    original = worker.request
    def count(packet):
        frames.append(packet['op'])
        return original(packet)
    with patch.object(worker, 'request', side_effect=count):
        assert w.journal.health() == h
        assert frames == ['health']
        w.add('heartbeat', 'sentinel', T0 + 2001, seen=0)
        frames.clear()
        h = w.journal.health()
        assert frames == ['entry', 'health']
    assert w.journal.auditor._worker.child.pid == pid
    worker.child.kill()
    worker.child.wait()
    rebuilt = w.journal.health()
    assert rebuilt == h and w.journal.auditor._worker.child.pid != pid
    with sqlite3.connect(w.path) as db:
        rows = [parse(raw) for (raw,) in db.execute('SELECT raw FROM entries ORDER BY seq')]
    assert len(canon(rows)) > (1 << 20)
    expected = audit(w.kernel, w.acc, rows, genesis_pin=w.state['domain'], checkpoints=w.pins.load())
    assert {k: v for k, v in h.items() if k not in ('head', 'size')} == expected
    w.journal.close()


def test_slow_accountability_does_not_hold_the_admission_lock():
    w = World()
    assert w.journal.health()['state'] == 'IN_PROGRESS'
    worker = w.journal.auditor._worker
    original = worker.request
    computing, release = threading.Event(), threading.Event()
    verdicts = []
    def pause(packet):
        if packet['op'] == 'health':
            computing.set()
            if not release.wait(5):
                raise WorkerFault('test timeout')
        return original(packet)
    with patch.object(worker, 'request', side_effect=pause):
        thread = threading.Thread(target=lambda: verdicts.append(w.journal.health()))
        thread.start()
        assert computing.wait(5)
        try:
            w.add('freeze', 'carol', T0 + 1, scope='repo:pr:*')
        finally:
            release.set()
        thread.join(5)
    # the admission went through while health was computing; the verdict is about the prefix it names
    assert 'repo:pr:*' in w.state['frozen']
    assert verdicts[0]['state'] == 'FAULT' and 'advanced' in verdicts[0]['fault']
    assert w.journal.health()['head'] == w.state['head']
    w.journal.close()


def test_transport_reply_larger_than_a_statement_keeps_its_own_limit():
    # A separate fake peer tests the real framing/parser, without changing the signed-entry limit.
    peer = """import sys,struct,json
n=struct.unpack('!I',sys.stdin.buffer.read(4))[0];sys.stdin.buffer.read(n)
r=json.dumps({'ok':True,'value':'x'*1100000},sort_keys=True,separators=(',',':')).encode()
sys.stdout.buffer.write(struct.pack('!I',len(r))+r);sys.stdout.buffer.flush()
"""
    worker = StreamWorker.__new__(StreamWorker)
    worker.timeout = 5
    worker.child = subprocess.Popen([sys.executable, '-I', '-c', peer], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    import os
    os.set_blocking(worker.child.stdin.fileno(), False)
    os.set_blocking(worker.child.stdout.fileno(), False)
    try:
        assert len(worker.request({'small': 'request'})) == 1100000
    finally:
        worker.close()
    with raises(CanonError, 'at most'):
        parse(canon('x' * 1100000))


def test_genesis_and_kernel_refuse_a_different_code_pin():
    w = World(genesis=False)
    w.refuse('CODE.MISMATCH', 'genesis', 'alice', T0, ['alice', 'bob'], root=w.root,
             law=w.law, code=digest({'wrong': 'code'}))
    with raises(ValueError, 'code release'):
        Journal(w.tmp / 'different.sqlite3', Kernel(code_pin=digest({'wrong': 'code'})))


def test_first_write_must_match_an_explicit_external_genesis_pin():
    w = World(genesis=False)
    w.journal.genesis_pin = digest({'different': 'genesis'})
    w.refuse('HIST.GENESIS_PIN', 'genesis', 'alice', T0, ['alice', 'bob'], root=w.root, law=w.law)
    assert w.pins.load() == [] and w.state['size'] == 0


def copied_release(w):
    root = Path(__file__).resolve().parents[1]
    target = w.tmp / 'release'
    shutil.copytree(root / 'tcb', target / 'tcb', ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copy2(root / 'bootstrap.py', target / 'bootstrap.py')
    shutil.copytree(root / 'hybrid_kernel', target / 'hybrid_kernel', ignore=shutil.ignore_patterns('__pycache__'))
    if (root / 'adapters').is_dir():
        shutil.copytree(root / 'adapters', target / 'adapters', ignore=shutil.ignore_patterns('__pycache__'))
    return target


def test_bootstrap_rejects_tampered_code_before_importing_it():
    w = World()
    target = copied_release(w)
    marker = w.tmp / 'should-not-execute'
    source = target / 'tcb' / 'canon.py'
    source.write_text(f"from pathlib import Path; Path({str(marker)!r}).write_text('bad')\n" + source.read_text())
    result = subprocess.run([sys.executable, '-I', '-B', str(target / 'bootstrap.py'), w.kernel.code_pin, '--verify'],
                            capture_output=True, timeout=10)
    assert result.returncode != 0 and not marker.exists()


def test_bootstrap_ignores_forged_bytecode_for_verified_source():
    import py_compile
    w = World()
    target = copied_release(w)
    marker = w.tmp / 'bytecode-should-not-execute'
    evil = w.tmp / 'evil.py'
    evil.write_text(f"from pathlib import Path; Path({str(marker)!r}).write_text('bad')\nraise RuntimeError('forged bytecode')\n")
    source = target / 'tcb' / 'canon.py'
    cache = Path(importlib.util.cache_from_source(str(source)))
    cache.parent.mkdir()
    py_compile.compile(str(evil), cfile=str(cache), doraise=True)
    data = bytearray(cache.read_bytes())
    data[4:16] = struct.pack('<III', 0, int(source.stat().st_mtime), source.stat().st_size)
    cache.write_bytes(data)
    config = w.tmp / 'config.json'
    config.write_bytes(canon({'law': w.law, 'law_pin': digest(w.law), 'genesis_pin': w.state['domain'],
                             'journal': str(w.path), 'pins': str(w.pins.path)}))
    result = subprocess.run([sys.executable, '-I', '-B', str(target / 'bootstrap.py'), w.kernel.code_pin,
                             '--health', str(config)], capture_output=True, timeout=15)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['state'] == 'IN_PROGRESS'
    assert not marker.exists()


if __name__ == '__main__':
    run(globals())
