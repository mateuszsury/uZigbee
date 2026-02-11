#include "uzb_core.h"

#include <limits.h>
#include <string.h>

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include "esp_log.h"
#include "esp_coexist.h"

#include "esp_zigbee_core.h"
#include "esp_zigbee_ota.h"
#include "esp_zigbee_secur.h"
#include "esp_zigbee_attribute.h"
#include "esp_zigbee_cluster.h"
#include "esp_zigbee_endpoint.h"
#include "aps/esp_zigbee_aps.h"
#include "bdb/esp_zigbee_bdb_commissioning.h"
#include "ha/esp_zigbee_ha_standard.h"
#include "nwk/esp_zigbee_nwk.h"
#include "zcl/esp_zigbee_zcl_basic.h"
#include "zcl/esp_zigbee_zcl_core.h"
#include "zcl/esp_zigbee_zcl_common.h"
#include "zcl/esp_zigbee_zcl_humidity_meas.h"
#include "zcl/esp_zigbee_zcl_pressure_meas.h"
#include "zcl/esp_zigbee_zcl_command.h"
#include "zcl/esp_zigbee_zcl_electrical_meas.h"
#include "zcl/esp_zigbee_zcl_groups.h"
#include "zcl/esp_zigbee_zcl_identify.h"
#include "zcl/esp_zigbee_zcl_level.h"
#include "zcl/esp_zigbee_zcl_on_off.h"
#include "zcl/esp_zigbee_zcl_occupancy_sensing.h"
#include "zcl/esp_zigbee_zcl_ias_zone.h"
#include "zcl/esp_zigbee_zcl_window_covering.h"
#include "zcl/esp_zigbee_zcl_scenes.h"
#include "zcl/esp_zigbee_zcl_thermostat.h"
#include "zcl/esp_zigbee_zcl_temperature_meas.h"
#include "zcl/esp_zigbee_zcl_door_lock.h"
#include "zdo/esp_zigbee_zdo_common.h"
#include "zdo/esp_zigbee_zdo_command.h"

static const char *TAG = "uzb_core";

typedef enum {
    UZB_ENDPOINT_KIND_NONE = 0,
    UZB_ENDPOINT_KIND_GENERIC = 1,
    UZB_ENDPOINT_KIND_ON_OFF_LIGHT = 2,
    UZB_ENDPOINT_KIND_ON_OFF_SWITCH = 3,
    UZB_ENDPOINT_KIND_DIMMABLE_SWITCH = 4,
    UZB_ENDPOINT_KIND_DIMMABLE_LIGHT = 5,
    UZB_ENDPOINT_KIND_COLOR_LIGHT = 6,
    UZB_ENDPOINT_KIND_TEMPERATURE_SENSOR = 7,
    UZB_ENDPOINT_KIND_HUMIDITY_SENSOR = 8,
    UZB_ENDPOINT_KIND_PRESSURE_SENSOR = 9,
    UZB_ENDPOINT_KIND_CLIMATE_SENSOR = 10,
    UZB_ENDPOINT_KIND_POWER_OUTLET = 11,
    UZB_ENDPOINT_KIND_POWER_OUTLET_METERING = 12,
    UZB_ENDPOINT_KIND_DOOR_LOCK = 13,
    UZB_ENDPOINT_KIND_DOOR_LOCK_CONTROLLER = 14,
    UZB_ENDPOINT_KIND_THERMOSTAT = 15,
    UZB_ENDPOINT_KIND_OCCUPANCY_SENSOR = 16,
    UZB_ENDPOINT_KIND_WINDOW_COVERING = 17,
    UZB_ENDPOINT_KIND_IAS_ZONE = 18,
} uzb_endpoint_kind_t;

static bool s_inited = false;
static bool s_started = false;
static bool s_endpoint_defined = false;
static bool s_device_registered = false;
static bool s_device_register_committed = false;
static bool s_action_handler_registered = false;
static bool s_form_network = false;
static esp_zb_nwk_device_type_t s_role = ESP_ZB_DEVICE_TYPE_COORDINATOR;
static bool s_install_code_policy = false;
static bool s_network_security_enabled = true;
static bool s_pending_network_key_valid = false;
static uint8_t s_pending_network_key[16] = {0};
static uint32_t s_primary_channel_mask = ESP_ZB_TRANSCEIVER_ALL_CHANNELS_MASK;
static bool s_pan_id_configured = false;
static uint16_t s_pan_id = 0;
static bool s_extended_pan_id_configured = false;
static uint8_t s_extended_pan_id[8] = {0};
static TaskHandle_t s_zb_task = NULL;
static esp_zb_endpoint_config_t s_endpoint_cfg = {0};
static uzb_endpoint_kind_t s_endpoint_kind = UZB_ENDPOINT_KIND_NONE;
static esp_zb_ep_list_t *s_registered_ep_list = NULL;
static bool s_basic_identity_configured = false;
static uint8_t s_basic_identity_endpoint = 1;
static uzb_basic_identity_cfg_t s_basic_identity_cfg = {0};
static uint16_t s_ias_zone_type = ESP_ZB_ZCL_IAS_ZONE_ZONETYPE_CONTACT_SWITCH;
static uint16_t s_window_current_position_lift = ESP_ZB_ZCL_WINDOW_COVERING_CURRENT_POSITION_LIFT_DEFAULT_VALUE;
static uint16_t s_window_current_position_tilt = ESP_ZB_ZCL_WINDOW_COVERING_CURRENT_POSITION_TILT_DEFAULT_VALUE;
static uint8_t s_window_current_position_lift_percentage = ESP_ZB_ZCL_WINDOW_COVERING_CURRENT_POSITION_LIFT_PERCENTAGE_DEFAULT_VALUE;
static uint8_t s_window_current_position_tilt_percentage = ESP_ZB_ZCL_WINDOW_COVERING_CURRENT_POSITION_TILT_PERCENTAGE_DEFAULT_VALUE;

#define UZB_EVENT_QUEUE_LEN (16)

static uzb_dispatch_request_cb_t s_dispatch_request_cb = NULL;
static bool s_dispatch_pending = false;

static uzb_event_t s_event_queue[UZB_EVENT_QUEUE_LEN];
static uint8_t s_event_head = 0;
static uint8_t s_event_tail = 0;
static uint8_t s_event_depth = 0;
static uzb_event_stats_t s_event_stats = {0};
static portMUX_TYPE s_event_lock = portMUX_INITIALIZER_UNLOCKED;
static bool s_last_joined_valid = false;
static uint16_t s_last_joined_short_addr = 0;
static bool s_network_formed = false;
static bool s_network_joined = false;
static portMUX_TYPE s_network_state_lock = portMUX_INITIALIZER_UNLOCKED;
static uzb_bind_table_snapshot_t s_bind_table_snapshot = {0};
static portMUX_TYPE s_bind_table_lock = portMUX_INITIALIZER_UNLOCKED;
static uzb_active_ep_snapshot_t s_active_ep_snapshot = {0};
static portMUX_TYPE s_active_ep_lock = portMUX_INITIALIZER_UNLOCKED;
static uzb_node_desc_snapshot_t s_node_desc_snapshot = {0};
static portMUX_TYPE s_node_desc_lock = portMUX_INITIALIZER_UNLOCKED;
static uzb_simple_desc_snapshot_t s_simple_desc_snapshot = {0};
static portMUX_TYPE s_simple_desc_lock = portMUX_INITIALIZER_UNLOCKED;
static uzb_power_desc_snapshot_t s_power_desc_snapshot = {0};
static portMUX_TYPE s_power_desc_lock = portMUX_INITIALIZER_UNLOCKED;

#define UZB_CUSTOM_CLUSTER_MAX (6)
#define UZB_CUSTOM_ATTR_MAX (24)
#define UZB_LOCAL_ENDPOINT_MAX (24)

typedef struct {
    bool used;
    uint16_t cluster_id;
    uint8_t cluster_role;
} uzb_custom_cluster_cfg_t;

typedef union {
    bool b;
    uint8_t u8;
    uint16_t u16;
    uint32_t u32;
    int8_t s8;
    int16_t s16;
    int32_t s32;
} uzb_custom_attr_storage_t;

typedef struct {
    bool used;
    uint16_t cluster_id;
    uint16_t attr_id;
    uint8_t attr_type;
    uint8_t attr_access;
    uzb_custom_attr_storage_t value;
} uzb_custom_attr_cfg_t;

static uzb_custom_cluster_cfg_t s_custom_clusters[UZB_CUSTOM_CLUSTER_MAX];
static uzb_custom_attr_cfg_t s_custom_attrs[UZB_CUSTOM_ATTR_MAX];
static uint8_t s_local_endpoints[UZB_LOCAL_ENDPOINT_MAX] = {0};
static uint8_t s_local_endpoint_count = 0;

static esp_zb_nwk_device_type_t uzb_role_to_zb(uzb_role_t role) {
    switch (role) {
        case UZB_ROLE_COORDINATOR:
            return ESP_ZB_DEVICE_TYPE_COORDINATOR;
        case UZB_ROLE_ROUTER:
            return ESP_ZB_DEVICE_TYPE_ROUTER;
        case UZB_ROLE_END_DEVICE:
            return ESP_ZB_DEVICE_TYPE_ED;
        default:
            return ESP_ZB_DEVICE_TYPE_COORDINATOR;
    }
}

static bool uzb_valid_endpoint_id(uint8_t endpoint) {
    return endpoint > 0 && endpoint < 0xF0;
}

static bool uzb_is_local_endpoint(uint8_t endpoint) {
    for (uint8_t i = 0; i < s_local_endpoint_count; ++i) {
        if (s_local_endpoints[i] == endpoint) {
            return true;
        }
    }
    return false;
}

static void uzb_track_local_endpoint(uint8_t endpoint) {
    if (!uzb_valid_endpoint_id(endpoint) || uzb_is_local_endpoint(endpoint)) {
        return;
    }
    if (s_local_endpoint_count >= UZB_LOCAL_ENDPOINT_MAX) {
        return;
    }
    s_local_endpoints[s_local_endpoint_count++] = endpoint;
}

static bool uzb_valid_channel_mask(uint32_t channel_mask) {
    uint32_t allowed = (uint32_t)ESP_ZB_TRANSCEIVER_ALL_CHANNELS_MASK;
    if (channel_mask == 0) {
        return false;
    }
    if ((channel_mask & ~allowed) != 0) {
        return false;
    }
    return (channel_mask & allowed) != 0;
}

static bool uzb_valid_custom_cluster_id(uint16_t cluster_id) {
    return cluster_id >= 0xFC00;
}

static bool uzb_valid_cluster_role(uint8_t cluster_role) {
    return cluster_role == ESP_ZB_ZCL_CLUSTER_SERVER_ROLE || cluster_role == ESP_ZB_ZCL_CLUSTER_CLIENT_ROLE;
}

static void uzb_custom_clusters_reset(void) {
    memset(s_custom_clusters, 0, sizeof(s_custom_clusters));
    memset(s_custom_attrs, 0, sizeof(s_custom_attrs));
}

static int uzb_find_custom_cluster_slot(uint16_t cluster_id, uint8_t cluster_role) {
    for (size_t i = 0; i < UZB_CUSTOM_CLUSTER_MAX; ++i) {
        if (!s_custom_clusters[i].used) {
            continue;
        }
        if (s_custom_clusters[i].cluster_id == cluster_id && s_custom_clusters[i].cluster_role == cluster_role) {
            return (int)i;
        }
    }
    return -1;
}

static int uzb_find_custom_attr_slot(uint16_t cluster_id, uint16_t attr_id) {
    for (size_t i = 0; i < UZB_CUSTOM_ATTR_MAX; ++i) {
        if (!s_custom_attrs[i].used) {
            continue;
        }
        if (s_custom_attrs[i].cluster_id == cluster_id && s_custom_attrs[i].attr_id == attr_id) {
            return (int)i;
        }
    }
    return -1;
}

static esp_err_t uzb_set_custom_attr_value(uzb_custom_attr_cfg_t *cfg, int32_t value) {
    if (cfg == NULL) {
        return ESP_ERR_INVALID_ARG;
    }
    switch (cfg->attr_type) {
        case ESP_ZB_ZCL_ATTR_TYPE_BOOL:
            cfg->value.b = (value != 0);
            return ESP_OK;
        case ESP_ZB_ZCL_ATTR_TYPE_U8:
        case ESP_ZB_ZCL_ATTR_TYPE_8BITMAP:
        case ESP_ZB_ZCL_ATTR_TYPE_8BIT_ENUM:
            if (value < 0 || value > 0xFF) {
                return ESP_ERR_INVALID_ARG;
            }
            cfg->value.u8 = (uint8_t)value;
            return ESP_OK;
        case ESP_ZB_ZCL_ATTR_TYPE_U16:
        case ESP_ZB_ZCL_ATTR_TYPE_16BITMAP:
        case ESP_ZB_ZCL_ATTR_TYPE_16BIT_ENUM:
        case ESP_ZB_ZCL_ATTR_TYPE_CLUSTER_ID:
        case ESP_ZB_ZCL_ATTR_TYPE_ATTRIBUTE_ID:
            if (value < 0 || value > 0xFFFF) {
                return ESP_ERR_INVALID_ARG;
            }
            cfg->value.u16 = (uint16_t)value;
            return ESP_OK;
        case ESP_ZB_ZCL_ATTR_TYPE_U32:
        case ESP_ZB_ZCL_ATTR_TYPE_32BITMAP:
        case ESP_ZB_ZCL_ATTR_TYPE_UTC_TIME:
        case ESP_ZB_ZCL_ATTR_TYPE_BACNET_OID:
            if (value < 0) {
                return ESP_ERR_INVALID_ARG;
            }
            cfg->value.u32 = (uint32_t)value;
            return ESP_OK;
        case ESP_ZB_ZCL_ATTR_TYPE_S8:
            if (value < INT8_MIN || value > INT8_MAX) {
                return ESP_ERR_INVALID_ARG;
            }
            cfg->value.s8 = (int8_t)value;
            return ESP_OK;
        case ESP_ZB_ZCL_ATTR_TYPE_S16:
            if (value < INT16_MIN || value > INT16_MAX) {
                return ESP_ERR_INVALID_ARG;
            }
            cfg->value.s16 = (int16_t)value;
            return ESP_OK;
        case ESP_ZB_ZCL_ATTR_TYPE_S32:
            cfg->value.s32 = value;
            return ESP_OK;
        default:
            return ESP_ERR_NOT_SUPPORTED;
    }
}

static void *uzb_custom_attr_value_ptr(uzb_custom_attr_cfg_t *cfg) {
    if (cfg == NULL) {
        return NULL;
    }
    switch (cfg->attr_type) {
        case ESP_ZB_ZCL_ATTR_TYPE_BOOL:
            return &cfg->value.b;
        case ESP_ZB_ZCL_ATTR_TYPE_U8:
        case ESP_ZB_ZCL_ATTR_TYPE_8BITMAP:
        case ESP_ZB_ZCL_ATTR_TYPE_8BIT_ENUM:
            return &cfg->value.u8;
        case ESP_ZB_ZCL_ATTR_TYPE_U16:
        case ESP_ZB_ZCL_ATTR_TYPE_16BITMAP:
        case ESP_ZB_ZCL_ATTR_TYPE_16BIT_ENUM:
        case ESP_ZB_ZCL_ATTR_TYPE_CLUSTER_ID:
        case ESP_ZB_ZCL_ATTR_TYPE_ATTRIBUTE_ID:
            return &cfg->value.u16;
        case ESP_ZB_ZCL_ATTR_TYPE_U32:
        case ESP_ZB_ZCL_ATTR_TYPE_32BITMAP:
        case ESP_ZB_ZCL_ATTR_TYPE_UTC_TIME:
        case ESP_ZB_ZCL_ATTR_TYPE_BACNET_OID:
            return &cfg->value.u32;
        case ESP_ZB_ZCL_ATTR_TYPE_S8:
            return &cfg->value.s8;
        case ESP_ZB_ZCL_ATTR_TYPE_S16:
            return &cfg->value.s16;
        case ESP_ZB_ZCL_ATTR_TYPE_S32:
            return &cfg->value.s32;
        default:
            return NULL;
    }
}

static bool uzb_valid_pascal_string(const uint8_t *value, uint8_t max_len) {
    if (value == NULL) {
        return false;
    }
    uint8_t len = value[0];
    return len <= max_len;
}

