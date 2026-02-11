"""Launch `mpremote run` with retry on transient startup failures.

This is used by HIL runners to avoid flaky raw-REPL attach failures
(`could not enter raw repl`) while still keeping long-running scripts attached.
"""

import argparse
import atexit
import subprocess
import signal
import sys
import time

_CHILD = None


def _kill_child():
    global _CHILD
    proc = _CHILD
    if proc is None:
        return
    try:
        if proc.poll() is None:
            proc.kill()
    except Exception:
        pass
    _CHILD = None


def _signal_handler(_signum, _frame):
    _kill_child()
    raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", required=True)
    parser.add_argument("--script", required=True)
    parser.add_argument("--retries", type=int, default=6)
    parser.add_argument("--retry-delay-s", type=float, default=1.0)
    parser.add_argument("--stable-seconds", type=float, default=6.0)
    args = parser.parse_args()

    cmd = [
        sys.executable,
        "-m",
        "mpremote",
        "connect",
        str(args.port),
        "run",
        str(args.script),
    ]

    retries = int(args.retries)
    retry_delay_s = float(args.retry_delay_s)
    stable_seconds = float(args.stable_seconds)
    attempt = 0
    atexit.register(_kill_child)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _signal_handler)
    if hasattr(signal, "SIGINT"):
        signal.signal(signal.SIGINT, _signal_handler)

    while True:
        attempt += 1
        proc = subprocess.Popen(cmd)
        global _CHILD
        _CHILD = proc
        t0 = time.time()

        while True:
            rc = proc.poll()
            if rc is not None:
                _CHILD = None
                elapsed = time.time() - t0
                if rc == 0:
                    return 0
                if elapsed < stable_seconds and attempt <= retries:
                    print(
                        "mpremote_retry attempt=%d/%d rc=%d elapsed=%.2fs"
                        % (attempt, retries, int(rc), float(elapsed)),
                        flush=True,
                    )
                    time.sleep(max(0.0, retry_delay_s))
                    break
                return int(rc)

            if (time.time() - t0) >= stable_seconds:
                # Treat as attached successfully; forward final exit code.
                rc = int(proc.wait())
                _CHILD = None
                return rc
            time.sleep(0.1)


if __name__ == "__main__":
    raise SystemExit(main())
