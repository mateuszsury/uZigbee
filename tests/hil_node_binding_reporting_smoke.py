"""HIL smoke for node reporting+binding policy managers (Phase 4.6)."""

import sys

if "/remote/python" not in sys.path:
    sys.path.insert(0, "/remote/python")

import ubinascii
import uzigbee


ESP_ERR_INVALID_STATE = 259

stack = uzigbee.ZigbeeStack()
stack.init(uzigbee.ROLE_COORDINATOR)
try:
    stack.start(form_network=False)
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise

router = (
    uzigbee.Router(stack=stack, auto_register=False)
    .add_ias_zone(endpoint_id=5, name="zone_ias")
    .add_thermostat(endpoint_id=6, name="thermo")
)

local_ieee = stack.get_ieee_addr()
local_ieee_hex = ubinascii.hexlify(local_ieee).decode()
report_cfg = router.configure_reporting_policy("thermostat", endpoint_id=6, dst_short_addr=0x0000)
report_apply = ()
report_errno = None
try:
    report_apply = router.apply_reporting_policy(endpoint_id=6)
except OSError as exc:
    report_errno = exc.args[0] if exc.args else None
    if report_errno != ESP_ERR_INVALID_STATE:
        raise
bind_cfg = router.configure_binding_policy(
    "ias_zone",
    endpoint_id=5,
    dst_ieee_addr=local_ieee,
    dst_endpoint=1,
    req_dst_short_addr=0x0000,
    ias_enroll=True,
)
bind_apply = ()
bind_errno = None
try:
    bind_apply = router.apply_binding_policy(endpoint_id=5)
except OSError as exc:
    bind_errno = exc.args[0] if exc.args else None
    if bind_errno != ESP_ERR_INVALID_STATE:
        raise
status = router.status()
stack_stats = stack.event_stats()

print("uzigbee.hil.node.binding.local_ieee", local_ieee_hex)
print("uzigbee.hil.node.binding.report_cfg", report_cfg)
print("uzigbee.hil.node.binding.report_apply_count", len(report_apply))
print("uzigbee.hil.node.binding.report_errno", report_errno)
print("uzigbee.hil.node.binding.bind_cfg", bind_cfg)
print("uzigbee.hil.node.binding.bind_apply", bind_apply)
print("uzigbee.hil.node.binding.bind_errno", bind_errno)
print("uzigbee.hil.node.binding.status", status)
print("uzigbee.hil.node.binding.stats", stack_stats)

assert len(report_cfg) == 1
assert len(report_apply) >= 1 or report_errno == ESP_ERR_INVALID_STATE
assert len(bind_cfg) == 1
assert len(bind_apply) == 1 or bind_errno == ESP_ERR_INVALID_STATE
if bind_apply:
    assert bind_apply[0]["status"] in ("ok", "partial")
assert status["reporting_policy_count"] >= 1
assert status["binding_policy_count"] >= 1
assert stack_stats["dropped_queue_full"] == 0
assert stack_stats["dropped_schedule_fail"] == 0
print("uzigbee.hil.node.binding.result PASS")
