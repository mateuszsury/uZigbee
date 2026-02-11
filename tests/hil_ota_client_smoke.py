"""HIL smoke for OTA client control helpers."""

import uzigbee


ESP_ERR_INVALID_STATE = 259
ESP_ERR_INVALID_ARG = 258
ESP_ERR_NOT_FOUND = 261
ESP_ERR_NOT_SUPPORTED = 262
ESP_FAIL = -1
ALLOWED_ERRNO = {ESP_ERR_INVALID_STATE, ESP_ERR_INVALID_ARG, ESP_ERR_NOT_FOUND, ESP_ERR_NOT_SUPPORTED, ESP_FAIL}


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

light = uzigbee.Light(
    endpoint_id=1,
    stack=z,
    manufacturer="uzigbee",
    model="uzb_ota_client_01",
    sw_build_id="step46",
)

try:
    light.provision(register=True)
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise

try:
    z.start(form_network=False)
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise

set_interval = allow_expected_error(z.ota_client_query_interval_set, endpoint_id=1, interval_min=5)
query_image = allow_expected_error(z.ota_client_query_image_req, server_ep=1, server_addr=0x00)
stop_query = allow_expected_error(z.ota_client_query_image_stop)
stats = z.event_stats()

print("uzigbee.hil.ota.set_interval", set_interval)
print("uzigbee.hil.ota.query_image", query_image)
print("uzigbee.hil.ota.stop_query", stop_query)
print("uzigbee.hil.ota.stats", stats)
assert stats["dropped_queue_full"] == 0
assert stats["dropped_schedule_fail"] == 0
print("uzigbee.hil.ota.result PASS")
