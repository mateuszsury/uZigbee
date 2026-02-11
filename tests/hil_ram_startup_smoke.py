"""HIL smoke for RAM metrics after Zigbee stack startup."""

import gc
import time
import ubinascii
import uzigbee


ESP_ERR_INVALID_STATE = 259


def snapshot(stack, tag):
    gc.collect()
    heap = stack.heap_stats()
    out = {
        "tag": tag,
        "gc_free": gc.mem_free(),
        "gc_alloc": gc.mem_alloc(),
        "free_8bit": heap["free_8bit"],
        "min_free_8bit": heap["min_free_8bit"],
        "largest_free_8bit": heap["largest_free_8bit"],
        "free_internal": heap["free_internal"],
    }
    print("uzigbee.hil.ram.snapshot", out)
    return out


z = uzigbee.ZigbeeStack()

before_init = snapshot(z, "before_init")
z.init(uzigbee.ROLE_COORDINATOR)
after_init = snapshot(z, "after_init")

try:
    z.create_on_off_light(1)
    z.register_device()
    register_ok = True
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise
    register_ok = False

after_register = snapshot(z, "after_register")

try:
    z.start(form_network=True)
    start_ok = True
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise
    start_ok = False

time.sleep(3)
after_start = snapshot(z, "after_start_3s")
stats = z.event_stats()
ieee = z.get_ieee_addr()
short_addr = z.get_short_addr()

print("uzigbee.hil.ram.ieee", ubinascii.hexlify(ieee).decode())
print("uzigbee.hil.ram.short_addr", hex(short_addr))
print("uzigbee.hil.ram.stats", stats)
print("uzigbee.hil.ram.delta.gc_free", before_init["gc_free"] - after_start["gc_free"])
print("uzigbee.hil.ram.delta.free_8bit", before_init["free_8bit"] - after_start["free_8bit"])

assert isinstance(ieee, (bytes, bytearray)) and len(ieee) == 8
assert isinstance(short_addr, int)
assert register_ok, "register_device hit invalid state, run after hard reset"
assert start_ok, "start hit invalid state, run after hard reset"
assert stats["dropped_queue_full"] == 0
assert stats["dropped_schedule_fail"] == 0
assert after_start["free_8bit"] > 0
assert after_start["largest_free_8bit"] > 0
print("uzigbee.hil.ram.result PASS")