static esp_err_t uzb_basic_add_or_update_attr(esp_zb_attribute_list_t *basic_cluster, uint16_t attr_id, void *value, bool allow_update_fallback, bool optional_attr) {
    if (basic_cluster == NULL || value == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    if (allow_update_fallback) {
        // Prefer update first to avoid "already existed" warnings from add_attr.
        esp_err_t update_err = esp_zb_cluster_update_attr(basic_cluster, attr_id, value);
        if (update_err == ESP_OK) {
            return ESP_OK;
        }
        if (update_err != ESP_ERR_NOT_FOUND) {
            return update_err;
        }
    }

    esp_err_t add_err = esp_zb_basic_cluster_add_attr(basic_cluster, attr_id, value);
    if (add_err == ESP_OK) {
        return ESP_OK;
    }
    if (add_err == ESP_ERR_INVALID_ARG && optional_attr) {
        return ESP_OK;
    }
    return add_err;
}

static esp_err_t uzb_apply_basic_identity_to_ep_list(esp_zb_ep_list_t *ep_list) {
    if (!s_basic_identity_configured) {
        return ESP_OK;
    }
    if (s_basic_identity_endpoint != s_endpoint_cfg.endpoint) {
        return ESP_OK;
    }

    esp_zb_cluster_list_t *cluster_list = esp_zb_ep_list_get_ep(ep_list, s_basic_identity_endpoint);
    if (cluster_list == NULL) {
        return ESP_ERR_NOT_FOUND;
    }
    esp_zb_attribute_list_t *basic_cluster = esp_zb_cluster_list_get_cluster(cluster_list, ESP_ZB_ZCL_CLUSTER_ID_BASIC, ESP_ZB_ZCL_CLUSTER_SERVER_ROLE);
    if (basic_cluster == NULL) {
        return ESP_ERR_NOT_FOUND;
    }

    esp_err_t err = ESP_OK;
    if (s_basic_identity_cfg.has_manufacturer) {
        err = uzb_basic_add_or_update_attr(basic_cluster, ESP_ZB_ZCL_ATTR_BASIC_MANUFACTURER_NAME_ID, s_basic_identity_cfg.manufacturer, true, false);
        if (err != ESP_OK) {
            return err;
        }
    }
    if (s_basic_identity_cfg.has_model) {
        err = uzb_basic_add_or_update_attr(basic_cluster, ESP_ZB_ZCL_ATTR_BASIC_MODEL_IDENTIFIER_ID, s_basic_identity_cfg.model, true, false);
        if (err != ESP_OK) {
            return err;
        }
    }
    if (s_basic_identity_cfg.has_date_code) {
        err = uzb_basic_add_or_update_attr(basic_cluster, ESP_ZB_ZCL_ATTR_BASIC_DATE_CODE_ID, s_basic_identity_cfg.date_code, false, true);
        if (err != ESP_OK) {
            return err;
        }
    }
    if (s_basic_identity_cfg.has_sw_build_id) {
        err = uzb_basic_add_or_update_attr(basic_cluster, ESP_ZB_ZCL_ATTR_BASIC_SW_BUILD_ID, s_basic_identity_cfg.sw_build_id, false, true);
        if (err != ESP_OK) {
            return err;
        }
    }
    if (s_basic_identity_cfg.has_power_source) {
        err = uzb_basic_add_or_update_attr(basic_cluster, ESP_ZB_ZCL_ATTR_BASIC_POWER_SOURCE_ID, &s_basic_identity_cfg.power_source, true, false);
        if (err != ESP_OK) {
            return err;
        }
    }
    return ESP_OK;
}

static esp_err_t uzb_decode_attr_data(uint8_t attr_type, const void *data, uzb_attr_value_t *out_value) {
    if (out_value == NULL || data == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    out_value->zcl_type = attr_type;
    switch (attr_type) {
        case ESP_ZB_ZCL_ATTR_TYPE_BOOL: {
            bool v = *((const bool *)data);
            out_value->bool_value = v;
            out_value->int_value = v ? 1 : 0;
            out_value->uint_value = v ? 1U : 0U;
            return ESP_OK;
        }
        case ESP_ZB_ZCL_ATTR_TYPE_U8:
        case ESP_ZB_ZCL_ATTR_TYPE_8BITMAP:
        case ESP_ZB_ZCL_ATTR_TYPE_8BIT_ENUM: {
            uint8_t v = *((const uint8_t *)data);
            out_value->bool_value = (v != 0);
            out_value->int_value = (int32_t)v;
            out_value->uint_value = (uint32_t)v;
            return ESP_OK;
        }
        case ESP_ZB_ZCL_ATTR_TYPE_U16:
        case ESP_ZB_ZCL_ATTR_TYPE_16BITMAP:
        case ESP_ZB_ZCL_ATTR_TYPE_16BIT_ENUM:
        case ESP_ZB_ZCL_ATTR_TYPE_CLUSTER_ID:
        case ESP_ZB_ZCL_ATTR_TYPE_ATTRIBUTE_ID: {
            uint16_t v = *((const uint16_t *)data);
            out_value->bool_value = (v != 0);
            out_value->int_value = (int32_t)v;
            out_value->uint_value = (uint32_t)v;
            return ESP_OK;
        }
        case ESP_ZB_ZCL_ATTR_TYPE_U32:
        case ESP_ZB_ZCL_ATTR_TYPE_32BITMAP:
        case ESP_ZB_ZCL_ATTR_TYPE_UTC_TIME:
        case ESP_ZB_ZCL_ATTR_TYPE_BACNET_OID: {
            uint32_t v = *((const uint32_t *)data);
            out_value->bool_value = (v != 0);
            out_value->int_value = (int32_t)v;
            out_value->uint_value = v;
            return ESP_OK;
        }
        case ESP_ZB_ZCL_ATTR_TYPE_S8: {
            int8_t v = *((const int8_t *)data);
            out_value->bool_value = (v != 0);
            out_value->int_value = (int32_t)v;
            out_value->uint_value = (uint32_t)(uint8_t)v;
            return ESP_OK;
        }
        case ESP_ZB_ZCL_ATTR_TYPE_S16: {
            int16_t v = *((const int16_t *)data);
            out_value->bool_value = (v != 0);
            out_value->int_value = (int32_t)v;
            out_value->uint_value = (uint32_t)(uint16_t)v;
            return ESP_OK;
        }
        case ESP_ZB_ZCL_ATTR_TYPE_S32: {
            int32_t v = *((const int32_t *)data);
            out_value->bool_value = (v != 0);
            out_value->int_value = v;
            out_value->uint_value = (uint32_t)v;
            return ESP_OK;
        }
        default:
            return ESP_ERR_NOT_SUPPORTED;
    }
}

static esp_err_t uzb_decode_attr_value(const esp_zb_zcl_attr_t *attr, uzb_attr_value_t *out_value) {
    if (attr == NULL || out_value == NULL || attr->data_p == NULL) {
        return ESP_ERR_INVALID_ARG;
    }
    return uzb_decode_attr_data(attr->type, attr->data_p, out_value);
}

static esp_err_t uzb_read_basic_string_attr(uint8_t endpoint, uint16_t attr_id, uint8_t *out_value, uint8_t out_max_len, bool required) {
    if (out_value == NULL || out_max_len == 0) {
        return ESP_ERR_INVALID_ARG;
    }

    esp_zb_zcl_attr_t *attr = esp_zb_zcl_get_attribute(endpoint, ESP_ZB_ZCL_CLUSTER_ID_BASIC, ESP_ZB_ZCL_CLUSTER_SERVER_ROLE, attr_id);
    if (attr == NULL || attr->data_p == NULL) {
        return required ? ESP_ERR_NOT_FOUND : ESP_OK;
    }
    if (attr->type != ESP_ZB_ZCL_ATTR_TYPE_CHAR_STRING) {
        return required ? ESP_ERR_INVALID_ARG : ESP_OK;
    }

    const uint8_t *in = (const uint8_t *)attr->data_p;
    uint8_t len = in[0];
    if (len > out_max_len) {
        return ESP_ERR_INVALID_SIZE;
    }

    out_value[0] = len;
    if (len > 0) {
        memcpy(out_value + 1, in + 1, len);
    }
    return ESP_OK;
}

static void uzb_zigbee_task(void *arg) {
    (void)arg;
    ESP_LOGI(TAG, "zigbee task start");
    esp_zb_stack_main_loop();
    vTaskDelete(NULL);
}

static inline void uzb_event_lock(void) {
    taskENTER_CRITICAL(&s_event_lock);
}

static inline void uzb_event_unlock(void) {
    taskEXIT_CRITICAL(&s_event_lock);
}

static inline void uzb_bind_table_lock(void) {
    taskENTER_CRITICAL(&s_bind_table_lock);
}

static inline void uzb_bind_table_unlock(void) {
    taskEXIT_CRITICAL(&s_bind_table_lock);
}

static inline void uzb_active_ep_lock(void) {
    taskENTER_CRITICAL(&s_active_ep_lock);
}

static inline void uzb_active_ep_unlock(void) {
    taskEXIT_CRITICAL(&s_active_ep_lock);
}

static inline void uzb_node_desc_lock(void) {
    taskENTER_CRITICAL(&s_node_desc_lock);
}

static inline void uzb_node_desc_unlock(void) {
    taskEXIT_CRITICAL(&s_node_desc_lock);
}

static inline void uzb_simple_desc_lock(void) {
    taskENTER_CRITICAL(&s_simple_desc_lock);
}

static inline void uzb_simple_desc_unlock(void) {
    taskEXIT_CRITICAL(&s_simple_desc_lock);
}

static inline void uzb_power_desc_lock(void) {
    taskENTER_CRITICAL(&s_power_desc_lock);
}

static inline void uzb_power_desc_unlock(void) {
    taskEXIT_CRITICAL(&s_power_desc_lock);
}

static inline void uzb_network_state_lock(void) {
    taskENTER_CRITICAL(&s_network_state_lock);
}

static inline void uzb_network_state_unlock(void) {
    taskEXIT_CRITICAL(&s_network_state_lock);
}

static inline void uzb_set_network_state(bool formed, bool joined) {
    uzb_network_state_lock();
    s_network_formed = formed;
    s_network_joined = joined;
    uzb_network_state_unlock();
}

static inline void uzb_set_network_formed(bool formed) {
    uzb_network_state_lock();
    s_network_formed = formed;
    uzb_network_state_unlock();
}

static inline void uzb_set_network_joined(bool joined) {
    uzb_network_state_lock();
    s_network_joined = joined;
    uzb_network_state_unlock();
}

static void uzb_request_dispatch_if_needed(void) {
    bool request = false;
    uzb_dispatch_request_cb_t cb = NULL;

    uzb_event_lock();
    if (s_event_depth > 0 && !s_dispatch_pending && s_dispatch_request_cb != NULL) {
        s_dispatch_pending = true;
        cb = s_dispatch_request_cb;
        request = true;
    }
    uzb_event_unlock();

    if (!request) {
        return;
    }

    if (!cb()) {
        uzb_event_lock();
        s_dispatch_pending = false;
        s_event_stats.dropped_schedule_fail += 1;
        uzb_event_unlock();
    }
}

static void uzb_enqueue_event(const uzb_event_t *event) {
    if (event == NULL) {
        return;
    }

    bool queued = false;

    uzb_event_lock();
    if (s_event_depth >= UZB_EVENT_QUEUE_LEN) {
        s_event_stats.dropped_queue_full += 1;
    } else {
        s_event_queue[s_event_head] = *event;
        s_event_head = (uint8_t)((s_event_head + 1) % UZB_EVENT_QUEUE_LEN);
        s_event_depth += 1;
        s_event_stats.enqueued += 1;
        s_event_stats.depth = s_event_depth;
        if (s_event_depth > s_event_stats.max_depth) {
            s_event_stats.max_depth = s_event_depth;
        }
        queued = true;
    }
    uzb_event_unlock();

    if (queued) {
        uzb_request_dispatch_if_needed();
    }
}

static void uzb_enqueue_app_signal_event(uint16_t signal, int32_t status) {
    uzb_event_t event = {0};
    event.type = UZB_EVENT_TYPE_APP_SIGNAL;
    event.data.app_signal.signal = signal;
    event.data.app_signal.status = status;
    uzb_enqueue_event(&event);
}

static void uzb_enqueue_attr_set_event(const esp_zb_zcl_set_attr_value_message_t *message) {
    if (message == NULL) {
        return;
    }
    if (message->info.status != ESP_ZB_ZCL_STATUS_SUCCESS) {
        return;
    }

    uzb_event_t event = {0};
    event.type = UZB_EVENT_TYPE_ATTR_SET;
    event.data.attr_set.has_source = 0;
    event.data.attr_set.source_short_addr = 0xFFFF;
    event.data.attr_set.source_endpoint = 0;
    event.data.attr_set.endpoint = message->info.dst_endpoint;
    event.data.attr_set.cluster_id = message->info.cluster;
    event.data.attr_set.attr_id = message->attribute.id;
    event.data.attr_set.status = (int32_t)message->info.status;

    esp_err_t err = uzb_decode_attr_data(message->attribute.data.type, message->attribute.data.value, &event.data.attr_set.value);
    if (err != ESP_OK) {
        return;
    }

    uzb_enqueue_event(&event);
}

static void uzb_enqueue_report_attr_event(const esp_zb_zcl_report_attr_message_t *message) {
    if (message == NULL) {
        return;
    }
    if (message->status != ESP_ZB_ZCL_STATUS_SUCCESS) {
        return;
    }

    uzb_event_t event = {0};
    event.type = UZB_EVENT_TYPE_ATTR_SET;
    event.data.attr_set.has_source = 0;
    event.data.attr_set.source_short_addr = 0xFFFF;
    event.data.attr_set.source_endpoint = 0;
    event.data.attr_set.endpoint = message->src_endpoint;
    event.data.attr_set.cluster_id = message->cluster;
    event.data.attr_set.attr_id = message->attribute.id;
    event.data.attr_set.status = (int32_t)message->status;

    if (message->src_address.addr_type == ESP_ZB_ZCL_ADDR_TYPE_SHORT) {
        event.data.attr_set.has_source = 1;
        event.data.attr_set.source_short_addr = message->src_address.u.short_addr;
        event.data.attr_set.source_endpoint = message->src_endpoint;
    }

    esp_err_t err = uzb_decode_attr_data(message->attribute.data.type, message->attribute.data.value, &event.data.attr_set.value);
    if (err != ESP_OK) {
        return;
    }

    uzb_enqueue_event(&event);
}

static inline void uzb_update_last_joined_short_addr(uint16_t short_addr) {
    if (short_addr == 0 || short_addr == 0xFFFF) {
        return;
    }
    s_last_joined_short_addr = short_addr;
    s_last_joined_valid = true;
    ESP_LOGI(TAG, "last_joined_short=0x%04x", short_addr);
}

static inline void uzb_clear_last_joined_short_addr(uint16_t short_addr) {
    if (!s_last_joined_valid) {
        return;
    }
    if (short_addr != s_last_joined_short_addr) {
        return;
    }
    s_last_joined_valid = false;
    ESP_LOGI(TAG, "last_joined_short cleared (0x%04x left)", short_addr);
}

static void uzb_binding_table_response_cb(const esp_zb_zdo_binding_table_info_t *table_info, void *user_ctx) {
    (void)user_ctx;
    if (table_info == NULL) {
        return;
    }

    uzb_bind_table_lock();
    memset(&s_bind_table_snapshot, 0, sizeof(s_bind_table_snapshot));
    s_bind_table_snapshot.valid = 1;
    s_bind_table_snapshot.status = table_info->status;
    s_bind_table_snapshot.index = table_info->index;
    s_bind_table_snapshot.total = table_info->total;
    s_bind_table_snapshot.count = table_info->count;

    uint8_t stored = 0;
    const esp_zb_zdo_binding_table_record_t *rec = table_info->record;
    while (rec != NULL && stored < UZB_BIND_TABLE_MAX_RECORDS) {
        uzb_bind_table_record_t *out = &s_bind_table_snapshot.records[stored];
        memcpy(out->src_ieee_addr, rec->src_address, sizeof(out->src_ieee_addr));
        out->src_endpoint = rec->src_endp;
        out->cluster_id = rec->cluster_id;
        out->dst_addr_mode = rec->dst_addr_mode;
        out->has_dst_endpoint = (rec->dst_addr_mode == ESP_ZB_ZDO_BIND_DST_ADDR_MODE_64_BIT_EXTENDED) ? 1 : 0;
        out->dst_endpoint = rec->dst_endp;

        if (rec->dst_addr_mode == ESP_ZB_ZDO_BIND_DST_ADDR_MODE_16_BIT_GROUP) {
            out->has_dst_short_addr = 1;
            out->dst_short_addr = rec->dst_address.addr_short;
        } else if (rec->dst_addr_mode == ESP_ZB_ZDO_BIND_DST_ADDR_MODE_64_BIT_EXTENDED) {
            out->has_dst_ieee_addr = 1;
            memcpy(out->dst_ieee_addr, rec->dst_address.addr_long, sizeof(out->dst_ieee_addr));
        }

        stored += 1;
        rec = rec->next;
    }
    s_bind_table_snapshot.record_count = stored;
    uzb_bind_table_unlock();

    ESP_LOGI(TAG,
             "bind_table rsp status=0x%02x index=%u total=%u count=%u stored=%u",
             (unsigned int)table_info->status,
             (unsigned int)table_info->index,
             (unsigned int)table_info->total,
             (unsigned int)table_info->count,
             (unsigned int)stored);
}

static void uzb_active_ep_response_cb(esp_zb_zdp_status_t zdo_status, uint8_t ep_count, uint8_t *ep_id_list, void *user_ctx) {
    (void)user_ctx;

    uzb_active_ep_lock();
    memset(&s_active_ep_snapshot, 0, sizeof(s_active_ep_snapshot));
    s_active_ep_snapshot.valid = 1;
    s_active_ep_snapshot.status = (uint8_t)zdo_status;
    uint8_t count = ep_count;
    if (count > UZB_ACTIVE_EP_MAX_ENDPOINTS) {
        count = UZB_ACTIVE_EP_MAX_ENDPOINTS;
    }
    s_active_ep_snapshot.count = count;
    if (count > 0 && ep_id_list != NULL) {
        memcpy(s_active_ep_snapshot.endpoints, ep_id_list, count);
    }
    uzb_active_ep_unlock();

    ESP_LOGI(TAG,
             "active_ep rsp status=0x%02x count=%u stored=%u",
             (unsigned int)zdo_status,
             (unsigned int)ep_count,
             (unsigned int)count);
}

static void uzb_node_desc_response_cb(esp_zb_zdp_status_t zdo_status, uint16_t addr, esp_zb_af_node_desc_t *node_desc, void *user_ctx) {
    (void)user_ctx;

    uzb_node_desc_lock();
    memset(&s_node_desc_snapshot, 0, sizeof(s_node_desc_snapshot));
    s_node_desc_snapshot.valid = 1;
    s_node_desc_snapshot.status = (uint8_t)zdo_status;
    s_node_desc_snapshot.addr = addr;
    if (node_desc != NULL) {
        s_node_desc_snapshot.has_desc = 1;
        s_node_desc_snapshot.node_desc_flags = node_desc->node_desc_flags;
        s_node_desc_snapshot.mac_capability_flags = node_desc->mac_capability_flags;
        s_node_desc_snapshot.manufacturer_code = node_desc->manufacturer_code;
        s_node_desc_snapshot.max_buf_size = node_desc->max_buf_size;
        s_node_desc_snapshot.max_incoming_transfer_size = node_desc->max_incoming_transfer_size;
        s_node_desc_snapshot.server_mask = node_desc->server_mask;
        s_node_desc_snapshot.max_outgoing_transfer_size = node_desc->max_outgoing_transfer_size;
        s_node_desc_snapshot.desc_capability_field = node_desc->desc_capability_field;
    }
    uzb_node_desc_unlock();

    ESP_LOGI(TAG,
             "node_desc rsp status=0x%02x addr=0x%04x has_desc=%u",
             (unsigned int)zdo_status,
             (unsigned int)addr,
             (unsigned int)(node_desc != NULL ? 1 : 0));
}

static void uzb_simple_desc_response_cb(esp_zb_zdp_status_t zdo_status, esp_zb_af_simple_desc_1_1_t *simple_desc, void *user_ctx) {
    (void)user_ctx;

    uzb_simple_desc_lock();
    uint16_t req_addr = s_simple_desc_snapshot.addr;
    memset(&s_simple_desc_snapshot, 0, sizeof(s_simple_desc_snapshot));
    s_simple_desc_snapshot.valid = 1;
    s_simple_desc_snapshot.status = (uint8_t)zdo_status;
    s_simple_desc_snapshot.addr = req_addr;

    if (simple_desc != NULL) {
        s_simple_desc_snapshot.has_desc = 1;
        s_simple_desc_snapshot.endpoint = simple_desc->endpoint;
        s_simple_desc_snapshot.profile_id = simple_desc->app_profile_id;
        s_simple_desc_snapshot.device_id = simple_desc->app_device_id;
        s_simple_desc_snapshot.device_version = (uint8_t)(simple_desc->app_device_version & 0x0F);

        uint8_t in_count = simple_desc->app_input_cluster_count;
        uint8_t out_count = simple_desc->app_output_cluster_count;
        if (in_count > UZB_SIMPLE_DESC_MAX_CLUSTERS) {
            in_count = UZB_SIMPLE_DESC_MAX_CLUSTERS;
        }
        if (out_count > UZB_SIMPLE_DESC_MAX_CLUSTERS) {
            out_count = UZB_SIMPLE_DESC_MAX_CLUSTERS;
        }
        s_simple_desc_snapshot.input_count = in_count;
        s_simple_desc_snapshot.output_count = out_count;

        if (simple_desc->app_cluster_list != NULL) {
            for (uint8_t i = 0; i < in_count; ++i) {
                s_simple_desc_snapshot.input_clusters[i] = simple_desc->app_cluster_list[i];
            }
            for (uint8_t i = 0; i < out_count; ++i) {
                s_simple_desc_snapshot.output_clusters[i] = simple_desc->app_cluster_list[simple_desc->app_input_cluster_count + i];
            }
        }
    }
    uzb_simple_desc_unlock();

    ESP_LOGI(TAG,
             "simple_desc rsp status=0x%02x has_desc=%u",
             (unsigned int)zdo_status,
             (unsigned int)(simple_desc != NULL ? 1 : 0));
}

static void uzb_power_desc_response_cb(esp_zb_zdo_power_desc_rsp_t *power_desc, void *user_ctx) {
    (void)user_ctx;
    if (power_desc == NULL) {
        return;
    }

    uzb_power_desc_lock();
    memset(&s_power_desc_snapshot, 0, sizeof(s_power_desc_snapshot));
    s_power_desc_snapshot.valid = 1;
    s_power_desc_snapshot.status = power_desc->status;
    s_power_desc_snapshot.addr = power_desc->nwk_addr_of_interest;
    s_power_desc_snapshot.has_desc = 1;
    s_power_desc_snapshot.current_power_mode = power_desc->desc.current_power_mode;
    s_power_desc_snapshot.available_power_sources = power_desc->desc.available_power_sources;
    s_power_desc_snapshot.current_power_source = power_desc->desc.current_power_source;
    s_power_desc_snapshot.current_power_source_level = power_desc->desc.current_power_source_level;
    uzb_power_desc_unlock();

    ESP_LOGI(TAG,
             "power_desc rsp status=0x%02x addr=0x%04x",
             (unsigned int)power_desc->status,
             (unsigned int)power_desc->nwk_addr_of_interest);
}

static esp_err_t uzb_action_handler(esp_zb_core_action_callback_id_t callback_id, const void *message) {
    if (callback_id == ESP_ZB_CORE_SET_ATTR_VALUE_CB_ID) {
        uzb_enqueue_attr_set_event((const esp_zb_zcl_set_attr_value_message_t *)message);
    } else if (callback_id == ESP_ZB_CORE_REPORT_ATTR_CB_ID) {
        uzb_enqueue_report_attr_event((const esp_zb_zcl_report_attr_message_t *)message);
    }
    return ESP_OK;
}

esp_err_t uzb_core_init(uzb_role_t role) {
    if (s_inited) {
        s_role = uzb_role_to_zb(role);
        return ESP_OK;
    }

    s_role = uzb_role_to_zb(role);

    esp_zb_platform_config_t platform_cfg = {0};
    platform_cfg.radio_config.radio_mode = ZB_RADIO_MODE_NATIVE;
    platform_cfg.host_config.host_connection_mode = ZB_HOST_CONNECTION_MODE_NONE;
    esp_err_t err = esp_zb_platform_config(&platform_cfg);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "platform config failed: %s", esp_err_to_name(err));
        return err;
    }

    esp_zb_cfg_t zb_cfg = {0};
    zb_cfg.esp_zb_role = s_role;
    zb_cfg.install_code_policy = s_install_code_policy;
    if (s_role == ESP_ZB_DEVICE_TYPE_ED) {
        zb_cfg.nwk_cfg.zed_cfg.ed_timeout = ESP_ZB_ED_AGING_TIMEOUT_64MIN;
        zb_cfg.nwk_cfg.zed_cfg.keep_alive = 3000;
    } else {
        zb_cfg.nwk_cfg.zczr_cfg.max_children = 10;
    }

    esp_zb_init(&zb_cfg);

    if (!esp_zb_lock_acquire(pdMS_TO_TICKS(5000))) {
        ESP_LOGE(TAG, "lock acquire failed during init");
        return ESP_ERR_TIMEOUT;
    }
    if (s_extended_pan_id_configured) {
        esp_zb_set_extended_pan_id(s_extended_pan_id);
    }
    if (s_pan_id_configured) {
        esp_zb_set_pan_id(s_pan_id);
    }
    err = esp_zb_set_primary_network_channel_set(s_primary_channel_mask);
    if (err == ESP_OK) {
        err = esp_zb_secur_ic_only_enable(s_install_code_policy);
    }
    if (err == ESP_OK) {
        err = esp_zb_secur_network_security_enable(s_network_security_enabled);
    }
    if (err == ESP_OK && s_pending_network_key_valid) {
        err = esp_zb_secur_network_key_set(s_pending_network_key);
    }
    esp_zb_lock_release();
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "set channel mask failed: %s", esp_err_to_name(err));
        return err;
    }

    s_inited = true;
    return ESP_OK;
}

