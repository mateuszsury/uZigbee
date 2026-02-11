#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "esp_err.h"

typedef enum {
    UZB_ROLE_COORDINATOR = 0,
    UZB_ROLE_ROUTER = 1,
    UZB_ROLE_END_DEVICE = 2,
} uzb_role_t;

typedef struct {
    uint16_t signal;
    int32_t status;
} uzb_app_signal_event_t;

typedef struct {
    uint8_t zcl_type;
    bool bool_value;
    int32_t int_value;
    uint32_t uint_value;
} uzb_attr_value_t;

#define UZB_BASIC_STR_MAX_MANUFACTURER 32
#define UZB_BASIC_STR_MAX_MODEL 32
#define UZB_BASIC_STR_MAX_DATE_CODE 16
#define UZB_BASIC_STR_MAX_SW_BUILD_ID 16

typedef struct {
    uint8_t has_manufacturer;
    uint8_t has_model;
    uint8_t has_date_code;
    uint8_t has_sw_build_id;
    uint8_t has_power_source;
    uint8_t manufacturer[UZB_BASIC_STR_MAX_MANUFACTURER + 1];
    uint8_t model[UZB_BASIC_STR_MAX_MODEL + 1];
    uint8_t date_code[UZB_BASIC_STR_MAX_DATE_CODE + 1];
    uint8_t sw_build_id[UZB_BASIC_STR_MAX_SW_BUILD_ID + 1];
    uint8_t power_source;
} uzb_basic_identity_cfg_t;

typedef struct {
    uint32_t enqueued;
    uint32_t dropped_queue_full;
    uint32_t dropped_schedule_fail;
    uint32_t dispatched;
    uint32_t max_depth;
    uint32_t depth;
} uzb_event_stats_t;

// Keep snapshot bounded to protect RAM usage on ESP32-C6.
#define UZB_BIND_TABLE_MAX_RECORDS (8)
#define UZB_ACTIVE_EP_MAX_ENDPOINTS (16)
#define UZB_SIMPLE_DESC_MAX_CLUSTERS (16)

typedef struct {
    uint8_t src_ieee_addr[8];
    uint8_t src_endpoint;
    uint16_t cluster_id;
    uint8_t dst_addr_mode;
    uint8_t has_dst_short_addr;
    uint16_t dst_short_addr;
    uint8_t has_dst_ieee_addr;
    uint8_t dst_ieee_addr[8];
    uint8_t has_dst_endpoint;
    uint8_t dst_endpoint;
} uzb_bind_table_record_t;

typedef struct {
    uint8_t valid;
    uint8_t status;
    uint8_t index;
    uint8_t total;
    uint8_t count;
    uint8_t record_count;
    uzb_bind_table_record_t records[UZB_BIND_TABLE_MAX_RECORDS];
} uzb_bind_table_snapshot_t;

typedef struct {
    uint8_t valid;
    uint8_t status;
    uint8_t count;
    uint8_t endpoints[UZB_ACTIVE_EP_MAX_ENDPOINTS];
} uzb_active_ep_snapshot_t;

typedef struct {
    uint8_t valid;
    uint8_t status;
    uint16_t addr;
    uint8_t has_desc;
    uint16_t node_desc_flags;
    uint8_t mac_capability_flags;
    uint16_t manufacturer_code;
    uint8_t max_buf_size;
    uint16_t max_incoming_transfer_size;
    uint16_t server_mask;
    uint16_t max_outgoing_transfer_size;
    uint8_t desc_capability_field;
} uzb_node_desc_snapshot_t;

typedef struct {
    uint8_t valid;
    uint8_t status;
    uint16_t addr;
    uint8_t has_desc;
    uint8_t endpoint;
    uint16_t profile_id;
    uint16_t device_id;
    uint8_t device_version;
    uint8_t input_count;
    uint8_t output_count;
    uint16_t input_clusters[UZB_SIMPLE_DESC_MAX_CLUSTERS];
    uint16_t output_clusters[UZB_SIMPLE_DESC_MAX_CLUSTERS];
} uzb_simple_desc_snapshot_t;

