#include "py/obj.h"
#include "py/nlr.h"
#include "py/runtime.h"

#include <stdint.h>
#include <string.h>

#include "esp_err.h"
#include "esp_heap_caps.h"
#include "zcl/esp_zigbee_zcl_basic.h"
#include "zcl/esp_zigbee_zcl_color_control.h"
#include "zcl/esp_zigbee_zcl_common.h"
#include "zcl/esp_zigbee_zcl_level.h"
#include "zcl/esp_zigbee_zcl_on_off.h"
#include "zcl/esp_zigbee_zcl_electrical_meas.h"
#include "zcl/esp_zigbee_zcl_groups.h"
#include "zcl/esp_zigbee_zcl_scenes.h"
#include "zcl/esp_zigbee_zcl_humidity_meas.h"
#include "zcl/esp_zigbee_zcl_pressure_meas.h"
#include "zcl/esp_zigbee_zcl_temperature_meas.h"
#include "zcl/esp_zigbee_zcl_thermostat.h"
#include "zcl/esp_zigbee_zcl_door_lock.h"
#include "zcl/esp_zigbee_zcl_occupancy_sensing.h"
#include "zcl/esp_zigbee_zcl_ias_zone.h"
#include "zcl/esp_zigbee_zcl_window_covering.h"
#include "zdo/esp_zigbee_zdo_common.h"
#include "esp_zigbee_secur.h"

#include "uzb_core.h"

MP_REGISTER_ROOT_POINTER(mp_obj_t uzigbee_signal_callback);
MP_REGISTER_ROOT_POINTER(mp_obj_t uzigbee_attr_callback);

static mp_obj_t uzigbee_dispatch_events(mp_obj_t unused);
static MP_DEFINE_CONST_FUN_OBJ_1(uzigbee_dispatch_events_obj, uzigbee_dispatch_events);

static mp_obj_t uzigbee_get_signal_callback(void) {
    mp_obj_t cb = MP_STATE_PORT(uzigbee_signal_callback);
    if (cb == MP_OBJ_NULL) {
        return mp_const_none;
    }
    return cb;
}

static mp_obj_t uzigbee_get_attr_callback(void) {
    mp_obj_t cb = MP_STATE_PORT(uzigbee_attr_callback);
    if (cb == MP_OBJ_NULL) {
        return mp_const_none;
    }
    return cb;
}

static bool uzigbee_is_type_error_exception(mp_obj_t exc) {
    if (!mp_obj_is_exception_instance(exc)) {
        return false;
    }
    return mp_obj_is_subclass_fast(
        MP_OBJ_FROM_PTR(mp_obj_get_type(exc)),
        MP_OBJ_FROM_PTR(&mp_type_TypeError));
}

static bool uzigbee_call_callback(mp_obj_t callback, size_t n_args, const mp_obj_t *args, mp_obj_t *out_exception) {
    nlr_buf_t nlr;
    if (nlr_push(&nlr) == 0) {
        mp_call_function_n_kw(callback, n_args, 0, args);
        nlr_pop();
        return true;
    }
    if (out_exception != NULL) {
        *out_exception = MP_OBJ_FROM_PTR(nlr.ret_val);
    }
    return false;
}

static mp_obj_t uzigbee_attr_value_to_obj(const uzb_attr_value_t *value) {
    if (value == NULL) {
        return mp_const_none;
    }

    switch (value->zcl_type) {
        case ESP_ZB_ZCL_ATTR_TYPE_BOOL:
            return mp_obj_new_bool(value->bool_value);
        case ESP_ZB_ZCL_ATTR_TYPE_U8:
        case ESP_ZB_ZCL_ATTR_TYPE_8BITMAP:
        case ESP_ZB_ZCL_ATTR_TYPE_8BIT_ENUM:
        case ESP_ZB_ZCL_ATTR_TYPE_U16:
        case ESP_ZB_ZCL_ATTR_TYPE_16BITMAP:
        case ESP_ZB_ZCL_ATTR_TYPE_16BIT_ENUM:
        case ESP_ZB_ZCL_ATTR_TYPE_CLUSTER_ID:
        case ESP_ZB_ZCL_ATTR_TYPE_ATTRIBUTE_ID:
        case ESP_ZB_ZCL_ATTR_TYPE_U32:
        case ESP_ZB_ZCL_ATTR_TYPE_32BITMAP:
        case ESP_ZB_ZCL_ATTR_TYPE_UTC_TIME:
        case ESP_ZB_ZCL_ATTR_TYPE_BACNET_OID:
            return mp_obj_new_int_from_uint(value->uint_value);
        case ESP_ZB_ZCL_ATTR_TYPE_S8:
        case ESP_ZB_ZCL_ATTR_TYPE_S16:
        case ESP_ZB_ZCL_ATTR_TYPE_S32:
            return mp_obj_new_int(value->int_value);
        default:
            return mp_const_none;
    }
}

static bool uzigbee_request_dispatch(void) {
    return mp_sched_schedule(MP_OBJ_FROM_PTR(&uzigbee_dispatch_events_obj), mp_const_none);
}

static void uzigbee_obj_to_pascal_string(mp_obj_t in_obj, uint8_t *out, size_t out_size) {
    if (out == NULL || out_size < 2) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid string buffer"));
    }

    size_t len = 0;
    const char *data = mp_obj_str_get_data(in_obj, &len);
    if (len > (out_size - 1)) {
        mp_raise_ValueError(MP_ERROR_TEXT("string too long"));
    }

    out[0] = (uint8_t)len;
    if (len > 0) {
        memcpy(out + 1, data, len);
    }
    if (len < (out_size - 1)) {
        out[len + 1] = 0;
    }
}

static mp_obj_t uzigbee_pascal_to_obj(const uint8_t *in, uint8_t max_len) {
    if (in == NULL) {
        return mp_const_none;
    }
    uint8_t len = in[0];
    if (len == 0) {
        return mp_const_none;
    }
    if (len > max_len) {
        return mp_const_none;
    }
    return mp_obj_new_str((const char *)(in + 1), len);
}

static void uzigbee_obj_to_ieee_addr(mp_obj_t in_obj, uint8_t out_ieee_addr[8]) {
    if (out_ieee_addr == NULL) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid ieee buffer"));
    }
    mp_buffer_info_t buf_info = {0};
    mp_get_buffer_raise(in_obj, &buf_info, MP_BUFFER_READ);
    if (buf_info.len != 8) {
        mp_raise_ValueError(MP_ERROR_TEXT("ieee address must be 8 bytes"));
    }
    memcpy(out_ieee_addr, buf_info.buf, 8);
}

static void uzigbee_obj_to_key16(mp_obj_t in_obj, uint8_t out_key[16]) {
    if (out_key == NULL) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid key buffer"));
    }
    mp_buffer_info_t buf_info = {0};
    mp_get_buffer_raise(in_obj, &buf_info, MP_BUFFER_READ);
    if (buf_info.len != 16) {
        mp_raise_ValueError(MP_ERROR_TEXT("key must be 16 bytes"));
    }
    memcpy(out_key, buf_info.buf, 16);
}

static void uzigbee_obj_to_optional_payload(mp_obj_t in_obj, const uint8_t **out_payload, uint16_t *out_len) {
    if (out_payload == NULL || out_len == NULL) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid payload buffer"));
    }
    if (in_obj == mp_const_none || in_obj == MP_OBJ_NULL) {
        *out_payload = NULL;
        *out_len = 0;
        return;
    }

    mp_buffer_info_t buf_info = {0};
    mp_get_buffer_raise(in_obj, &buf_info, MP_BUFFER_READ);
    if (buf_info.len > 0xFFFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("payload too long"));
    }

    *out_payload = (const uint8_t *)buf_info.buf;
    *out_len = (uint16_t)buf_info.len;
}

static mp_obj_t uzigbee_init(mp_obj_t role_in) {
    mp_int_t role = mp_obj_get_int(role_in);
    if (role < 0 || role > 2) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid role"));
    }
    uzb_core_set_dispatch_request_cb(uzigbee_request_dispatch);
    esp_err_t err = uzb_core_init((uzb_role_t)role);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(uzigbee_init_obj, uzigbee_init);

static mp_obj_t uzigbee_start(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_form_network };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_form_network, MP_ARG_BOOL, {.u_bool = false} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    esp_err_t err = uzb_core_start(args[ARG_form_network].u_bool);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_start_obj, 0, uzigbee_start);

static mp_obj_t uzigbee_create_endpoint(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_endpoint, ARG_device_id, ARG_profile_id };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_endpoint, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
        { MP_QSTR_device_id, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
        { MP_QSTR_profile_id, MP_ARG_INT, {.u_int = 0x0104} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t endpoint = args[ARG_endpoint].u_int;
    mp_int_t device_id = args[ARG_device_id].u_int;
    mp_int_t profile_id = args[ARG_profile_id].u_int;
    if (endpoint <= 0 || endpoint >= 0xF0) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid endpoint"));
    }
    if (device_id < 0 || device_id > 0xFFFF || profile_id <= 0 || profile_id > 0xFFFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid endpoint config"));
    }

    esp_err_t err = uzb_core_create_endpoint((uint8_t)endpoint, (uint16_t)device_id, (uint16_t)profile_id);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_create_endpoint_obj, 0, uzigbee_create_endpoint);

static mp_obj_t uzigbee_register_device(void) {
    esp_err_t err = uzb_core_register_device();
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_0(uzigbee_register_device_obj, uzigbee_register_device);

static mp_obj_t uzigbee_create_on_off_light(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_endpoint };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_endpoint, MP_ARG_INT, {.u_int = 1} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t endpoint = args[ARG_endpoint].u_int;
    if (endpoint <= 0 || endpoint >= 0xF0) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid endpoint"));
    }

    esp_err_t err = uzb_core_create_on_off_light_endpoint((uint8_t)endpoint);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_create_on_off_light_obj, 0, uzigbee_create_on_off_light);

static mp_obj_t uzigbee_create_on_off_switch(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_endpoint };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_endpoint, MP_ARG_INT, {.u_int = 1} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t endpoint = args[ARG_endpoint].u_int;
    if (endpoint <= 0 || endpoint >= 0xF0) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid endpoint"));
    }

    esp_err_t err = uzb_core_create_on_off_switch_endpoint((uint8_t)endpoint);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_create_on_off_switch_obj, 0, uzigbee_create_on_off_switch);

static mp_obj_t uzigbee_create_dimmable_switch(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_endpoint };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_endpoint, MP_ARG_INT, {.u_int = 1} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t endpoint = args[ARG_endpoint].u_int;
    if (endpoint <= 0 || endpoint >= 0xF0) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid endpoint"));
    }

    esp_err_t err = uzb_core_create_dimmable_switch_endpoint((uint8_t)endpoint);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_create_dimmable_switch_obj, 0, uzigbee_create_dimmable_switch);

static mp_obj_t uzigbee_create_dimmable_light(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_endpoint };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_endpoint, MP_ARG_INT, {.u_int = 1} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t endpoint = args[ARG_endpoint].u_int;
    if (endpoint <= 0 || endpoint >= 0xF0) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid endpoint"));
    }

    esp_err_t err = uzb_core_create_dimmable_light_endpoint((uint8_t)endpoint);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_create_dimmable_light_obj, 0, uzigbee_create_dimmable_light);

static mp_obj_t uzigbee_create_color_light(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_endpoint };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_endpoint, MP_ARG_INT, {.u_int = 1} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t endpoint = args[ARG_endpoint].u_int;
    if (endpoint <= 0 || endpoint >= 0xF0) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid endpoint"));
    }

    esp_err_t err = uzb_core_create_color_light_endpoint((uint8_t)endpoint);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_create_color_light_obj, 0, uzigbee_create_color_light);

static mp_obj_t uzigbee_create_temperature_sensor(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_endpoint };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_endpoint, MP_ARG_INT, {.u_int = 1} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t endpoint = args[ARG_endpoint].u_int;
    if (endpoint <= 0 || endpoint >= 0xF0) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid endpoint"));
    }

    esp_err_t err = uzb_core_create_temperature_sensor_endpoint((uint8_t)endpoint);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_create_temperature_sensor_obj, 0, uzigbee_create_temperature_sensor);

static mp_obj_t uzigbee_create_humidity_sensor(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_endpoint };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_endpoint, MP_ARG_INT, {.u_int = 1} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t endpoint = args[ARG_endpoint].u_int;
    if (endpoint <= 0 || endpoint >= 0xF0) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid endpoint"));
    }

    esp_err_t err = uzb_core_create_humidity_sensor_endpoint((uint8_t)endpoint);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_create_humidity_sensor_obj, 0, uzigbee_create_humidity_sensor);

static mp_obj_t uzigbee_create_pressure_sensor(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_endpoint };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_endpoint, MP_ARG_INT, {.u_int = 1} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t endpoint = args[ARG_endpoint].u_int;
    if (endpoint <= 0 || endpoint >= 0xF0) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid endpoint"));
    }

    esp_err_t err = uzb_core_create_pressure_sensor_endpoint((uint8_t)endpoint);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_create_pressure_sensor_obj, 0, uzigbee_create_pressure_sensor);

static mp_obj_t uzigbee_create_climate_sensor(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_endpoint };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_endpoint, MP_ARG_INT, {.u_int = 1} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t endpoint = args[ARG_endpoint].u_int;
    if (endpoint <= 0 || endpoint >= 0xF0) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid endpoint"));
    }

    esp_err_t err = uzb_core_create_climate_sensor_endpoint((uint8_t)endpoint);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_create_climate_sensor_obj, 0, uzigbee_create_climate_sensor);

static mp_obj_t uzigbee_create_power_outlet(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_endpoint, ARG_with_metering };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_endpoint, MP_ARG_INT, {.u_int = 1} },
        { MP_QSTR_with_metering, MP_ARG_BOOL, {.u_bool = false} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t endpoint = args[ARG_endpoint].u_int;
    if (endpoint <= 0 || endpoint >= 0xF0) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid endpoint"));
    }

    esp_err_t err = uzb_core_create_power_outlet_endpoint((uint8_t)endpoint, args[ARG_with_metering].u_bool);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_create_power_outlet_obj, 0, uzigbee_create_power_outlet);

static mp_obj_t uzigbee_create_door_lock(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_endpoint };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_endpoint, MP_ARG_INT, {.u_int = 1} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t endpoint = args[ARG_endpoint].u_int;
    if (endpoint <= 0 || endpoint >= 0xF0) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid endpoint"));
    }

    esp_err_t err = uzb_core_create_door_lock_endpoint((uint8_t)endpoint);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_create_door_lock_obj, 0, uzigbee_create_door_lock);

static mp_obj_t uzigbee_create_door_lock_controller(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_endpoint };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_endpoint, MP_ARG_INT, {.u_int = 1} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t endpoint = args[ARG_endpoint].u_int;
    if (endpoint <= 0 || endpoint >= 0xF0) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid endpoint"));
    }

    esp_err_t err = uzb_core_create_door_lock_controller_endpoint((uint8_t)endpoint);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_create_door_lock_controller_obj, 0, uzigbee_create_door_lock_controller);

static mp_obj_t uzigbee_create_thermostat(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_endpoint };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_endpoint, MP_ARG_INT, {.u_int = 1} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t endpoint = args[ARG_endpoint].u_int;
    if (endpoint <= 0 || endpoint >= 0xF0) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid endpoint"));
    }

    esp_err_t err = uzb_core_create_thermostat_endpoint((uint8_t)endpoint);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_create_thermostat_obj, 0, uzigbee_create_thermostat);

static mp_obj_t uzigbee_create_occupancy_sensor(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_endpoint };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_endpoint, MP_ARG_INT, {.u_int = 1} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t endpoint = args[ARG_endpoint].u_int;
    if (endpoint <= 0 || endpoint >= 0xF0) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid endpoint"));
    }

    esp_err_t err = uzb_core_create_occupancy_sensor_endpoint((uint8_t)endpoint);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_create_occupancy_sensor_obj, 0, uzigbee_create_occupancy_sensor);

static mp_obj_t uzigbee_create_window_covering(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_endpoint };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_endpoint, MP_ARG_INT, {.u_int = 1} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t endpoint = args[ARG_endpoint].u_int;
    if (endpoint <= 0 || endpoint >= 0xF0) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid endpoint"));
    }

    esp_err_t err = uzb_core_create_window_covering_endpoint((uint8_t)endpoint);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_create_window_covering_obj, 0, uzigbee_create_window_covering);