esp_err_t uzb_core_create_endpoint(uint8_t endpoint, uint16_t device_id, uint16_t profile_id) {
    if (!s_inited) {
        return ESP_ERR_INVALID_STATE;
    }
    if (s_started) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!uzb_valid_endpoint_id(endpoint) || profile_id == 0) {
        return ESP_ERR_INVALID_ARG;
    }

    s_endpoint_cfg.endpoint = endpoint;
    s_endpoint_cfg.app_profile_id = profile_id;
    s_endpoint_cfg.app_device_id = device_id;
    s_endpoint_cfg.app_device_version = 0;
    s_endpoint_defined = true;
    s_endpoint_kind = UZB_ENDPOINT_KIND_GENERIC;
    return ESP_OK;
}

esp_err_t uzb_core_create_on_off_light_endpoint(uint8_t endpoint) {
    if (!s_inited) {
        return ESP_ERR_INVALID_STATE;
    }
    if (s_started) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!uzb_valid_endpoint_id(endpoint)) {
        return ESP_ERR_INVALID_ARG;
    }

    s_endpoint_cfg.endpoint = endpoint;
    s_endpoint_cfg.app_profile_id = ESP_ZB_AF_HA_PROFILE_ID;
    s_endpoint_cfg.app_device_id = ESP_ZB_HA_ON_OFF_LIGHT_DEVICE_ID;
    s_endpoint_cfg.app_device_version = 0;
    s_endpoint_defined = true;
    s_endpoint_kind = UZB_ENDPOINT_KIND_ON_OFF_LIGHT;
    return ESP_OK;
}

esp_err_t uzb_core_create_on_off_switch_endpoint(uint8_t endpoint) {
    if (!s_inited) {
        return ESP_ERR_INVALID_STATE;
    }
    if (s_started) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!uzb_valid_endpoint_id(endpoint)) {
        return ESP_ERR_INVALID_ARG;
    }

    s_endpoint_cfg.endpoint = endpoint;
    s_endpoint_cfg.app_profile_id = ESP_ZB_AF_HA_PROFILE_ID;
    s_endpoint_cfg.app_device_id = ESP_ZB_HA_ON_OFF_SWITCH_DEVICE_ID;
    s_endpoint_cfg.app_device_version = 0;
    s_endpoint_defined = true;
    s_endpoint_kind = UZB_ENDPOINT_KIND_ON_OFF_SWITCH;
    return ESP_OK;
}

esp_err_t uzb_core_create_dimmable_switch_endpoint(uint8_t endpoint) {
    if (!s_inited) {
        return ESP_ERR_INVALID_STATE;
    }
    if (s_started) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!uzb_valid_endpoint_id(endpoint)) {
        return ESP_ERR_INVALID_ARG;
    }

    s_endpoint_cfg.endpoint = endpoint;
    s_endpoint_cfg.app_profile_id = ESP_ZB_AF_HA_PROFILE_ID;
    s_endpoint_cfg.app_device_id = ESP_ZB_HA_DIMMER_SWITCH_DEVICE_ID;
    s_endpoint_cfg.app_device_version = 0;
    s_endpoint_defined = true;
    s_endpoint_kind = UZB_ENDPOINT_KIND_DIMMABLE_SWITCH;
    return ESP_OK;
}

esp_err_t uzb_core_create_dimmable_light_endpoint(uint8_t endpoint) {
    if (!s_inited) {
        return ESP_ERR_INVALID_STATE;
    }
    if (s_started) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!uzb_valid_endpoint_id(endpoint)) {
        return ESP_ERR_INVALID_ARG;
    }

    s_endpoint_cfg.endpoint = endpoint;
    s_endpoint_cfg.app_profile_id = ESP_ZB_AF_HA_PROFILE_ID;
    s_endpoint_cfg.app_device_id = ESP_ZB_HA_DIMMABLE_LIGHT_DEVICE_ID;
    s_endpoint_cfg.app_device_version = 0;
    s_endpoint_defined = true;
    s_endpoint_kind = UZB_ENDPOINT_KIND_DIMMABLE_LIGHT;
    return ESP_OK;
}

esp_err_t uzb_core_create_color_light_endpoint(uint8_t endpoint) {
    if (!s_inited) {
        return ESP_ERR_INVALID_STATE;
    }
    if (s_started) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!uzb_valid_endpoint_id(endpoint)) {
        return ESP_ERR_INVALID_ARG;
    }

    s_endpoint_cfg.endpoint = endpoint;
    s_endpoint_cfg.app_profile_id = ESP_ZB_AF_HA_PROFILE_ID;
    s_endpoint_cfg.app_device_id = ESP_ZB_HA_COLOR_DIMMABLE_LIGHT_DEVICE_ID;
    s_endpoint_cfg.app_device_version = 0;
    s_endpoint_defined = true;
    s_endpoint_kind = UZB_ENDPOINT_KIND_COLOR_LIGHT;
    return ESP_OK;
}

esp_err_t uzb_core_create_temperature_sensor_endpoint(uint8_t endpoint) {
    if (!s_inited) {
        return ESP_ERR_INVALID_STATE;
    }
    if (s_started) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!uzb_valid_endpoint_id(endpoint)) {
        return ESP_ERR_INVALID_ARG;
    }

    s_endpoint_cfg.endpoint = endpoint;
    s_endpoint_cfg.app_profile_id = ESP_ZB_AF_HA_PROFILE_ID;
    s_endpoint_cfg.app_device_id = ESP_ZB_HA_TEMPERATURE_SENSOR_DEVICE_ID;
    s_endpoint_cfg.app_device_version = 0;
    s_endpoint_defined = true;
    s_endpoint_kind = UZB_ENDPOINT_KIND_TEMPERATURE_SENSOR;
    return ESP_OK;
}

esp_err_t uzb_core_create_humidity_sensor_endpoint(uint8_t endpoint) {
    if (!s_inited) {
        return ESP_ERR_INVALID_STATE;
    }
    if (s_started) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!uzb_valid_endpoint_id(endpoint)) {
        return ESP_ERR_INVALID_ARG;
    }

    s_endpoint_cfg.endpoint = endpoint;
    s_endpoint_cfg.app_profile_id = ESP_ZB_AF_HA_PROFILE_ID;
    s_endpoint_cfg.app_device_id = ESP_ZB_HA_SIMPLE_SENSOR_DEVICE_ID;
    s_endpoint_cfg.app_device_version = 0;
    s_endpoint_defined = true;
    s_endpoint_kind = UZB_ENDPOINT_KIND_HUMIDITY_SENSOR;
    return ESP_OK;
}

esp_err_t uzb_core_create_pressure_sensor_endpoint(uint8_t endpoint) {
    if (!s_inited) {
        return ESP_ERR_INVALID_STATE;
    }
    if (s_started) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!uzb_valid_endpoint_id(endpoint)) {
        return ESP_ERR_INVALID_ARG;
    }

    s_endpoint_cfg.endpoint = endpoint;
    s_endpoint_cfg.app_profile_id = ESP_ZB_AF_HA_PROFILE_ID;
    s_endpoint_cfg.app_device_id = ESP_ZB_HA_SIMPLE_SENSOR_DEVICE_ID;
    s_endpoint_cfg.app_device_version = 0;
    s_endpoint_defined = true;
    s_endpoint_kind = UZB_ENDPOINT_KIND_PRESSURE_SENSOR;
    return ESP_OK;
}

esp_err_t uzb_core_create_climate_sensor_endpoint(uint8_t endpoint) {
    if (!s_inited) {
        return ESP_ERR_INVALID_STATE;
    }
    if (s_started) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!uzb_valid_endpoint_id(endpoint)) {
        return ESP_ERR_INVALID_ARG;
    }

    s_endpoint_cfg.endpoint = endpoint;
    s_endpoint_cfg.app_profile_id = ESP_ZB_AF_HA_PROFILE_ID;
    s_endpoint_cfg.app_device_id = ESP_ZB_HA_SIMPLE_SENSOR_DEVICE_ID;
    s_endpoint_cfg.app_device_version = 0;
    s_endpoint_defined = true;
    s_endpoint_kind = UZB_ENDPOINT_KIND_CLIMATE_SENSOR;
    return ESP_OK;
}

esp_err_t uzb_core_create_power_outlet_endpoint(uint8_t endpoint, bool with_metering) {
    if (!s_inited) {
        return ESP_ERR_INVALID_STATE;
    }
    if (s_started) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!uzb_valid_endpoint_id(endpoint)) {
        return ESP_ERR_INVALID_ARG;
    }

    s_endpoint_cfg.endpoint = endpoint;
    s_endpoint_cfg.app_profile_id = ESP_ZB_AF_HA_PROFILE_ID;
    s_endpoint_cfg.app_device_id = ESP_ZB_HA_MAINS_POWER_OUTLET_DEVICE_ID;
    s_endpoint_cfg.app_device_version = 0;
    s_endpoint_defined = true;
    s_endpoint_kind = with_metering ? UZB_ENDPOINT_KIND_POWER_OUTLET_METERING : UZB_ENDPOINT_KIND_POWER_OUTLET;
    return ESP_OK;
}

esp_err_t uzb_core_create_door_lock_endpoint(uint8_t endpoint) {
    if (!s_inited) {
        return ESP_ERR_INVALID_STATE;
    }
    if (s_started) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!uzb_valid_endpoint_id(endpoint)) {
        return ESP_ERR_INVALID_ARG;
    }

    s_endpoint_cfg.endpoint = endpoint;
    s_endpoint_cfg.app_profile_id = ESP_ZB_AF_HA_PROFILE_ID;
    s_endpoint_cfg.app_device_id = ESP_ZB_HA_DOOR_LOCK_DEVICE_ID;
    s_endpoint_cfg.app_device_version = 0;
    s_endpoint_defined = true;
    s_endpoint_kind = UZB_ENDPOINT_KIND_DOOR_LOCK;
    return ESP_OK;
}

esp_err_t uzb_core_create_door_lock_controller_endpoint(uint8_t endpoint) {
    if (!s_inited) {
        return ESP_ERR_INVALID_STATE;
    }
    if (s_started) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!uzb_valid_endpoint_id(endpoint)) {
        return ESP_ERR_INVALID_ARG;
    }

    s_endpoint_cfg.endpoint = endpoint;
    s_endpoint_cfg.app_profile_id = ESP_ZB_AF_HA_PROFILE_ID;
    s_endpoint_cfg.app_device_id = ESP_ZB_HA_DOOR_LOCK_CONTROLLER_DEVICE_ID;
    s_endpoint_cfg.app_device_version = 0;
    s_endpoint_defined = true;
    s_endpoint_kind = UZB_ENDPOINT_KIND_DOOR_LOCK_CONTROLLER;
    return ESP_OK;
}

esp_err_t uzb_core_create_thermostat_endpoint(uint8_t endpoint) {
    if (!s_inited) {
        return ESP_ERR_INVALID_STATE;
    }
    if (s_started) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!uzb_valid_endpoint_id(endpoint)) {
        return ESP_ERR_INVALID_ARG;
    }

    s_endpoint_cfg.endpoint = endpoint;
    s_endpoint_cfg.app_profile_id = ESP_ZB_AF_HA_PROFILE_ID;
    s_endpoint_cfg.app_device_id = ESP_ZB_HA_THERMOSTAT_DEVICE_ID;
    s_endpoint_cfg.app_device_version = 0;
    s_endpoint_defined = true;
    s_endpoint_kind = UZB_ENDPOINT_KIND_THERMOSTAT;
    return ESP_OK;
}

esp_err_t uzb_core_create_occupancy_sensor_endpoint(uint8_t endpoint) {
    if (!s_inited) {
        return ESP_ERR_INVALID_STATE;
    }
    if (s_started) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!uzb_valid_endpoint_id(endpoint)) {
        return ESP_ERR_INVALID_ARG;
    }

    s_endpoint_cfg.endpoint = endpoint;
    s_endpoint_cfg.app_profile_id = ESP_ZB_AF_HA_PROFILE_ID;
    s_endpoint_cfg.app_device_id = ESP_ZB_HA_SIMPLE_SENSOR_DEVICE_ID;
    s_endpoint_cfg.app_device_version = 0;
    s_endpoint_defined = true;
    s_endpoint_kind = UZB_ENDPOINT_KIND_OCCUPANCY_SENSOR;
    return ESP_OK;
}

esp_err_t uzb_core_create_window_covering_endpoint(uint8_t endpoint) {
    if (!s_inited) {
        return ESP_ERR_INVALID_STATE;
    }
    if (s_started) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!uzb_valid_endpoint_id(endpoint)) {
        return ESP_ERR_INVALID_ARG;
    }

    s_endpoint_cfg.endpoint = endpoint;
    s_endpoint_cfg.app_profile_id = ESP_ZB_AF_HA_PROFILE_ID;
    s_endpoint_cfg.app_device_id = ESP_ZB_HA_WINDOW_COVERING_DEVICE_ID;
    s_endpoint_cfg.app_device_version = 0;
    s_endpoint_defined = true;
    s_endpoint_kind = UZB_ENDPOINT_KIND_WINDOW_COVERING;
    s_window_current_position_lift = ESP_ZB_ZCL_WINDOW_COVERING_CURRENT_POSITION_LIFT_DEFAULT_VALUE;
    s_window_current_position_tilt = ESP_ZB_ZCL_WINDOW_COVERING_CURRENT_POSITION_TILT_DEFAULT_VALUE;
    s_window_current_position_lift_percentage = ESP_ZB_ZCL_WINDOW_COVERING_CURRENT_POSITION_LIFT_PERCENTAGE_DEFAULT_VALUE;
    s_window_current_position_tilt_percentage = ESP_ZB_ZCL_WINDOW_COVERING_CURRENT_POSITION_TILT_PERCENTAGE_DEFAULT_VALUE;
    return ESP_OK;
}

esp_err_t uzb_core_create_ias_zone_endpoint(uint8_t endpoint, uint16_t zone_type) {
    if (!s_inited) {
        return ESP_ERR_INVALID_STATE;
    }
    if (s_started) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!uzb_valid_endpoint_id(endpoint)) {
        return ESP_ERR_INVALID_ARG;
    }
    if (zone_type == ESP_ZB_ZCL_IAS_ZONE_ZONETYPE_INVALID) {
        return ESP_ERR_INVALID_ARG;
    }

    s_endpoint_cfg.endpoint = endpoint;
    s_endpoint_cfg.app_profile_id = ESP_ZB_AF_HA_PROFILE_ID;
    s_endpoint_cfg.app_device_id = ESP_ZB_HA_IAS_ZONE_ID;
    s_endpoint_cfg.app_device_version = 0;
    s_endpoint_defined = true;
    s_endpoint_kind = UZB_ENDPOINT_KIND_IAS_ZONE;
    s_ias_zone_type = zone_type;
    return ESP_OK;
}

esp_err_t uzb_core_create_contact_sensor_endpoint(uint8_t endpoint) {
    return uzb_core_create_ias_zone_endpoint(endpoint, ESP_ZB_ZCL_IAS_ZONE_ZONETYPE_CONTACT_SWITCH);
}

esp_err_t uzb_core_create_motion_sensor_endpoint(uint8_t endpoint) {
    return uzb_core_create_ias_zone_endpoint(endpoint, ESP_ZB_ZCL_IAS_ZONE_ZONETYPE_MOTION);
}

esp_err_t uzb_core_clear_custom_clusters(void) {
    if (s_started) {
        return ESP_ERR_INVALID_STATE;
    }
    uzb_custom_clusters_reset();
    return ESP_OK;
}

esp_err_t uzb_core_add_custom_cluster(uint16_t cluster_id, uint8_t cluster_role) {
    if (!s_inited) {
        return ESP_ERR_INVALID_STATE;
    }
    if (s_started) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!uzb_valid_custom_cluster_id(cluster_id) || !uzb_valid_cluster_role(cluster_role)) {
        return ESP_ERR_INVALID_ARG;
    }

    if (uzb_find_custom_cluster_slot(cluster_id, cluster_role) >= 0) {
        return ESP_OK;
    }

    for (size_t i = 0; i < UZB_CUSTOM_CLUSTER_MAX; ++i) {
        if (s_custom_clusters[i].used) {
            continue;
        }
        s_custom_clusters[i].used = true;
        s_custom_clusters[i].cluster_id = cluster_id;
        s_custom_clusters[i].cluster_role = cluster_role;
        return ESP_OK;
    }
    return ESP_ERR_NO_MEM;
}

esp_err_t uzb_core_add_custom_attr(uint16_t cluster_id, uint16_t attr_id, uint8_t attr_type, uint8_t attr_access, int32_t initial_value) {
    if (!s_inited) {
        return ESP_ERR_INVALID_STATE;
    }
    if (s_started) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!uzb_valid_custom_cluster_id(cluster_id) || attr_access == 0) {
        return ESP_ERR_INVALID_ARG;
    }
    if (uzb_find_custom_cluster_slot(cluster_id, ESP_ZB_ZCL_CLUSTER_SERVER_ROLE) < 0 &&
        uzb_find_custom_cluster_slot(cluster_id, ESP_ZB_ZCL_CLUSTER_CLIENT_ROLE) < 0) {
        esp_err_t add_err = uzb_core_add_custom_cluster(cluster_id, ESP_ZB_ZCL_CLUSTER_SERVER_ROLE);
        if (add_err != ESP_OK) {
            return add_err;
        }
    }

    int attr_slot = uzb_find_custom_attr_slot(cluster_id, attr_id);
    if (attr_slot < 0) {
        for (size_t i = 0; i < UZB_CUSTOM_ATTR_MAX; ++i) {
            if (s_custom_attrs[i].used) {
                continue;
            }
            attr_slot = (int)i;
            break;
        }
    }
    if (attr_slot < 0) {
        return ESP_ERR_NO_MEM;
    }

    uzb_custom_attr_cfg_t *cfg = &s_custom_attrs[attr_slot];
    cfg->used = true;
    cfg->cluster_id = cluster_id;
    cfg->attr_id = attr_id;
    cfg->attr_type = attr_type;
    cfg->attr_access = attr_access;
    return uzb_set_custom_attr_value(cfg, initial_value);
}

esp_err_t uzb_core_set_basic_identity(uint8_t endpoint, const uzb_basic_identity_cfg_t *cfg) {
    if (cfg == NULL) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!s_inited) {
        return ESP_ERR_INVALID_STATE;
    }
    if (s_started) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!uzb_valid_endpoint_id(endpoint)) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!cfg->has_manufacturer || !cfg->has_model) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!uzb_valid_pascal_string(cfg->manufacturer, UZB_BASIC_STR_MAX_MANUFACTURER)) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!uzb_valid_pascal_string(cfg->model, UZB_BASIC_STR_MAX_MODEL)) {
        return ESP_ERR_INVALID_ARG;
    }
    if (cfg->has_date_code && !uzb_valid_pascal_string(cfg->date_code, UZB_BASIC_STR_MAX_DATE_CODE)) {
        return ESP_ERR_INVALID_ARG;
    }
    if (cfg->has_sw_build_id && !uzb_valid_pascal_string(cfg->sw_build_id, UZB_BASIC_STR_MAX_SW_BUILD_ID)) {
        return ESP_ERR_INVALID_ARG;
    }
    if (cfg->has_power_source && cfg->power_source > ESP_ZB_ZCL_BASIC_POWER_SOURCE_EMERGENCY_MAINS_TRANSF) {
        return ESP_ERR_INVALID_ARG;
    }

    s_basic_identity_cfg = *cfg;
    s_basic_identity_endpoint = endpoint;
    s_basic_identity_configured = true;
    return ESP_OK;
}

