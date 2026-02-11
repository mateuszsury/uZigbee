# Skill: uzigbee-c-module

Purpose: Implement the C bridge between MicroPython and ESP-Zigbee-SDK.

Use when:
- Editing c_module/*.c or c_module/*.h
- Implementing callbacks, event queue, ZCL/ZDO, or core APIs
- Changing thread model or locking

Core rules:
- Zigbee stack runs in its own FreeRTOS task.
- All Zigbee API calls must hold esp_zb_lock_acquire()/release().
- Do not allocate or touch MicroPython objects in the Zigbee task.
- Use a thread-safe ring buffer for events and schedule into MicroPython with mp_sched_schedule().

Implementation checklist:
1. Define the public MicroPython module API in mod_uzigbee.c
   - Use MP_DEFINE_CONST_FUN_OBJ_* and MP_REGISTER_MODULE.
2. Keep a thin wrapper layer that validates args and forwards to uzb_* helpers.
3. Event queue:
   - Static ring buffer for events.
   - Zigbee callbacks push events only.
   - MicroPython task drains queue and invokes Python callbacks.
4. Error handling:
   - Return mp_raise_OSError or ValueError with clear messages.
5. Memory:
   - Prefer static buffers and small structs.
   - Avoid large stack allocations inside callbacks.

Files to touch (planned):
- c_module/mod_uzigbee.c
- c_module/uzb_core.c/.h
- c_module/uzb_callbacks.c/.h
- c_module/uzb_event_queue.c/.h
- c_module/uzb_zcl.c
- c_module/uzb_zdo.c
- c_module/uzb_network.c
- c_module/uzb_security.c
- c_module/uzb_ota.c

Do not:
- Call Zigbee APIs from MicroPython without the lock.
- Call Python from Zigbee task directly.
- Add blocking waits in callbacks.
