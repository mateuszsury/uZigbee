"""Keep the pinned IDF compatibility patch idempotent and board-preserving."""
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]

def test_vendor_board_patch_preserves_upstream_and_is_idempotent():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / 'tools').mkdir()
        shutil.copy(ROOT / 'tools/apply_vendor_overrides.sh', root / 'tools')
        shutil.copytree(ROOT / 'firmware/vendor_overrides', root / 'firmware/vendor_overrides')
        header = root / 'third_party/micropython-esp32/ports/esp32/boards/ESP32_GENERIC_C6/mpconfigboard.h'
        header.parent.mkdir(parents=True)
        original = '#define MICROPY_HW_BOARD_NAME "ESP32C6 module"\n'
        header.write_text(original)
        for _ in range(2):
            subprocess.run(['bash', str(root / 'tools/apply_vendor_overrides.sh')], check=True, capture_output=True)
        text = header.read_text()
        assert text.startswith(original)
        assert text.count('UZIGBEE_IDF53_I2C_TARGET_COMPAT') == 1
        assert '#define MICROPY_PY_MACHINE_I2C_TARGET (0)' in text