esp_err_t uzb_core_get_basic_identity(uint8_t endpoint, uzb_basic_identity_cfg_t *out_cfg) {
    if (out_cfg == NULL) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!s_device_registered) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!uzb_valid_endpoint_id(endpoint)) {
        return ESP_ERR_INVALID_ARG;
    }

    if (!esp_zb_lock_acquire(pdMS_TO_TICKS(5000))) {
        ESP_LOGE(TAG, "lock acquire failed during get_basic_identity");
        return ESP_ERR_TIMEOUT;
    }

    memset(out_cfg, 0, sizeof(*out_cfg));
    esp_err_t err = uzb_read_basic_string_attr(endpoint, ESP_ZB_ZCL_ATTR_BASIC_MANUFACTURER_NAME_ID, out_cfg->manufacturer, UZB_BASIC_STR_MAX_MANUFACTURER, true);
    if (err != ESP_OK) {
        goto done;
    }
    out_cfg->has_manufacturer = 1;

    err = uzb_read_basic_string_attr(endpoint, ESP_ZB_ZCL_ATTR_BASIC_MODEL_IDENTIFIER_ID, out_cfg->model, UZB_BASIC_STR_MAX_MODEL, true);
    if (err != ESP_OK) {
        goto done;
    }
    out_cfg->has_model = 1;

    err = uzb_read_basic_string_attr(endpoint, ESP_ZB_ZCL_ATTR_BASIC_DATE_CODE_ID, out_cfg->date_code, UZB_BASIC_STR_MAX_DATE_CODE, false);
    if (err != ESP_OK) {
        goto done;
    }
    if (out_cfg->date_code[0] > 0) {
        out_cfg->has_date_code = 1;
    }

    err = uzb_read_basic_string_attr(endpoint, ESP_ZB_ZCL_ATTR_BASIC_SW_BUILD_ID, out_cfg->sw_build_id, UZB_BASIC_STR_MAX_SW_BUILD_ID, false);
    if (err != ESP_OK) {
        goto done;
    }
    if (out_cfg->sw_build_id[0] > 0) {
        out_cfg->has_sw_build_id = 1;
    }

    esp_zb_zcl_attr_t *power_attr = esp_zb_zcl_get_attribute(endpoint, ESP_ZB_ZCL_CLUSTER_ID_BASIC, ESP_ZB_ZCL_CLUSTER_SERVER_ROLE, ESP_ZB_ZCL_ATTR_BASIC_POWER_SOURCE_ID);
    if (power_attr == NULL || power_attr->data_p == NULL) {
        err = ESP_ERR_NOT_FOUND;
        goto done;
    }
    if (power_attr->type != ESP_ZB_ZCL_ATTR_TYPE_8BIT_ENUM && power_attr->type != ESP_ZB_ZCL_ATTR_TYPE_U8) {
        err = ESP_ERR_INVALID_ARG;
        goto done;
    }
    out_cfg->power_source = *((const uint8_t *)power_attr->data_p);
    out_cfg->has_power_source = 1;
    err = ESP_OK;

done:
    esp_zb_lock_release();
    return err;
}

static esp_err_t uzb_attach_custom_clusters_to_endpoint(esp_zb_ep_list_t *ep_list, uint8_t endpoint) {
    if (ep_list == NULL || !uzb_valid_endpoint_id(endpoint)) {
        return ESP_ERR_INVALID_ARG;
    }
    esp_zb_cluster_list_t *cluster_list = esp_zb_ep_list_get_ep(ep_list, endpoint);
    if (cluster_list == NULL) {
        return ESP_ERR_NOT_FOUND;
    }

    for (size_t c = 0; c < UZB_CUSTOM_CLUSTER_MAX; ++c) {
        if (!s_custom_clusters[c].used) {
            continue;
        }

        esp_zb_attribute_list_t *attr_list = esp_zb_zcl_attr_list_create(s_custom_clusters[c].cluster_id);
        if (attr_list == NULL) {
            return ESP_ERR_NO_MEM;
        }

        for (size_t a = 0; a < UZB_CUSTOM_ATTR_MAX; ++a) {
            if (!s_custom_attrs[a].used || s_custom_attrs[a].cluster_id != s_custom_clusters[c].cluster_id) {
                continue;
            }
            void *value_ptr = uzb_custom_attr_value_ptr(&s_custom_attrs[a]);
            if (value_ptr == NULL) {
                return ESP_ERR_NOT_SUPPORTED;
            }
            esp_err_t attr_err = esp_zb_custom_cluster_add_custom_attr(
                attr_list,
                s_custom_attrs[a].attr_id,
                s_custom_attrs[a].attr_type,
                s_custom_attrs[a].attr_access,
                value_ptr
            );
            if (attr_err != ESP_OK) {
                return attr_err;
            }
        }

        esp_err_t add_err = esp_zb_cluster_list_add_custom_cluster(
            cluster_list,
            attr_list,
            s_custom_clusters[c].cluster_role
        );
        if (add_err != ESP_OK) {
            return add_err;
        }
    }

    return ESP_OK;
}