typedef struct {
    uint8_t valid;
    uint8_t status;
    uint16_t addr;
    uint8_t has_desc;
    uint8_t current_power_mode;
    uint8_t available_power_sources;
    uint8_t current_power_source;
    uint8_t current_power_source_level;
} uzb_power_desc_snapshot_t;

typedef struct {
    uint8_t channel;
    uint16_t pan_id;
    uint8_t extended_pan_id[8];
    uint16_t short_addr;
    uint8_t formed;
    uint8_t joined;
} uzb_network_runtime_t;

typedef enum {
    UZB_EVENT_TYPE_APP_SIGNAL = 1,
    UZB_EVENT_TYPE_ATTR_SET = 2,
} uzb_event_type_t;

typedef struct {
    uint8_t has_source;
    uint16_t source_short_addr;
    uint8_t source_endpoint;
    uint8_t endpoint;
    uint16_t cluster_id;
    uint16_t attr_id;
    int32_t status;
    uzb_attr_value_t value;
} uzb_attr_set_event_t;

typedef struct {
    uint8_t type;
    union {
        uzb_app_signal_event_t app_signal;
        uzb_attr_set_event_t attr_set;
    } data;
} uzb_event_t;

typedef bool (*uzb_dispatch_request_cb_t)(void);

esp_err_t uzb_core_init(uzb_role_t role);
esp_err_t uzb_core_create_endpoint(uint8_t endpoint, uint16_t device_id, uint16_t profile_id);
esp_err_t uzb_core_create_on_off_light_endpoint(uint8_t endpoint);
esp_err_t uzb_core_create_on_off_switch_endpoint(uint8_t endpoint);
esp_err_t uzb_core_create_dimmable_switch_endpoint(uint8_t endpoint);
esp_err_t uzb_core_create_dimmable_light_endpoint(uint8_t endpoint);
esp_err_t uzb_core_create_color_light_endpoint(uint8_t endpoint);
esp_err_t uzb_core_create_temperature_sensor_endpoint(uint8_t endpoint);
esp_err_t uzb_core_create_humidity_sensor_endpoint(uint8_t endpoint);
esp_err_t uzb_core_create_pressure_sensor_endpoint(uint8_t endpoint);
esp_err_t uzb_core_create_climate_sensor_endpoint(uint8_t endpoint);
esp_err_t uzb_core_create_power_outlet_endpoint(uint8_t endpoint, bool with_metering);
esp_err_t uzb_core_create_door_lock_endpoint(uint8_t endpoint);
esp_err_t uzb_core_create_door_lock_controller_endpoint(uint8_t endpoint);
esp_err_t uzb_core_create_thermostat_endpoint(uint8_t endpoint);
esp_err_t uzb_core_create_occupancy_sensor_endpoint(uint8_t endpoint);
esp_err_t uzb_core_create_window_covering_endpoint(uint8_t endpoint);
esp_err_t uzb_core_create_ias_zone_endpoint(uint8_t endpoint, uint16_t zone_type);
esp_err_t uzb_core_create_contact_sensor_endpoint(uint8_t endpoint);
esp_err_t uzb_core_create_motion_sensor_endpoint(uint8_t endpoint);
esp_err_t uzb_core_clear_custom_clusters(void);
esp_err_t uzb_core_add_custom_cluster(uint16_t cluster_id, uint8_t cluster_role);
esp_err_t uzb_core_add_custom_attr(uint16_t cluster_id, uint16_t attr_id, uint8_t attr_type, uint8_t attr_access, int32_t initial_value);
esp_err_t uzb_core_set_basic_identity(uint8_t endpoint, const uzb_basic_identity_cfg_t *cfg);
esp_err_t uzb_core_get_basic_identity(uint8_t endpoint, uzb_basic_identity_cfg_t *out_cfg);
esp_err_t uzb_core_register_device(void);
esp_err_t uzb_core_start(bool form_network);
esp_err_t uzb_core_permit_join(uint8_t duration_s);
esp_err_t uzb_core_set_primary_channel_mask(uint32_t channel_mask);
esp_err_t uzb_core_set_pan_id(uint16_t pan_id);
esp_err_t uzb_core_set_extended_pan_id(const uint8_t ext_pan_id[8]);
esp_err_t uzb_core_enable_wifi_i154_coex(void);
esp_err_t uzb_core_start_network_steering(void);
esp_err_t uzb_core_get_last_joined_short_addr(uint16_t *out_short_addr);
esp_err_t uzb_core_get_attribute(uint8_t endpoint, uint16_t cluster_id, uint8_t cluster_role, uint16_t attr_id, uzb_attr_value_t *out_value);
esp_err_t uzb_core_set_attribute(uint8_t endpoint, uint16_t cluster_id, uint8_t cluster_role, uint16_t attr_id, const uzb_attr_value_t *in_value, bool check, uint8_t *out_zcl_status);
esp_err_t uzb_core_configure_reporting(uint8_t src_endpoint, uint16_t dst_short_addr, uint8_t dst_endpoint,
                                       uint16_t cluster_id, uint16_t attr_id, uint8_t attr_type,
                                       uint16_t min_interval, uint16_t max_interval,
                                       bool has_reportable_change, int32_t reportable_change);
