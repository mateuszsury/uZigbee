# User C module definition for MicroPython
set(UZIGBEE_DIR ${CMAKE_CURRENT_LIST_DIR})

add_library(usermod_uzigbee INTERFACE)

target_sources(usermod_uzigbee INTERFACE
    ${UZIGBEE_DIR}/mod_uzigbee.c
    ${UZIGBEE_DIR}/uzb_core.c
)

target_include_directories(usermod_uzigbee INTERFACE
    ${UZIGBEE_DIR}
    ${MICROPY_PORT_DIR}/managed_components/espressif__esp-zigbee-lib/include
    ${MICROPY_PORT_DIR}/managed_components/espressif__esp-zboss-lib/include
)

target_link_libraries(usermod INTERFACE usermod_uzigbee)