static mp_obj_t uzigbee_create_ias_zone(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_endpoint, ARG_zone_type };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_endpoint, MP_ARG_INT, {.u_int = 1} },
        { MP_QSTR_zone_type, MP_ARG_INT, {.u_int = ESP_ZB_ZCL_IAS_ZONE_ZONETYPE_CONTACT_SWITCH} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t endpoint = args[ARG_endpoint].u_int;
    mp_int_t zone_type = args[ARG_zone_type].u_int;
    if (endpoint <= 0 || endpoint >= 0xF0) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid endpoint"));
    }
    if (zone_type < 0 || zone_type > 0xFFFE) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid zone_type"));
    }

    esp_err_t err = uzb_core_create_ias_zone_endpoint((uint8_t)endpoint, (uint16_t)zone_type);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_create_ias_zone_obj, 0, uzigbee_create_ias_zone);

static mp_obj_t uzigbee_create_contact_sensor(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_endpoint };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_endpoint, MP_ARG_INT, {.u_int = 1} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t endpoint = args[ARG_endpoint].u_int;
    if (endpoint <= 0 || endpoint >= 0xF0) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid endpoint"));
    }

    esp_err_t err = uzb_core_create_contact_sensor_endpoint((uint8_t)endpoint);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_create_contact_sensor_obj, 0, uzigbee_create_contact_sensor);

static mp_obj_t uzigbee_create_motion_sensor(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_endpoint };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_endpoint, MP_ARG_INT, {.u_int = 1} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t endpoint = args[ARG_endpoint].u_int;
    if (endpoint <= 0 || endpoint >= 0xF0) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid endpoint"));
    }

    esp_err_t err = uzb_core_create_motion_sensor_endpoint((uint8_t)endpoint);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_create_motion_sensor_obj, 0, uzigbee_create_motion_sensor);

static mp_obj_t uzigbee_clear_custom_clusters(void) {
    esp_err_t err = uzb_core_clear_custom_clusters();
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_0(uzigbee_clear_custom_clusters_obj, uzigbee_clear_custom_clusters);

static mp_obj_t uzigbee_add_custom_cluster(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_cluster_id, ARG_cluster_role };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_cluster_id, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
        { MP_QSTR_cluster_role, MP_ARG_INT, {.u_int = ESP_ZB_ZCL_CLUSTER_SERVER_ROLE} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t cluster_id = args[ARG_cluster_id].u_int;
    mp_int_t cluster_role = args[ARG_cluster_role].u_int;
    if (cluster_id < 0xFC00 || cluster_id > 0xFFFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid custom cluster_id"));
    }
    if (cluster_role != ESP_ZB_ZCL_CLUSTER_SERVER_ROLE && cluster_role != ESP_ZB_ZCL_CLUSTER_CLIENT_ROLE) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid cluster_role"));
    }

    esp_err_t err = uzb_core_add_custom_cluster((uint16_t)cluster_id, (uint8_t)cluster_role);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_add_custom_cluster_obj, 0, uzigbee_add_custom_cluster);

static mp_obj_t uzigbee_add_custom_attr(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_cluster_id, ARG_attr_id, ARG_attr_type, ARG_attr_access, ARG_initial_value };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_cluster_id, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
        { MP_QSTR_attr_id, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
        { MP_QSTR_attr_type, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
        { MP_QSTR_attr_access, MP_ARG_INT, {.u_int = ESP_ZB_ZCL_ATTR_ACCESS_READ_WRITE} },
        { MP_QSTR_initial_value, MP_ARG_INT, {.u_int = 0} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t cluster_id = args[ARG_cluster_id].u_int;
    mp_int_t attr_id = args[ARG_attr_id].u_int;
    mp_int_t attr_type = args[ARG_attr_type].u_int;
    mp_int_t attr_access = args[ARG_attr_access].u_int;
    mp_int_t initial_value = args[ARG_initial_value].u_int;
    if (cluster_id < 0xFC00 || cluster_id > 0xFFFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid custom cluster_id"));
    }
    if (attr_id < 0 || attr_id > 0xFFFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid attr_id"));
    }
    if (attr_type < 0 || attr_type > 0xFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid attr_type"));
    }
    if (attr_access <= 0 || attr_access > 0xFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid attr_access"));
    }
    if (initial_value < INT32_MIN || initial_value > INT32_MAX) {
        mp_raise_ValueError(MP_ERROR_TEXT("initial_value out of range"));
    }

    esp_err_t err = uzb_core_add_custom_attr(
        (uint16_t)cluster_id,
        (uint16_t)attr_id,
        (uint8_t)attr_type,
        (uint8_t)attr_access,
        (int32_t)initial_value);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_add_custom_attr_obj, 0, uzigbee_add_custom_attr);

static mp_obj_t uzigbee_set_basic_identity(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_endpoint, ARG_manufacturer, ARG_model, ARG_date_code, ARG_sw_build_id, ARG_power_source };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_endpoint, MP_ARG_INT, {.u_int = 1} },
        { MP_QSTR_manufacturer, MP_ARG_REQUIRED | MP_ARG_OBJ, {.u_obj = MP_OBJ_NULL} },
        { MP_QSTR_model, MP_ARG_REQUIRED | MP_ARG_OBJ, {.u_obj = MP_OBJ_NULL} },
        { MP_QSTR_date_code, MP_ARG_OBJ, {.u_obj = MP_OBJ_NULL} },
        { MP_QSTR_sw_build_id, MP_ARG_OBJ, {.u_obj = MP_OBJ_NULL} },
        { MP_QSTR_power_source, MP_ARG_INT, {.u_int = ESP_ZB_ZCL_BASIC_POWER_SOURCE_MAINS_SINGLE_PHASE} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t endpoint = args[ARG_endpoint].u_int;
    if (endpoint <= 0 || endpoint >= 0xF0) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid endpoint"));
    }

    uzb_basic_identity_cfg_t cfg = {0};
    cfg.has_manufacturer = 1;
    cfg.has_model = 1;
    uzigbee_obj_to_pascal_string(args[ARG_manufacturer].u_obj, cfg.manufacturer, sizeof(cfg.manufacturer));
    uzigbee_obj_to_pascal_string(args[ARG_model].u_obj, cfg.model, sizeof(cfg.model));

    if (args[ARG_date_code].u_obj != MP_OBJ_NULL && args[ARG_date_code].u_obj != mp_const_none) {
        cfg.has_date_code = 1;
        uzigbee_obj_to_pascal_string(args[ARG_date_code].u_obj, cfg.date_code, sizeof(cfg.date_code));
    }
    if (args[ARG_sw_build_id].u_obj != MP_OBJ_NULL && args[ARG_sw_build_id].u_obj != mp_const_none) {
        cfg.has_sw_build_id = 1;
        uzigbee_obj_to_pascal_string(args[ARG_sw_build_id].u_obj, cfg.sw_build_id, sizeof(cfg.sw_build_id));
    }

    mp_int_t power_source = args[ARG_power_source].u_int;
    if (power_source < 0 || power_source > ESP_ZB_ZCL_BASIC_POWER_SOURCE_EMERGENCY_MAINS_TRANSF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid power_source"));
    }
    cfg.has_power_source = 1;
    cfg.power_source = (uint8_t)power_source;

    esp_err_t err = uzb_core_set_basic_identity((uint8_t)endpoint, &cfg);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_set_basic_identity_obj, 0, uzigbee_set_basic_identity);