esp_err_t uzb_core_register_device(void) {
    if (!s_inited) {
        return ESP_ERR_INVALID_STATE;
    }
    if (s_started) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!s_endpoint_defined) {
        return s_device_registered ? ESP_OK : ESP_ERR_INVALID_STATE;
    }
    if (!esp_zb_lock_acquire(pdMS_TO_TICKS(5000))) {
        ESP_LOGE(TAG, "lock acquire failed during register_device");
        return ESP_ERR_TIMEOUT;
    }

    esp_err_t err = ESP_OK;
    esp_zb_ep_list_t *ep_list = NULL;
    esp_zb_cluster_list_t *direct_cluster_list = NULL;
    if (s_endpoint_kind == UZB_ENDPOINT_KIND_ON_OFF_LIGHT) {
        esp_zb_on_off_light_cfg_t light_cfg = ESP_ZB_DEFAULT_ON_OFF_LIGHT_CONFIG();
        direct_cluster_list = esp_zb_on_off_light_clusters_create(&light_cfg);
        if (direct_cluster_list == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }
    } else if (s_endpoint_kind == UZB_ENDPOINT_KIND_ON_OFF_SWITCH) {
        esp_zb_on_off_switch_cfg_t switch_cfg = ESP_ZB_DEFAULT_ON_OFF_SWITCH_CONFIG();
        direct_cluster_list = esp_zb_on_off_switch_clusters_create(&switch_cfg);
        if (direct_cluster_list == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }
    } else if (s_endpoint_kind == UZB_ENDPOINT_KIND_DIMMABLE_SWITCH) {
        esp_zb_on_off_switch_cfg_t switch_cfg = ESP_ZB_DEFAULT_ON_OFF_SWITCH_CONFIG();
        esp_zb_cluster_list_t *cluster_list = esp_zb_on_off_switch_clusters_create(&switch_cfg);
        if (cluster_list == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }

        esp_zb_level_cluster_cfg_t level_cfg = {
            .current_level = ESP_ZB_ZCL_LEVEL_CONTROL_CURRENT_LEVEL_DEFAULT_VALUE,
        };
        esp_zb_attribute_list_t *level_cluster = esp_zb_level_cluster_create(&level_cfg);
        if (level_cluster == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }
        err = esp_zb_cluster_list_add_level_cluster(cluster_list, level_cluster, ESP_ZB_ZCL_CLUSTER_CLIENT_ROLE);
        if (err != ESP_OK) {
            goto done;
        }

        ep_list = esp_zb_ep_list_create();
        if (ep_list == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }
        err = esp_zb_ep_list_add_ep(ep_list, cluster_list, s_endpoint_cfg);
        if (err != ESP_OK) {
            goto done;
        }
    } else if (s_endpoint_kind == UZB_ENDPOINT_KIND_DIMMABLE_LIGHT) {
        ep_list = esp_zb_ep_list_create();
        if (ep_list == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }

        esp_zb_cluster_list_t *cluster_list = esp_zb_zcl_cluster_list_create();
        if (cluster_list == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }

        esp_zb_basic_cluster_cfg_t basic_cfg = {
            .zcl_version = ESP_ZB_ZCL_BASIC_ZCL_VERSION_DEFAULT_VALUE,
            .power_source = ESP_ZB_ZCL_BASIC_POWER_SOURCE_DEFAULT_VALUE,
        };
        esp_zb_attribute_list_t *basic_cluster = esp_zb_basic_cluster_create(&basic_cfg);
        if (basic_cluster == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }
        err = esp_zb_cluster_list_add_basic_cluster(cluster_list, basic_cluster, ESP_ZB_ZCL_CLUSTER_SERVER_ROLE);
        if (err != ESP_OK) {
            goto done;
        }

        esp_zb_identify_cluster_cfg_t identify_cfg = {
            .identify_time = ESP_ZB_ZCL_IDENTIFY_IDENTIFY_TIME_DEFAULT_VALUE,
        };
        esp_zb_attribute_list_t *identify_cluster = esp_zb_identify_cluster_create(&identify_cfg);
        if (identify_cluster == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }
        err = esp_zb_cluster_list_add_identify_cluster(cluster_list, identify_cluster, ESP_ZB_ZCL_CLUSTER_SERVER_ROLE);
        if (err != ESP_OK) {
            goto done;
        }

        esp_zb_groups_cluster_cfg_t groups_cfg = {
            .groups_name_support_id = ESP_ZB_ZCL_GROUPS_NAME_SUPPORT_DEFAULT_VALUE,
        };
        esp_zb_attribute_list_t *groups_cluster = esp_zb_groups_cluster_create(&groups_cfg);
        if (groups_cluster == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }
        err = esp_zb_cluster_list_add_groups_cluster(cluster_list, groups_cluster, ESP_ZB_ZCL_CLUSTER_SERVER_ROLE);
        if (err != ESP_OK) {
            goto done;
        }

        esp_zb_scenes_cluster_cfg_t scenes_cfg = {
            .scenes_count = ESP_ZB_ZCL_SCENES_SCENE_COUNT_DEFAULT_VALUE,
            .current_scene = ESP_ZB_ZCL_SCENES_CURRENT_SCENE_DEFAULT_VALUE,
            .current_group = ESP_ZB_ZCL_SCENES_CURRENT_GROUP_DEFAULT_VALUE,
            .scene_valid = ESP_ZB_ZCL_SCENES_SCENE_VALID_DEFAULT_VALUE,
            .name_support = ESP_ZB_ZCL_SCENES_NAME_SUPPORT_DEFAULT_VALUE,
        };
        esp_zb_attribute_list_t *scenes_cluster = esp_zb_scenes_cluster_create(&scenes_cfg);
        if (scenes_cluster == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }
        err = esp_zb_cluster_list_add_scenes_cluster(cluster_list, scenes_cluster, ESP_ZB_ZCL_CLUSTER_SERVER_ROLE);
        if (err != ESP_OK) {
            goto done;
        }

        esp_zb_on_off_cluster_cfg_t on_off_cfg = {
            .on_off = ESP_ZB_ZCL_ON_OFF_ON_OFF_DEFAULT_VALUE,
        };
        esp_zb_attribute_list_t *on_off_cluster = esp_zb_on_off_cluster_create(&on_off_cfg);
        if (on_off_cluster == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }
        err = esp_zb_cluster_list_add_on_off_cluster(cluster_list, on_off_cluster, ESP_ZB_ZCL_CLUSTER_SERVER_ROLE);
        if (err != ESP_OK) {
            goto done;
        }

        esp_zb_level_cluster_cfg_t level_cfg = {
            .current_level = ESP_ZB_ZCL_LEVEL_CONTROL_CURRENT_LEVEL_DEFAULT_VALUE,
        };
        esp_zb_attribute_list_t *level_cluster = esp_zb_level_cluster_create(&level_cfg);
        if (level_cluster == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }
        err = esp_zb_cluster_list_add_level_cluster(cluster_list, level_cluster, ESP_ZB_ZCL_CLUSTER_SERVER_ROLE);
        if (err != ESP_OK) {
            goto done;
        }

        err = esp_zb_ep_list_add_ep(ep_list, cluster_list, s_endpoint_cfg);
        if (err != ESP_OK) {
            goto done;
        }
    } else if (s_endpoint_kind == UZB_ENDPOINT_KIND_COLOR_LIGHT) {
        esp_zb_color_dimmable_light_cfg_t light_cfg = ESP_ZB_DEFAULT_COLOR_DIMMABLE_LIGHT_CONFIG();
        direct_cluster_list = esp_zb_color_dimmable_light_clusters_create(&light_cfg);
        if (direct_cluster_list == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }
    } else if (s_endpoint_kind == UZB_ENDPOINT_KIND_TEMPERATURE_SENSOR) {
        esp_zb_temperature_sensor_cfg_t sensor_cfg = ESP_ZB_DEFAULT_TEMPERATURE_SENSOR_CONFIG();
        direct_cluster_list = esp_zb_temperature_sensor_clusters_create(&sensor_cfg);
        if (direct_cluster_list == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }
    } else if (s_endpoint_kind == UZB_ENDPOINT_KIND_HUMIDITY_SENSOR) {
        ep_list = esp_zb_ep_list_create();
        if (ep_list == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }

        esp_zb_cluster_list_t *cluster_list = esp_zb_zcl_cluster_list_create();
        if (cluster_list == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }

        esp_zb_basic_cluster_cfg_t basic_cfg = {
            .zcl_version = ESP_ZB_ZCL_BASIC_ZCL_VERSION_DEFAULT_VALUE,
            .power_source = ESP_ZB_ZCL_BASIC_POWER_SOURCE_DEFAULT_VALUE,
        };
        esp_zb_attribute_list_t *basic_cluster = esp_zb_basic_cluster_create(&basic_cfg);
        if (basic_cluster == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }
        err = esp_zb_cluster_list_add_basic_cluster(cluster_list, basic_cluster, ESP_ZB_ZCL_CLUSTER_SERVER_ROLE);
        if (err != ESP_OK) {
            goto done;
        }

        esp_zb_identify_cluster_cfg_t identify_cfg = {
            .identify_time = ESP_ZB_ZCL_IDENTIFY_IDENTIFY_TIME_DEFAULT_VALUE,
        };
        esp_zb_attribute_list_t *identify_cluster = esp_zb_identify_cluster_create(&identify_cfg);
        if (identify_cluster == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }
        err = esp_zb_cluster_list_add_identify_cluster(cluster_list, identify_cluster, ESP_ZB_ZCL_CLUSTER_SERVER_ROLE);
        if (err != ESP_OK) {
            goto done;
        }

        esp_zb_humidity_meas_cluster_cfg_t humidity_cfg = {
            .measured_value = ESP_ZB_ZCL_REL_HUMIDITY_MEASUREMENT_MEASURED_VALUE_DEFAULT,
            .min_value = ESP_ZB_ZCL_REL_HUMIDITY_MEASUREMENT_MIN_MEASURED_VALUE_DEFAULT,
            .max_value = ESP_ZB_ZCL_REL_HUMIDITY_MEASUREMENT_MAX_MEASURED_VALUE_DEFAULT,
        };
        esp_zb_attribute_list_t *humidity_cluster = esp_zb_humidity_meas_cluster_create(&humidity_cfg);
        if (humidity_cluster == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }
        err = esp_zb_cluster_list_add_humidity_meas_cluster(cluster_list, humidity_cluster, ESP_ZB_ZCL_CLUSTER_SERVER_ROLE);
        if (err != ESP_OK) {
            goto done;
        }

        err = esp_zb_ep_list_add_ep(ep_list, cluster_list, s_endpoint_cfg);
        if (err != ESP_OK) {
            goto done;
        }
    } else if (s_endpoint_kind == UZB_ENDPOINT_KIND_PRESSURE_SENSOR) {
        ep_list = esp_zb_ep_list_create();
        if (ep_list == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }

        esp_zb_cluster_list_t *cluster_list = esp_zb_zcl_cluster_list_create();
        if (cluster_list == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }

        esp_zb_basic_cluster_cfg_t basic_cfg = {
            .zcl_version = ESP_ZB_ZCL_BASIC_ZCL_VERSION_DEFAULT_VALUE,
            .power_source = ESP_ZB_ZCL_BASIC_POWER_SOURCE_DEFAULT_VALUE,
        };
        esp_zb_attribute_list_t *basic_cluster = esp_zb_basic_cluster_create(&basic_cfg);
        if (basic_cluster == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }
        err = esp_zb_cluster_list_add_basic_cluster(cluster_list, basic_cluster, ESP_ZB_ZCL_CLUSTER_SERVER_ROLE);
        if (err != ESP_OK) {
            goto done;
        }

        esp_zb_identify_cluster_cfg_t identify_cfg = {
            .identify_time = ESP_ZB_ZCL_IDENTIFY_IDENTIFY_TIME_DEFAULT_VALUE,
        };
        esp_zb_attribute_list_t *identify_cluster = esp_zb_identify_cluster_create(&identify_cfg);
        if (identify_cluster == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }
        err = esp_zb_cluster_list_add_identify_cluster(cluster_list, identify_cluster, ESP_ZB_ZCL_CLUSTER_SERVER_ROLE);
        if (err != ESP_OK) {
            goto done;
        }

        esp_zb_pressure_meas_cluster_cfg_t pressure_cfg = {
            .measured_value = ESP_ZB_ZCL_ATTR_PRESSURE_MEASUREMENT_VALUE_DEFAULT_VALUE,
            .min_value = ESP_ZB_ZCL_ATTR_PRESSURE_MEASUREMENT_MIN_VALUE_DEFAULT_VALUE,
            .max_value = ESP_ZB_ZCL_ATTR_PRESSURE_MEASUREMENT_MAX_VALUE_DEFAULT_VALUE,
        };
        esp_zb_attribute_list_t *pressure_cluster = esp_zb_pressure_meas_cluster_create(&pressure_cfg);
        if (pressure_cluster == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }
        err = esp_zb_cluster_list_add_pressure_meas_cluster(cluster_list, pressure_cluster, ESP_ZB_ZCL_CLUSTER_SERVER_ROLE);
        if (err != ESP_OK) {
            goto done;
        }

        err = esp_zb_ep_list_add_ep(ep_list, cluster_list, s_endpoint_cfg);
        if (err != ESP_OK) {
            goto done;
        }
    } else if (s_endpoint_kind == UZB_ENDPOINT_KIND_CLIMATE_SENSOR) {
        ep_list = esp_zb_ep_list_create();
        if (ep_list == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }

        esp_zb_cluster_list_t *cluster_list = esp_zb_zcl_cluster_list_create();
        if (cluster_list == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }

        esp_zb_basic_cluster_cfg_t basic_cfg = {
            .zcl_version = ESP_ZB_ZCL_BASIC_ZCL_VERSION_DEFAULT_VALUE,
            .power_source = ESP_ZB_ZCL_BASIC_POWER_SOURCE_DEFAULT_VALUE,
        };
        esp_zb_attribute_list_t *basic_cluster = esp_zb_basic_cluster_create(&basic_cfg);
        if (basic_cluster == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }
        err = esp_zb_cluster_list_add_basic_cluster(cluster_list, basic_cluster, ESP_ZB_ZCL_CLUSTER_SERVER_ROLE);
        if (err != ESP_OK) {
            goto done;
        }

        esp_zb_identify_cluster_cfg_t identify_cfg = {
            .identify_time = ESP_ZB_ZCL_IDENTIFY_IDENTIFY_TIME_DEFAULT_VALUE,
        };
        esp_zb_attribute_list_t *identify_cluster = esp_zb_identify_cluster_create(&identify_cfg);
        if (identify_cluster == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }
        err = esp_zb_cluster_list_add_identify_cluster(cluster_list, identify_cluster, ESP_ZB_ZCL_CLUSTER_SERVER_ROLE);
        if (err != ESP_OK) {
            goto done;
        }

        esp_zb_temperature_meas_cluster_cfg_t temperature_cfg = {
            .measured_value = ESP_ZB_ZCL_TEMP_MEASUREMENT_MEASURED_VALUE_DEFAULT,
            .min_value = ESP_ZB_ZCL_TEMP_MEASUREMENT_MIN_MEASURED_VALUE_DEFAULT,
            .max_value = ESP_ZB_ZCL_TEMP_MEASUREMENT_MAX_MEASURED_VALUE_DEFAULT,
        };
        esp_zb_attribute_list_t *temperature_cluster = esp_zb_temperature_meas_cluster_create(&temperature_cfg);
        if (temperature_cluster == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }
        err = esp_zb_cluster_list_add_temperature_meas_cluster(cluster_list, temperature_cluster, ESP_ZB_ZCL_CLUSTER_SERVER_ROLE);
        if (err != ESP_OK) {
            goto done;
        }

        esp_zb_humidity_meas_cluster_cfg_t humidity_cfg = {
            .measured_value = ESP_ZB_ZCL_REL_HUMIDITY_MEASUREMENT_MEASURED_VALUE_DEFAULT,
            .min_value = ESP_ZB_ZCL_REL_HUMIDITY_MEASUREMENT_MIN_MEASURED_VALUE_DEFAULT,
            .max_value = ESP_ZB_ZCL_REL_HUMIDITY_MEASUREMENT_MAX_MEASURED_VALUE_DEFAULT,
        };
        esp_zb_attribute_list_t *humidity_cluster = esp_zb_humidity_meas_cluster_create(&humidity_cfg);
        if (humidity_cluster == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }
        err = esp_zb_cluster_list_add_humidity_meas_cluster(cluster_list, humidity_cluster, ESP_ZB_ZCL_CLUSTER_SERVER_ROLE);
        if (err != ESP_OK) {
            goto done;
        }

        esp_zb_pressure_meas_cluster_cfg_t pressure_cfg = {
            .measured_value = ESP_ZB_ZCL_ATTR_PRESSURE_MEASUREMENT_VALUE_DEFAULT_VALUE,
            .min_value = ESP_ZB_ZCL_ATTR_PRESSURE_MEASUREMENT_MIN_VALUE_DEFAULT_VALUE,
            .max_value = ESP_ZB_ZCL_ATTR_PRESSURE_MEASUREMENT_MAX_VALUE_DEFAULT_VALUE,
        };
        esp_zb_attribute_list_t *pressure_cluster = esp_zb_pressure_meas_cluster_create(&pressure_cfg);
        if (pressure_cluster == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }
        err = esp_zb_cluster_list_add_pressure_meas_cluster(cluster_list, pressure_cluster, ESP_ZB_ZCL_CLUSTER_SERVER_ROLE);
        if (err != ESP_OK) {
            goto done;
        }

        err = esp_zb_ep_list_add_ep(ep_list, cluster_list, s_endpoint_cfg);
        if (err != ESP_OK) {
            goto done;
        }
    } else if (s_endpoint_kind == UZB_ENDPOINT_KIND_POWER_OUTLET) {
        esp_zb_mains_power_outlet_cfg_t outlet_cfg = ESP_ZB_DEFAULT_MAINS_POWER_OUTLET_CONFIG();
        direct_cluster_list = esp_zb_mains_power_outlet_clusters_create(&outlet_cfg);
        if (direct_cluster_list == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }
    } else if (s_endpoint_kind == UZB_ENDPOINT_KIND_POWER_OUTLET_METERING) {
        ep_list = esp_zb_ep_list_create();
        if (ep_list == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }

        esp_zb_mains_power_outlet_cfg_t outlet_cfg = ESP_ZB_DEFAULT_MAINS_POWER_OUTLET_CONFIG();
        esp_zb_cluster_list_t *cluster_list = esp_zb_mains_power_outlet_clusters_create(&outlet_cfg);
        if (cluster_list == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }

        esp_zb_electrical_meas_cluster_cfg_t electrical_cfg = {
            .measured_type = ESP_ZB_ZCL_ELECTRICAL_MEASUREMENT_ACTIVE_MEASUREMENT |
                             ESP_ZB_ZCL_ELECTRICAL_MEASUREMENT_PHASE_A_MEASUREMENT,
        };
        esp_zb_attribute_list_t *electrical_cluster = esp_zb_electrical_meas_cluster_create(&electrical_cfg);
        if (electrical_cluster == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }
        err = esp_zb_cluster_list_add_electrical_meas_cluster(cluster_list, electrical_cluster, ESP_ZB_ZCL_CLUSTER_SERVER_ROLE);
        if (err != ESP_OK) {
            goto done;
        }

        int16_t active_power = 0;
        uint16_t rms_voltage = 0;
        uint16_t rms_current = 0;
        err = esp_zb_electrical_meas_cluster_add_attr(
            electrical_cluster,
            ESP_ZB_ZCL_ATTR_ELECTRICAL_MEASUREMENT_ACTIVE_POWER_ID,
            &active_power
        );
        if (err == ESP_ERR_INVALID_ARG) {
            err = esp_zb_cluster_update_attr(
                electrical_cluster,
                ESP_ZB_ZCL_ATTR_ELECTRICAL_MEASUREMENT_ACTIVE_POWER_ID,
                &active_power
            );
        }
        if (err != ESP_OK) {
            goto done;
        }

        err = esp_zb_electrical_meas_cluster_add_attr(
            electrical_cluster,
            ESP_ZB_ZCL_ATTR_ELECTRICAL_MEASUREMENT_RMSVOLTAGE_ID,
            &rms_voltage
        );
        if (err == ESP_ERR_INVALID_ARG) {
            err = esp_zb_cluster_update_attr(
                electrical_cluster,
                ESP_ZB_ZCL_ATTR_ELECTRICAL_MEASUREMENT_RMSVOLTAGE_ID,
                &rms_voltage
            );
        }
        if (err != ESP_OK) {
            goto done;
        }

        err = esp_zb_electrical_meas_cluster_add_attr(
            electrical_cluster,
            ESP_ZB_ZCL_ATTR_ELECTRICAL_MEASUREMENT_RMSCURRENT_ID,
            &rms_current
        );
        if (err == ESP_ERR_INVALID_ARG) {
            err = esp_zb_cluster_update_attr(
                electrical_cluster,
                ESP_ZB_ZCL_ATTR_ELECTRICAL_MEASUREMENT_RMSCURRENT_ID,
                &rms_current
            );
        }
        if (err != ESP_OK) {
            goto done;
        }

        uint16_t one = 1;
        uint16_t current_divisor = 1000;
        err = esp_zb_cluster_update_attr(electrical_cluster, ESP_ZB_ZCL_ATTR_ELECTRICAL_MEASUREMENT_ACVOLTAGE_MULTIPLIER_ID, &one);
        if (err != ESP_OK && err != ESP_ERR_NOT_FOUND) {
            goto done;
        }
        err = esp_zb_cluster_update_attr(electrical_cluster, ESP_ZB_ZCL_ATTR_ELECTRICAL_MEASUREMENT_ACVOLTAGE_DIVISOR_ID, &one);
        if (err != ESP_OK && err != ESP_ERR_NOT_FOUND) {
            goto done;
        }
        err = esp_zb_cluster_update_attr(electrical_cluster, ESP_ZB_ZCL_ATTR_ELECTRICAL_MEASUREMENT_ACCURRENT_MULTIPLIER_ID, &one);
        if (err != ESP_OK && err != ESP_ERR_NOT_FOUND) {
            goto done;
        }
        err = esp_zb_cluster_update_attr(electrical_cluster, ESP_ZB_ZCL_ATTR_ELECTRICAL_MEASUREMENT_ACCURRENT_DIVISOR_ID, &current_divisor);
        if (err != ESP_OK && err != ESP_ERR_NOT_FOUND) {
            goto done;
        }
        err = esp_zb_cluster_update_attr(electrical_cluster, ESP_ZB_ZCL_ATTR_ELECTRICAL_MEASUREMENT_ACPOWER_MULTIPLIER_ID, &one);
        if (err != ESP_OK && err != ESP_ERR_NOT_FOUND) {
            goto done;
        }
        err = esp_zb_cluster_update_attr(electrical_cluster, ESP_ZB_ZCL_ATTR_ELECTRICAL_MEASUREMENT_ACPOWER_DIVISOR_ID, &one);
        if (err != ESP_OK && err != ESP_ERR_NOT_FOUND) {
            goto done;
        }

        err = esp_zb_ep_list_add_ep(ep_list, cluster_list, s_endpoint_cfg);
        if (err != ESP_OK) {
            goto done;
        }
    } else if (s_endpoint_kind == UZB_ENDPOINT_KIND_DOOR_LOCK) {
        esp_zb_door_lock_cfg_t lock_cfg = ESP_ZB_DEFAULT_DOOR_LOCK_CONFIG();
        direct_cluster_list = esp_zb_door_lock_clusters_create(&lock_cfg);
        if (direct_cluster_list == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }
    } else if (s_endpoint_kind == UZB_ENDPOINT_KIND_DOOR_LOCK_CONTROLLER) {
        esp_zb_door_lock_controller_cfg_t controller_cfg = ESP_ZB_DEFAULT_DOOR_LOCK_CONTROLLER_CONFIG();
        direct_cluster_list = esp_zb_door_lock_controller_clusters_create(&controller_cfg);
        if (direct_cluster_list == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }
    } else if (s_endpoint_kind == UZB_ENDPOINT_KIND_THERMOSTAT) {
        esp_zb_thermostat_cfg_t thermostat_cfg = ESP_ZB_DEFAULT_THERMOSTAT_CONFIG();
        direct_cluster_list = esp_zb_thermostat_clusters_create(&thermostat_cfg);
        if (direct_cluster_list == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }
    } else if (s_endpoint_kind == UZB_ENDPOINT_KIND_WINDOW_COVERING) {
        esp_zb_window_covering_cfg_t window_cfg = ESP_ZB_DEFAULT_WINDOW_COVERING_CONFIG();
        direct_cluster_list = esp_zb_window_covering_clusters_create(&window_cfg);
        if (direct_cluster_list == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }

        esp_zb_attribute_list_t *window_cluster = esp_zb_cluster_list_get_cluster(
            direct_cluster_list, ESP_ZB_ZCL_CLUSTER_ID_WINDOW_COVERING, ESP_ZB_ZCL_CLUSTER_SERVER_ROLE);
        if (window_cluster == NULL) {
            err = ESP_ERR_NOT_FOUND;
            goto done;
        }

        err = esp_zb_window_covering_cluster_add_attr(
            window_cluster, ESP_ZB_ZCL_ATTR_WINDOW_COVERING_CURRENT_POSITION_LIFT_ID, &s_window_current_position_lift);
        if (err != ESP_OK) {
            goto done;
        }
        err = esp_zb_window_covering_cluster_add_attr(
            window_cluster, ESP_ZB_ZCL_ATTR_WINDOW_COVERING_CURRENT_POSITION_TILT_ID, &s_window_current_position_tilt);
        if (err != ESP_OK) {
            goto done;
        }
        err = esp_zb_window_covering_cluster_add_attr(
            window_cluster, ESP_ZB_ZCL_ATTR_WINDOW_COVERING_CURRENT_POSITION_LIFT_PERCENTAGE_ID, &s_window_current_position_lift_percentage);
        if (err != ESP_OK) {
            goto done;
        }
        err = esp_zb_window_covering_cluster_add_attr(
            window_cluster, ESP_ZB_ZCL_ATTR_WINDOW_COVERING_CURRENT_POSITION_TILT_PERCENTAGE_ID, &s_window_current_position_tilt_percentage);
        if (err != ESP_OK) {
            goto done;
        }
    } else if (s_endpoint_kind == UZB_ENDPOINT_KIND_OCCUPANCY_SENSOR) {
        ep_list = esp_zb_ep_list_create();
        if (ep_list == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }

        esp_zb_cluster_list_t *cluster_list = esp_zb_zcl_cluster_list_create();
        if (cluster_list == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }

        esp_zb_basic_cluster_cfg_t basic_cfg = {
            .zcl_version = ESP_ZB_ZCL_BASIC_ZCL_VERSION_DEFAULT_VALUE,
            .power_source = ESP_ZB_ZCL_BASIC_POWER_SOURCE_DEFAULT_VALUE,
        };
        esp_zb_attribute_list_t *basic_cluster = esp_zb_basic_cluster_create(&basic_cfg);
        if (basic_cluster == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }
        err = esp_zb_cluster_list_add_basic_cluster(cluster_list, basic_cluster, ESP_ZB_ZCL_CLUSTER_SERVER_ROLE);
        if (err != ESP_OK) {
            goto done;
        }

        esp_zb_identify_cluster_cfg_t identify_cfg = {
            .identify_time = ESP_ZB_ZCL_IDENTIFY_IDENTIFY_TIME_DEFAULT_VALUE,
        };
        esp_zb_attribute_list_t *identify_cluster = esp_zb_identify_cluster_create(&identify_cfg);
        if (identify_cluster == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }
        err = esp_zb_cluster_list_add_identify_cluster(cluster_list, identify_cluster, ESP_ZB_ZCL_CLUSTER_SERVER_ROLE);
        if (err != ESP_OK) {
            goto done;
        }

        esp_zb_occupancy_sensing_cluster_cfg_t occupancy_cfg = {
            .occupancy = ESP_ZB_ZCL_OCCUPANCY_SENSING_OCCUPANCY_UNOCCUPIED,
            .sensor_type = ESP_ZB_ZCL_OCCUPANCY_SENSING_OCCUPANCY_SENSOR_TYPE_PIR,
            .sensor_type_bitmap = 0x01,
        };
        esp_zb_attribute_list_t *occupancy_cluster = esp_zb_occupancy_sensing_cluster_create(&occupancy_cfg);
        if (occupancy_cluster == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }
        err = esp_zb_cluster_list_add_occupancy_sensing_cluster(cluster_list, occupancy_cluster, ESP_ZB_ZCL_CLUSTER_SERVER_ROLE);
        if (err != ESP_OK) {
            goto done;
        }

        err = esp_zb_ep_list_add_ep(ep_list, cluster_list, s_endpoint_cfg);
        if (err != ESP_OK) {
            goto done;
        }
    } else if (s_endpoint_kind == UZB_ENDPOINT_KIND_IAS_ZONE) {
        ep_list = esp_zb_ep_list_create();
        if (ep_list == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }

        esp_zb_cluster_list_t *cluster_list = esp_zb_zcl_cluster_list_create();
        if (cluster_list == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }

        esp_zb_basic_cluster_cfg_t basic_cfg = {
            .zcl_version = ESP_ZB_ZCL_BASIC_ZCL_VERSION_DEFAULT_VALUE,
            .power_source = ESP_ZB_ZCL_BASIC_POWER_SOURCE_DEFAULT_VALUE,
        };
        esp_zb_attribute_list_t *basic_cluster = esp_zb_basic_cluster_create(&basic_cfg);
        if (basic_cluster == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }
        err = esp_zb_cluster_list_add_basic_cluster(cluster_list, basic_cluster, ESP_ZB_ZCL_CLUSTER_SERVER_ROLE);
        if (err != ESP_OK) {
            goto done;
        }

        esp_zb_identify_cluster_cfg_t identify_cfg = {
            .identify_time = ESP_ZB_ZCL_IDENTIFY_IDENTIFY_TIME_DEFAULT_VALUE,
        };
        esp_zb_attribute_list_t *identify_cluster = esp_zb_identify_cluster_create(&identify_cfg);
        if (identify_cluster == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }
        err = esp_zb_cluster_list_add_identify_cluster(cluster_list, identify_cluster, ESP_ZB_ZCL_CLUSTER_SERVER_ROLE);
        if (err != ESP_OK) {
            goto done;
        }

        esp_zb_ias_zone_cluster_cfg_t ias_cfg = {
            .zone_state = ESP_ZB_ZCL_IAS_ZONE_ZONESTATE_NOT_ENROLLED,
            .zone_type = s_ias_zone_type,
            .zone_status = 0,
            .ias_cie_addr = ESP_ZB_ZCL_ZONE_IAS_CIE_ADDR_DEFAULT,
            .zone_id = 0xFF,
        };
        esp_zb_attribute_list_t *ias_cluster = esp_zb_ias_zone_cluster_create(&ias_cfg);
        if (ias_cluster == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }
        err = esp_zb_cluster_list_add_ias_zone_cluster(cluster_list, ias_cluster, ESP_ZB_ZCL_CLUSTER_SERVER_ROLE);
        if (err != ESP_OK) {
            goto done;
        }

        err = esp_zb_ep_list_add_ep(ep_list, cluster_list, s_endpoint_cfg);
        if (err != ESP_OK) {
            goto done;
        }
    } else if (s_endpoint_kind == UZB_ENDPOINT_KIND_GENERIC) {
        ep_list = esp_zb_ep_list_create();
        if (ep_list == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }

        esp_zb_cluster_list_t *cluster_list = esp_zb_zcl_cluster_list_create();
        if (cluster_list == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }

        esp_zb_attribute_list_t *basic_cluster = esp_zb_basic_cluster_create(NULL);
        if (basic_cluster == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }
        err = esp_zb_cluster_list_add_basic_cluster(cluster_list, basic_cluster, ESP_ZB_ZCL_CLUSTER_SERVER_ROLE);
        if (err != ESP_OK) {
            goto done;
        }

        esp_zb_attribute_list_t *identify_cluster = esp_zb_identify_cluster_create(NULL);
        if (identify_cluster == NULL) {
            err = ESP_ERR_NO_MEM;
            goto done;
        }
        err = esp_zb_cluster_list_add_identify_cluster(cluster_list, identify_cluster, ESP_ZB_ZCL_CLUSTER_SERVER_ROLE);
        if (err != ESP_OK) {
            goto done;
        }

        err = esp_zb_ep_list_add_ep(ep_list, cluster_list, s_endpoint_cfg);
        if (err != ESP_OK) {
            goto done;
        }
    } else {
        err = ESP_ERR_INVALID_STATE;
        goto done;
    }

    if (direct_cluster_list != NULL) {
        if (s_registered_ep_list == NULL) {
            s_registered_ep_list = esp_zb_ep_list_create();
            if (s_registered_ep_list == NULL) {
                err = ESP_ERR_NO_MEM;
                goto done;
            }
        }
        err = esp_zb_ep_list_add_ep(s_registered_ep_list, direct_cluster_list, s_endpoint_cfg);
        if (err != ESP_OK) {
            goto done;
        }
    } else if (s_registered_ep_list == NULL) {
        s_registered_ep_list = ep_list;
        ep_list = NULL;
    } else {
        if (ep_list == NULL) {
            err = ESP_ERR_INVALID_STATE;
            goto done;
        }
        esp_zb_cluster_list_t *cluster_list = esp_zb_ep_list_get_ep(ep_list, s_endpoint_cfg.endpoint);
        if (cluster_list == NULL) {
            err = ESP_ERR_NOT_FOUND;
            goto done;
        }
        err = esp_zb_ep_list_add_ep(s_registered_ep_list, cluster_list, s_endpoint_cfg);
        if (err != ESP_OK) {
            goto done;
        }
    }

    err = uzb_attach_custom_clusters_to_endpoint(s_registered_ep_list, s_endpoint_cfg.endpoint);
    if (err != ESP_OK) {
        goto done;
    }

    err = uzb_apply_basic_identity_to_ep_list(s_registered_ep_list);
    if (err != ESP_OK) {
        goto done;
    }

    s_device_registered = true;
    s_device_register_committed = false;
    uzb_track_local_endpoint(s_endpoint_cfg.endpoint);
    s_endpoint_defined = false;
    s_endpoint_kind = UZB_ENDPOINT_KIND_NONE;
    err = ESP_OK;

done:
    esp_zb_lock_release();
    return err;
}

