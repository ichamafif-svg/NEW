"""Linux pure-compute worker: no filesystem open, network, exec or process access.

Bootstrap verifies the code pin and completes imports before lock_down(). Only three data descriptors remain.
Unsupported seccomp is an error; there is no unrestricted fallback.
"""
from __future__ import annotations

import ctypes
import ctypes.util
import errno
import os
import resource
import subprocess
import sys
import select
import struct
import time
from pathlib import Path

from .canon import canon, parse

MAX_PACKET = 2 * 1024 * 1024
MAX_REPLY = 8 * 1024 * 1024


class WorkerFault(RuntimeError):
    pass


def lock_down():
    if sys.platform != "linux":
        raise WorkerFault("Linux seccomp is required")
    name = ctypes.util.find_library("seccomp")
    if not name:
        raise WorkerFault("libseccomp is required")
    lib = ctypes.CDLL(name, use_errno=True)
    lib.seccomp_init.argtypes = [ctypes.c_uint32]
    lib.seccomp_init.restype = ctypes.c_void_p
    lib.seccomp_syscall_resolve_name.argtypes = [ctypes.c_char_p]
    lib.seccomp_syscall_resolve_name.restype = ctypes.c_int
    lib.seccomp_rule_add.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_uint]
    lib.seccomp_load.argtypes = [ctypes.c_void_p]
    lib.seccomp_release.argtypes = [ctypes.c_void_p]
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_AS, (768 * 1024 * 1024,) * 2)
    resource.setrlimit(resource.RLIMIT_CPU, (120, 120))
    resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_REPLY,) * 2)
    ctx = lib.seccomp_init(0x00050000 | errno.EPERM)
    if not ctx:
        raise WorkerFault("cannot create seccomp policy")
    # No open/openat/socket/connect/exec/clone/ptrace/process_vm/kill/prctl/io_uring.
    allowed = ("read", "write", "readv", "writev", "close", "lseek", "fstat", "newfstatat",
               "mmap", "mprotect", "munmap", "mremap", "brk", "madvise",
               "rt_sigaction", "rt_sigprocmask", "rt_sigreturn", "sigaltstack", "futex",
               "getrandom", "clock_gettime", "gettimeofday", "time", "getpid", "gettid",
               "getuid", "geteuid", "getgid", "getegid", "sched_yield", "exit", "exit_group")
    try:
        for syscall in allowed:
            number = lib.seccomp_syscall_resolve_name(syscall.encode())
            if number >= 0 and lib.seccomp_rule_add(ctx, 0x7FFF0000, number, 0) != 0:
                raise WorkerFault("cannot define seccomp policy")
        if lib.seccomp_load(ctx) != 0:
            raise WorkerFault("cannot enforce seccomp policy")
    finally:
        lib.seccomp_release(ctx)


class StreamWorker:
    """One confined reducer, bounded canonical frames, deadline on every exchange."""
    def __init__(self, code_pin, *, timeout=30):
        self.timeout, self.size, self.head = timeout, 0, None
        script = Path(__file__).resolve().parents[1] / "bootstrap.py"
        self.child = subprocess.Popen([sys.executable, "-I", "-B", str(script), code_pin, "--worker", "health"],
                                      stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                      close_fds=True, cwd=script.parent,
                                      env={"LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"})
        os.set_blocking(self.child.stdin.fileno(), False)
        os.set_blocking(self.child.stdout.fileno(), False)

    def _ready(self, fd, deadline, *, write=False):
        left = deadline - time.monotonic()
        if left <= 0:
            raise WorkerFault("worker timed out")
        r, w, _ = select.select([] if write else [fd], [fd] if write else [], [], left)
        if not (r or w):
            raise WorkerFault("worker timed out")

    def _read(self, count, deadline):
        data = bytearray()
        fd = self.child.stdout.fileno()
        while len(data) < count:
            self._ready(fd, deadline)
            part = os.read(fd, count - len(data))
            if not part:
                raise WorkerFault("worker closed its output")
            data.extend(part)
        return bytes(data)

    def request(self, packet):
        raw = canon(packet)
        if len(raw) > MAX_PACKET:
            raise WorkerFault("worker frame exceeds its limit")
        deadline = time.monotonic() + self.timeout
        pending = memoryview(struct.pack("!I", len(raw)) + raw)
        fd = self.child.stdin.fileno()
        try:
            while pending:
                self._ready(fd, deadline, write=True)
                pending = pending[os.write(fd, pending):]
            length = struct.unpack("!I", self._read(4, deadline))[0]
            if length > MAX_REPLY:
                raise WorkerFault("worker reply exceeds its limit")
            reply = parse(self._read(length, deadline), max_bytes=MAX_REPLY)
        except (OSError, ValueError) as exc:
            raise WorkerFault("invalid worker transport: " + type(exc).__name__) from None
        if (not isinstance(reply, dict) or set(reply) != {"ok", "value"}
                or type(reply["ok"]) is not bool):
            raise WorkerFault("invalid worker reply")
        if not reply["ok"]:
            raise WorkerFault(str(reply["value"]))
        return reply["value"]

    def close(self):
        if self.child.poll() is None:
            self.child.kill()
        self.child.wait(timeout=5)
        self.child.stdin.close()
        self.child.stdout.close()