static mp_obj_t uzigbee_get_attribute(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_endpoint, ARG_cluster_id, ARG_attr_id, ARG_cluster_role };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_endpoint, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
        { MP_QSTR_cluster_id, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
        { MP_QSTR_attr_id, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
        { MP_QSTR_cluster_role, MP_ARG_INT, {.u_int = ESP_ZB_ZCL_CLUSTER_SERVER_ROLE} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t endpoint = args[ARG_endpoint].u_int;
    mp_int_t cluster_id = args[ARG_cluster_id].u_int;
    mp_int_t attr_id = args[ARG_attr_id].u_int;
    mp_int_t cluster_role = args[ARG_cluster_role].u_int;
    if (endpoint <= 0 || endpoint >= 0xF0 || cluster_id < 0 || cluster_id > 0xFFFF || attr_id < 0 || attr_id > 0xFFFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid attribute selector"));
    }

    uzb_attr_value_t out = {0};
    esp_err_t err = uzb_core_get_attribute((uint8_t)endpoint, (uint16_t)cluster_id, (uint8_t)cluster_role, (uint16_t)attr_id, &out);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    mp_obj_t out_obj = uzigbee_attr_value_to_obj(&out);
    if (out_obj == mp_const_none && out.zcl_type != ESP_ZB_ZCL_ATTR_TYPE_BOOL) {
        mp_raise_OSError(ESP_ERR_NOT_SUPPORTED);
    }
    return out_obj;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_get_attribute_obj, 0, uzigbee_get_attribute);

static mp_obj_t uzigbee_set_attribute(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_endpoint, ARG_cluster_id, ARG_attr_id, ARG_value, ARG_cluster_role, ARG_check };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_endpoint, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
        { MP_QSTR_cluster_id, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
        { MP_QSTR_attr_id, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
        { MP_QSTR_value, MP_ARG_REQUIRED | MP_ARG_OBJ, {.u_obj = MP_OBJ_NULL} },
        { MP_QSTR_cluster_role, MP_ARG_INT, {.u_int = ESP_ZB_ZCL_CLUSTER_SERVER_ROLE} },
        { MP_QSTR_check, MP_ARG_BOOL, {.u_bool = false} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t endpoint = args[ARG_endpoint].u_int;
    mp_int_t cluster_id = args[ARG_cluster_id].u_int;
    mp_int_t attr_id = args[ARG_attr_id].u_int;
    mp_int_t cluster_role = args[ARG_cluster_role].u_int;
    if (endpoint <= 0 || endpoint >= 0xF0 || cluster_id < 0 || cluster_id > 0xFFFF || attr_id < 0 || attr_id > 0xFFFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid attribute selector"));
    }

    uzb_attr_value_t in = {0};
    in.bool_value = mp_obj_is_true(args[ARG_value].u_obj);
    mp_int_t value_int = mp_obj_get_int(args[ARG_value].u_obj);
    in.int_value = (int32_t)value_int;
    in.uint_value = (uint32_t)value_int;

    uint8_t zcl_status = ESP_ZB_ZCL_STATUS_SUCCESS;
    esp_err_t err = uzb_core_set_attribute((uint8_t)endpoint, (uint16_t)cluster_id, (uint8_t)cluster_role, (uint16_t)attr_id, &in, args[ARG_check].u_bool, &zcl_status);
    if (err != ESP_OK) {
        if (err == ESP_FAIL) {
            mp_raise_OSError(zcl_status);
        }
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_set_attribute_obj, 0, uzigbee_set_attribute);

static mp_obj_t uzigbee_configure_reporting(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum {
        ARG_src_endpoint,
        ARG_dst_short_addr,
        ARG_dst_endpoint,
        ARG_cluster_id,
        ARG_attr_id,
        ARG_attr_type,
        ARG_min_interval,
        ARG_max_interval,
        ARG_reportable_change,
    };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_src_endpoint, MP_ARG_INT, {.u_int = 1} },
        { MP_QSTR_dst_short_addr, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
        { MP_QSTR_dst_endpoint, MP_ARG_INT, {.u_int = 1} },
        { MP_QSTR_cluster_id, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
        { MP_QSTR_attr_id, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
        { MP_QSTR_attr_type, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
        { MP_QSTR_min_interval, MP_ARG_INT, {.u_int = 0} },
        { MP_QSTR_max_interval, MP_ARG_INT, {.u_int = 300} },
        { MP_QSTR_reportable_change, MP_ARG_OBJ, {.u_obj = mp_const_none} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t src_endpoint = args[ARG_src_endpoint].u_int;
    mp_int_t dst_short_addr = args[ARG_dst_short_addr].u_int;
    mp_int_t dst_endpoint = args[ARG_dst_endpoint].u_int;
    mp_int_t cluster_id = args[ARG_cluster_id].u_int;
    mp_int_t attr_id = args[ARG_attr_id].u_int;
    mp_int_t attr_type = args[ARG_attr_type].u_int;
    mp_int_t min_interval = args[ARG_min_interval].u_int;
    mp_int_t max_interval = args[ARG_max_interval].u_int;
    if (src_endpoint <= 0 || src_endpoint >= 0xF0 || dst_endpoint <= 0 || dst_endpoint >= 0xF0) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid endpoint"));
    }
    if (dst_short_addr < 0 || dst_short_addr > 0xFFFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid dst_short_addr"));
    }
    if (cluster_id < 0 || cluster_id > 0xFFFF || attr_id < 0 || attr_id > 0xFFFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid cluster/attr"));
    }
    if (attr_type < 0 || attr_type > 0xFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid attr_type"));
    }
    if (min_interval < 0 || min_interval > 0xFFFF || max_interval < 0 || max_interval > 0xFFFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid interval"));
    }

    bool has_reportable_change = false;
    int32_t reportable_change = 0;
    if (args[ARG_reportable_change].u_obj != mp_const_none) {
        mp_int_t in_change = mp_obj_get_int(args[ARG_reportable_change].u_obj);
        if (in_change < INT32_MIN || in_change > INT32_MAX) {
            mp_raise_ValueError(MP_ERROR_TEXT("reportable_change out of range"));
        }
        has_reportable_change = true;
        reportable_change = (int32_t)in_change;
    }

    esp_err_t err = uzb_core_configure_reporting(
        (uint8_t)src_endpoint,
        (uint16_t)dst_short_addr,
        (uint8_t)dst_endpoint,
        (uint16_t)cluster_id,
        (uint16_t)attr_id,
        (uint8_t)attr_type,
        (uint16_t)min_interval,
        (uint16_t)max_interval,
        has_reportable_change,
        reportable_change);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_configure_reporting_obj, 0, uzigbee_configure_reporting);

static mp_obj_t uzigbee_send_on_off_cmd(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_src_endpoint, ARG_dst_short_addr, ARG_dst_endpoint, ARG_cmd_id };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_src_endpoint, MP_ARG_INT, {.u_int = 1} },
        { MP_QSTR_dst_short_addr, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
        { MP_QSTR_dst_endpoint, MP_ARG_INT, {.u_int = 1} },
        { MP_QSTR_cmd_id, MP_ARG_INT, {.u_int = ESP_ZB_ZCL_CMD_ON_OFF_TOGGLE_ID} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t src_endpoint = args[ARG_src_endpoint].u_int;
    mp_int_t dst_short_addr = args[ARG_dst_short_addr].u_int;
    mp_int_t dst_endpoint = args[ARG_dst_endpoint].u_int;
    mp_int_t cmd_id = args[ARG_cmd_id].u_int;
    if (src_endpoint <= 0 || src_endpoint >= 0xF0 || dst_endpoint <= 0 || dst_endpoint >= 0xF0) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid endpoint"));
    }
    if (dst_short_addr < 0 || dst_short_addr > 0xFFFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid dst_short_addr"));
    }
    if (cmd_id != ESP_ZB_ZCL_CMD_ON_OFF_OFF_ID &&
        cmd_id != ESP_ZB_ZCL_CMD_ON_OFF_ON_ID &&
        cmd_id != ESP_ZB_ZCL_CMD_ON_OFF_TOGGLE_ID) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid cmd_id"));
    }

    esp_err_t err = uzb_core_send_on_off_cmd(
        (uint8_t)src_endpoint,
        (uint16_t)dst_short_addr,
        (uint8_t)dst_endpoint,
        (uint8_t)cmd_id);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_send_on_off_cmd_obj, 0, uzigbee_send_on_off_cmd);

static mp_obj_t uzigbee_send_level_cmd(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_src_endpoint, ARG_dst_short_addr, ARG_dst_endpoint, ARG_level, ARG_transition_ds, ARG_with_onoff };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_src_endpoint, MP_ARG_INT, {.u_int = 1} },
        { MP_QSTR_dst_short_addr, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
        { MP_QSTR_dst_endpoint, MP_ARG_INT, {.u_int = 1} },
        { MP_QSTR_level, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
        { MP_QSTR_transition_ds, MP_ARG_INT, {.u_int = 0} },
        { MP_QSTR_with_onoff, MP_ARG_BOOL, {.u_bool = true} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t src_endpoint = args[ARG_src_endpoint].u_int;
    mp_int_t dst_short_addr = args[ARG_dst_short_addr].u_int;
    mp_int_t dst_endpoint = args[ARG_dst_endpoint].u_int;
    mp_int_t level = args[ARG_level].u_int;
    mp_int_t transition_ds = args[ARG_transition_ds].u_int;
    if (src_endpoint <= 0 || src_endpoint >= 0xF0 || dst_endpoint <= 0 || dst_endpoint >= 0xF0) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid endpoint"));
    }
    if (dst_short_addr < 0 || dst_short_addr > 0xFFFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid dst_short_addr"));
    }
    if (level < 0 || level > 254) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid level"));
    }
    if (transition_ds < 0 || transition_ds > 0xFFFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid transition_ds"));
    }

    esp_err_t err = uzb_core_send_level_cmd(
        (uint8_t)src_endpoint,
        (uint16_t)dst_short_addr,
        (uint8_t)dst_endpoint,
        (uint8_t)level,
        (uint16_t)transition_ds,
        args[ARG_with_onoff].u_bool);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_send_level_cmd_obj, 0, uzigbee_send_level_cmd);

static mp_obj_t uzigbee_send_color_move_to_color_cmd(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_src_endpoint, ARG_dst_short_addr, ARG_dst_endpoint, ARG_color_x, ARG_color_y, ARG_transition_ds };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_src_endpoint, MP_ARG_INT, {.u_int = 1} },
        { MP_QSTR_dst_short_addr, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
        { MP_QSTR_dst_endpoint, MP_ARG_INT, {.u_int = 1} },
        { MP_QSTR_color_x, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
        { MP_QSTR_color_y, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
        { MP_QSTR_transition_ds, MP_ARG_INT, {.u_int = 0} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t src_endpoint = args[ARG_src_endpoint].u_int;
    mp_int_t dst_short_addr = args[ARG_dst_short_addr].u_int;
    mp_int_t dst_endpoint = args[ARG_dst_endpoint].u_int;
    mp_int_t color_x = args[ARG_color_x].u_int;
    mp_int_t color_y = args[ARG_color_y].u_int;
    mp_int_t transition_ds = args[ARG_transition_ds].u_int;

    if (src_endpoint <= 0 || src_endpoint >= 0xF0 || dst_endpoint <= 0 || dst_endpoint >= 0xF0) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid endpoint"));
    }
    if (dst_short_addr < 0 || dst_short_addr > 0xFFFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid dst_short_addr"));
    }
    if (color_x < 0 || color_x > 0xFFFF || color_y < 0 || color_y > 0xFFFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid color xy"));
    }
    if (transition_ds < 0 || transition_ds > 0xFFFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid transition_ds"));
    }

    esp_err_t err = uzb_core_send_color_move_to_color_cmd(
        (uint8_t)src_endpoint,
        (uint16_t)dst_short_addr,
        (uint8_t)dst_endpoint,
        (uint16_t)color_x,
        (uint16_t)color_y,
        (uint16_t)transition_ds);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_send_color_move_to_color_cmd_obj, 0, uzigbee_send_color_move_to_color_cmd);

static mp_obj_t uzigbee_send_color_move_to_color_temperature_cmd(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_src_endpoint, ARG_dst_short_addr, ARG_dst_endpoint, ARG_color_temperature, ARG_transition_ds };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_src_endpoint, MP_ARG_INT, {.u_int = 1} },
        { MP_QSTR_dst_short_addr, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
        { MP_QSTR_dst_endpoint, MP_ARG_INT, {.u_int = 1} },
        { MP_QSTR_color_temperature, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
        { MP_QSTR_transition_ds, MP_ARG_INT, {.u_int = 0} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t src_endpoint = args[ARG_src_endpoint].u_int;
    mp_int_t dst_short_addr = args[ARG_dst_short_addr].u_int;
    mp_int_t dst_endpoint = args[ARG_dst_endpoint].u_int;
    mp_int_t color_temperature = args[ARG_color_temperature].u_int;
    mp_int_t transition_ds = args[ARG_transition_ds].u_int;

    if (src_endpoint <= 0 || src_endpoint >= 0xF0 || dst_endpoint <= 0 || dst_endpoint >= 0xF0) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid endpoint"));
    }
    if (dst_short_addr < 0 || dst_short_addr > 0xFFFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid dst_short_addr"));
    }
    if (color_temperature < 0 || color_temperature > 0xFFFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid color_temperature"));
    }
    if (transition_ds < 0 || transition_ds > 0xFFFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid transition_ds"));
    }

    esp_err_t err = uzb_core_send_color_move_to_color_temperature_cmd(
        (uint8_t)src_endpoint,
        (uint16_t)dst_short_addr,
        (uint8_t)dst_endpoint,
        (uint16_t)color_temperature,
        (uint16_t)transition_ds);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_send_color_move_to_color_temperature_cmd_obj, 0, uzigbee_send_color_move_to_color_temperature_cmd);

static mp_obj_t uzigbee_send_lock_cmd(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_src_endpoint, ARG_dst_short_addr, ARG_dst_endpoint, ARG_lock };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_src_endpoint, MP_ARG_INT, {.u_int = 1} },
        { MP_QSTR_dst_short_addr, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
        { MP_QSTR_dst_endpoint, MP_ARG_INT, {.u_int = 1} },
        { MP_QSTR_lock, MP_ARG_BOOL, {.u_bool = true} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t src_endpoint = args[ARG_src_endpoint].u_int;
    mp_int_t dst_short_addr = args[ARG_dst_short_addr].u_int;
    mp_int_t dst_endpoint = args[ARG_dst_endpoint].u_int;
    if (src_endpoint <= 0 || src_endpoint >= 0xF0 || dst_endpoint <= 0 || dst_endpoint >= 0xF0) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid endpoint"));
    }
    if (dst_short_addr < 0 || dst_short_addr > 0xFFFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid dst_short_addr"));
    }

    esp_err_t err = uzb_core_send_lock_cmd(
        (uint8_t)src_endpoint,
        (uint16_t)dst_short_addr,
        (uint8_t)dst_endpoint,
        args[ARG_lock].u_bool);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_send_lock_cmd_obj, 0, uzigbee_send_lock_cmd);

static mp_obj_t uzigbee_send_group_add_cmd(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_src_endpoint, ARG_dst_short_addr, ARG_dst_endpoint, ARG_group_id };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_src_endpoint, MP_ARG_INT, {.u_int = 1} },
        { MP_QSTR_dst_short_addr, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
        { MP_QSTR_dst_endpoint, MP_ARG_INT, {.u_int = 1} },
        { MP_QSTR_group_id, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t src_endpoint = args[ARG_src_endpoint].u_int;
    mp_int_t dst_short_addr = args[ARG_dst_short_addr].u_int;
    mp_int_t dst_endpoint = args[ARG_dst_endpoint].u_int;
    mp_int_t group_id = args[ARG_group_id].u_int;
    if (src_endpoint <= 0 || src_endpoint >= 0xF0 || dst_endpoint <= 0 || dst_endpoint >= 0xF0) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid endpoint"));
    }
    if (dst_short_addr < 0 || dst_short_addr > 0xFFFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid dst_short_addr"));
    }
    if (group_id < 0 || group_id > 0xFFFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid group_id"));
    }

    esp_err_t err = uzb_core_send_group_add_cmd(
        (uint8_t)src_endpoint,
        (uint16_t)dst_short_addr,
        (uint8_t)dst_endpoint,
        (uint16_t)group_id);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_send_group_add_cmd_obj, 0, uzigbee_send_group_add_cmd);

static mp_obj_t uzigbee_send_group_remove_cmd(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_src_endpoint, ARG_dst_short_addr, ARG_dst_endpoint, ARG_group_id };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_src_endpoint, MP_ARG_INT, {.u_int = 1} },
        { MP_QSTR_dst_short_addr, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
        { MP_QSTR_dst_endpoint, MP_ARG_INT, {.u_int = 1} },
        { MP_QSTR_group_id, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t src_endpoint = args[ARG_src_endpoint].u_int;
    mp_int_t dst_short_addr = args[ARG_dst_short_addr].u_int;
    mp_int_t dst_endpoint = args[ARG_dst_endpoint].u_int;
    mp_int_t group_id = args[ARG_group_id].u_int;
    if (src_endpoint <= 0 || src_endpoint >= 0xF0 || dst_endpoint <= 0 || dst_endpoint >= 0xF0) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid endpoint"));
    }
    if (dst_short_addr < 0 || dst_short_addr > 0xFFFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid dst_short_addr"));
    }
    if (group_id < 0 || group_id > 0xFFFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid group_id"));
    }

    esp_err_t err = uzb_core_send_group_remove_cmd(
        (uint8_t)src_endpoint,
        (uint16_t)dst_short_addr,
        (uint8_t)dst_endpoint,
        (uint16_t)group_id);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_send_group_remove_cmd_obj, 0, uzigbee_send_group_remove_cmd);

static mp_obj_t uzigbee_send_group_remove_all_cmd(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_src_endpoint, ARG_dst_short_addr, ARG_dst_endpoint };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_src_endpoint, MP_ARG_INT, {.u_int = 1} },
        { MP_QSTR_dst_short_addr, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
        { MP_QSTR_dst_endpoint, MP_ARG_INT, {.u_int = 1} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t src_endpoint = args[ARG_src_endpoint].u_int;
    mp_int_t dst_short_addr = args[ARG_dst_short_addr].u_int;
    mp_int_t dst_endpoint = args[ARG_dst_endpoint].u_int;
    if (src_endpoint <= 0 || src_endpoint >= 0xF0 || dst_endpoint <= 0 || dst_endpoint >= 0xF0) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid endpoint"));
    }
    if (dst_short_addr < 0 || dst_short_addr > 0xFFFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid dst_short_addr"));
    }

    esp_err_t err = uzb_core_send_group_remove_all_cmd(
        (uint8_t)src_endpoint,
        (uint16_t)dst_short_addr,
        (uint8_t)dst_endpoint);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_send_group_remove_all_cmd_obj, 0, uzigbee_send_group_remove_all_cmd);

static mp_obj_t uzigbee_send_scene_add_cmd(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_src_endpoint, ARG_dst_short_addr, ARG_dst_endpoint, ARG_group_id, ARG_scene_id, ARG_transition_ds };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_src_endpoint, MP_ARG_INT, {.u_int = 1} },
        { MP_QSTR_dst_short_addr, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
        { MP_QSTR_dst_endpoint, MP_ARG_INT, {.u_int = 1} },
        { MP_QSTR_group_id, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
        { MP_QSTR_scene_id, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
        { MP_QSTR_transition_ds, MP_ARG_INT, {.u_int = 0} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t src_endpoint = args[ARG_src_endpoint].u_int;
    mp_int_t dst_short_addr = args[ARG_dst_short_addr].u_int;
    mp_int_t dst_endpoint = args[ARG_dst_endpoint].u_int;
    mp_int_t group_id = args[ARG_group_id].u_int;
    mp_int_t scene_id = args[ARG_scene_id].u_int;
    mp_int_t transition_ds = args[ARG_transition_ds].u_int;
    if (src_endpoint <= 0 || src_endpoint >= 0xF0 || dst_endpoint <= 0 || dst_endpoint >= 0xF0) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid endpoint"));
    }
    if (dst_short_addr < 0 || dst_short_addr > 0xFFFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid dst_short_addr"));
    }
    if (group_id < 0 || group_id > 0xFFFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid group_id"));
    }
    if (scene_id < 0 || scene_id > 0xFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid scene_id"));
    }
    if (transition_ds < 0 || transition_ds > 0xFFFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid transition_ds"));
    }

    esp_err_t err = uzb_core_send_scene_add_cmd(
        (uint8_t)src_endpoint,
        (uint16_t)dst_short_addr,
        (uint8_t)dst_endpoint,
        (uint16_t)group_id,
        (uint8_t)scene_id,
        (uint16_t)transition_ds);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_send_scene_add_cmd_obj, 0, uzigbee_send_scene_add_cmd);

static mp_obj_t uzigbee_send_scene_remove_cmd(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_src_endpoint, ARG_dst_short_addr, ARG_dst_endpoint, ARG_group_id, ARG_scene_id };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_src_endpoint, MP_ARG_INT, {.u_int = 1} },
        { MP_QSTR_dst_short_addr, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
        { MP_QSTR_dst_endpoint, MP_ARG_INT, {.u_int = 1} },
        { MP_QSTR_group_id, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
        { MP_QSTR_scene_id, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t src_endpoint = args[ARG_src_endpoint].u_int;
    mp_int_t dst_short_addr = args[ARG_dst_short_addr].u_int;
    mp_int_t dst_endpoint = args[ARG_dst_endpoint].u_int;
    mp_int_t group_id = args[ARG_group_id].u_int;
    mp_int_t scene_id = args[ARG_scene_id].u_int;
    if (src_endpoint <= 0 || src_endpoint >= 0xF0 || dst_endpoint <= 0 || dst_endpoint >= 0xF0) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid endpoint"));
    }
    if (dst_short_addr < 0 || dst_short_addr > 0xFFFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid dst_short_addr"));
    }
    if (group_id < 0 || group_id > 0xFFFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid group_id"));
    }
    if (scene_id < 0 || scene_id > 0xFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid scene_id"));
    }

    esp_err_t err = uzb_core_send_scene_remove_cmd(
        (uint8_t)src_endpoint,
        (uint16_t)dst_short_addr,
        (uint8_t)dst_endpoint,
        (uint16_t)group_id,
        (uint8_t)scene_id);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_send_scene_remove_cmd_obj, 0, uzigbee_send_scene_remove_cmd);

static mp_obj_t uzigbee_send_scene_remove_all_cmd(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_src_endpoint, ARG_dst_short_addr, ARG_dst_endpoint, ARG_group_id };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_src_endpoint, MP_ARG_INT, {.u_int = 1} },
        { MP_QSTR_dst_short_addr, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
        { MP_QSTR_dst_endpoint, MP_ARG_INT, {.u_int = 1} },
        { MP_QSTR_group_id, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t src_endpoint = args[ARG_src_endpoint].u_int;
    mp_int_t dst_short_addr = args[ARG_dst_short_addr].u_int;
    mp_int_t dst_endpoint = args[ARG_dst_endpoint].u_int;
    mp_int_t group_id = args[ARG_group_id].u_int;
    if (src_endpoint <= 0 || src_endpoint >= 0xF0 || dst_endpoint <= 0 || dst_endpoint >= 0xF0) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid endpoint"));
    }
    if (dst_short_addr < 0 || dst_short_addr > 0xFFFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid dst_short_addr"));
    }
    if (group_id < 0 || group_id > 0xFFFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid group_id"));
    }

    esp_err_t err = uzb_core_send_scene_remove_all_cmd(
        (uint8_t)src_endpoint,
        (uint16_t)dst_short_addr,
        (uint8_t)dst_endpoint,
        (uint16_t)group_id);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_send_scene_remove_all_cmd_obj, 0, uzigbee_send_scene_remove_all_cmd);

static mp_obj_t uzigbee_send_scene_recall_cmd(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_src_endpoint, ARG_dst_short_addr, ARG_dst_endpoint, ARG_group_id, ARG_scene_id };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_src_endpoint, MP_ARG_INT, {.u_int = 1} },
        { MP_QSTR_dst_short_addr, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
        { MP_QSTR_dst_endpoint, MP_ARG_INT, {.u_int = 1} },
        { MP_QSTR_group_id, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
        { MP_QSTR_scene_id, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t src_endpoint = args[ARG_src_endpoint].u_int;
    mp_int_t dst_short_addr = args[ARG_dst_short_addr].u_int;
    mp_int_t dst_endpoint = args[ARG_dst_endpoint].u_int;
    mp_int_t group_id = args[ARG_group_id].u_int;
    mp_int_t scene_id = args[ARG_scene_id].u_int;
    if (src_endpoint <= 0 || src_endpoint >= 0xF0 || dst_endpoint <= 0 || dst_endpoint >= 0xF0) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid endpoint"));
    }
    if (dst_short_addr < 0 || dst_short_addr > 0xFFFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid dst_short_addr"));
    }
    if (group_id < 0 || group_id > 0xFFFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid group_id"));
    }
    if (scene_id < 0 || scene_id > 0xFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid scene_id"));
    }

    esp_err_t err = uzb_core_send_scene_recall_cmd(
        (uint8_t)src_endpoint,
        (uint16_t)dst_short_addr,
        (uint8_t)dst_endpoint,
        (uint16_t)group_id,
        (uint8_t)scene_id);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_send_scene_recall_cmd_obj, 0, uzigbee_send_scene_recall_cmd);

static mp_obj_t uzigbee_send_custom_cmd(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum {
        ARG_src_endpoint,
        ARG_dst_short_addr,
        ARG_dst_endpoint,
        ARG_profile_id,
        ARG_cluster_id,
        ARG_custom_cmd_id,
        ARG_direction,
        ARG_disable_default_resp,
        ARG_manuf_specific,
        ARG_manuf_code,
        ARG_data_type,
        ARG_payload,
    };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_src_endpoint, MP_ARG_INT, {.u_int = 1} },
        { MP_QSTR_dst_short_addr, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
        { MP_QSTR_dst_endpoint, MP_ARG_INT, {.u_int = 1} },
        { MP_QSTR_profile_id, MP_ARG_INT, {.u_int = ESP_ZB_AF_HA_PROFILE_ID} },
        { MP_QSTR_cluster_id, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
        { MP_QSTR_custom_cmd_id, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
        { MP_QSTR_direction, MP_ARG_INT, {.u_int = ESP_ZB_ZCL_CMD_DIRECTION_TO_SRV} },
        { MP_QSTR_disable_default_resp, MP_ARG_BOOL, {.u_bool = false} },
        { MP_QSTR_manuf_specific, MP_ARG_BOOL, {.u_bool = false} },
        { MP_QSTR_manuf_code, MP_ARG_INT, {.u_int = 0} },
        { MP_QSTR_data_type, MP_ARG_INT, {.u_int = ESP_ZB_ZCL_ATTR_TYPE_OCTET_STRING} },
        { MP_QSTR_payload, MP_ARG_OBJ, {.u_obj = mp_const_none} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t src_endpoint = args[ARG_src_endpoint].u_int;
    mp_int_t dst_short_addr = args[ARG_dst_short_addr].u_int;
    mp_int_t dst_endpoint = args[ARG_dst_endpoint].u_int;
    mp_int_t profile_id = args[ARG_profile_id].u_int;
    mp_int_t cluster_id = args[ARG_cluster_id].u_int;
    mp_int_t custom_cmd_id = args[ARG_custom_cmd_id].u_int;
    mp_int_t direction = args[ARG_direction].u_int;
    mp_int_t manuf_code = args[ARG_manuf_code].u_int;
    mp_int_t data_type = args[ARG_data_type].u_int;
    if (src_endpoint <= 0 || src_endpoint >= 0xF0 || dst_endpoint <= 0 || dst_endpoint >= 0xF0) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid endpoint"));
    }
    if (dst_short_addr < 0 || dst_short_addr > 0xFFFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid dst_short_addr"));
    }
    if (profile_id <= 0 || profile_id > 0xFFFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid profile_id"));
    }
    if (cluster_id < 0xFC00 || cluster_id > 0xFFFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid custom cluster_id"));
    }
    if (custom_cmd_id < 0 || custom_cmd_id > 0xFFFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid custom_cmd_id"));
    }
    if (direction != ESP_ZB_ZCL_CMD_DIRECTION_TO_SRV && direction != ESP_ZB_ZCL_CMD_DIRECTION_TO_CLI) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid direction"));
    }
    if (manuf_code < 0 || manuf_code > 0xFFFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid manuf_code"));
    }
    if (data_type < 0 || data_type > 0xFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid data_type"));
    }

    const uint8_t *payload = NULL;
    uint16_t payload_len = 0;
    uzigbee_obj_to_optional_payload(args[ARG_payload].u_obj, &payload, &payload_len);

    esp_err_t err = uzb_core_send_custom_cmd(
        (uint8_t)src_endpoint,
        (uint16_t)dst_short_addr,
        (uint8_t)dst_endpoint,
        (uint16_t)profile_id,
        (uint16_t)cluster_id,
        (uint16_t)custom_cmd_id,
        (uint8_t)direction,
        args[ARG_disable_default_resp].u_bool,
        args[ARG_manuf_specific].u_bool,
        (uint16_t)manuf_code,
        (uint8_t)data_type,
        payload,
        payload_len);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_send_custom_cmd_obj, 0, uzigbee_send_custom_cmd);

static mp_obj_t uzigbee_ota_client_query_interval_set(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_endpoint, ARG_interval_min };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_endpoint, MP_ARG_INT, {.u_int = 1} },
        { MP_QSTR_interval_min, MP_ARG_INT, {.u_int = 5} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t endpoint = args[ARG_endpoint].u_int;
    mp_int_t interval_min = args[ARG_interval_min].u_int;
    if (endpoint <= 0 || endpoint >= 0xF0) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid endpoint"));
    }
    if (interval_min < 0 || interval_min > 0xFFFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid interval_min"));
    }

    esp_err_t err = uzb_core_ota_client_query_interval_set((uint8_t)endpoint, (uint16_t)interval_min);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_ota_client_query_interval_set_obj, 0, uzigbee_ota_client_query_interval_set);

static mp_obj_t uzigbee_ota_client_query_image_req(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_server_ep, ARG_server_addr };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_server_ep, MP_ARG_INT, {.u_int = 1} },
        { MP_QSTR_server_addr, MP_ARG_INT, {.u_int = 0x00} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t server_ep = args[ARG_server_ep].u_int;
    mp_int_t server_addr = args[ARG_server_addr].u_int;
    if (server_ep <= 0 || server_ep >= 0xF0) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid server_ep"));
    }
    if (server_addr < 0 || server_addr > 0xFFFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid server_addr"));
    }

    esp_err_t err = uzb_core_ota_client_query_image_req((uint8_t)server_ep, (uint16_t)server_addr);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_ota_client_query_image_req_obj, 0, uzigbee_ota_client_query_image_req);