esp_err_t uzb_core_start(bool form_network) {
    if (!s_inited) {
        return ESP_ERR_INVALID_STATE;
    }
    if (s_started) {
        return ESP_OK;
    }

    s_form_network = form_network;
    s_last_joined_valid = false;
    s_last_joined_short_addr = 0;
    uzb_set_network_state(false, false);
    uzb_bind_table_lock();
    memset(&s_bind_table_snapshot, 0, sizeof(s_bind_table_snapshot));
    uzb_bind_table_unlock();
    uzb_active_ep_lock();
    memset(&s_active_ep_snapshot, 0, sizeof(s_active_ep_snapshot));
    uzb_active_ep_unlock();
    uzb_node_desc_lock();
    memset(&s_node_desc_snapshot, 0, sizeof(s_node_desc_snapshot));
    uzb_node_desc_unlock();
    uzb_simple_desc_lock();
    memset(&s_simple_desc_snapshot, 0, sizeof(s_simple_desc_snapshot));
    uzb_simple_desc_unlock();
    uzb_power_desc_lock();
    memset(&s_power_desc_snapshot, 0, sizeof(s_power_desc_snapshot));
    uzb_power_desc_unlock();

    if (!esp_zb_lock_acquire(pdMS_TO_TICKS(5000))) {
        ESP_LOGE(TAG, "lock acquire failed during start");
        return ESP_ERR_TIMEOUT;
    }
    esp_err_t err = ESP_OK;
    if (s_device_registered && !s_device_register_committed) {
        if (s_registered_ep_list == NULL) {
            err = ESP_ERR_INVALID_STATE;
        } else {
            err = esp_zb_device_register(s_registered_ep_list);
            if (err == ESP_OK && !s_action_handler_registered) {
                esp_zb_core_action_handler_register(uzb_action_handler);
                s_action_handler_registered = true;
            }
            if (err == ESP_OK) {
                s_registered_ep_list = NULL;
                s_device_register_committed = true;
            }
        }
    }
    if (err == ESP_OK) {
        err = esp_zb_start(false);
    }
    esp_zb_lock_release();
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "esp_zb_start failed: %s", esp_err_to_name(err));
        return err;
    }

    if (s_zb_task == NULL) {
        BaseType_t ok = xTaskCreate(uzb_zigbee_task, "zigbee", 4096, NULL, 5, &s_zb_task);
        if (ok != pdPASS) {
            ESP_LOGE(TAG, "zigbee task create failed");
            return ESP_ERR_NO_MEM;
        }
    }

    s_started = true;
    return ESP_OK;
}

esp_err_t uzb_core_permit_join(uint8_t duration_s) {
    if (!s_started) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!esp_zb_lock_acquire(pdMS_TO_TICKS(5000))) {
        ESP_LOGE(TAG, "lock acquire failed during permit_join");
        return ESP_ERR_TIMEOUT;
    }
    esp_err_t err = esp_zb_bdb_open_network(duration_s);
    esp_zb_lock_release();
    return err;
}

esp_err_t uzb_core_start_network_steering(void) {
    if (!s_started) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!esp_zb_lock_acquire(pdMS_TO_TICKS(5000))) {
        ESP_LOGE(TAG, "lock acquire failed during start_network_steering");
        return ESP_ERR_TIMEOUT;
    }
    esp_err_t err = esp_zb_bdb_start_top_level_commissioning(ESP_ZB_BDB_MODE_NETWORK_STEERING);
    esp_zb_lock_release();
    return err;
}

esp_err_t uzb_core_set_primary_channel_mask(uint32_t channel_mask) {
    if (!uzb_valid_channel_mask(channel_mask)) {
        return ESP_ERR_INVALID_ARG;
    }
    s_primary_channel_mask = channel_mask;
    if (!s_inited) {
        return ESP_OK;
    }
    if (!esp_zb_lock_acquire(pdMS_TO_TICKS(5000))) {
        ESP_LOGE(TAG, "lock acquire failed during set_primary_channel_mask");
        return ESP_ERR_TIMEOUT;
    }
    esp_err_t err = esp_zb_set_primary_network_channel_set(channel_mask);
    esp_zb_lock_release();
    return err;
}

esp_err_t uzb_core_set_pan_id(uint16_t pan_id) {
    if (pan_id == 0 || pan_id == 0xFFFF) {
        return ESP_ERR_INVALID_ARG;
    }
    s_pan_id = pan_id;
    s_pan_id_configured = true;
    if (!s_inited) {
        return ESP_OK;
    }
    if (!esp_zb_lock_acquire(pdMS_TO_TICKS(5000))) {
        ESP_LOGE(TAG, "lock acquire failed during set_pan_id");
        return ESP_ERR_TIMEOUT;
    }
    esp_zb_set_pan_id(s_pan_id);
    esp_zb_lock_release();
    return ESP_OK;
}

esp_err_t uzb_core_set_extended_pan_id(const uint8_t ext_pan_id[8]) {
    if (ext_pan_id == NULL) {
        return ESP_ERR_INVALID_ARG;
    }
    memcpy(s_extended_pan_id, ext_pan_id, sizeof(s_extended_pan_id));
    s_extended_pan_id_configured = true;
    if (!s_inited) {
        return ESP_OK;
    }
    if (!esp_zb_lock_acquire(pdMS_TO_TICKS(5000))) {
        ESP_LOGE(TAG, "lock acquire failed during set_extended_pan_id");
        return ESP_ERR_TIMEOUT;
    }
    esp_zb_set_extended_pan_id(s_extended_pan_id);
    esp_zb_lock_release();
    return ESP_OK;
}

esp_err_t uzb_core_enable_wifi_i154_coex(void) {
#if defined(CONFIG_ESP_COEX_SW_COEXIST_ENABLE) && CONFIG_ESP_COEX_SW_COEXIST_ENABLE && defined(CONFIG_SOC_IEEE802154_SUPPORTED) && CONFIG_SOC_IEEE802154_SUPPORTED
    return esp_coex_wifi_i154_enable();
#else
    return ESP_ERR_NOT_SUPPORTED;
#endif
}

esp_err_t uzb_core_get_attribute(uint8_t endpoint, uint16_t cluster_id, uint8_t cluster_role, uint16_t attr_id, uzb_attr_value_t *out_value) {
    if (out_value == NULL) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!s_device_registered) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!uzb_is_local_endpoint(endpoint)) {
        return ESP_ERR_NOT_FOUND;
    }
    if (!esp_zb_lock_acquire(pdMS_TO_TICKS(5000))) {
        ESP_LOGE(TAG, "lock acquire failed during get_attribute");
        return ESP_ERR_TIMEOUT;
    }

    esp_err_t err = ESP_OK;
    esp_zb_zcl_attr_t *attr = esp_zb_zcl_get_attribute(endpoint, cluster_id, cluster_role, attr_id);
    if (attr == NULL) {
        err = ESP_ERR_NOT_FOUND;
    } else {
        err = uzb_decode_attr_value(attr, out_value);
    }

    esp_zb_lock_release();
    return err;
}

esp_err_t uzb_core_set_attribute(uint8_t endpoint, uint16_t cluster_id, uint8_t cluster_role, uint16_t attr_id, const uzb_attr_value_t *in_value, bool check, uint8_t *out_zcl_status) {
    if (in_value == NULL) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!s_device_registered) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!uzb_is_local_endpoint(endpoint)) {
        return ESP_ERR_NOT_FOUND;
    }
    if (!esp_zb_lock_acquire(pdMS_TO_TICKS(5000))) {
        ESP_LOGE(TAG, "lock acquire failed during set_attribute");
        return ESP_ERR_TIMEOUT;
    }

    esp_err_t err = ESP_OK;
    uint8_t status = ESP_ZB_ZCL_STATUS_FAIL;
    esp_zb_zcl_attr_t *attr = esp_zb_zcl_get_attribute(endpoint, cluster_id, cluster_role, attr_id);
    if (attr == NULL || attr->data_p == NULL) {
        err = ESP_ERR_NOT_FOUND;
        goto done;
    }

    switch (attr->type) {
        case ESP_ZB_ZCL_ATTR_TYPE_BOOL: {
            bool v = in_value->bool_value;
            status = (uint8_t)esp_zb_zcl_set_attribute_val(endpoint, cluster_id, cluster_role, attr_id, &v, check);
            break;
        }
        case ESP_ZB_ZCL_ATTR_TYPE_U8:
        case ESP_ZB_ZCL_ATTR_TYPE_8BITMAP:
        case ESP_ZB_ZCL_ATTR_TYPE_8BIT_ENUM: {
            uint8_t v = (uint8_t)in_value->uint_value;
            status = (uint8_t)esp_zb_zcl_set_attribute_val(endpoint, cluster_id, cluster_role, attr_id, &v, check);
            break;
        }
        case ESP_ZB_ZCL_ATTR_TYPE_U16:
        case ESP_ZB_ZCL_ATTR_TYPE_16BITMAP:
        case ESP_ZB_ZCL_ATTR_TYPE_16BIT_ENUM:
        case ESP_ZB_ZCL_ATTR_TYPE_CLUSTER_ID:
        case ESP_ZB_ZCL_ATTR_TYPE_ATTRIBUTE_ID: {
            uint16_t v = (uint16_t)in_value->uint_value;
            status = (uint8_t)esp_zb_zcl_set_attribute_val(endpoint, cluster_id, cluster_role, attr_id, &v, check);
            break;
        }
        case ESP_ZB_ZCL_ATTR_TYPE_U32:
        case ESP_ZB_ZCL_ATTR_TYPE_32BITMAP:
        case ESP_ZB_ZCL_ATTR_TYPE_UTC_TIME:
        case ESP_ZB_ZCL_ATTR_TYPE_BACNET_OID: {
            uint32_t v = in_value->uint_value;
            status = (uint8_t)esp_zb_zcl_set_attribute_val(endpoint, cluster_id, cluster_role, attr_id, &v, check);
            break;
        }
        case ESP_ZB_ZCL_ATTR_TYPE_S8: {
            int8_t v = (int8_t)in_value->int_value;
            status = (uint8_t)esp_zb_zcl_set_attribute_val(endpoint, cluster_id, cluster_role, attr_id, &v, check);
            break;
        }
        case ESP_ZB_ZCL_ATTR_TYPE_S16: {
            int16_t v = (int16_t)in_value->int_value;
            status = (uint8_t)esp_zb_zcl_set_attribute_val(endpoint, cluster_id, cluster_role, attr_id, &v, check);
            break;
        }
        case ESP_ZB_ZCL_ATTR_TYPE_S32: {
            int32_t v = in_value->int_value;
            status = (uint8_t)esp_zb_zcl_set_attribute_val(endpoint, cluster_id, cluster_role, attr_id, &v, check);
            break;
        }
        default:
            err = ESP_ERR_NOT_SUPPORTED;
            goto done;
    }

    if (status != ESP_ZB_ZCL_STATUS_SUCCESS) {
        err = ESP_FAIL;
    } else {
        uzb_attr_value_t out_value = {0};
        if (uzb_decode_attr_value(attr, &out_value) == ESP_OK) {
            uzb_event_t event = {0};
            event.type = UZB_EVENT_TYPE_ATTR_SET;
            event.data.attr_set.has_source = 0;
            event.data.attr_set.source_short_addr = 0xFFFF;
            event.data.attr_set.source_endpoint = 0;
            event.data.attr_set.endpoint = endpoint;
            event.data.attr_set.cluster_id = cluster_id;
            event.data.attr_set.attr_id = attr_id;
            event.data.attr_set.status = (int32_t)ESP_ZB_ZCL_STATUS_SUCCESS;
            event.data.attr_set.value = out_value;
            uzb_enqueue_event(&event);
        }
    }

done:
    if (out_zcl_status != NULL) {
        *out_zcl_status = status;
    }
    esp_zb_lock_release();
    return err;
}

esp_err_t uzb_core_configure_reporting(uint8_t src_endpoint, uint16_t dst_short_addr, uint8_t dst_endpoint,
                                       uint16_t cluster_id, uint16_t attr_id, uint8_t attr_type,
                                       uint16_t min_interval, uint16_t max_interval,
                                       bool has_reportable_change, int32_t reportable_change) {
    if (!s_started || !s_device_registered) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!uzb_valid_endpoint_id(src_endpoint) || !uzb_valid_endpoint_id(dst_endpoint)) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!esp_zb_lock_acquire(pdMS_TO_TICKS(5000))) {
        ESP_LOGE(TAG, "lock acquire failed during configure_reporting");
        return ESP_ERR_TIMEOUT;
    }

    esp_zb_zcl_config_report_record_t record = {0};
    record.direction = ESP_ZB_ZCL_REPORT_DIRECTION_SEND;
    record.attributeID = attr_id;
    record.attrType = attr_type;
    record.min_interval = min_interval;
    record.max_interval = max_interval;
    record.reportable_change = NULL;

    uint8_t change_u8 = 0;
    int8_t change_s8 = 0;
    uint16_t change_u16 = 0;
    int16_t change_s16 = 0;
    uint32_t change_u32 = 0;
    int32_t change_s32 = 0;
    if (has_reportable_change) {
        switch (attr_type) {
            case ESP_ZB_ZCL_ATTR_TYPE_U8:
            case ESP_ZB_ZCL_ATTR_TYPE_8BIT_ENUM:
            case ESP_ZB_ZCL_ATTR_TYPE_8BITMAP:
                if (reportable_change < 0 || reportable_change > 0xFF) {
                    esp_zb_lock_release();
                    return ESP_ERR_INVALID_ARG;
                }
                change_u8 = (uint8_t)reportable_change;
                record.reportable_change = &change_u8;
                break;
            case ESP_ZB_ZCL_ATTR_TYPE_S8:
                if (reportable_change < -128 || reportable_change > 127) {
                    esp_zb_lock_release();
                    return ESP_ERR_INVALID_ARG;
                }
                change_s8 = (int8_t)reportable_change;
                record.reportable_change = &change_s8;
                break;
            case ESP_ZB_ZCL_ATTR_TYPE_U16:
            case ESP_ZB_ZCL_ATTR_TYPE_16BIT_ENUM:
            case ESP_ZB_ZCL_ATTR_TYPE_16BITMAP:
            case ESP_ZB_ZCL_ATTR_TYPE_CLUSTER_ID:
            case ESP_ZB_ZCL_ATTR_TYPE_ATTRIBUTE_ID:
                if (reportable_change < 0 || reportable_change > 0xFFFF) {
                    esp_zb_lock_release();
                    return ESP_ERR_INVALID_ARG;
                }
                change_u16 = (uint16_t)reportable_change;
                record.reportable_change = &change_u16;
                break;
            case ESP_ZB_ZCL_ATTR_TYPE_S16:
                if (reportable_change < -32768 || reportable_change > 32767) {
                    esp_zb_lock_release();
                    return ESP_ERR_INVALID_ARG;
                }
                change_s16 = (int16_t)reportable_change;
                record.reportable_change = &change_s16;
                break;
            case ESP_ZB_ZCL_ATTR_TYPE_U32:
            case ESP_ZB_ZCL_ATTR_TYPE_32BITMAP:
            case ESP_ZB_ZCL_ATTR_TYPE_UTC_TIME:
            case ESP_ZB_ZCL_ATTR_TYPE_BACNET_OID:
                if (reportable_change < 0) {
                    esp_zb_lock_release();
                    return ESP_ERR_INVALID_ARG;
                }
                change_u32 = (uint32_t)reportable_change;
                record.reportable_change = &change_u32;
                break;
            case ESP_ZB_ZCL_ATTR_TYPE_S32:
                change_s32 = (int32_t)reportable_change;
                record.reportable_change = &change_s32;
                break;
            default:
                esp_zb_lock_release();
                return ESP_ERR_NOT_SUPPORTED;
        }
    } else {
        // The SDK dereferences reportable_change for analog types.
        // Keep default threshold 0 to avoid NULL access and report any change.
        switch (attr_type) {
            case ESP_ZB_ZCL_ATTR_TYPE_U8:
            case ESP_ZB_ZCL_ATTR_TYPE_8BIT_ENUM:
            case ESP_ZB_ZCL_ATTR_TYPE_8BITMAP:
                record.reportable_change = &change_u8;
                break;
            case ESP_ZB_ZCL_ATTR_TYPE_S8:
                record.reportable_change = &change_s8;
                break;
            case ESP_ZB_ZCL_ATTR_TYPE_U16:
            case ESP_ZB_ZCL_ATTR_TYPE_16BIT_ENUM:
            case ESP_ZB_ZCL_ATTR_TYPE_16BITMAP:
            case ESP_ZB_ZCL_ATTR_TYPE_CLUSTER_ID:
            case ESP_ZB_ZCL_ATTR_TYPE_ATTRIBUTE_ID:
                record.reportable_change = &change_u16;
                break;
            case ESP_ZB_ZCL_ATTR_TYPE_S16:
                record.reportable_change = &change_s16;
                break;
            case ESP_ZB_ZCL_ATTR_TYPE_U32:
            case ESP_ZB_ZCL_ATTR_TYPE_32BITMAP:
            case ESP_ZB_ZCL_ATTR_TYPE_UTC_TIME:
            case ESP_ZB_ZCL_ATTR_TYPE_BACNET_OID:
                record.reportable_change = &change_u32;
                break;
            case ESP_ZB_ZCL_ATTR_TYPE_S32:
                record.reportable_change = &change_s32;
                break;
            default:
                break;
        }
    }

    esp_zb_zcl_config_report_cmd_t cmd_req = {0};
    cmd_req.zcl_basic_cmd.src_endpoint = src_endpoint;
    cmd_req.zcl_basic_cmd.dst_endpoint = dst_endpoint;
    cmd_req.zcl_basic_cmd.dst_addr_u.addr_short = dst_short_addr;
    cmd_req.address_mode = ESP_ZB_APS_ADDR_MODE_16_ENDP_PRESENT;
    cmd_req.clusterID = cluster_id;
    cmd_req.direction = ESP_ZB_ZCL_CMD_DIRECTION_TO_SRV;
    cmd_req.record_number = 1;
    cmd_req.record_field = &record;
    (void)esp_zb_zcl_config_report_cmd_req(&cmd_req);

    esp_zb_lock_release();
    return ESP_OK;
}

esp_err_t uzb_core_send_on_off_cmd(uint8_t src_endpoint, uint16_t dst_short_addr, uint8_t dst_endpoint, uint8_t cmd_id) {
    if (!s_started || !s_device_registered) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!uzb_valid_endpoint_id(src_endpoint) || !uzb_valid_endpoint_id(dst_endpoint)) {
        return ESP_ERR_INVALID_ARG;
    }
    if (cmd_id != ESP_ZB_ZCL_CMD_ON_OFF_OFF_ID &&
        cmd_id != ESP_ZB_ZCL_CMD_ON_OFF_ON_ID &&
        cmd_id != ESP_ZB_ZCL_CMD_ON_OFF_TOGGLE_ID) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!esp_zb_lock_acquire(pdMS_TO_TICKS(5000))) {
        ESP_LOGE(TAG, "lock acquire failed during send_on_off_cmd");
        return ESP_ERR_TIMEOUT;
    }

    esp_zb_zcl_on_off_cmd_t cmd_req = {0};
    cmd_req.zcl_basic_cmd.src_endpoint = src_endpoint;
    cmd_req.zcl_basic_cmd.dst_endpoint = dst_endpoint;
    cmd_req.zcl_basic_cmd.dst_addr_u.addr_short = dst_short_addr;
    cmd_req.address_mode = ESP_ZB_APS_ADDR_MODE_16_ENDP_PRESENT;
    cmd_req.on_off_cmd_id = cmd_id;
    (void)esp_zb_zcl_on_off_cmd_req(&cmd_req);
    esp_zb_lock_release();
    return ESP_OK;
}

esp_err_t uzb_core_send_level_cmd(uint8_t src_endpoint, uint16_t dst_short_addr, uint8_t dst_endpoint, uint8_t level, uint16_t transition_time_ds, bool with_onoff) {
    if (!s_started || !s_device_registered) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!uzb_valid_endpoint_id(src_endpoint) || !uzb_valid_endpoint_id(dst_endpoint)) {
        return ESP_ERR_INVALID_ARG;
    }
    if (level > 254) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!esp_zb_lock_acquire(pdMS_TO_TICKS(5000))) {
        ESP_LOGE(TAG, "lock acquire failed during send_level_cmd");
        return ESP_ERR_TIMEOUT;
    }

    esp_zb_zcl_move_to_level_cmd_t cmd_req = {0};
    cmd_req.zcl_basic_cmd.src_endpoint = src_endpoint;
    cmd_req.zcl_basic_cmd.dst_endpoint = dst_endpoint;
    cmd_req.zcl_basic_cmd.dst_addr_u.addr_short = dst_short_addr;
    cmd_req.address_mode = ESP_ZB_APS_ADDR_MODE_16_ENDP_PRESENT;
    cmd_req.level = level;
    cmd_req.transition_time = transition_time_ds;
    if (with_onoff) {
        (void)esp_zb_zcl_level_move_to_level_with_onoff_cmd_req(&cmd_req);
    } else {
        (void)esp_zb_zcl_level_move_to_level_cmd_req(&cmd_req);
    }
    esp_zb_lock_release();
    return ESP_OK;
}

