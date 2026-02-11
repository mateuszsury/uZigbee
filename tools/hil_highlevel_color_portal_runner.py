"""HIL runner: coordinator color web portal + router neopixel (pin8) via high-level API."""

import argparse
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen


def _tail(path, max_chars=16000):
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text) <= max_chars:
        return text
    return text[-max_chars:]


def _print_safe(text):
    try:
        print(text)
    except UnicodeEncodeError:
        enc = getattr(sys.stdout, "encoding", None) or "utf-8"
        safe = str(text).encode(enc, "replace").decode(enc, "replace")
        print(safe)


def _start_launcher(py, cwd, port, script, out_path, err_path):
    return subprocess.Popen(
        [
            str(py),
            "tools/run_web_demo_serial.py",
            "--port",
            str(port),
            "--script",
            str(script),
            "--reset",
        ],
        cwd=str(cwd),
        stdout=open(out_path, "w", encoding="utf-8"),
        stderr=open(err_path, "w", encoding="utf-8"),
    )


def _erase_runtime_state(py, port):
    # Keep firmware intact; clear only Zigbee/Wi-Fi runtime partitions for deterministic join.
    regions = (
        ("0x9000", "0x6000"),   # nvs
        ("0x3FB000", "0x4000"), # zb_storage
        ("0x3FF000", "0x1000"), # zb_fct
    )
    for offset, size in regions:
        cmd = [
            str(py),
            "-m",
            "esptool",
            "--chip",
            "esp32c6",
            "--port",
            str(port),
            "--baud",
            "460800",
            "erase_region",
            str(offset),
            str(size),
        ]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        if proc.returncode != 0:
            print("runner: erase_region failed port=%s offset=%s rc=%d" % (port, offset, int(proc.returncode)))
            _print_safe(proc.stdout[-1200:])
            return False
    subprocess.run(
        [
            str(py),
            "-m",
            "esptool",
            "--chip",
            "esp32c6",
            "--port",
            str(port),
            "run",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    return True


def _http_get(url, timeout=5):
    with urlopen(url, timeout=timeout) as res:
        payload = res.read()
    try:
        return payload.decode("utf-8", "replace")
    except Exception:
        return repr(payload)


def _extract_ip(coord_text):
    marker = "web server started http://"
    idx = coord_text.rfind(marker)
    if idx < 0:
        return None
    frag = coord_text[idx + len(marker):]
    token = frag.split(":", 1)[0].strip()
    if token.count(".") == 3:
        return token
    return None


def main():
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(errors="replace")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(errors="replace")
        except Exception:
            pass

    parser = argparse.ArgumentParser()
    parser.add_argument("--coord-port", default="COM3")
    parser.add_argument("--router-port", default="COM6")
    parser.add_argument("--timeout-s", type=int, default=260)
    args = parser.parse_args()

    cwd = Path(__file__).resolve().parents[1]
    py = cwd / ".venv" / "Scripts" / "python.exe"
    if not py.exists():
        py = Path(sys.executable)

    coord_script = "examples/coordinator_web_portal_color_highlevel.py"
    router_script = "examples/router_neopixel_color_light_highlevel.py"
    coord_out = cwd / "tmp_hil_color_coord.out"
    coord_err = cwd / "tmp_hil_color_coord.err"
    router_out = cwd / "tmp_hil_color_router.out"
    router_err = cwd / "tmp_hil_color_router.err"
    for path in (coord_out, coord_err, router_out, router_err):
        try:
            path.unlink()
        except FileNotFoundError:
            pass

    print("runner: erase runtime state on", args.coord_port, args.router_port)
    if not _erase_runtime_state(py, args.coord_port):
        return 1
    if not _erase_runtime_state(py, args.router_port):
        return 1

    print("runner: start coordinator on", args.coord_port)
    coord_proc = _start_launcher(py, cwd, args.coord_port, coord_script, coord_out, coord_err)
    router_proc = None
    started_router = False
    router_started_at = 0.0
    router_restart_count = 0
    enable_router_restart = False
    ip = None
    t0 = time.time()

    try:
        while time.time() - t0 < float(args.timeout_s):
            time.sleep(1.0)
            coord_text = _tail(coord_out, max_chars=24000)
            router_text = _tail(router_out, max_chars=24000)
            if ip is None:
                ip = _extract_ip(coord_text)
            if (not started_router) and ("permit_join open" in coord_text):
                print("runner: coordinator ready, start router on", args.router_port)
                router_proc = _start_launcher(py, cwd, args.router_port, router_script, router_out, router_err)
                started_router = True
                router_started_at = time.time()
                router_restart_count = 0

            if started_router and ip is not None:
                base = "http://%s" % ip
                try:
                    _http_get(base + "/permit?sec=180", timeout=6)
                    for _ in range(8):
                        probe = _http_get(base + "/probe", timeout=6)
                        if "short_addr" in probe and "xy" in probe:
                            break
                        _http_get(base + "/discover", timeout=6)
                        time.sleep(1.0)

                    _http_get(base + "/on", timeout=6)
                    time.sleep(1.2)
                    _http_get(base + "/rgb?r=255&g=0&b=0&bri=0.1", timeout=6)
                    time.sleep(1.2)
                    _http_get(base + "/rgb?r=0&g=255&b=0&bri=0.1", timeout=6)
                    time.sleep(1.2)
                    _http_get(base + "/rgb?r=0&g=0&b=255&bri=0.1", timeout=6)
                    time.sleep(1.2)
                    _http_get(base + "/off", timeout=6)
                    time.sleep(1.2)
                except (URLError, TimeoutError, OSError):
                    pass

                coord_text = _tail(coord_out, max_chars=28000)
                router_text = _tail(router_out, max_chars=28000)
                has_onoff = ("cluster=0x0006 attr=0x0000" in router_text)
                has_level = ("cluster=0x0008 attr=0x0000" in router_text)
                has_x = ("cluster=0x0300 attr=0x0003" in router_text)
                has_y = ("cluster=0x0300 attr=0x0004" in router_text)
                if has_onoff and has_level and has_x and has_y:
                    print("runner: TEST_PASS")
                    _print_safe(coord_text[-2500:])
                    _print_safe(router_text[-2500:])
                    return 0

            if enable_router_restart and started_router and router_proc is not None:
                router_text_now = _tail(router_out, max_chars=32000)
                has_activity = (
                    ("cluster=0x0006 attr=0x0000" in router_text_now)
                    or ("cluster=0x0008 attr=0x0000" in router_text_now)
                    or ("cluster=0x0300 attr=0x0003" in router_text_now)
                    or ("cluster=0x0300 attr=0x0004" in router_text_now)
                )
                stale_start = (time.time() - router_started_at) > 40.0
                if (not has_activity) and stale_start and router_restart_count < 6:
                    router_restart_count += 1
                    print("runner: restart router attempt", router_restart_count)
                    router_proc.kill()
                    time.sleep(0.8)
                    router_proc = _start_launcher(py, cwd, args.router_port, router_script, router_out, router_err)
                    router_started_at = time.time()

            if "TEST_FAIL" in coord_text or "TEST_FAIL" in router_text:
                print("runner: TEST_FAIL marker in logs")
                _print_safe(_tail(coord_out, 2600))
                _print_safe(_tail(router_out, 2600))
                return 1

        print("runner: TIMEOUT")
        _print_safe(_tail(coord_out, 2600))
        _print_safe(_tail(coord_err, 2600))
        _print_safe(_tail(router_out, 2600))
        _print_safe(_tail(router_err, 2600))
        return 1
    finally:
        if router_proc is not None:
            router_proc.kill()
        coord_proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())