static mp_obj_t uzigbee_ota_client_query_image_stop(void) {
    esp_err_t err = uzb_core_ota_client_query_image_stop();
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_0(uzigbee_ota_client_query_image_stop_obj, uzigbee_ota_client_query_image_stop);

static mp_obj_t uzigbee_ota_client_control_supported(void) {
    return mp_obj_new_bool(uzb_core_ota_client_control_supported());
}
static MP_DEFINE_CONST_FUN_OBJ_0(uzigbee_ota_client_control_supported_obj, uzigbee_ota_client_control_supported);

static mp_obj_t uzigbee_send_bind_cmd(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_src_ieee_addr, ARG_src_endpoint, ARG_cluster_id, ARG_dst_ieee_addr, ARG_dst_endpoint, ARG_req_dst_short_addr };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_src_ieee_addr, MP_ARG_REQUIRED | MP_ARG_OBJ, {.u_obj = MP_OBJ_NULL} },
        { MP_QSTR_src_endpoint, MP_ARG_INT, {.u_int = 1} },
        { MP_QSTR_cluster_id, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
        { MP_QSTR_dst_ieee_addr, MP_ARG_REQUIRED | MP_ARG_OBJ, {.u_obj = MP_OBJ_NULL} },
        { MP_QSTR_dst_endpoint, MP_ARG_INT, {.u_int = 1} },
        { MP_QSTR_req_dst_short_addr, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t src_endpoint = args[ARG_src_endpoint].u_int;
    mp_int_t dst_endpoint = args[ARG_dst_endpoint].u_int;
    mp_int_t cluster_id = args[ARG_cluster_id].u_int;
    mp_int_t req_dst_short_addr = args[ARG_req_dst_short_addr].u_int;
    if (src_endpoint <= 0 || src_endpoint >= 0xF0 || dst_endpoint <= 0 || dst_endpoint >= 0xF0) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid endpoint"));
    }
    if (cluster_id < 0 || cluster_id > 0xFFFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid cluster_id"));
    }
    if (req_dst_short_addr < 0 || req_dst_short_addr > 0xFFFE) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid req_dst_short_addr"));
    }

    uint8_t src_ieee_addr[8] = {0};
    uint8_t dst_ieee_addr[8] = {0};
    uzigbee_obj_to_ieee_addr(args[ARG_src_ieee_addr].u_obj, src_ieee_addr);
    uzigbee_obj_to_ieee_addr(args[ARG_dst_ieee_addr].u_obj, dst_ieee_addr);

    esp_err_t err = uzb_core_send_bind_cmd(
        src_ieee_addr,
        (uint8_t)src_endpoint,
        (uint16_t)cluster_id,
        dst_ieee_addr,
        (uint8_t)dst_endpoint,
        (uint16_t)req_dst_short_addr);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_send_bind_cmd_obj, 0, uzigbee_send_bind_cmd);

static mp_obj_t uzigbee_send_unbind_cmd(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_src_ieee_addr, ARG_src_endpoint, ARG_cluster_id, ARG_dst_ieee_addr, ARG_dst_endpoint, ARG_req_dst_short_addr };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_src_ieee_addr, MP_ARG_REQUIRED | MP_ARG_OBJ, {.u_obj = MP_OBJ_NULL} },
        { MP_QSTR_src_endpoint, MP_ARG_INT, {.u_int = 1} },
        { MP_QSTR_cluster_id, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
        { MP_QSTR_dst_ieee_addr, MP_ARG_REQUIRED | MP_ARG_OBJ, {.u_obj = MP_OBJ_NULL} },
        { MP_QSTR_dst_endpoint, MP_ARG_INT, {.u_int = 1} },
        { MP_QSTR_req_dst_short_addr, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t src_endpoint = args[ARG_src_endpoint].u_int;
    mp_int_t dst_endpoint = args[ARG_dst_endpoint].u_int;
    mp_int_t cluster_id = args[ARG_cluster_id].u_int;
    mp_int_t req_dst_short_addr = args[ARG_req_dst_short_addr].u_int;
    if (src_endpoint <= 0 || src_endpoint >= 0xF0 || dst_endpoint <= 0 || dst_endpoint >= 0xF0) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid endpoint"));
    }
    if (cluster_id < 0 || cluster_id > 0xFFFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid cluster_id"));
    }
    if (req_dst_short_addr < 0 || req_dst_short_addr > 0xFFFE) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid req_dst_short_addr"));
    }

    uint8_t src_ieee_addr[8] = {0};
    uint8_t dst_ieee_addr[8] = {0};
    uzigbee_obj_to_ieee_addr(args[ARG_src_ieee_addr].u_obj, src_ieee_addr);
    uzigbee_obj_to_ieee_addr(args[ARG_dst_ieee_addr].u_obj, dst_ieee_addr);

    esp_err_t err = uzb_core_send_unbind_cmd(
        src_ieee_addr,
        (uint8_t)src_endpoint,
        (uint16_t)cluster_id,
        dst_ieee_addr,
        (uint8_t)dst_endpoint,
        (uint16_t)req_dst_short_addr);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_send_unbind_cmd_obj, 0, uzigbee_send_unbind_cmd);

static mp_obj_t uzigbee_request_binding_table(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_dst_short_addr, ARG_start_index };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_dst_short_addr, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
        { MP_QSTR_start_index, MP_ARG_INT, {.u_int = 0} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t dst_short_addr = args[ARG_dst_short_addr].u_int;
    mp_int_t start_index = args[ARG_start_index].u_int;
    if (dst_short_addr < 0 || dst_short_addr > 0xFFFE) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid dst_short_addr"));
    }
    if (start_index < 0 || start_index > 0xFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid start_index"));
    }

    esp_err_t err = uzb_core_request_binding_table((uint16_t)dst_short_addr, (uint8_t)start_index);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_request_binding_table_obj, 0, uzigbee_request_binding_table);

static mp_obj_t uzigbee_get_binding_table_snapshot(void) {
    uzb_bind_table_snapshot_t snapshot = {0};
    esp_err_t err = uzb_core_get_binding_table_snapshot(&snapshot);
    if (err == ESP_ERR_NOT_FOUND) {
        return mp_const_none;
    }
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    if (!snapshot.valid) {
        return mp_const_none;
    }

    mp_obj_t record_objs[UZB_BIND_TABLE_MAX_RECORDS];
    for (size_t i = 0; i < snapshot.record_count; ++i) {
        const uzb_bind_table_record_t *rec = &snapshot.records[i];
        mp_obj_t rec_tuple[7] = {
            mp_obj_new_bytes(rec->src_ieee_addr, 8),
            mp_obj_new_int_from_uint(rec->src_endpoint),
            mp_obj_new_int_from_uint(rec->cluster_id),
            mp_obj_new_int_from_uint(rec->dst_addr_mode),
            rec->has_dst_short_addr ? mp_obj_new_int_from_uint(rec->dst_short_addr) : mp_const_none,
            rec->has_dst_ieee_addr ? mp_obj_new_bytes(rec->dst_ieee_addr, 8) : mp_const_none,
            rec->has_dst_endpoint ? mp_obj_new_int_from_uint(rec->dst_endpoint) : mp_const_none,
        };
        record_objs[i] = mp_obj_new_tuple(7, rec_tuple);
    }

    mp_obj_t out[5] = {
        mp_obj_new_int_from_uint(snapshot.status),
        mp_obj_new_int_from_uint(snapshot.index),
        mp_obj_new_int_from_uint(snapshot.total),
        mp_obj_new_int_from_uint(snapshot.count),
        mp_obj_new_tuple(snapshot.record_count, record_objs),
    };
    return mp_obj_new_tuple(5, out);
}
static MP_DEFINE_CONST_FUN_OBJ_0(uzigbee_get_binding_table_snapshot_obj, uzigbee_get_binding_table_snapshot);

static mp_obj_t uzigbee_request_active_endpoints(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_dst_short_addr };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_dst_short_addr, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t dst_short_addr = args[ARG_dst_short_addr].u_int;
    if (dst_short_addr < 0 || dst_short_addr > 0xFFFE) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid dst_short_addr"));
    }

    esp_err_t err = uzb_core_request_active_endpoints((uint16_t)dst_short_addr);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_request_active_endpoints_obj, 0, uzigbee_request_active_endpoints);

static mp_obj_t uzigbee_get_active_endpoints_snapshot(void) {
    uzb_active_ep_snapshot_t snapshot = {0};
    esp_err_t err = uzb_core_get_active_endpoints_snapshot(&snapshot);
    if (err == ESP_ERR_NOT_FOUND) {
        return mp_const_none;
    }
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    if (!snapshot.valid) {
        return mp_const_none;
    }

    mp_obj_t ep_objs[UZB_ACTIVE_EP_MAX_ENDPOINTS];
    for (size_t i = 0; i < snapshot.count; ++i) {
        ep_objs[i] = mp_obj_new_int_from_uint(snapshot.endpoints[i]);
    }

    mp_obj_t out[3] = {
        mp_obj_new_int_from_uint(snapshot.status),
        mp_obj_new_int_from_uint(snapshot.count),
        mp_obj_new_tuple(snapshot.count, ep_objs),
    };
    return mp_obj_new_tuple(3, out);
}
static MP_DEFINE_CONST_FUN_OBJ_0(uzigbee_get_active_endpoints_snapshot_obj, uzigbee_get_active_endpoints_snapshot);

static mp_obj_t uzigbee_request_node_descriptor(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_dst_short_addr };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_dst_short_addr, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t dst_short_addr = args[ARG_dst_short_addr].u_int;
    if (dst_short_addr < 0 || dst_short_addr > 0xFFFE) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid dst_short_addr"));
    }

    esp_err_t err = uzb_core_request_node_descriptor((uint16_t)dst_short_addr);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_request_node_descriptor_obj, 0, uzigbee_request_node_descriptor);

static mp_obj_t uzigbee_get_node_descriptor_snapshot(void) {
    uzb_node_desc_snapshot_t snapshot = {0};
    esp_err_t err = uzb_core_get_node_descriptor_snapshot(&snapshot);
    if (err == ESP_ERR_NOT_FOUND) {
        return mp_const_none;
    }
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    if (!snapshot.valid) {
        return mp_const_none;
    }

    mp_obj_t desc_obj = mp_const_none;
    if (snapshot.has_desc) {
        mp_obj_t desc[8] = {
            mp_obj_new_int_from_uint(snapshot.node_desc_flags),
            mp_obj_new_int_from_uint(snapshot.mac_capability_flags),
            mp_obj_new_int_from_uint(snapshot.manufacturer_code),
            mp_obj_new_int_from_uint(snapshot.max_buf_size),
            mp_obj_new_int_from_uint(snapshot.max_incoming_transfer_size),
            mp_obj_new_int_from_uint(snapshot.server_mask),
            mp_obj_new_int_from_uint(snapshot.max_outgoing_transfer_size),
            mp_obj_new_int_from_uint(snapshot.desc_capability_field),
        };
        desc_obj = mp_obj_new_tuple(8, desc);
    }

    mp_obj_t out[3] = {
        mp_obj_new_int_from_uint(snapshot.status),
        mp_obj_new_int_from_uint(snapshot.addr),
        desc_obj,
    };
    return mp_obj_new_tuple(3, out);
}
static MP_DEFINE_CONST_FUN_OBJ_0(uzigbee_get_node_descriptor_snapshot_obj, uzigbee_get_node_descriptor_snapshot);

static mp_obj_t uzigbee_request_simple_descriptor(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_dst_short_addr, ARG_endpoint };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_dst_short_addr, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
        { MP_QSTR_endpoint, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 1} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t dst_short_addr = args[ARG_dst_short_addr].u_int;
    mp_int_t endpoint = args[ARG_endpoint].u_int;
    if (dst_short_addr < 0 || dst_short_addr > 0xFFFE) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid dst_short_addr"));
    }
    if (endpoint <= 0 || endpoint >= 0xF0) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid endpoint"));
    }

    esp_err_t err = uzb_core_request_simple_descriptor((uint16_t)dst_short_addr, (uint8_t)endpoint);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_request_simple_descriptor_obj, 0, uzigbee_request_simple_descriptor);