esp_err_t uzb_core_send_on_off_cmd(uint8_t src_endpoint, uint16_t dst_short_addr, uint8_t dst_endpoint, uint8_t cmd_id);
esp_err_t uzb_core_send_level_cmd(uint8_t src_endpoint, uint16_t dst_short_addr, uint8_t dst_endpoint, uint8_t level, uint16_t transition_time_ds, bool with_onoff);
esp_err_t uzb_core_send_color_move_to_color_cmd(
    uint8_t src_endpoint,
    uint16_t dst_short_addr,
    uint8_t dst_endpoint,
    uint16_t color_x,
    uint16_t color_y,
    uint16_t transition_time_ds
);
esp_err_t uzb_core_send_color_move_to_color_temperature_cmd(
    uint8_t src_endpoint,
    uint16_t dst_short_addr,
    uint8_t dst_endpoint,
    uint16_t color_temperature,
    uint16_t transition_time_ds
);
esp_err_t uzb_core_send_lock_cmd(uint8_t src_endpoint, uint16_t dst_short_addr, uint8_t dst_endpoint, bool lock);
esp_err_t uzb_core_send_group_add_cmd(uint8_t src_endpoint, uint16_t dst_short_addr, uint8_t dst_endpoint, uint16_t group_id);
esp_err_t uzb_core_send_group_remove_cmd(uint8_t src_endpoint, uint16_t dst_short_addr, uint8_t dst_endpoint, uint16_t group_id);
esp_err_t uzb_core_send_group_remove_all_cmd(uint8_t src_endpoint, uint16_t dst_short_addr, uint8_t dst_endpoint);
esp_err_t uzb_core_send_scene_add_cmd(uint8_t src_endpoint, uint16_t dst_short_addr, uint8_t dst_endpoint,
                                      uint16_t group_id, uint8_t scene_id, uint16_t transition_time_ds);
esp_err_t uzb_core_send_scene_remove_cmd(uint8_t src_endpoint, uint16_t dst_short_addr, uint8_t dst_endpoint,
                                         uint16_t group_id, uint8_t scene_id);
esp_err_t uzb_core_send_scene_remove_all_cmd(uint8_t src_endpoint, uint16_t dst_short_addr, uint8_t dst_endpoint,
                                             uint16_t group_id);
esp_err_t uzb_core_send_scene_recall_cmd(uint8_t src_endpoint, uint16_t dst_short_addr, uint8_t dst_endpoint,
                                         uint16_t group_id, uint8_t scene_id);
