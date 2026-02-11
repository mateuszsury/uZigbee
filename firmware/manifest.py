# uzigbee frozen manifest
# Usage: set FROZEN_MANIFEST=/path/to/firmware/manifest.py

# Keep standard ESP32 frozen boot helpers (_boot.py, inisetup, flashbdev, etc.)
# so VFS initialization and first-boot setup behave like upstream MicroPython.
include("$(PORT_DIR)/boards/manifest.py")

freeze("../python", "uzigbee")