esp_err_t uzb_core_send_color_move_to_color_cmd(
    uint8_t src_endpoint,
    uint16_t dst_short_addr,
    uint8_t dst_endpoint,
    uint16_t color_x,
    uint16_t color_y,
    uint16_t transition_time_ds
) {
    if (!s_started || !s_device_registered) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!uzb_valid_endpoint_id(src_endpoint) || !uzb_valid_endpoint_id(dst_endpoint)) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!esp_zb_lock_acquire(pdMS_TO_TICKS(5000))) {
        ESP_LOGE(TAG, "lock acquire failed during send_color_move_to_color_cmd");
        return ESP_ERR_TIMEOUT;
    }

    esp_zb_zcl_color_move_to_color_cmd_t cmd_req = {0};
    cmd_req.zcl_basic_cmd.src_endpoint = src_endpoint;
    cmd_req.zcl_basic_cmd.dst_endpoint = dst_endpoint;
    cmd_req.zcl_basic_cmd.dst_addr_u.addr_short = dst_short_addr;
    cmd_req.address_mode = ESP_ZB_APS_ADDR_MODE_16_ENDP_PRESENT;
    cmd_req.color_x = color_x;
    cmd_req.color_y = color_y;
    cmd_req.transition_time = transition_time_ds;
    (void)esp_zb_zcl_color_move_to_color_cmd_req(&cmd_req);

    esp_zb_lock_release();
    return ESP_OK;
}

esp_err_t uzb_core_send_color_move_to_color_temperature_cmd(
    uint8_t src_endpoint,
    uint16_t dst_short_addr,
    uint8_t dst_endpoint,
    uint16_t color_temperature,
    uint16_t transition_time_ds
) {
    if (!s_started || !s_device_registered) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!uzb_valid_endpoint_id(src_endpoint) || !uzb_valid_endpoint_id(dst_endpoint)) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!esp_zb_lock_acquire(pdMS_TO_TICKS(5000))) {
        ESP_LOGE(TAG, "lock acquire failed during send_color_move_to_color_temperature_cmd");
        return ESP_ERR_TIMEOUT;
    }

    esp_zb_zcl_color_move_to_color_temperature_cmd_t cmd_req = {0};
    cmd_req.zcl_basic_cmd.src_endpoint = src_endpoint;
    cmd_req.zcl_basic_cmd.dst_endpoint = dst_endpoint;
    cmd_req.zcl_basic_cmd.dst_addr_u.addr_short = dst_short_addr;
    cmd_req.address_mode = ESP_ZB_APS_ADDR_MODE_16_ENDP_PRESENT;
    cmd_req.color_temperature = color_temperature;
    cmd_req.transition_time = transition_time_ds;
    (void)esp_zb_zcl_color_move_to_color_temperature_cmd_req(&cmd_req);

    esp_zb_lock_release();
    return ESP_OK;
}

esp_err_t uzb_core_send_lock_cmd(uint8_t src_endpoint, uint16_t dst_short_addr, uint8_t dst_endpoint, bool lock) {
    if (!s_started || !s_device_registered) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!uzb_valid_endpoint_id(src_endpoint) || !uzb_valid_endpoint_id(dst_endpoint)) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!esp_zb_lock_acquire(pdMS_TO_TICKS(5000))) {
        ESP_LOGE(TAG, "lock acquire failed during send_lock_cmd");
        return ESP_ERR_TIMEOUT;
    }

    esp_zb_zcl_lock_unlock_door_cmd_t cmd_req = {0};
    cmd_req.zcl_basic_cmd.src_endpoint = src_endpoint;
    cmd_req.zcl_basic_cmd.dst_endpoint = dst_endpoint;
    cmd_req.zcl_basic_cmd.dst_addr_u.addr_short = dst_short_addr;
    cmd_req.address_mode = ESP_ZB_APS_ADDR_MODE_16_ENDP_PRESENT;
    if (lock) {
        (void)esp_zb_zcl_lock_door_cmd_req(&cmd_req);
    } else {
        (void)esp_zb_zcl_unlock_door_cmd_req(&cmd_req);
    }
    esp_zb_lock_release();
    return ESP_OK;
}

esp_err_t uzb_core_send_group_add_cmd(uint8_t src_endpoint, uint16_t dst_short_addr, uint8_t dst_endpoint, uint16_t group_id) {
    if (!s_started || !s_device_registered) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!uzb_valid_endpoint_id(src_endpoint) || !uzb_valid_endpoint_id(dst_endpoint)) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!esp_zb_lock_acquire(pdMS_TO_TICKS(5000))) {
        ESP_LOGE(TAG, "lock acquire failed during send_group_add_cmd");
        return ESP_ERR_TIMEOUT;
    }

    esp_zb_zcl_groups_add_group_cmd_t cmd_req = {0};
    cmd_req.zcl_basic_cmd.src_endpoint = src_endpoint;
    cmd_req.zcl_basic_cmd.dst_endpoint = dst_endpoint;
    cmd_req.zcl_basic_cmd.dst_addr_u.addr_short = dst_short_addr;
    cmd_req.address_mode = ESP_ZB_APS_ADDR_MODE_16_ENDP_PRESENT;
    cmd_req.group_id = group_id;
    (void)esp_zb_zcl_groups_add_group_cmd_req(&cmd_req);

    esp_zb_lock_release();
    return ESP_OK;
}

esp_err_t uzb_core_send_group_remove_cmd(uint8_t src_endpoint, uint16_t dst_short_addr, uint8_t dst_endpoint, uint16_t group_id) {
    if (!s_started || !s_device_registered) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!uzb_valid_endpoint_id(src_endpoint) || !uzb_valid_endpoint_id(dst_endpoint)) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!esp_zb_lock_acquire(pdMS_TO_TICKS(5000))) {
        ESP_LOGE(TAG, "lock acquire failed during send_group_remove_cmd");
        return ESP_ERR_TIMEOUT;
    }

    esp_zb_zcl_groups_add_group_cmd_t cmd_req = {0};
    cmd_req.zcl_basic_cmd.src_endpoint = src_endpoint;
    cmd_req.zcl_basic_cmd.dst_endpoint = dst_endpoint;
    cmd_req.zcl_basic_cmd.dst_addr_u.addr_short = dst_short_addr;
    cmd_req.address_mode = ESP_ZB_APS_ADDR_MODE_16_ENDP_PRESENT;
    cmd_req.group_id = group_id;
    (void)esp_zb_zcl_groups_remove_group_cmd_req(&cmd_req);

    esp_zb_lock_release();
    return ESP_OK;
}

esp_err_t uzb_core_send_group_remove_all_cmd(uint8_t src_endpoint, uint16_t dst_short_addr, uint8_t dst_endpoint) {
    if (!s_started || !s_device_registered) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!uzb_valid_endpoint_id(src_endpoint) || !uzb_valid_endpoint_id(dst_endpoint)) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!esp_zb_lock_acquire(pdMS_TO_TICKS(5000))) {
        ESP_LOGE(TAG, "lock acquire failed during send_group_remove_all_cmd");
        return ESP_ERR_TIMEOUT;
    }

    esp_zb_zcl_groups_remove_all_groups_cmd_t cmd_req = {0};
    cmd_req.zcl_basic_cmd.src_endpoint = src_endpoint;
    cmd_req.zcl_basic_cmd.dst_endpoint = dst_endpoint;
    cmd_req.zcl_basic_cmd.dst_addr_u.addr_short = dst_short_addr;
    cmd_req.address_mode = ESP_ZB_APS_ADDR_MODE_16_ENDP_PRESENT;
    (void)esp_zb_zcl_groups_remove_all_groups_cmd_req(&cmd_req);

    esp_zb_lock_release();
    return ESP_OK;
}

esp_err_t uzb_core_send_scene_add_cmd(uint8_t src_endpoint, uint16_t dst_short_addr, uint8_t dst_endpoint,
                                      uint16_t group_id, uint8_t scene_id, uint16_t transition_time_ds) {
    if (!s_started || !s_device_registered) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!uzb_valid_endpoint_id(src_endpoint) || !uzb_valid_endpoint_id(dst_endpoint)) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!esp_zb_lock_acquire(pdMS_TO_TICKS(5000))) {
        ESP_LOGE(TAG, "lock acquire failed during send_scene_add_cmd");
        return ESP_ERR_TIMEOUT;
    }

    esp_zb_zcl_scenes_add_scene_cmd_t cmd_req = {0};
    cmd_req.zcl_basic_cmd.src_endpoint = src_endpoint;
    cmd_req.zcl_basic_cmd.dst_endpoint = dst_endpoint;
    cmd_req.zcl_basic_cmd.dst_addr_u.addr_short = dst_short_addr;
    cmd_req.group_id = group_id;
    cmd_req.scene_id = scene_id;
    cmd_req.transition_time = transition_time_ds;
    cmd_req.extension_field = NULL;
    (void)esp_zb_zcl_scenes_add_scene_cmd_req(&cmd_req);

    esp_zb_lock_release();
    return ESP_OK;
}

esp_err_t uzb_core_send_scene_remove_cmd(uint8_t src_endpoint, uint16_t dst_short_addr, uint8_t dst_endpoint,
                                         uint16_t group_id, uint8_t scene_id) {
    if (!s_started || !s_device_registered) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!uzb_valid_endpoint_id(src_endpoint) || !uzb_valid_endpoint_id(dst_endpoint)) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!esp_zb_lock_acquire(pdMS_TO_TICKS(5000))) {
        ESP_LOGE(TAG, "lock acquire failed during send_scene_remove_cmd");
        return ESP_ERR_TIMEOUT;
    }

    esp_zb_zcl_scenes_remove_scene_cmd_t cmd_req = {0};
    cmd_req.zcl_basic_cmd.src_endpoint = src_endpoint;
    cmd_req.zcl_basic_cmd.dst_endpoint = dst_endpoint;
    cmd_req.zcl_basic_cmd.dst_addr_u.addr_short = dst_short_addr;
    cmd_req.address_mode = ESP_ZB_APS_ADDR_MODE_16_ENDP_PRESENT;
    cmd_req.group_id = group_id;
    cmd_req.scene_id = scene_id;
    (void)esp_zb_zcl_scenes_remove_scene_cmd_req(&cmd_req);

    esp_zb_lock_release();
    return ESP_OK;
}

esp_err_t uzb_core_send_scene_remove_all_cmd(uint8_t src_endpoint, uint16_t dst_short_addr, uint8_t dst_endpoint,
                                             uint16_t group_id) {
    if (!s_started || !s_device_registered) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!uzb_valid_endpoint_id(src_endpoint) || !uzb_valid_endpoint_id(dst_endpoint)) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!esp_zb_lock_acquire(pdMS_TO_TICKS(5000))) {
        ESP_LOGE(TAG, "lock acquire failed during send_scene_remove_all_cmd");
        return ESP_ERR_TIMEOUT;
    }

    esp_zb_zcl_scenes_remove_all_scenes_cmd_t cmd_req = {0};
    cmd_req.zcl_basic_cmd.src_endpoint = src_endpoint;
    cmd_req.zcl_basic_cmd.dst_endpoint = dst_endpoint;
    cmd_req.zcl_basic_cmd.dst_addr_u.addr_short = dst_short_addr;
    cmd_req.address_mode = ESP_ZB_APS_ADDR_MODE_16_ENDP_PRESENT;
    cmd_req.group_id = group_id;
    (void)esp_zb_zcl_scenes_remove_all_scenes_cmd_req(&cmd_req);

    esp_zb_lock_release();
    return ESP_OK;
}

esp_err_t uzb_core_send_scene_recall_cmd(uint8_t src_endpoint, uint16_t dst_short_addr, uint8_t dst_endpoint,
                                         uint16_t group_id, uint8_t scene_id) {
    if (!s_started || !s_device_registered) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!uzb_valid_endpoint_id(src_endpoint) || !uzb_valid_endpoint_id(dst_endpoint)) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!esp_zb_lock_acquire(pdMS_TO_TICKS(5000))) {
        ESP_LOGE(TAG, "lock acquire failed during send_scene_recall_cmd");
        return ESP_ERR_TIMEOUT;
    }

    esp_zb_zcl_scenes_recall_scene_cmd_t cmd_req = {0};
    cmd_req.zcl_basic_cmd.src_endpoint = src_endpoint;
    cmd_req.zcl_basic_cmd.dst_endpoint = dst_endpoint;
    cmd_req.zcl_basic_cmd.dst_addr_u.addr_short = dst_short_addr;
    cmd_req.address_mode = ESP_ZB_APS_ADDR_MODE_16_ENDP_PRESENT;
    cmd_req.group_id = group_id;
    cmd_req.scene_id = scene_id;
    (void)esp_zb_zcl_scenes_recall_scene_cmd_req(&cmd_req);

    esp_zb_lock_release();
    return ESP_OK;
}

esp_err_t uzb_core_send_custom_cmd(uint8_t src_endpoint, uint16_t dst_short_addr, uint8_t dst_endpoint,
                                   uint16_t profile_id, uint16_t cluster_id, uint16_t custom_cmd_id,
                                   uint8_t direction, bool disable_default_resp,
                                   bool manuf_specific, uint16_t manuf_code,
                                   uint8_t data_type, const uint8_t *payload, uint16_t payload_len) {
    if (!s_started || !s_device_registered) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!uzb_valid_endpoint_id(src_endpoint) || !uzb_valid_endpoint_id(dst_endpoint)) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!uzb_valid_custom_cluster_id(cluster_id) || profile_id == 0) {
        return ESP_ERR_INVALID_ARG;
    }
    if (direction != ESP_ZB_ZCL_CMD_DIRECTION_TO_SRV && direction != ESP_ZB_ZCL_CMD_DIRECTION_TO_CLI) {
        return ESP_ERR_INVALID_ARG;
    }
    if (payload_len > 0 && payload == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    if (!esp_zb_lock_acquire(pdMS_TO_TICKS(5000))) {
        ESP_LOGE(TAG, "lock acquire failed during send_custom_cmd");
        return ESP_ERR_TIMEOUT;
    }

    esp_zb_zcl_custom_cluster_cmd_req_t cmd_req = {0};
    cmd_req.zcl_basic_cmd.src_endpoint = src_endpoint;
    cmd_req.zcl_basic_cmd.dst_endpoint = dst_endpoint;
    cmd_req.zcl_basic_cmd.dst_addr_u.addr_short = dst_short_addr;
    cmd_req.address_mode = ESP_ZB_APS_ADDR_MODE_16_ENDP_PRESENT;
    cmd_req.profile_id = profile_id;
    cmd_req.cluster_id = cluster_id;
    cmd_req.manuf_specific = manuf_specific ? 1 : 0;
    cmd_req.direction = direction;
    cmd_req.dis_default_resp = disable_default_resp ? 1 : 0;
    cmd_req.manuf_code = manuf_code;
    cmd_req.custom_cmd_id = custom_cmd_id;
    cmd_req.data.type = (esp_zb_zcl_attr_type_t)data_type;
    cmd_req.data.size = payload_len;
    cmd_req.data.value = (void *)payload;
    uint8_t zcl_status = esp_zb_zcl_custom_cluster_cmd_req(&cmd_req);

    esp_zb_lock_release();
    if (zcl_status != ESP_ZB_ZCL_STATUS_SUCCESS) {
        return ESP_FAIL;
    }
    return ESP_OK;
}

esp_err_t uzb_core_ota_client_query_interval_set(uint8_t endpoint, uint16_t interval_min) {
    if (!s_started || !s_device_registered) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!uzb_valid_endpoint_id(endpoint)) {
        return ESP_ERR_INVALID_ARG;
    }
    if (interval_min == 0) {
        return ESP_ERR_INVALID_ARG;
    }
    (void)endpoint;
    (void)interval_min;
    return ESP_ERR_NOT_SUPPORTED;
}

esp_err_t uzb_core_ota_client_query_image_req(uint8_t server_ep, uint16_t server_addr) {
    if (!s_started || !s_device_registered) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!uzb_valid_endpoint_id(server_ep) || server_addr == 0xFFFF) {
        return ESP_ERR_INVALID_ARG;
    }
    (void)server_addr;
    (void)server_ep;
    return ESP_ERR_NOT_SUPPORTED;
}

esp_err_t uzb_core_ota_client_query_image_stop(void) {
    if (!s_started || !s_device_registered) {
        return ESP_ERR_INVALID_STATE;
    }
    return ESP_ERR_NOT_SUPPORTED;
}

bool uzb_core_ota_client_control_supported(void) {
    return false;
}

esp_err_t uzb_core_set_install_code_policy(bool enabled) {
    if (!s_inited) {
        s_install_code_policy = enabled;
        return ESP_OK;
    }
    if (!esp_zb_lock_acquire(pdMS_TO_TICKS(5000))) {
        ESP_LOGE(TAG, "lock acquire failed during set_install_code_policy");
        return ESP_ERR_TIMEOUT;
    }
    esp_err_t err = esp_zb_secur_ic_only_enable(enabled);
    esp_zb_lock_release();
    if (err == ESP_OK) {
        s_install_code_policy = enabled;
    }
    return err;
}

esp_err_t uzb_core_get_install_code_policy(bool *out_enabled) {
    if (out_enabled == NULL) {
        return ESP_ERR_INVALID_ARG;
    }
    *out_enabled = s_install_code_policy;
    return ESP_OK;
}

esp_err_t uzb_core_set_network_security_enabled(bool enabled) {
    if (!s_inited) {
        s_network_security_enabled = enabled;
        return ESP_OK;
    }
    if (!esp_zb_lock_acquire(pdMS_TO_TICKS(5000))) {
        ESP_LOGE(TAG, "lock acquire failed during set_network_security_enabled");
        return ESP_ERR_TIMEOUT;
    }
    esp_err_t err = esp_zb_secur_network_security_enable(enabled);
    esp_zb_lock_release();
    if (err == ESP_OK) {
        s_network_security_enabled = enabled;
    }
    return err;
}

esp_err_t uzb_core_get_network_security_enabled(bool *out_enabled) {
    if (out_enabled == NULL) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!s_inited) {
        *out_enabled = s_network_security_enabled;
        return ESP_OK;
    }
    if (!esp_zb_lock_acquire(pdMS_TO_TICKS(5000))) {
        ESP_LOGE(TAG, "lock acquire failed during get_network_security_enabled");
        return ESP_ERR_TIMEOUT;
    }
    bool enabled = esp_zb_secur_network_security_is_enabled();
    esp_zb_lock_release();
    s_network_security_enabled = enabled;
    *out_enabled = enabled;
    return ESP_OK;
}

esp_err_t uzb_core_set_network_key(const uint8_t key[16]) {
    if (key == NULL) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!s_inited) {
        memcpy(s_pending_network_key, key, sizeof(s_pending_network_key));
        s_pending_network_key_valid = true;
        return ESP_OK;
    }
    if (!esp_zb_lock_acquire(pdMS_TO_TICKS(5000))) {
        ESP_LOGE(TAG, "lock acquire failed during set_network_key");
        return ESP_ERR_TIMEOUT;
    }
    esp_err_t err = esp_zb_secur_network_key_set((uint8_t *)key);
    esp_zb_lock_release();
    if (err == ESP_OK) {
        memcpy(s_pending_network_key, key, sizeof(s_pending_network_key));
        s_pending_network_key_valid = true;
    }
    return err;
}

esp_err_t uzb_core_get_primary_network_key(uint8_t out_key[16]) {
    if (out_key == NULL) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!s_started) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!esp_zb_lock_acquire(pdMS_TO_TICKS(5000))) {
        ESP_LOGE(TAG, "lock acquire failed during get_primary_network_key");
        return ESP_ERR_TIMEOUT;
    }
    esp_err_t err = esp_zb_secur_primary_network_key_get(out_key);
    esp_zb_lock_release();
    return err;
}

esp_err_t uzb_core_switch_network_key(const uint8_t key[16], uint8_t key_seq_num) {
    if (key == NULL) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!s_started) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!esp_zb_lock_acquire(pdMS_TO_TICKS(5000))) {
        ESP_LOGE(TAG, "lock acquire failed during switch_network_key");
        return ESP_ERR_TIMEOUT;
    }
    esp_err_t err = esp_zb_secur_network_key_switch(key, key_seq_num);
    esp_zb_lock_release();
    return err;
}

esp_err_t uzb_core_broadcast_network_key(const uint8_t key[16], uint8_t key_seq_num) {
    if (key == NULL) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!s_started) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!esp_zb_lock_acquire(pdMS_TO_TICKS(5000))) {
        ESP_LOGE(TAG, "lock acquire failed during broadcast_network_key");
        return ESP_ERR_TIMEOUT;
    }
    esp_err_t err = esp_zb_secur_broadcast_network_key(key, key_seq_num);
    esp_zb_lock_release();
    return err;
}

esp_err_t uzb_core_broadcast_network_key_switch(uint8_t key_seq_num) {
    if (!s_started) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!esp_zb_lock_acquire(pdMS_TO_TICKS(5000))) {
        ESP_LOGE(TAG, "lock acquire failed during broadcast_network_key_switch");
        return ESP_ERR_TIMEOUT;
    }
    esp_err_t err = esp_zb_secur_broadcast_network_key_switch(key_seq_num);
    esp_zb_lock_release();
    return err;
}