static mp_obj_t uzigbee_get_simple_descriptor_snapshot(void) {
    uzb_simple_desc_snapshot_t snapshot = {0};
    esp_err_t err = uzb_core_get_simple_descriptor_snapshot(&snapshot);
    if (err == ESP_ERR_NOT_FOUND) {
        return mp_const_none;
    }
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    if (!snapshot.valid) {
        return mp_const_none;
    }

    mp_obj_t desc_obj = mp_const_none;
    if (snapshot.has_desc) {
        mp_obj_t in_clusters[UZB_SIMPLE_DESC_MAX_CLUSTERS];
        mp_obj_t out_clusters[UZB_SIMPLE_DESC_MAX_CLUSTERS];
        for (size_t i = 0; i < snapshot.input_count; ++i) {
            in_clusters[i] = mp_obj_new_int_from_uint(snapshot.input_clusters[i]);
        }
        for (size_t i = 0; i < snapshot.output_count; ++i) {
            out_clusters[i] = mp_obj_new_int_from_uint(snapshot.output_clusters[i]);
        }
        mp_obj_t desc[6] = {
            mp_obj_new_int_from_uint(snapshot.endpoint),
            mp_obj_new_int_from_uint(snapshot.profile_id),
            mp_obj_new_int_from_uint(snapshot.device_id),
            mp_obj_new_int_from_uint(snapshot.device_version),
            mp_obj_new_tuple(snapshot.input_count, in_clusters),
            mp_obj_new_tuple(snapshot.output_count, out_clusters),
        };
        desc_obj = mp_obj_new_tuple(6, desc);
    }

    mp_obj_t out[3] = {
        mp_obj_new_int_from_uint(snapshot.status),
        mp_obj_new_int_from_uint(snapshot.addr),
        desc_obj,
    };
    return mp_obj_new_tuple(3, out);
}
static MP_DEFINE_CONST_FUN_OBJ_0(uzigbee_get_simple_descriptor_snapshot_obj, uzigbee_get_simple_descriptor_snapshot);

static mp_obj_t uzigbee_request_power_descriptor(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_dst_short_addr };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_dst_short_addr, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t dst_short_addr = args[ARG_dst_short_addr].u_int;
    if (dst_short_addr < 0 || dst_short_addr > 0xFFFE) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid dst_short_addr"));
    }

    esp_err_t err = uzb_core_request_power_descriptor((uint16_t)dst_short_addr);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_request_power_descriptor_obj, 0, uzigbee_request_power_descriptor);

static mp_obj_t uzigbee_get_power_descriptor_snapshot(void) {
    uzb_power_desc_snapshot_t snapshot = {0};
    esp_err_t err = uzb_core_get_power_descriptor_snapshot(&snapshot);
    if (err == ESP_ERR_NOT_FOUND) {
        return mp_const_none;
    }
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    if (!snapshot.valid) {
        return mp_const_none;
    }

    mp_obj_t desc_obj = mp_const_none;
    if (snapshot.has_desc) {
        mp_obj_t desc[4] = {
            mp_obj_new_int_from_uint(snapshot.current_power_mode),
            mp_obj_new_int_from_uint(snapshot.available_power_sources),
            mp_obj_new_int_from_uint(snapshot.current_power_source),
            mp_obj_new_int_from_uint(snapshot.current_power_source_level),
        };
        desc_obj = mp_obj_new_tuple(4, desc);
    }

    mp_obj_t out[3] = {
        mp_obj_new_int_from_uint(snapshot.status),
        mp_obj_new_int_from_uint(snapshot.addr),
        desc_obj,
    };
    return mp_obj_new_tuple(3, out);
}
static MP_DEFINE_CONST_FUN_OBJ_0(uzigbee_get_power_descriptor_snapshot_obj, uzigbee_get_power_descriptor_snapshot);

static mp_obj_t uzigbee_set_install_code_policy(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_enabled };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_enabled, MP_ARG_BOOL, {.u_bool = false} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    esp_err_t err = uzb_core_set_install_code_policy(args[ARG_enabled].u_bool);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_set_install_code_policy_obj, 0, uzigbee_set_install_code_policy);

static mp_obj_t uzigbee_get_install_code_policy(void) {
    bool enabled = false;
    esp_err_t err = uzb_core_get_install_code_policy(&enabled);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_obj_new_bool(enabled);
}
static MP_DEFINE_CONST_FUN_OBJ_0(uzigbee_get_install_code_policy_obj, uzigbee_get_install_code_policy);

static mp_obj_t uzigbee_set_network_security_enabled(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_enabled };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_enabled, MP_ARG_BOOL, {.u_bool = true} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    esp_err_t err = uzb_core_set_network_security_enabled(args[ARG_enabled].u_bool);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_set_network_security_enabled_obj, 0, uzigbee_set_network_security_enabled);

static mp_obj_t uzigbee_is_network_security_enabled(void) {
    bool enabled = false;
    esp_err_t err = uzb_core_get_network_security_enabled(&enabled);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_obj_new_bool(enabled);
}
static MP_DEFINE_CONST_FUN_OBJ_0(uzigbee_is_network_security_enabled_obj, uzigbee_is_network_security_enabled);

static mp_obj_t uzigbee_set_network_key(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_key };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_key, MP_ARG_REQUIRED | MP_ARG_OBJ, {.u_obj = MP_OBJ_NULL} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    uint8_t key[16] = {0};
    uzigbee_obj_to_key16(args[ARG_key].u_obj, key);
    esp_err_t err = uzb_core_set_network_key(key);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_set_network_key_obj, 0, uzigbee_set_network_key);

static mp_obj_t uzigbee_get_primary_network_key(void) {
    uint8_t key[16] = {0};
    esp_err_t err = uzb_core_get_primary_network_key(key);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_obj_new_bytes(key, 16);
}
static MP_DEFINE_CONST_FUN_OBJ_0(uzigbee_get_primary_network_key_obj, uzigbee_get_primary_network_key);

static mp_obj_t uzigbee_switch_network_key(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_key, ARG_key_seq_num };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_key, MP_ARG_REQUIRED | MP_ARG_OBJ, {.u_obj = MP_OBJ_NULL} },
        { MP_QSTR_key_seq_num, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t key_seq_num = args[ARG_key_seq_num].u_int;
    if (key_seq_num < 0 || key_seq_num > 0xFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid key_seq_num"));
    }

    uint8_t key[16] = {0};
    uzigbee_obj_to_key16(args[ARG_key].u_obj, key);
    esp_err_t err = uzb_core_switch_network_key(key, (uint8_t)key_seq_num);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_switch_network_key_obj, 0, uzigbee_switch_network_key);

static mp_obj_t uzigbee_broadcast_network_key(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_key, ARG_key_seq_num };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_key, MP_ARG_REQUIRED | MP_ARG_OBJ, {.u_obj = MP_OBJ_NULL} },
        { MP_QSTR_key_seq_num, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t key_seq_num = args[ARG_key_seq_num].u_int;
    if (key_seq_num < 0 || key_seq_num > 0xFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid key_seq_num"));
    }

    uint8_t key[16] = {0};
    uzigbee_obj_to_key16(args[ARG_key].u_obj, key);
    esp_err_t err = uzb_core_broadcast_network_key(key, (uint8_t)key_seq_num);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_broadcast_network_key_obj, 0, uzigbee_broadcast_network_key);

static mp_obj_t uzigbee_broadcast_network_key_switch(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_key_seq_num };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_key_seq_num, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t key_seq_num = args[ARG_key_seq_num].u_int;
    if (key_seq_num < 0 || key_seq_num > 0xFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid key_seq_num"));
    }

    esp_err_t err = uzb_core_broadcast_network_key_switch((uint8_t)key_seq_num);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_broadcast_network_key_switch_obj, 0, uzigbee_broadcast_network_key_switch);

static mp_obj_t uzigbee_add_install_code(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_ieee_addr, ARG_ic_str };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_ieee_addr, MP_ARG_REQUIRED | MP_ARG_OBJ, {.u_obj = MP_OBJ_NULL} },
        { MP_QSTR_ic_str, MP_ARG_REQUIRED | MP_ARG_OBJ, {.u_obj = MP_OBJ_NULL} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    uint8_t ieee_addr[8] = {0};
    uzigbee_obj_to_ieee_addr(args[ARG_ieee_addr].u_obj, ieee_addr);
    const char *ic_str = mp_obj_str_get_str(args[ARG_ic_str].u_obj);
    esp_err_t err = uzb_core_add_install_code(ieee_addr, ic_str);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_add_install_code_obj, 0, uzigbee_add_install_code);

static mp_obj_t uzigbee_set_local_install_code(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_ic_str };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_ic_str, MP_ARG_REQUIRED | MP_ARG_OBJ, {.u_obj = MP_OBJ_NULL} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    const char *ic_str = mp_obj_str_get_str(args[ARG_ic_str].u_obj);
    esp_err_t err = uzb_core_set_local_install_code(ic_str);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_set_local_install_code_obj, 0, uzigbee_set_local_install_code);

static mp_obj_t uzigbee_remove_install_code(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_ieee_addr };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_ieee_addr, MP_ARG_REQUIRED | MP_ARG_OBJ, {.u_obj = MP_OBJ_NULL} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    uint8_t ieee_addr[8] = {0};
    uzigbee_obj_to_ieee_addr(args[ARG_ieee_addr].u_obj, ieee_addr);
    esp_err_t err = uzb_core_remove_install_code(ieee_addr);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_remove_install_code_obj, 0, uzigbee_remove_install_code);

static mp_obj_t uzigbee_remove_all_install_codes(void) {
    esp_err_t err = uzb_core_remove_all_install_codes();
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_0(uzigbee_remove_all_install_codes_obj, uzigbee_remove_all_install_codes);

static mp_obj_t uzigbee_permit_join(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_duration_s };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_duration_s, MP_ARG_INT, {.u_int = 60} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    esp_err_t err = uzb_core_permit_join((uint8_t)args[ARG_duration_s].u_int);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_permit_join_obj, 0, uzigbee_permit_join);

static mp_obj_t uzigbee_set_primary_channel_mask(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_channel_mask };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_channel_mask, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t channel_mask = args[ARG_channel_mask].u_int;
    if (channel_mask < 0) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid channel_mask"));
    }

    esp_err_t err = uzb_core_set_primary_channel_mask((uint32_t)channel_mask);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_set_primary_channel_mask_obj, 0, uzigbee_set_primary_channel_mask);

static mp_obj_t uzigbee_set_pan_id(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_pan_id };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_pan_id, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t pan_id = args[ARG_pan_id].u_int;
    if (pan_id <= 0 || pan_id >= 0xFFFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid pan_id"));
    }

    esp_err_t err = uzb_core_set_pan_id((uint16_t)pan_id);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_set_pan_id_obj, 0, uzigbee_set_pan_id);

static mp_obj_t uzigbee_set_extended_pan_id(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_ext_pan_id };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_ext_pan_id, MP_ARG_REQUIRED | MP_ARG_OBJ, {.u_obj = MP_OBJ_NULL} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_buffer_info_t info = {0};
    mp_get_buffer_raise(args[ARG_ext_pan_id].u_obj, &info, MP_BUFFER_READ);
    if (info.len != 8) {
        mp_raise_ValueError(MP_ERROR_TEXT("ext_pan_id must be 8 bytes"));
    }

    uint8_t ext_pan_id[8] = {0};
    memcpy(ext_pan_id, info.buf, 8);
    esp_err_t err = uzb_core_set_extended_pan_id(ext_pan_id);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_set_extended_pan_id_obj, 0, uzigbee_set_extended_pan_id);

static mp_obj_t uzigbee_enable_wifi_i154_coex(void) {
    esp_err_t err = uzb_core_enable_wifi_i154_coex();
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_0(uzigbee_enable_wifi_i154_coex_obj, uzigbee_enable_wifi_i154_coex);

static mp_obj_t uzigbee_start_network_steering(void) {
    esp_err_t err = uzb_core_start_network_steering();
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_0(uzigbee_start_network_steering_obj, uzigbee_start_network_steering);

static mp_obj_t uzigbee_get_short_addr(void) {
    uint16_t short_addr = 0;
    esp_err_t err = uzb_core_get_short_addr(&short_addr);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_obj_new_int_from_uint(short_addr);
}
static MP_DEFINE_CONST_FUN_OBJ_0(uzigbee_get_short_addr_obj, uzigbee_get_short_addr);

static mp_obj_t uzigbee_get_last_joined_short_addr(void) {
    uint16_t short_addr = 0;
    esp_err_t err = uzb_core_get_last_joined_short_addr(&short_addr);
    if (err == ESP_ERR_NOT_FOUND) {
        return mp_const_none;
    }
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_obj_new_int_from_uint(short_addr);
}
static MP_DEFINE_CONST_FUN_OBJ_0(uzigbee_get_last_joined_short_addr_obj, uzigbee_get_last_joined_short_addr);

static mp_obj_t uzigbee_get_ieee_addr(void) {
    uint8_t ieee_addr[8] = {0};
    esp_err_t err = uzb_core_get_ieee_addr(ieee_addr);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }
    return mp_obj_new_bytes(ieee_addr, 8);
}
static MP_DEFINE_CONST_FUN_OBJ_0(uzigbee_get_ieee_addr_obj, uzigbee_get_ieee_addr);

static mp_obj_t uzigbee_get_network_runtime(void) {
    uzb_network_runtime_t runtime = {0};
    esp_err_t err = uzb_core_get_network_runtime(&runtime);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }

    mp_obj_t out[6] = {
        mp_obj_new_int_from_uint(runtime.channel),
        mp_obj_new_int_from_uint(runtime.pan_id),
        mp_obj_new_bytes(runtime.extended_pan_id, 8),
        mp_obj_new_int_from_uint(runtime.short_addr),
        runtime.formed ? mp_const_true : mp_const_false,
        runtime.joined ? mp_const_true : mp_const_false,
    };
    return mp_obj_new_tuple(6, out);
}
static MP_DEFINE_CONST_FUN_OBJ_0(uzigbee_get_network_runtime_obj, uzigbee_get_network_runtime);

static mp_obj_t uzigbee_get_basic_identity(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_endpoint };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_endpoint, MP_ARG_INT, {.u_int = 1} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_int_t endpoint = args[ARG_endpoint].u_int;
    if (endpoint <= 0 || endpoint >= 0xF0) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid endpoint"));
    }

    uzb_basic_identity_cfg_t cfg = {0};
    esp_err_t err = uzb_core_get_basic_identity((uint8_t)endpoint, &cfg);
    if (err != ESP_OK) {
        mp_raise_OSError(err);
    }

    mp_obj_t out[5] = {
        cfg.has_manufacturer ? uzigbee_pascal_to_obj(cfg.manufacturer, UZB_BASIC_STR_MAX_MANUFACTURER) : mp_const_none,
        cfg.has_model ? uzigbee_pascal_to_obj(cfg.model, UZB_BASIC_STR_MAX_MODEL) : mp_const_none,
        cfg.has_date_code ? uzigbee_pascal_to_obj(cfg.date_code, UZB_BASIC_STR_MAX_DATE_CODE) : mp_const_none,
        cfg.has_sw_build_id ? uzigbee_pascal_to_obj(cfg.sw_build_id, UZB_BASIC_STR_MAX_SW_BUILD_ID) : mp_const_none,
        cfg.has_power_source ? mp_obj_new_int_from_uint(cfg.power_source) : mp_const_none,
    };
    return mp_obj_new_tuple(5, out);
}
static MP_DEFINE_CONST_FUN_OBJ_KW(uzigbee_get_basic_identity_obj, 0, uzigbee_get_basic_identity);

