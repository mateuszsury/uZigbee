"""HIL smoke for security APIs (install code policy + network key operations)."""

import uzigbee


ESP_ERR_INVALID_STATE = 259
ESP_ERR_INVALID_ARG = 258
ESP_ERR_NOT_FOUND = 261
ESP_ERR_NOT_SUPPORTED = 262
ALLOWED_ERRNO = {ESP_ERR_INVALID_STATE, ESP_ERR_INVALID_ARG, ESP_ERR_NOT_FOUND, ESP_ERR_NOT_SUPPORTED}


def allow_expected_error(func, *args, **kwargs):
    try:
        return {"ok": True, "value": func(*args, **kwargs), "errno": None}
    except OSError as exc:
        errno = exc.args[0] if exc.args else None
        if errno not in ALLOWED_ERRNO:
            raise
        return {"ok": False, "value": None, "errno": int(errno)}


z = uzigbee.ZigbeeStack()
z.init(uzigbee.ROLE_COORDINATOR)

switch = uzigbee.Switch(
    endpoint_id=1,
    stack=z,
    manufacturer="uzigbee",
    model="uzb_security_switch_01",
    sw_build_id="step44",
)

try:
    switch.provision(register=True)
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise

try:
    z.start(form_network=False)
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise

key_a = b"\x00\x11\x22\x33\x44\x55\x66\x77\x88\x99\xaa\xbb\xcc\xdd\xee\xff"
key_b = b"\x10\x21\x32\x43\x54\x65\x76\x87\x98\xa9\xba\xcb\xdc\xed\xfe\x0f"
dummy_ieee = b"\xaa\xbb\xcc\xdd\xee\xff\x00\x11"
dummy_ic = "83FED3407A939723A5C639B26916D5054195"

z.set_install_code_policy(True)
install_policy = z.get_install_code_policy()

set_net_sec = allow_expected_error(z.set_network_security_enabled, True)
net_sec_enabled = allow_expected_error(z.is_network_security_enabled)
set_key = allow_expected_error(z.set_network_key, key_a)
get_key = allow_expected_error(z.get_primary_network_key)
switch_key = allow_expected_error(z.switch_network_key, key_b, 1)
broadcast_key = allow_expected_error(z.broadcast_network_key, key_b, 2)
broadcast_switch = allow_expected_error(z.broadcast_network_key_switch, 2)
add_ic = allow_expected_error(z.add_install_code, dummy_ieee, dummy_ic)
remove_ic = allow_expected_error(z.remove_install_code, dummy_ieee)
remove_all_ic = allow_expected_error(z.remove_all_install_codes)

stats = z.event_stats()
print("uzigbee.hil.security.install_code_policy", install_policy)
print("uzigbee.hil.security.set_net_sec", set_net_sec)
print("uzigbee.hil.security.net_sec_enabled", net_sec_enabled)
print("uzigbee.hil.security.set_key", set_key)
print("uzigbee.hil.security.get_key", get_key)
print("uzigbee.hil.security.switch_key", switch_key)
print("uzigbee.hil.security.broadcast_key", broadcast_key)
print("uzigbee.hil.security.broadcast_switch", broadcast_switch)
print("uzigbee.hil.security.add_ic", add_ic)
print("uzigbee.hil.security.remove_ic", remove_ic)
print("uzigbee.hil.security.remove_all_ic", remove_all_ic)
print("uzigbee.hil.security.stats", stats)
assert install_policy is True
assert stats["dropped_queue_full"] == 0
assert stats["dropped_schedule_fail"] == 0
print("uzigbee.hil.security.result PASS")