esp_err_t uzb_core_add_install_code(const uint8_t ieee_addr[8], const char *ic_str) {
    if (!s_inited) {
        return ESP_ERR_INVALID_STATE;
    }
    if (ieee_addr == NULL || ic_str == NULL || ic_str[0] == '\0') {
        return ESP_ERR_INVALID_ARG;
    }
    if (!esp_zb_lock_acquire(pdMS_TO_TICKS(5000))) {
        ESP_LOGE(TAG, "lock acquire failed during add_install_code");
        return ESP_ERR_TIMEOUT;
    }
    esp_zb_ieee_addr_t addr = {0};
    memcpy(addr, ieee_addr, sizeof(addr));
    esp_err_t err = esp_zb_secur_ic_str_add(addr, (char *)ic_str);
    esp_zb_lock_release();
    return err;
}

esp_err_t uzb_core_set_local_install_code(const char *ic_str) {
    if (!s_inited) {
        return ESP_ERR_INVALID_STATE;
    }
    if (ic_str == NULL || ic_str[0] == '\0') {
        return ESP_ERR_INVALID_ARG;
    }
    if (!esp_zb_lock_acquire(pdMS_TO_TICKS(5000))) {
        ESP_LOGE(TAG, "lock acquire failed during set_local_install_code");
        return ESP_ERR_TIMEOUT;
    }
    esp_err_t err = esp_zb_secur_ic_str_set((char *)ic_str);
    esp_zb_lock_release();
    return err;
}

esp_err_t uzb_core_remove_install_code(const uint8_t ieee_addr[8]) {
    if (!s_inited) {
        return ESP_ERR_INVALID_STATE;
    }
    if (ieee_addr == NULL) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!esp_zb_lock_acquire(pdMS_TO_TICKS(5000))) {
        ESP_LOGE(TAG, "lock acquire failed during remove_install_code");
        return ESP_ERR_TIMEOUT;
    }
    esp_zb_ieee_addr_t addr = {0};
    memcpy(addr, ieee_addr, sizeof(addr));
    esp_err_t err = esp_zb_secur_ic_remove_req(addr);
    esp_zb_lock_release();
    return err;
}

esp_err_t uzb_core_remove_all_install_codes(void) {
    if (!s_inited) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!esp_zb_lock_acquire(pdMS_TO_TICKS(5000))) {
        ESP_LOGE(TAG, "lock acquire failed during remove_all_install_codes");
        return ESP_ERR_TIMEOUT;
    }
    esp_err_t err = esp_zb_secur_ic_remove_all_req();
    esp_zb_lock_release();
    return err;
}

static esp_err_t uzb_core_send_bind_like_cmd(const uint8_t src_ieee_addr[8], uint8_t src_endpoint, uint16_t cluster_id,
                                             const uint8_t dst_ieee_addr[8], uint8_t dst_endpoint, uint16_t req_dst_short_addr,
                                             bool unbind) {
    if (!s_started || !s_device_registered) {
        return ESP_ERR_INVALID_STATE;
    }
    if (src_ieee_addr == NULL || dst_ieee_addr == NULL) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!uzb_valid_endpoint_id(src_endpoint) || !uzb_valid_endpoint_id(dst_endpoint)) {
        return ESP_ERR_INVALID_ARG;
    }
    if (req_dst_short_addr == 0xFFFF) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!esp_zb_lock_acquire(pdMS_TO_TICKS(5000))) {
        ESP_LOGE(TAG, "lock acquire failed during %sbind_cmd", unbind ? "un" : "");
        return ESP_ERR_TIMEOUT;
    }

    esp_zb_zdo_bind_req_param_t req = {0};
    memcpy(req.src_address, src_ieee_addr, sizeof(req.src_address));
    req.src_endp = src_endpoint;
    req.cluster_id = cluster_id;
    req.dst_addr_mode = ESP_ZB_ZDO_BIND_DST_ADDR_MODE_64_BIT_EXTENDED;
    memcpy(req.dst_address_u.addr_long, dst_ieee_addr, sizeof(req.dst_address_u.addr_long));
    req.dst_endp = dst_endpoint;
    req.req_dst_addr = req_dst_short_addr;

    if (unbind) {
        esp_zb_zdo_device_unbind_req(&req, NULL, NULL);
    } else {
        esp_zb_zdo_device_bind_req(&req, NULL, NULL);
    }

    esp_zb_lock_release();
    return ESP_OK;
}

esp_err_t uzb_core_send_bind_cmd(const uint8_t src_ieee_addr[8], uint8_t src_endpoint, uint16_t cluster_id,
                                 const uint8_t dst_ieee_addr[8], uint8_t dst_endpoint, uint16_t req_dst_short_addr) {
    return uzb_core_send_bind_like_cmd(src_ieee_addr, src_endpoint, cluster_id, dst_ieee_addr, dst_endpoint, req_dst_short_addr, false);
}

esp_err_t uzb_core_send_unbind_cmd(const uint8_t src_ieee_addr[8], uint8_t src_endpoint, uint16_t cluster_id,
                                   const uint8_t dst_ieee_addr[8], uint8_t dst_endpoint, uint16_t req_dst_short_addr) {
    return uzb_core_send_bind_like_cmd(src_ieee_addr, src_endpoint, cluster_id, dst_ieee_addr, dst_endpoint, req_dst_short_addr, true);
}

esp_err_t uzb_core_request_binding_table(uint16_t dst_short_addr, uint8_t start_index) {
    // Read-only ZDO queries must work for coordinator-only stacks
    // even if no local ZCL endpoint was registered.
    if (!s_started) {
        return ESP_ERR_INVALID_STATE;
    }
    if (dst_short_addr == 0xFFFF) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!esp_zb_lock_acquire(pdMS_TO_TICKS(5000))) {
        ESP_LOGE(TAG, "lock acquire failed during request_binding_table");
        return ESP_ERR_TIMEOUT;
    }

    uzb_bind_table_lock();
    memset(&s_bind_table_snapshot, 0, sizeof(s_bind_table_snapshot));
    uzb_bind_table_unlock();

    esp_zb_zdo_mgmt_bind_param_t req = {0};
    req.start_index = start_index;
    req.dst_addr = dst_short_addr;
    esp_zb_zdo_binding_table_req(&req, uzb_binding_table_response_cb, NULL);

    esp_zb_lock_release();
    return ESP_OK;
}

esp_err_t uzb_core_get_binding_table_snapshot(uzb_bind_table_snapshot_t *out_snapshot) {
    if (out_snapshot == NULL) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!s_started) {
        return ESP_ERR_INVALID_STATE;
    }

    uzb_bind_table_lock();
    if (!s_bind_table_snapshot.valid) {
        uzb_bind_table_unlock();
        return ESP_ERR_NOT_FOUND;
    }
    *out_snapshot = s_bind_table_snapshot;
    uzb_bind_table_unlock();
    return ESP_OK;
}

esp_err_t uzb_core_request_active_endpoints(uint16_t dst_short_addr) {
    if (!s_started) {
        return ESP_ERR_INVALID_STATE;
    }
    if (dst_short_addr == 0xFFFF) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!esp_zb_lock_acquire(pdMS_TO_TICKS(5000))) {
        ESP_LOGE(TAG, "lock acquire failed during request_active_endpoints");
        return ESP_ERR_TIMEOUT;
    }

    uzb_active_ep_lock();
    memset(&s_active_ep_snapshot, 0, sizeof(s_active_ep_snapshot));
    uzb_active_ep_unlock();

    esp_zb_zdo_active_ep_req_param_t req = {0};
    req.addr_of_interest = dst_short_addr;
    esp_zb_zdo_active_ep_req(&req, uzb_active_ep_response_cb, NULL);

    esp_zb_lock_release();
    return ESP_OK;
}

esp_err_t uzb_core_get_active_endpoints_snapshot(uzb_active_ep_snapshot_t *out_snapshot) {
    if (out_snapshot == NULL) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!s_started) {
        return ESP_ERR_INVALID_STATE;
    }

    uzb_active_ep_lock();
    if (!s_active_ep_snapshot.valid) {
        uzb_active_ep_unlock();
        return ESP_ERR_NOT_FOUND;
    }
    *out_snapshot = s_active_ep_snapshot;
    uzb_active_ep_unlock();
    return ESP_OK;
}

esp_err_t uzb_core_request_node_descriptor(uint16_t dst_short_addr) {
    if (!s_started) {
        return ESP_ERR_INVALID_STATE;
    }
    if (dst_short_addr == 0xFFFF) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!esp_zb_lock_acquire(pdMS_TO_TICKS(5000))) {
        ESP_LOGE(TAG, "lock acquire failed during request_node_descriptor");
        return ESP_ERR_TIMEOUT;
    }

    uzb_node_desc_lock();
    memset(&s_node_desc_snapshot, 0, sizeof(s_node_desc_snapshot));
    uzb_node_desc_unlock();

    esp_zb_zdo_node_desc_req_param_t req = {0};
    req.dst_nwk_addr = dst_short_addr;
    esp_zb_zdo_node_desc_req(&req, uzb_node_desc_response_cb, NULL);

    esp_zb_lock_release();
    return ESP_OK;
}

esp_err_t uzb_core_get_node_descriptor_snapshot(uzb_node_desc_snapshot_t *out_snapshot) {
    if (out_snapshot == NULL) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!s_started) {
        return ESP_ERR_INVALID_STATE;
    }

    uzb_node_desc_lock();
    if (!s_node_desc_snapshot.valid) {
        uzb_node_desc_unlock();
        return ESP_ERR_NOT_FOUND;
    }
    *out_snapshot = s_node_desc_snapshot;
    uzb_node_desc_unlock();
    return ESP_OK;
}

esp_err_t uzb_core_request_simple_descriptor(uint16_t dst_short_addr, uint8_t endpoint) {
    if (!s_started) {
        return ESP_ERR_INVALID_STATE;
    }
    if (dst_short_addr == 0xFFFF || !uzb_valid_endpoint_id(endpoint)) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!esp_zb_lock_acquire(pdMS_TO_TICKS(5000))) {
        ESP_LOGE(TAG, "lock acquire failed during request_simple_descriptor");
        return ESP_ERR_TIMEOUT;
    }

    uzb_simple_desc_lock();
    memset(&s_simple_desc_snapshot, 0, sizeof(s_simple_desc_snapshot));
    s_simple_desc_snapshot.addr = dst_short_addr;
    uzb_simple_desc_unlock();

    esp_zb_zdo_simple_desc_req_param_t req = {0};
    req.addr_of_interest = dst_short_addr;
    req.endpoint = endpoint;
    esp_zb_zdo_simple_desc_req(&req, uzb_simple_desc_response_cb, NULL);

    esp_zb_lock_release();
    return ESP_OK;
}

esp_err_t uzb_core_get_simple_descriptor_snapshot(uzb_simple_desc_snapshot_t *out_snapshot) {
    if (out_snapshot == NULL) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!s_started) {
        return ESP_ERR_INVALID_STATE;
    }

    uzb_simple_desc_lock();
    if (!s_simple_desc_snapshot.valid) {
        uzb_simple_desc_unlock();
        return ESP_ERR_NOT_FOUND;
    }
    *out_snapshot = s_simple_desc_snapshot;
    uzb_simple_desc_unlock();
    return ESP_OK;
}

esp_err_t uzb_core_request_power_descriptor(uint16_t dst_short_addr) {
    if (!s_started) {
        return ESP_ERR_INVALID_STATE;
    }
    if (dst_short_addr == 0xFFFF) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!esp_zb_lock_acquire(pdMS_TO_TICKS(5000))) {
        ESP_LOGE(TAG, "lock acquire failed during request_power_descriptor");
        return ESP_ERR_TIMEOUT;
    }

    uzb_power_desc_lock();
    memset(&s_power_desc_snapshot, 0, sizeof(s_power_desc_snapshot));
    uzb_power_desc_unlock();

    esp_zb_zdo_power_desc_req_param_t req = {0};
    req.dst_nwk_addr = dst_short_addr;
    esp_zb_zdo_power_desc_req(&req, uzb_power_desc_response_cb, NULL);

    esp_zb_lock_release();
    return ESP_OK;
}

esp_err_t uzb_core_get_power_descriptor_snapshot(uzb_power_desc_snapshot_t *out_snapshot) {
    if (out_snapshot == NULL) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!s_started) {
        return ESP_ERR_INVALID_STATE;
    }

    uzb_power_desc_lock();
    if (!s_power_desc_snapshot.valid) {
        uzb_power_desc_unlock();
        return ESP_ERR_NOT_FOUND;
    }
    *out_snapshot = s_power_desc_snapshot;
    uzb_power_desc_unlock();
    return ESP_OK;
}

esp_err_t uzb_core_get_network_runtime(uzb_network_runtime_t *out_runtime) {
    if (out_runtime == NULL) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!s_started) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!esp_zb_lock_acquire(pdMS_TO_TICKS(5000))) {
        ESP_LOGE(TAG, "lock acquire failed during get_network_runtime");
        return ESP_ERR_TIMEOUT;
    }

    memset(out_runtime, 0, sizeof(*out_runtime));
    out_runtime->channel = (uint8_t)esp_zb_get_current_channel();
    out_runtime->pan_id = esp_zb_get_pan_id();
    out_runtime->short_addr = esp_zb_get_short_address();
    esp_zb_get_extended_pan_id(out_runtime->extended_pan_id);

    esp_zb_lock_release();

    uzb_network_state_lock();
    out_runtime->formed = s_network_formed ? 1 : 0;
    out_runtime->joined = s_network_joined ? 1 : 0;
    uzb_network_state_unlock();
    return ESP_OK;
}

esp_err_t uzb_core_get_short_addr(uint16_t *out_short_addr) {
    if (out_short_addr == NULL) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!s_started) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!esp_zb_lock_acquire(pdMS_TO_TICKS(5000))) {
        ESP_LOGE(TAG, "lock acquire failed during get_short_addr");
        return ESP_ERR_TIMEOUT;
    }
    *out_short_addr = esp_zb_get_short_address();
    esp_zb_lock_release();
    return ESP_OK;
}

esp_err_t uzb_core_get_last_joined_short_addr(uint16_t *out_short_addr) {
    if (out_short_addr == NULL) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!s_started) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!s_last_joined_valid) {
        return ESP_ERR_NOT_FOUND;
    }
    *out_short_addr = s_last_joined_short_addr;
    return ESP_OK;
}

esp_err_t uzb_core_get_ieee_addr(uint8_t out_ieee_addr[8]) {
    if (out_ieee_addr == NULL) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!s_started) {
        return ESP_ERR_INVALID_STATE;
    }
    if (!esp_zb_lock_acquire(pdMS_TO_TICKS(5000))) {
        ESP_LOGE(TAG, "lock acquire failed during get_ieee_addr");
        return ESP_ERR_TIMEOUT;
    }
    esp_zb_ieee_addr_t long_addr = {0};
    esp_zb_get_long_address(long_addr);
    esp_zb_lock_release();
    memcpy(out_ieee_addr, long_addr, 8);
    return ESP_OK;
}

bool uzb_core_is_started(void) {
    return s_started;
}

void uzb_core_set_dispatch_request_cb(uzb_dispatch_request_cb_t cb) {
    uzb_event_lock();
    s_dispatch_request_cb = cb;
    uzb_event_unlock();
    uzb_request_dispatch_if_needed();
}

bool uzb_core_pop_event(uzb_event_t *out_event) {
    if (out_event == NULL) {
        return false;
    }

    bool has_event = false;
    uzb_event_lock();
    if (s_event_depth > 0) {
        *out_event = s_event_queue[s_event_tail];
        s_event_tail = (uint8_t)((s_event_tail + 1) % UZB_EVENT_QUEUE_LEN);
        s_event_depth -= 1;
        s_event_stats.depth = s_event_depth;
        s_event_stats.dispatched += 1;
        has_event = true;
    }
    uzb_event_unlock();
    return has_event;
}

void uzb_core_dispatch_complete(void) {
    bool need_reschedule = false;
    uzb_dispatch_request_cb_t cb = NULL;

    uzb_event_lock();
    if (s_event_depth == 0) {
        s_dispatch_pending = false;
    } else {
        cb = s_dispatch_request_cb;
        need_reschedule = (cb != NULL);
        if (!need_reschedule) {
            s_dispatch_pending = false;
        }
    }
    uzb_event_unlock();

    if (!need_reschedule) {
        return;
    }

    if (!cb()) {
        uzb_event_lock();
        s_dispatch_pending = false;
        s_event_stats.dropped_schedule_fail += 1;
        uzb_event_unlock();
    }
}

void uzb_core_get_event_stats(uzb_event_stats_t *out_stats) {
    if (out_stats == NULL) {
        return;
    }
    uzb_event_lock();
    *out_stats = s_event_stats;
    uzb_event_unlock();
}

void esp_zb_app_signal_handler(esp_zb_app_signal_t *signal_s) {
    if (signal_s == NULL || signal_s->p_app_signal == NULL) {
        ESP_LOGW(TAG, "app signal: null");
        return;
    }

    esp_zb_app_signal_type_t sig = *(signal_s->p_app_signal);
    esp_err_t status = signal_s->esp_err_status;
    void *params = esp_zb_app_signal_get_params(signal_s->p_app_signal);
    ESP_LOGI(TAG, "signal=0x%02x status=%s", (unsigned int)sig, esp_err_to_name(status));
    uzb_enqueue_app_signal_event((uint16_t)sig, (int32_t)status);

    if (status == ESP_OK && params != NULL) {
        switch (sig) {
            case ESP_ZB_ZDO_SIGNAL_DEVICE_ANNCE: {
                const esp_zb_zdo_signal_device_annce_params_t *p = (const esp_zb_zdo_signal_device_annce_params_t *)params;
                uzb_update_last_joined_short_addr(p->device_short_addr);
                break;
            }
            case ESP_ZB_ZDO_SIGNAL_DEVICE_UPDATE: {
                const esp_zb_zdo_signal_device_update_params_t *p = (const esp_zb_zdo_signal_device_update_params_t *)params;
                if (p->status != ESP_ZB_ZDO_STANDARD_DEV_LEFT) {
                    uzb_update_last_joined_short_addr(p->short_addr);
                } else {
                    uzb_clear_last_joined_short_addr(p->short_addr);
                }
                break;
            }
            case ESP_ZB_ZDO_SIGNAL_DEVICE_AUTHORIZED: {
                const esp_zb_zdo_signal_device_authorized_params_t *p = (const esp_zb_zdo_signal_device_authorized_params_t *)params;
                uzb_update_last_joined_short_addr(p->short_addr);
                break;
            }
            case ESP_ZB_ZDO_SIGNAL_LEAVE_INDICATION: {
                const esp_zb_zdo_signal_leave_indication_params_t *p = (const esp_zb_zdo_signal_leave_indication_params_t *)params;
                uzb_clear_last_joined_short_addr(p->short_addr);
                break;
            }
            default:
                break;
        }
    }

    if (status == ESP_OK) {
        switch (sig) {
            case ESP_ZB_BDB_SIGNAL_FORMATION:
                uzb_set_network_state(true, true);
                break;
            case ESP_ZB_BDB_SIGNAL_STEERING:
                if (s_role == ESP_ZB_DEVICE_TYPE_COORDINATOR) {
                    uzb_set_network_state(true, true);
                } else {
                    uzb_set_network_joined(true);
                }
                break;
            default:
                break;
        }
    }

    switch (sig) {
        case ESP_ZB_ZDO_SIGNAL_SKIP_STARTUP:
        case ESP_ZB_BDB_SIGNAL_DEVICE_FIRST_START:
        case ESP_ZB_BDB_SIGNAL_DEVICE_REBOOT: {
            if (status != ESP_OK) {
                break;
            }
            bool factory_new = esp_zb_bdb_is_factory_new();
            if (factory_new) {
                uzb_set_network_state(false, false);
            } else if (s_role == ESP_ZB_DEVICE_TYPE_COORDINATOR) {
                uzb_set_network_state(true, true);
            } else {
                uzb_set_network_state(false, true);
            }
            uint8_t mode = ESP_ZB_BDB_MODE_NETWORK_STEERING;
            if (s_form_network && s_role == ESP_ZB_DEVICE_TYPE_COORDINATOR) {
                mode = ESP_ZB_BDB_MODE_NETWORK_FORMATION;
            }
            esp_err_t err = esp_zb_bdb_start_top_level_commissioning(mode);
            if (err != ESP_OK) {
                ESP_LOGE(TAG, "commissioning start failed: %s", esp_err_to_name(err));
            }
            break;
        }
        default:
            break;
    }
}