static mp_obj_t uzigbee_set_signal_callback(mp_obj_t callback_in) {
    if (callback_in != mp_const_none && !mp_obj_is_callable(callback_in)) {
        mp_raise_ValueError(MP_ERROR_TEXT("callback must be callable or None"));
    }
    MP_STATE_PORT(uzigbee_signal_callback) = callback_in;
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(uzigbee_set_signal_callback_obj, uzigbee_set_signal_callback);

static mp_obj_t uzigbee_on_signal(mp_obj_t callback_in) {
    return uzigbee_set_signal_callback(callback_in);
}
static MP_DEFINE_CONST_FUN_OBJ_1(uzigbee_on_signal_obj, uzigbee_on_signal);

static mp_obj_t uzigbee_set_attribute_callback(mp_obj_t callback_in) {
    if (callback_in != mp_const_none && !mp_obj_is_callable(callback_in)) {
        mp_raise_ValueError(MP_ERROR_TEXT("callback must be callable or None"));
    }
    MP_STATE_PORT(uzigbee_attr_callback) = callback_in;
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(uzigbee_set_attribute_callback_obj, uzigbee_set_attribute_callback);

static mp_obj_t uzigbee_on_attribute(mp_obj_t callback_in) {
    return uzigbee_set_attribute_callback(callback_in);
}
static MP_DEFINE_CONST_FUN_OBJ_1(uzigbee_on_attribute_obj, uzigbee_on_attribute);

static mp_obj_t uzigbee_get_event_stats(void) {
    uzb_event_stats_t stats;
    uzb_core_get_event_stats(&stats);

    mp_obj_t out[6] = {
        mp_obj_new_int_from_uint(stats.enqueued),
        mp_obj_new_int_from_uint(stats.dropped_queue_full),
        mp_obj_new_int_from_uint(stats.dropped_schedule_fail),
        mp_obj_new_int_from_uint(stats.dispatched),
        mp_obj_new_int_from_uint(stats.max_depth),
        mp_obj_new_int_from_uint(stats.depth),
    };
    return mp_obj_new_tuple(6, out);
}
static MP_DEFINE_CONST_FUN_OBJ_0(uzigbee_get_event_stats_obj, uzigbee_get_event_stats);

static mp_obj_t uzigbee_get_heap_stats(void) {
    mp_obj_t out[4] = {
        mp_obj_new_int_from_uint(heap_caps_get_free_size(MALLOC_CAP_8BIT)),
        mp_obj_new_int_from_uint(heap_caps_get_minimum_free_size(MALLOC_CAP_8BIT)),
        mp_obj_new_int_from_uint(heap_caps_get_largest_free_block(MALLOC_CAP_8BIT)),
        mp_obj_new_int_from_uint(heap_caps_get_free_size(MALLOC_CAP_INTERNAL)),
    };
    return mp_obj_new_tuple(4, out);
}
static MP_DEFINE_CONST_FUN_OBJ_0(uzigbee_get_heap_stats_obj, uzigbee_get_heap_stats);

static mp_obj_t uzigbee_dispatch_events(mp_obj_t unused) {
    (void)unused;

    uzb_event_t event;
    mp_obj_t signal_cb = uzigbee_get_signal_callback();
    mp_obj_t attr_cb = uzigbee_get_attr_callback();
    while (uzb_core_pop_event(&event)) {
        if (event.type == UZB_EVENT_TYPE_APP_SIGNAL) {
            if (signal_cb == mp_const_none) {
                continue;
            }

            mp_obj_t args[2] = {
                mp_obj_new_int_from_uint(event.data.app_signal.signal),
                mp_obj_new_int(event.data.app_signal.status),
            };

            nlr_buf_t nlr;
            if (nlr_push(&nlr) == 0) {
                mp_call_function_n_kw(signal_cb, 2, 0, args);
                nlr_pop();
            } else {
                mp_obj_print_exception(&mp_plat_print, MP_OBJ_FROM_PTR(nlr.ret_val));
            }
        } else if (event.type == UZB_EVENT_TYPE_ATTR_SET) {
            if (attr_cb == mp_const_none) {
                continue;
            }

            mp_obj_t endpoint_obj = mp_obj_new_int_from_uint(event.data.attr_set.endpoint);
            mp_obj_t cluster_obj = mp_obj_new_int_from_uint(event.data.attr_set.cluster_id);
            mp_obj_t attr_obj = mp_obj_new_int_from_uint(event.data.attr_set.attr_id);
            mp_obj_t value_obj = uzigbee_attr_value_to_obj(&event.data.attr_set.value);
            mp_obj_t attr_type_obj = mp_obj_new_int_from_uint(event.data.attr_set.value.zcl_type);
            mp_obj_t status_obj = mp_obj_new_int(event.data.attr_set.status);

            mp_obj_t legacy_args[6] = {
                endpoint_obj,
                cluster_obj,
                attr_obj,
                value_obj,
                attr_type_obj,
                status_obj,
            };

            if (event.data.attr_set.has_source) {
                mp_obj_t source_args[7] = {
                    mp_obj_new_int_from_uint(event.data.attr_set.source_short_addr),
                    endpoint_obj,
                    cluster_obj,
                    attr_obj,
                    value_obj,
                    attr_type_obj,
                    status_obj,
                };
                mp_obj_t callback_exc = mp_const_none;
                if (!uzigbee_call_callback(attr_cb, 7, source_args, &callback_exc)) {
                    if (uzigbee_is_type_error_exception(callback_exc)) {
                        mp_obj_t fallback_exc = mp_const_none;
                        if (!uzigbee_call_callback(attr_cb, 6, legacy_args, &fallback_exc)) {
                            mp_obj_print_exception(&mp_plat_print, fallback_exc);
                        }
                    } else {
                        mp_obj_print_exception(&mp_plat_print, callback_exc);
                    }
                }
                continue;
            }

            mp_obj_t callback_exc = mp_const_none;
            if (!uzigbee_call_callback(attr_cb, 6, legacy_args, &callback_exc)) {
                mp_obj_print_exception(&mp_plat_print, callback_exc);
            }
        }
    }

    uzb_core_dispatch_complete();
    return mp_const_none;
}

static const mp_rom_map_elem_t uzigbee_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR__uzigbee) },
    { MP_ROM_QSTR(MP_QSTR_init), MP_ROM_PTR(&uzigbee_init_obj) },
    { MP_ROM_QSTR(MP_QSTR_start), MP_ROM_PTR(&uzigbee_start_obj) },
    { MP_ROM_QSTR(MP_QSTR_create_endpoint), MP_ROM_PTR(&uzigbee_create_endpoint_obj) },
    { MP_ROM_QSTR(MP_QSTR_create_on_off_light), MP_ROM_PTR(&uzigbee_create_on_off_light_obj) },
    { MP_ROM_QSTR(MP_QSTR_create_on_off_switch), MP_ROM_PTR(&uzigbee_create_on_off_switch_obj) },
    { MP_ROM_QSTR(MP_QSTR_create_dimmable_switch), MP_ROM_PTR(&uzigbee_create_dimmable_switch_obj) },
    { MP_ROM_QSTR(MP_QSTR_create_dimmable_light), MP_ROM_PTR(&uzigbee_create_dimmable_light_obj) },
    { MP_ROM_QSTR(MP_QSTR_create_color_light), MP_ROM_PTR(&uzigbee_create_color_light_obj) },
    { MP_ROM_QSTR(MP_QSTR_create_temperature_sensor), MP_ROM_PTR(&uzigbee_create_temperature_sensor_obj) },
    { MP_ROM_QSTR(MP_QSTR_create_humidity_sensor), MP_ROM_PTR(&uzigbee_create_humidity_sensor_obj) },
    { MP_ROM_QSTR(MP_QSTR_create_pressure_sensor), MP_ROM_PTR(&uzigbee_create_pressure_sensor_obj) },
    { MP_ROM_QSTR(MP_QSTR_create_climate_sensor), MP_ROM_PTR(&uzigbee_create_climate_sensor_obj) },
    { MP_ROM_QSTR(MP_QSTR_create_power_outlet), MP_ROM_PTR(&uzigbee_create_power_outlet_obj) },
    { MP_ROM_QSTR(MP_QSTR_create_door_lock), MP_ROM_PTR(&uzigbee_create_door_lock_obj) },
    { MP_ROM_QSTR(MP_QSTR_create_door_lock_controller), MP_ROM_PTR(&uzigbee_create_door_lock_controller_obj) },
    { MP_ROM_QSTR(MP_QSTR_create_thermostat), MP_ROM_PTR(&uzigbee_create_thermostat_obj) },
    { MP_ROM_QSTR(MP_QSTR_create_occupancy_sensor), MP_ROM_PTR(&uzigbee_create_occupancy_sensor_obj) },
    { MP_ROM_QSTR(MP_QSTR_create_window_covering), MP_ROM_PTR(&uzigbee_create_window_covering_obj) },
    { MP_ROM_QSTR(MP_QSTR_create_ias_zone), MP_ROM_PTR(&uzigbee_create_ias_zone_obj) },
    { MP_ROM_QSTR(MP_QSTR_create_contact_sensor), MP_ROM_PTR(&uzigbee_create_contact_sensor_obj) },
    { MP_ROM_QSTR(MP_QSTR_create_motion_sensor), MP_ROM_PTR(&uzigbee_create_motion_sensor_obj) },
    { MP_ROM_QSTR(MP_QSTR_clear_custom_clusters), MP_ROM_PTR(&uzigbee_clear_custom_clusters_obj) },
    { MP_ROM_QSTR(MP_QSTR_add_custom_cluster), MP_ROM_PTR(&uzigbee_add_custom_cluster_obj) },
    { MP_ROM_QSTR(MP_QSTR_add_custom_attr), MP_ROM_PTR(&uzigbee_add_custom_attr_obj) },
    { MP_ROM_QSTR(MP_QSTR_set_basic_identity), MP_ROM_PTR(&uzigbee_set_basic_identity_obj) },
    { MP_ROM_QSTR(MP_QSTR_register_device), MP_ROM_PTR(&uzigbee_register_device_obj) },
    { MP_ROM_QSTR(MP_QSTR_get_attribute), MP_ROM_PTR(&uzigbee_get_attribute_obj) },
    { MP_ROM_QSTR(MP_QSTR_set_attribute), MP_ROM_PTR(&uzigbee_set_attribute_obj) },
    { MP_ROM_QSTR(MP_QSTR_configure_reporting), MP_ROM_PTR(&uzigbee_configure_reporting_obj) },
    { MP_ROM_QSTR(MP_QSTR_send_on_off_cmd), MP_ROM_PTR(&uzigbee_send_on_off_cmd_obj) },
    { MP_ROM_QSTR(MP_QSTR_send_level_cmd), MP_ROM_PTR(&uzigbee_send_level_cmd_obj) },
    { MP_ROM_QSTR(MP_QSTR_send_color_move_to_color_cmd), MP_ROM_PTR(&uzigbee_send_color_move_to_color_cmd_obj) },
    { MP_ROM_QSTR(MP_QSTR_send_color_move_to_color_temperature_cmd), MP_ROM_PTR(&uzigbee_send_color_move_to_color_temperature_cmd_obj) },
    { MP_ROM_QSTR(MP_QSTR_send_lock_cmd), MP_ROM_PTR(&uzigbee_send_lock_cmd_obj) },
    { MP_ROM_QSTR(MP_QSTR_send_group_add_cmd), MP_ROM_PTR(&uzigbee_send_group_add_cmd_obj) },
    { MP_ROM_QSTR(MP_QSTR_send_group_remove_cmd), MP_ROM_PTR(&uzigbee_send_group_remove_cmd_obj) },
    { MP_ROM_QSTR(MP_QSTR_send_group_remove_all_cmd), MP_ROM_PTR(&uzigbee_send_group_remove_all_cmd_obj) },
    { MP_ROM_QSTR(MP_QSTR_send_scene_add_cmd), MP_ROM_PTR(&uzigbee_send_scene_add_cmd_obj) },
    { MP_ROM_QSTR(MP_QSTR_send_scene_remove_cmd), MP_ROM_PTR(&uzigbee_send_scene_remove_cmd_obj) },
    { MP_ROM_QSTR(MP_QSTR_send_scene_remove_all_cmd), MP_ROM_PTR(&uzigbee_send_scene_remove_all_cmd_obj) },
    { MP_ROM_QSTR(MP_QSTR_send_scene_recall_cmd), MP_ROM_PTR(&uzigbee_send_scene_recall_cmd_obj) },
    { MP_ROM_QSTR(MP_QSTR_send_custom_cmd), MP_ROM_PTR(&uzigbee_send_custom_cmd_obj) },
    { MP_ROM_QSTR(MP_QSTR_ota_client_query_interval_set), MP_ROM_PTR(&uzigbee_ota_client_query_interval_set_obj) },
    { MP_ROM_QSTR(MP_QSTR_ota_client_query_image_req), MP_ROM_PTR(&uzigbee_ota_client_query_image_req_obj) },
    { MP_ROM_QSTR(MP_QSTR_ota_client_query_image_stop), MP_ROM_PTR(&uzigbee_ota_client_query_image_stop_obj) },
    { MP_ROM_QSTR(MP_QSTR_ota_client_control_supported), MP_ROM_PTR(&uzigbee_ota_client_control_supported_obj) },
    { MP_ROM_QSTR(MP_QSTR_send_bind_cmd), MP_ROM_PTR(&uzigbee_send_bind_cmd_obj) },
    { MP_ROM_QSTR(MP_QSTR_send_unbind_cmd), MP_ROM_PTR(&uzigbee_send_unbind_cmd_obj) },
    { MP_ROM_QSTR(MP_QSTR_request_binding_table), MP_ROM_PTR(&uzigbee_request_binding_table_obj) },
    { MP_ROM_QSTR(MP_QSTR_get_binding_table_snapshot), MP_ROM_PTR(&uzigbee_get_binding_table_snapshot_obj) },
    { MP_ROM_QSTR(MP_QSTR_request_active_endpoints), MP_ROM_PTR(&uzigbee_request_active_endpoints_obj) },
    { MP_ROM_QSTR(MP_QSTR_get_active_endpoints_snapshot), MP_ROM_PTR(&uzigbee_get_active_endpoints_snapshot_obj) },
    { MP_ROM_QSTR(MP_QSTR_request_node_descriptor), MP_ROM_PTR(&uzigbee_request_node_descriptor_obj) },
    { MP_ROM_QSTR(MP_QSTR_get_node_descriptor_snapshot), MP_ROM_PTR(&uzigbee_get_node_descriptor_snapshot_obj) },
    { MP_ROM_QSTR(MP_QSTR_request_simple_descriptor), MP_ROM_PTR(&uzigbee_request_simple_descriptor_obj) },
    { MP_ROM_QSTR(MP_QSTR_get_simple_descriptor_snapshot), MP_ROM_PTR(&uzigbee_get_simple_descriptor_snapshot_obj) },
    { MP_ROM_QSTR(MP_QSTR_request_power_descriptor), MP_ROM_PTR(&uzigbee_request_power_descriptor_obj) },
    { MP_ROM_QSTR(MP_QSTR_get_power_descriptor_snapshot), MP_ROM_PTR(&uzigbee_get_power_descriptor_snapshot_obj) },
    { MP_ROM_QSTR(MP_QSTR_set_install_code_policy), MP_ROM_PTR(&uzigbee_set_install_code_policy_obj) },
    { MP_ROM_QSTR(MP_QSTR_get_install_code_policy), MP_ROM_PTR(&uzigbee_get_install_code_policy_obj) },
    { MP_ROM_QSTR(MP_QSTR_set_network_security_enabled), MP_ROM_PTR(&uzigbee_set_network_security_enabled_obj) },
    { MP_ROM_QSTR(MP_QSTR_is_network_security_enabled), MP_ROM_PTR(&uzigbee_is_network_security_enabled_obj) },
    { MP_ROM_QSTR(MP_QSTR_set_network_key), MP_ROM_PTR(&uzigbee_set_network_key_obj) },
    { MP_ROM_QSTR(MP_QSTR_get_primary_network_key), MP_ROM_PTR(&uzigbee_get_primary_network_key_obj) },
    { MP_ROM_QSTR(MP_QSTR_switch_network_key), MP_ROM_PTR(&uzigbee_switch_network_key_obj) },
    { MP_ROM_QSTR(MP_QSTR_broadcast_network_key), MP_ROM_PTR(&uzigbee_broadcast_network_key_obj) },
    { MP_ROM_QSTR(MP_QSTR_broadcast_network_key_switch), MP_ROM_PTR(&uzigbee_broadcast_network_key_switch_obj) },
    { MP_ROM_QSTR(MP_QSTR_add_install_code), MP_ROM_PTR(&uzigbee_add_install_code_obj) },
    { MP_ROM_QSTR(MP_QSTR_set_local_install_code), MP_ROM_PTR(&uzigbee_set_local_install_code_obj) },
    { MP_ROM_QSTR(MP_QSTR_remove_install_code), MP_ROM_PTR(&uzigbee_remove_install_code_obj) },
    { MP_ROM_QSTR(MP_QSTR_remove_all_install_codes), MP_ROM_PTR(&uzigbee_remove_all_install_codes_obj) },
    { MP_ROM_QSTR(MP_QSTR_get_basic_identity), MP_ROM_PTR(&uzigbee_get_basic_identity_obj) },
    { MP_ROM_QSTR(MP_QSTR_permit_join), MP_ROM_PTR(&uzigbee_permit_join_obj) },
    { MP_ROM_QSTR(MP_QSTR_set_primary_channel_mask), MP_ROM_PTR(&uzigbee_set_primary_channel_mask_obj) },
    { MP_ROM_QSTR(MP_QSTR_set_pan_id), MP_ROM_PTR(&uzigbee_set_pan_id_obj) },
    { MP_ROM_QSTR(MP_QSTR_set_extended_pan_id), MP_ROM_PTR(&uzigbee_set_extended_pan_id_obj) },
    { MP_ROM_QSTR(MP_QSTR_enable_wifi_i154_coex), MP_ROM_PTR(&uzigbee_enable_wifi_i154_coex_obj) },
    { MP_ROM_QSTR(MP_QSTR_start_network_steering), MP_ROM_PTR(&uzigbee_start_network_steering_obj) },
    { MP_ROM_QSTR(MP_QSTR_get_short_addr), MP_ROM_PTR(&uzigbee_get_short_addr_obj) },
    { MP_ROM_QSTR(MP_QSTR_get_last_joined_short_addr), MP_ROM_PTR(&uzigbee_get_last_joined_short_addr_obj) },
    { MP_ROM_QSTR(MP_QSTR_get_ieee_addr), MP_ROM_PTR(&uzigbee_get_ieee_addr_obj) },
    { MP_ROM_QSTR(MP_QSTR_get_network_runtime), MP_ROM_PTR(&uzigbee_get_network_runtime_obj) },
    { MP_ROM_QSTR(MP_QSTR_on_signal), MP_ROM_PTR(&uzigbee_on_signal_obj) },
    { MP_ROM_QSTR(MP_QSTR_set_signal_callback), MP_ROM_PTR(&uzigbee_set_signal_callback_obj) },
    { MP_ROM_QSTR(MP_QSTR_on_attribute), MP_ROM_PTR(&uzigbee_on_attribute_obj) },
    { MP_ROM_QSTR(MP_QSTR_set_attribute_callback), MP_ROM_PTR(&uzigbee_set_attribute_callback_obj) },
    { MP_ROM_QSTR(MP_QSTR_get_event_stats), MP_ROM_PTR(&uzigbee_get_event_stats_obj) },
    { MP_ROM_QSTR(MP_QSTR_get_heap_stats), MP_ROM_PTR(&uzigbee_get_heap_stats_obj) },
    { MP_ROM_QSTR(MP_QSTR_CLUSTER_ROLE_SERVER), MP_ROM_INT(ESP_ZB_ZCL_CLUSTER_SERVER_ROLE) },
    { MP_ROM_QSTR(MP_QSTR_CLUSTER_ROLE_CLIENT), MP_ROM_INT(ESP_ZB_ZCL_CLUSTER_CLIENT_ROLE) },
    { MP_ROM_QSTR(MP_QSTR_CLUSTER_ID_BASIC), MP_ROM_INT(ESP_ZB_ZCL_CLUSTER_ID_BASIC) },
    { MP_ROM_QSTR(MP_QSTR_CLUSTER_ID_GROUPS), MP_ROM_INT(ESP_ZB_ZCL_CLUSTER_ID_GROUPS) },
    { MP_ROM_QSTR(MP_QSTR_CLUSTER_ID_SCENES), MP_ROM_INT(ESP_ZB_ZCL_CLUSTER_ID_SCENES) },
    { MP_ROM_QSTR(MP_QSTR_CLUSTER_ID_ON_OFF), MP_ROM_INT(ESP_ZB_ZCL_CLUSTER_ID_ON_OFF) },
    { MP_ROM_QSTR(MP_QSTR_CLUSTER_ID_LEVEL_CONTROL), MP_ROM_INT(ESP_ZB_ZCL_CLUSTER_ID_LEVEL_CONTROL) },
    { MP_ROM_QSTR(MP_QSTR_CLUSTER_ID_COLOR_CONTROL), MP_ROM_INT(ESP_ZB_ZCL_CLUSTER_ID_COLOR_CONTROL) },
    { MP_ROM_QSTR(MP_QSTR_CLUSTER_ID_DOOR_LOCK), MP_ROM_INT(ESP_ZB_ZCL_CLUSTER_ID_DOOR_LOCK) },
    { MP_ROM_QSTR(MP_QSTR_CLUSTER_ID_WINDOW_COVERING), MP_ROM_INT(ESP_ZB_ZCL_CLUSTER_ID_WINDOW_COVERING) },
    { MP_ROM_QSTR(MP_QSTR_CLUSTER_ID_THERMOSTAT), MP_ROM_INT(ESP_ZB_ZCL_CLUSTER_ID_THERMOSTAT) },
    { MP_ROM_QSTR(MP_QSTR_CLUSTER_ID_TEMP_MEASUREMENT), MP_ROM_INT(ESP_ZB_ZCL_CLUSTER_ID_TEMP_MEASUREMENT) },
    { MP_ROM_QSTR(MP_QSTR_CLUSTER_ID_PRESSURE_MEASUREMENT), MP_ROM_INT(ESP_ZB_ZCL_CLUSTER_ID_PRESSURE_MEASUREMENT) },
    { MP_ROM_QSTR(MP_QSTR_CLUSTER_ID_REL_HUMIDITY_MEASUREMENT), MP_ROM_INT(ESP_ZB_ZCL_CLUSTER_ID_REL_HUMIDITY_MEASUREMENT) },
    { MP_ROM_QSTR(MP_QSTR_CLUSTER_ID_OCCUPANCY_SENSING), MP_ROM_INT(ESP_ZB_ZCL_CLUSTER_ID_OCCUPANCY_SENSING) },
    { MP_ROM_QSTR(MP_QSTR_CLUSTER_ID_IAS_ZONE), MP_ROM_INT(ESP_ZB_ZCL_CLUSTER_ID_IAS_ZONE) },
    { MP_ROM_QSTR(MP_QSTR_CLUSTER_ID_ELECTRICAL_MEASUREMENT), MP_ROM_INT(ESP_ZB_ZCL_CLUSTER_ID_ELECTRICAL_MEASUREMENT) },
    { MP_ROM_QSTR(MP_QSTR_CUSTOM_CLUSTER_ID_MIN), MP_ROM_INT(0xFC00) },
    { MP_ROM_QSTR(MP_QSTR_ATTR_ACCESS_READ_ONLY), MP_ROM_INT(ESP_ZB_ZCL_ATTR_ACCESS_READ_ONLY) },
    { MP_ROM_QSTR(MP_QSTR_ATTR_ACCESS_WRITE_ONLY), MP_ROM_INT(ESP_ZB_ZCL_ATTR_ACCESS_WRITE_ONLY) },
    { MP_ROM_QSTR(MP_QSTR_ATTR_ACCESS_READ_WRITE), MP_ROM_INT(ESP_ZB_ZCL_ATTR_ACCESS_READ_WRITE) },
    { MP_ROM_QSTR(MP_QSTR_ATTR_ACCESS_REPORTING), MP_ROM_INT(ESP_ZB_ZCL_ATTR_ACCESS_REPORTING) },
    { MP_ROM_QSTR(MP_QSTR_ATTR_ACCESS_SCENE), MP_ROM_INT(ESP_ZB_ZCL_ATTR_ACCESS_SCENE) },
    { MP_ROM_QSTR(MP_QSTR_CMD_DIRECTION_TO_SERVER), MP_ROM_INT(ESP_ZB_ZCL_CMD_DIRECTION_TO_SRV) },
    { MP_ROM_QSTR(MP_QSTR_CMD_DIRECTION_TO_CLIENT), MP_ROM_INT(ESP_ZB_ZCL_CMD_DIRECTION_TO_CLI) },
    { MP_ROM_QSTR(MP_QSTR_ATTR_BASIC_MANUFACTURER_NAME), MP_ROM_INT(ESP_ZB_ZCL_ATTR_BASIC_MANUFACTURER_NAME_ID) },
    { MP_ROM_QSTR(MP_QSTR_ATTR_BASIC_MODEL_IDENTIFIER), MP_ROM_INT(ESP_ZB_ZCL_ATTR_BASIC_MODEL_IDENTIFIER_ID) },
    { MP_ROM_QSTR(MP_QSTR_ATTR_BASIC_DATE_CODE), MP_ROM_INT(ESP_ZB_ZCL_ATTR_BASIC_DATE_CODE_ID) },
    { MP_ROM_QSTR(MP_QSTR_ATTR_BASIC_POWER_SOURCE), MP_ROM_INT(ESP_ZB_ZCL_ATTR_BASIC_POWER_SOURCE_ID) },
    { MP_ROM_QSTR(MP_QSTR_ATTR_BASIC_SW_BUILD_ID), MP_ROM_INT(ESP_ZB_ZCL_ATTR_BASIC_SW_BUILD_ID) },
    { MP_ROM_QSTR(MP_QSTR_ATTR_ON_OFF_ON_OFF), MP_ROM_INT(ESP_ZB_ZCL_ATTR_ON_OFF_ON_OFF_ID) },
    { MP_ROM_QSTR(MP_QSTR_ATTR_LEVEL_CONTROL_CURRENT_LEVEL), MP_ROM_INT(ESP_ZB_ZCL_ATTR_LEVEL_CONTROL_CURRENT_LEVEL_ID) },
    { MP_ROM_QSTR(MP_QSTR_ATTR_DOOR_LOCK_LOCK_STATE), MP_ROM_INT(ESP_ZB_ZCL_ATTR_DOOR_LOCK_LOCK_STATE_ID) },
    { MP_ROM_QSTR(MP_QSTR_ATTR_WINDOW_COVERING_CURRENT_POSITION_LIFT_PERCENTAGE),
      MP_ROM_INT(ESP_ZB_ZCL_ATTR_WINDOW_COVERING_CURRENT_POSITION_LIFT_PERCENTAGE_ID) },
    { MP_ROM_QSTR(MP_QSTR_ATTR_WINDOW_COVERING_CURRENT_POSITION_TILT_PERCENTAGE),
      MP_ROM_INT(ESP_ZB_ZCL_ATTR_WINDOW_COVERING_CURRENT_POSITION_TILT_PERCENTAGE_ID) },
    { MP_ROM_QSTR(MP_QSTR_ATTR_THERMOSTAT_LOCAL_TEMPERATURE), MP_ROM_INT(ESP_ZB_ZCL_ATTR_THERMOSTAT_LOCAL_TEMPERATURE_ID) },
    { MP_ROM_QSTR(MP_QSTR_ATTR_THERMOSTAT_OCCUPIED_HEATING_SETPOINT), MP_ROM_INT(ESP_ZB_ZCL_ATTR_THERMOSTAT_OCCUPIED_HEATING_SETPOINT_ID) },
    { MP_ROM_QSTR(MP_QSTR_ATTR_THERMOSTAT_SYSTEM_MODE), MP_ROM_INT(ESP_ZB_ZCL_ATTR_THERMOSTAT_SYSTEM_MODE_ID) },
    { MP_ROM_QSTR(MP_QSTR_ATTR_TEMP_MEASUREMENT_VALUE), MP_ROM_INT(ESP_ZB_ZCL_ATTR_TEMP_MEASUREMENT_VALUE_ID) },
    { MP_ROM_QSTR(MP_QSTR_ATTR_PRESSURE_MEASUREMENT_VALUE), MP_ROM_INT(ESP_ZB_ZCL_ATTR_PRESSURE_MEASUREMENT_VALUE_ID) },
    { MP_ROM_QSTR(MP_QSTR_ATTR_REL_HUMIDITY_MEASUREMENT_VALUE), MP_ROM_INT(ESP_ZB_ZCL_ATTR_REL_HUMIDITY_MEASUREMENT_VALUE_ID) },
    { MP_ROM_QSTR(MP_QSTR_ATTR_OCCUPANCY_SENSING_OCCUPANCY), MP_ROM_INT(ESP_ZB_ZCL_ATTR_OCCUPANCY_SENSING_OCCUPANCY_ID) },
    { MP_ROM_QSTR(MP_QSTR_ATTR_IAS_ZONE_STATE), MP_ROM_INT(ESP_ZB_ZCL_ATTR_IAS_ZONE_ZONESTATE_ID) },
    { MP_ROM_QSTR(MP_QSTR_ATTR_IAS_ZONE_TYPE), MP_ROM_INT(ESP_ZB_ZCL_ATTR_IAS_ZONE_ZONETYPE_ID) },
    { MP_ROM_QSTR(MP_QSTR_ATTR_IAS_ZONE_STATUS), MP_ROM_INT(ESP_ZB_ZCL_ATTR_IAS_ZONE_ZONESTATUS_ID) },
    { MP_ROM_QSTR(MP_QSTR_ATTR_IAS_ZONE_IAS_CIE_ADDRESS), MP_ROM_INT(ESP_ZB_ZCL_ATTR_IAS_ZONE_IAS_CIE_ADDRESS_ID) },
    { MP_ROM_QSTR(MP_QSTR_ATTR_IAS_ZONE_ID), MP_ROM_INT(ESP_ZB_ZCL_ATTR_IAS_ZONE_ZONEID_ID) },
    { MP_ROM_QSTR(MP_QSTR_ATTR_ELECTRICAL_MEASUREMENT_RMSVOLTAGE), MP_ROM_INT(ESP_ZB_ZCL_ATTR_ELECTRICAL_MEASUREMENT_RMSVOLTAGE_ID) },
    { MP_ROM_QSTR(MP_QSTR_ATTR_ELECTRICAL_MEASUREMENT_RMSCURRENT), MP_ROM_INT(ESP_ZB_ZCL_ATTR_ELECTRICAL_MEASUREMENT_RMSCURRENT_ID) },
    { MP_ROM_QSTR(MP_QSTR_ATTR_ELECTRICAL_MEASUREMENT_ACTIVE_POWER), MP_ROM_INT(ESP_ZB_ZCL_ATTR_ELECTRICAL_MEASUREMENT_ACTIVE_POWER_ID) },
    { MP_ROM_QSTR(MP_QSTR_DEVICE_ID_ON_OFF_SWITCH), MP_ROM_INT(ESP_ZB_HA_ON_OFF_SWITCH_DEVICE_ID) },
    { MP_ROM_QSTR(MP_QSTR_DEVICE_ID_LEVEL_CONTROL_SWITCH), MP_ROM_INT(ESP_ZB_HA_LEVEL_CONTROL_SWITCH_DEVICE_ID) },
    { MP_ROM_QSTR(MP_QSTR_DEVICE_ID_DIMMER_SWITCH), MP_ROM_INT(ESP_ZB_HA_DIMMER_SWITCH_DEVICE_ID) },
    { MP_ROM_QSTR(MP_QSTR_DEVICE_ID_SIMPLE_SENSOR), MP_ROM_INT(ESP_ZB_HA_SIMPLE_SENSOR_DEVICE_ID) },
    { MP_ROM_QSTR(MP_QSTR_DEVICE_ID_HUMIDITY_SENSOR), MP_ROM_INT(ESP_ZB_HA_SIMPLE_SENSOR_DEVICE_ID) },
    { MP_ROM_QSTR(MP_QSTR_DEVICE_ID_PRESSURE_SENSOR), MP_ROM_INT(ESP_ZB_HA_SIMPLE_SENSOR_DEVICE_ID) },
    { MP_ROM_QSTR(MP_QSTR_DEVICE_ID_CLIMATE_SENSOR), MP_ROM_INT(ESP_ZB_HA_SIMPLE_SENSOR_DEVICE_ID) },
    { MP_ROM_QSTR(MP_QSTR_DEVICE_ID_MAINS_POWER_OUTLET), MP_ROM_INT(ESP_ZB_HA_MAINS_POWER_OUTLET_DEVICE_ID) },
    { MP_ROM_QSTR(MP_QSTR_DEVICE_ID_SMART_PLUG), MP_ROM_INT(ESP_ZB_HA_SMART_PLUG_DEVICE_ID) },
    { MP_ROM_QSTR(MP_QSTR_DEVICE_ID_DOOR_LOCK), MP_ROM_INT(ESP_ZB_HA_DOOR_LOCK_DEVICE_ID) },
    { MP_ROM_QSTR(MP_QSTR_DEVICE_ID_DOOR_LOCK_CONTROLLER), MP_ROM_INT(ESP_ZB_HA_DOOR_LOCK_CONTROLLER_DEVICE_ID) },
    { MP_ROM_QSTR(MP_QSTR_DEVICE_ID_WINDOW_COVERING), MP_ROM_INT(ESP_ZB_HA_WINDOW_COVERING_DEVICE_ID) },
    { MP_ROM_QSTR(MP_QSTR_DEVICE_ID_THERMOSTAT), MP_ROM_INT(ESP_ZB_HA_THERMOSTAT_DEVICE_ID) },
    { MP_ROM_QSTR(MP_QSTR_DEVICE_ID_OCCUPANCY_SENSOR), MP_ROM_INT(ESP_ZB_HA_SIMPLE_SENSOR_DEVICE_ID) },
    { MP_ROM_QSTR(MP_QSTR_DEVICE_ID_IAS_ZONE), MP_ROM_INT(ESP_ZB_HA_IAS_ZONE_ID) },
    { MP_ROM_QSTR(MP_QSTR_DEVICE_ID_CONTACT_SENSOR), MP_ROM_INT(ESP_ZB_HA_IAS_ZONE_ID) },
    { MP_ROM_QSTR(MP_QSTR_DEVICE_ID_MOTION_SENSOR), MP_ROM_INT(ESP_ZB_HA_IAS_ZONE_ID) },
    { MP_ROM_QSTR(MP_QSTR_DEVICE_ID_DIMMABLE_LIGHT), MP_ROM_INT(ESP_ZB_HA_DIMMABLE_LIGHT_DEVICE_ID) },
    { MP_ROM_QSTR(MP_QSTR_DEVICE_ID_TEMPERATURE_SENSOR), MP_ROM_INT(ESP_ZB_HA_TEMPERATURE_SENSOR_DEVICE_ID) },
    { MP_ROM_QSTR(MP_QSTR_ATTR_COLOR_CONTROL_CURRENT_X), MP_ROM_INT(ESP_ZB_ZCL_ATTR_COLOR_CONTROL_CURRENT_X_ID) },
    { MP_ROM_QSTR(MP_QSTR_ATTR_COLOR_CONTROL_CURRENT_Y), MP_ROM_INT(ESP_ZB_ZCL_ATTR_COLOR_CONTROL_CURRENT_Y_ID) },
    { MP_ROM_QSTR(MP_QSTR_ATTR_COLOR_CONTROL_COLOR_TEMPERATURE), MP_ROM_INT(ESP_ZB_ZCL_ATTR_COLOR_CONTROL_COLOR_TEMPERATURE_ID) },
    { MP_ROM_QSTR(MP_QSTR_DEVICE_ID_COLOR_DIMMABLE_LIGHT), MP_ROM_INT(ESP_ZB_HA_COLOR_DIMMABLE_LIGHT_DEVICE_ID) },
    { MP_ROM_QSTR(MP_QSTR_CMD_ON_OFF_OFF), MP_ROM_INT(ESP_ZB_ZCL_CMD_ON_OFF_OFF_ID) },
    { MP_ROM_QSTR(MP_QSTR_CMD_ON_OFF_ON), MP_ROM_INT(ESP_ZB_ZCL_CMD_ON_OFF_ON_ID) },
    { MP_ROM_QSTR(MP_QSTR_CMD_ON_OFF_TOGGLE), MP_ROM_INT(ESP_ZB_ZCL_CMD_ON_OFF_TOGGLE_ID) },
    { MP_ROM_QSTR(MP_QSTR_CMD_SCENES_ADD), MP_ROM_INT(ESP_ZB_ZCL_CMD_SCENES_ADD_SCENE) },
    { MP_ROM_QSTR(MP_QSTR_CMD_SCENES_REMOVE), MP_ROM_INT(ESP_ZB_ZCL_CMD_SCENES_REMOVE_SCENE) },
    { MP_ROM_QSTR(MP_QSTR_CMD_SCENES_REMOVE_ALL), MP_ROM_INT(ESP_ZB_ZCL_CMD_SCENES_REMOVE_ALL_SCENES) },
    { MP_ROM_QSTR(MP_QSTR_CMD_SCENES_STORE), MP_ROM_INT(ESP_ZB_ZCL_CMD_SCENES_STORE_SCENE) },
    { MP_ROM_QSTR(MP_QSTR_CMD_SCENES_RECALL), MP_ROM_INT(ESP_ZB_ZCL_CMD_SCENES_RECALL_SCENE) },
    { MP_ROM_QSTR(MP_QSTR_CMD_SCENES_GET_MEMBERSHIP), MP_ROM_INT(ESP_ZB_ZCL_CMD_SCENES_GET_SCENE_MEMBERSHIP) },
    { MP_ROM_QSTR(MP_QSTR_IC_TYPE_48), MP_ROM_INT(ESP_ZB_IC_TYPE_48) },
    { MP_ROM_QSTR(MP_QSTR_IC_TYPE_64), MP_ROM_INT(ESP_ZB_IC_TYPE_64) },
    { MP_ROM_QSTR(MP_QSTR_IC_TYPE_96), MP_ROM_INT(ESP_ZB_IC_TYPE_96) },
    { MP_ROM_QSTR(MP_QSTR_IC_TYPE_128), MP_ROM_INT(ESP_ZB_IC_TYPE_128) },
    { MP_ROM_QSTR(MP_QSTR_CMD_DOOR_LOCK_LOCK_DOOR), MP_ROM_INT(ESP_ZB_ZCL_CMD_DOOR_LOCK_LOCK_DOOR) },
    { MP_ROM_QSTR(MP_QSTR_CMD_DOOR_LOCK_UNLOCK_DOOR), MP_ROM_INT(ESP_ZB_ZCL_CMD_DOOR_LOCK_UNLOCK_DOOR) },
    { MP_ROM_QSTR(MP_QSTR_CMD_WINDOW_COVERING_UP_OPEN), MP_ROM_INT(ESP_ZB_ZCL_CMD_WINDOW_COVERING_UP_OPEN) },
    { MP_ROM_QSTR(MP_QSTR_CMD_WINDOW_COVERING_DOWN_CLOSE), MP_ROM_INT(ESP_ZB_ZCL_CMD_WINDOW_COVERING_DOWN_CLOSE) },
    { MP_ROM_QSTR(MP_QSTR_CMD_WINDOW_COVERING_STOP), MP_ROM_INT(ESP_ZB_ZCL_CMD_WINDOW_COVERING_STOP) },
    { MP_ROM_QSTR(MP_QSTR_CMD_WINDOW_COVERING_GO_TO_LIFT_PERCENTAGE), MP_ROM_INT(ESP_ZB_ZCL_CMD_WINDOW_COVERING_GO_TO_LIFT_PERCENTAGE) },
    { MP_ROM_QSTR(MP_QSTR_CMD_LEVEL_MOVE_TO_LEVEL), MP_ROM_INT(ESP_ZB_ZCL_CMD_LEVEL_CONTROL_MOVE_TO_LEVEL) },
    { MP_ROM_QSTR(MP_QSTR_CMD_LEVEL_MOVE_TO_LEVEL_WITH_ONOFF), MP_ROM_INT(ESP_ZB_ZCL_CMD_LEVEL_CONTROL_MOVE_TO_LEVEL_WITH_ON_OFF) },
    { MP_ROM_QSTR(MP_QSTR_CMD_COLOR_MOVE_TO_COLOR), MP_ROM_INT(ESP_ZB_ZCL_CMD_COLOR_CONTROL_MOVE_TO_COLOR) },
    { MP_ROM_QSTR(MP_QSTR_CMD_COLOR_MOVE_TO_COLOR_TEMPERATURE), MP_ROM_INT(ESP_ZB_ZCL_CMD_COLOR_CONTROL_MOVE_TO_COLOR_TEMPERATURE) },
    { MP_ROM_QSTR(MP_QSTR_IAS_ZONE_TYPE_MOTION), MP_ROM_INT(ESP_ZB_ZCL_IAS_ZONE_ZONETYPE_MOTION) },
    { MP_ROM_QSTR(MP_QSTR_IAS_ZONE_TYPE_CONTACT_SWITCH), MP_ROM_INT(ESP_ZB_ZCL_IAS_ZONE_ZONETYPE_CONTACT_SWITCH) },
    { MP_ROM_QSTR(MP_QSTR_IAS_ZONE_STATUS_ALARM1), MP_ROM_INT(ESP_ZB_ZCL_IAS_ZONE_ZONE_STATUS_ALARM1) },
    { MP_ROM_QSTR(MP_QSTR_IAS_ZONE_STATUS_ALARM2), MP_ROM_INT(ESP_ZB_ZCL_IAS_ZONE_ZONE_STATUS_ALARM2) },
    { MP_ROM_QSTR(MP_QSTR_IAS_ZONE_STATUS_TAMPER), MP_ROM_INT(ESP_ZB_ZCL_IAS_ZONE_ZONE_STATUS_TAMPER) },
    { MP_ROM_QSTR(MP_QSTR_IAS_ZONE_STATUS_BATTERY), MP_ROM_INT(ESP_ZB_ZCL_IAS_ZONE_ZONE_STATUS_BATTERY) },
    { MP_ROM_QSTR(MP_QSTR_BASIC_POWER_SOURCE_UNKNOWN), MP_ROM_INT(ESP_ZB_ZCL_BASIC_POWER_SOURCE_UNKNOWN) },
    { MP_ROM_QSTR(MP_QSTR_BASIC_POWER_SOURCE_MAINS_SINGLE_PHASE), MP_ROM_INT(ESP_ZB_ZCL_BASIC_POWER_SOURCE_MAINS_SINGLE_PHASE) },
    { MP_ROM_QSTR(MP_QSTR_BASIC_POWER_SOURCE_MAINS_THREE_PHASE), MP_ROM_INT(ESP_ZB_ZCL_BASIC_POWER_SOURCE_MAINS_THREE_PHASE) },
    { MP_ROM_QSTR(MP_QSTR_BASIC_POWER_SOURCE_BATTERY), MP_ROM_INT(ESP_ZB_ZCL_BASIC_POWER_SOURCE_BATTERY) },
    { MP_ROM_QSTR(MP_QSTR_BASIC_POWER_SOURCE_DC_SOURCE), MP_ROM_INT(ESP_ZB_ZCL_BASIC_POWER_SOURCE_DC_SOURCE) },
    { MP_ROM_QSTR(MP_QSTR_BASIC_POWER_SOURCE_EMERGENCY_MAINS_CONST), MP_ROM_INT(ESP_ZB_ZCL_BASIC_POWER_SOURCE_EMERGENCY_MAINS_CONST) },
    { MP_ROM_QSTR(MP_QSTR_BASIC_POWER_SOURCE_EMERGENCY_MAINS_TRANSF), MP_ROM_INT(ESP_ZB_ZCL_BASIC_POWER_SOURCE_EMERGENCY_MAINS_TRANSF) },
    { MP_ROM_QSTR(MP_QSTR_SIGNAL_DEFAULT_START), MP_ROM_INT(ESP_ZB_ZDO_SIGNAL_DEFAULT_START) },
    { MP_ROM_QSTR(MP_QSTR_SIGNAL_SKIP_STARTUP), MP_ROM_INT(ESP_ZB_ZDO_SIGNAL_SKIP_STARTUP) },
    { MP_ROM_QSTR(MP_QSTR_SIGNAL_DEVICE_ANNCE), MP_ROM_INT(ESP_ZB_ZDO_SIGNAL_DEVICE_ANNCE) },
    { MP_ROM_QSTR(MP_QSTR_SIGNAL_LEAVE), MP_ROM_INT(ESP_ZB_ZDO_SIGNAL_LEAVE) },
    { MP_ROM_QSTR(MP_QSTR_SIGNAL_ERROR), MP_ROM_INT(ESP_ZB_ZDO_SIGNAL_ERROR) },
    { MP_ROM_QSTR(MP_QSTR_SIGNAL_DEVICE_FIRST_START), MP_ROM_INT(ESP_ZB_BDB_SIGNAL_DEVICE_FIRST_START) },
    { MP_ROM_QSTR(MP_QSTR_SIGNAL_DEVICE_REBOOT), MP_ROM_INT(ESP_ZB_BDB_SIGNAL_DEVICE_REBOOT) },
    { MP_ROM_QSTR(MP_QSTR_SIGNAL_TOUCHLINK_NWK_STARTED), MP_ROM_INT(ESP_ZB_BDB_SIGNAL_TOUCHLINK_NWK_STARTED) },
    { MP_ROM_QSTR(MP_QSTR_SIGNAL_TOUCHLINK_NWK_JOINED_ROUTER), MP_ROM_INT(ESP_ZB_BDB_SIGNAL_TOUCHLINK_NWK_JOINED_ROUTER) },
    { MP_ROM_QSTR(MP_QSTR_SIGNAL_TOUCHLINK), MP_ROM_INT(ESP_ZB_BDB_SIGNAL_TOUCHLINK) },
    { MP_ROM_QSTR(MP_QSTR_SIGNAL_STEERING), MP_ROM_INT(ESP_ZB_BDB_SIGNAL_STEERING) },
    { MP_ROM_QSTR(MP_QSTR_SIGNAL_FORMATION), MP_ROM_INT(ESP_ZB_BDB_SIGNAL_FORMATION) },
    { MP_ROM_QSTR(MP_QSTR_SIGNAL_FINDING_AND_BINDING_TARGET_FINISHED), MP_ROM_INT(ESP_ZB_BDB_SIGNAL_FINDING_AND_BINDING_TARGET_FINISHED) },
    { MP_ROM_QSTR(MP_QSTR_SIGNAL_FINDING_AND_BINDING_INITIATOR_FINISHED), MP_ROM_INT(ESP_ZB_BDB_SIGNAL_FINDING_AND_BINDING_INITIATOR_FINISHED) },
    { MP_ROM_QSTR(MP_QSTR_SIGNAL_TOUCHLINK_TARGET), MP_ROM_INT(ESP_ZB_BDB_SIGNAL_TOUCHLINK_TARGET) },
    { MP_ROM_QSTR(MP_QSTR_SIGNAL_TOUCHLINK_NWK), MP_ROM_INT(ESP_ZB_BDB_SIGNAL_TOUCHLINK_NWK) },
    { MP_ROM_QSTR(MP_QSTR_SIGNAL_TOUCHLINK_TARGET_FINISHED), MP_ROM_INT(ESP_ZB_BDB_SIGNAL_TOUCHLINK_TARGET_FINISHED) },
    { MP_ROM_QSTR(MP_QSTR_SIGNAL_DEVICE_ASSOCIATED), MP_ROM_INT(ESP_ZB_NWK_SIGNAL_DEVICE_ASSOCIATED) },
    { MP_ROM_QSTR(MP_QSTR_SIGNAL_LEAVE_INDICATION), MP_ROM_INT(ESP_ZB_ZDO_SIGNAL_LEAVE_INDICATION) },
    { MP_ROM_QSTR(MP_QSTR_SIGNAL_GPP_COMMISSIONING), MP_ROM_INT(ESP_ZB_ZGP_SIGNAL_COMMISSIONING) },
    { MP_ROM_QSTR(MP_QSTR_SIGNAL_CAN_SLEEP), MP_ROM_INT(ESP_ZB_COMMON_SIGNAL_CAN_SLEEP) },
    { MP_ROM_QSTR(MP_QSTR_SIGNAL_PRODUCTION_CONFIG_READY), MP_ROM_INT(ESP_ZB_ZDO_SIGNAL_PRODUCTION_CONFIG_READY) },
    { MP_ROM_QSTR(MP_QSTR_SIGNAL_NO_ACTIVE_LINKS_LEFT), MP_ROM_INT(ESP_ZB_NWK_SIGNAL_NO_ACTIVE_LINKS_LEFT) },
    { MP_ROM_QSTR(MP_QSTR_SIGNAL_DEVICE_AUTHORIZED), MP_ROM_INT(ESP_ZB_ZDO_SIGNAL_DEVICE_AUTHORIZED) },
    { MP_ROM_QSTR(MP_QSTR_SIGNAL_DEVICE_UPDATE), MP_ROM_INT(ESP_ZB_ZDO_SIGNAL_DEVICE_UPDATE) },
    { MP_ROM_QSTR(MP_QSTR_SIGNAL_PANID_CONFLICT_DETECTED), MP_ROM_INT(ESP_ZB_NWK_SIGNAL_PANID_CONFLICT_DETECTED) },
    { MP_ROM_QSTR(MP_QSTR_SIGNAL_NWK_STATUS_INDICATION), MP_ROM_INT(ESP_ZB_NLME_STATUS_INDICATION) },
    { MP_ROM_QSTR(MP_QSTR_SIGNAL_TC_REJOIN_DONE), MP_ROM_INT(ESP_ZB_BDB_SIGNAL_TC_REJOIN_DONE) },
    { MP_ROM_QSTR(MP_QSTR_SIGNAL_PERMIT_JOIN_STATUS), MP_ROM_INT(ESP_ZB_NWK_SIGNAL_PERMIT_JOIN_STATUS) },
    { MP_ROM_QSTR(MP_QSTR_SIGNAL_STEERING_CANCELLED), MP_ROM_INT(ESP_ZB_BDB_SIGNAL_STEERING_CANCELLED) },
    { MP_ROM_QSTR(MP_QSTR_SIGNAL_FORMATION_CANCELLED), MP_ROM_INT(ESP_ZB_BDB_SIGNAL_FORMATION_CANCELLED) },
    { MP_ROM_QSTR(MP_QSTR_SIGNAL_GPP_MODE_CHANGE), MP_ROM_INT(ESP_ZB_ZGP_SIGNAL_MODE_CHANGE) },
    { MP_ROM_QSTR(MP_QSTR_SIGNAL_GPP_APPROVE_COMMISSIONING), MP_ROM_INT(ESP_ZB_ZGP_SIGNAL_APPROVE_COMMISSIONING) },
    { MP_ROM_QSTR(MP_QSTR_SIGNAL_END), MP_ROM_INT(ESP_ZB_SIGNAL_END) },
};
static MP_DEFINE_CONST_DICT(uzigbee_module_globals, uzigbee_module_globals_table);

const mp_obj_module_t uzigbee_user_cmodule = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&uzigbee_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR__uzigbee, uzigbee_user_cmodule);