esp_err_t uzb_core_send_custom_cmd(uint8_t src_endpoint, uint16_t dst_short_addr, uint8_t dst_endpoint,
                                   uint16_t profile_id, uint16_t cluster_id, uint16_t custom_cmd_id,
                                   uint8_t direction, bool disable_default_resp,
                                   bool manuf_specific, uint16_t manuf_code,
                                   uint8_t data_type, const uint8_t *payload, uint16_t payload_len);
esp_err_t uzb_core_ota_client_query_interval_set(uint8_t endpoint, uint16_t interval_min);
esp_err_t uzb_core_ota_client_query_image_req(uint8_t server_ep, uint16_t server_addr);
esp_err_t uzb_core_ota_client_query_image_stop(void);
bool uzb_core_ota_client_control_supported(void);
esp_err_t uzb_core_set_install_code_policy(bool enabled);
esp_err_t uzb_core_get_install_code_policy(bool *out_enabled);
esp_err_t uzb_core_set_network_security_enabled(bool enabled);
esp_err_t uzb_core_get_network_security_enabled(bool *out_enabled);
esp_err_t uzb_core_set_network_key(const uint8_t key[16]);
esp_err_t uzb_core_get_primary_network_key(uint8_t out_key[16]);
esp_err_t uzb_core_switch_network_key(const uint8_t key[16], uint8_t key_seq_num);
esp_err_t uzb_core_broadcast_network_key(const uint8_t key[16], uint8_t key_seq_num);
esp_err_t uzb_core_broadcast_network_key_switch(uint8_t key_seq_num);
esp_err_t uzb_core_add_install_code(const uint8_t ieee_addr[8], const char *ic_str);
esp_err_t uzb_core_set_local_install_code(const char *ic_str);
esp_err_t uzb_core_remove_install_code(const uint8_t ieee_addr[8]);
esp_err_t uzb_core_remove_all_install_codes(void);
esp_err_t uzb_core_send_bind_cmd(const uint8_t src_ieee_addr[8], uint8_t src_endpoint, uint16_t cluster_id,
                                 const uint8_t dst_ieee_addr[8], uint8_t dst_endpoint, uint16_t req_dst_short_addr);
esp_err_t uzb_core_send_unbind_cmd(const uint8_t src_ieee_addr[8], uint8_t src_endpoint, uint16_t cluster_id,
                                   const uint8_t dst_ieee_addr[8], uint8_t dst_endpoint, uint16_t req_dst_short_addr);
esp_err_t uzb_core_request_binding_table(uint16_t dst_short_addr, uint8_t start_index);
esp_err_t uzb_core_get_binding_table_snapshot(uzb_bind_table_snapshot_t *out_snapshot);
esp_err_t uzb_core_request_active_endpoints(uint16_t dst_short_addr);
esp_err_t uzb_core_get_active_endpoints_snapshot(uzb_active_ep_snapshot_t *out_snapshot);
esp_err_t uzb_core_request_node_descriptor(uint16_t dst_short_addr);
esp_err_t uzb_core_get_node_descriptor_snapshot(uzb_node_desc_snapshot_t *out_snapshot);
esp_err_t uzb_core_request_simple_descriptor(uint16_t dst_short_addr, uint8_t endpoint);
esp_err_t uzb_core_get_simple_descriptor_snapshot(uzb_simple_desc_snapshot_t *out_snapshot);
esp_err_t uzb_core_request_power_descriptor(uint16_t dst_short_addr);
esp_err_t uzb_core_get_power_descriptor_snapshot(uzb_power_desc_snapshot_t *out_snapshot);
esp_err_t uzb_core_get_network_runtime(uzb_network_runtime_t *out_runtime);
esp_err_t uzb_core_get_short_addr(uint16_t *out_short_addr);
esp_err_t uzb_core_get_ieee_addr(uint8_t out_ieee_addr[8]);
bool uzb_core_is_started(void);
void uzb_core_set_dispatch_request_cb(uzb_dispatch_request_cb_t cb);
bool uzb_core_pop_event(uzb_event_t *out_event);
void uzb_core_dispatch_complete(void);
void uzb_core_get_event_stats(uzb_event_stats_t *out_stats);
