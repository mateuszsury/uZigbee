# MicroPython ZigBee Library for ESP32-C6 â€” PeĹ‚ny Plan Projektu

## 1. Streszczenie Wykonawcze

Projekt zakĹ‚ada stworzenie biblioteki **`uzigbee`** â€” kompletnego wrappera MicroPython nad Espressif ESP-Zigbee-SDK (opartym na certyfikowanym stosie ZBOSS), umoĹĽliwiajÄ…cego tworzenie urzÄ…dzeĹ„ ZigBee 3.0 (koordynator, router, end device) w Pythonie na pĹ‚ytkach ESP32-C6. Biblioteka ma oferowaÄ‡ zarĂłwno proste, jednoliniowe API dla poczÄ…tkujÄ…cych, jak i peĹ‚ny dostÄ™p do zaawansowanych funkcji ZCL dla doĹ›wiadczonych deweloperĂłw.

**Priorytet uĹĽytkowy:** UrzÄ…dzenia stworzone za pomocÄ… biblioteki muszÄ… **out-of-the-box poprawnie Ĺ‚Ä…czyÄ‡ siÄ™ i wyĹ›wietlaÄ‡ w Zigbee2MQTT (Z2M)** oraz Home Assistant (ZHA). Oznacza to, ĹĽe biblioteka automatycznie konfiguruje prawidĹ‚owe deskryptory, atrybuty Basic cluster, reporting i strukturÄ™ endpointĂłw tak, aby proces interview Z2M zakoĹ„czyĹ‚ siÄ™ sukcesem bez jakiejkolwiek dodatkowej konfiguracji po stronie uĹĽytkownika.

**Kluczowe wyzwanie:** Projekt ten nie jest typowÄ… bibliotekÄ… Python â€” wymaga stworzenia **customowego firmware MicroPython** z wkompilowanym moduĹ‚em C, ktĂłry stanowi most pomiÄ™dzy interpreterem Pythona a natywnym stosem ZigBee dziaĹ‚ajÄ…cym w osobnym wÄ…tku FreeRTOS.

**Kluczowa cecha:** PeĹ‚na kompatybilnoĹ›Ä‡ z Zigbee2MQTT (Z2M) out-of-the-box. UrzÄ…dzenia tworzone przy uĹĽyciu biblioteki muszÄ… przechodziÄ‡ interview Z2M bez ĹĽadnej dodatkowej konfiguracji, poprawnie siÄ™ wyĹ›wietlaÄ‡, raportowaÄ‡ stany i przyjmowaÄ‡ komendy â€” zarĂłwno jako â€žsupported" (z wbudowanÄ… definicjÄ…), jak i jako urzÄ…dzenia â€žgenerated" (automatycznie rozpoznane po standardowych klastrach ZCL).

---

## 2. Analiza Stanu Obecnego

### 2.1 Hardware: ESP32-C6

| Parametr | WartoĹ›Ä‡ |
|----------|---------|
| Procesor | RISC-V 32-bit, do 160 MHz |
| HP SRAM | 512 KB |
| LP SRAM | 16 KB |
| Flash | 4 MB (typowo), do 16 MB |
| Radio 802.15.4 | Tak â€” ZigBee 3.0, Thread |
| WiFi | Wi-Fi 6 (2.4 GHz) |
| BLE | Bluetooth 5.0 LE |
| PSRAM | Brak (!) |

**Implikacja krytyczna:** 512 KB SRAM to jedyna dostÄ™pna pamiÄ™Ä‡ RAM. Musi siÄ™ w niej zmieĹ›ciÄ‡: FreeRTOS (~30 KB), stos WiFi (opcjonalny, ~40-70 KB), stos ZigBee ZBOSS (~60-100 KB), interpreter MicroPython (~64 KB minimum heap, dynamicznie rosnÄ…cy), bufory sieciowe, tablice routingu i dane aplikacji uĹĽytkownika. Brak PSRAM oznacza, ĹĽe nie da siÄ™ po prostu â€ždorzuciÄ‡ pamiÄ™ci".

### 2.2 Software: ESP-Zigbee-SDK

ESP-Zigbee-SDK to oficjalny framework Espressif do budowy urzÄ…dzeĹ„ ZigBee 3.0. Kluczowe fakty:

- **Zbudowany na ZBOSS** â€” certyfikowany stos ZigBee PRO od DSR Corporation
- **ZBOSS jest zamkniÄ™toĹşrĂłdĹ‚owy** â€” dostarczany wyĹ‚Ä…cznie jako pre-built binary (esp-zboss-lib). Nie ma dostÄ™pu do kodu ĹşrĂłdĹ‚owego bez czĹ‚onkostwa w ZOI (ZBOSS Open Initiative)
- **Licencja esp-zigbee-lib:** Apache 2.0 (warstwa API Espressif)
- **Licencja esp-zboss-lib:** Osobna licencja Espressif â€” pozwala na uĹĽycie z produktami ESP32, ale z ograniczeniami redystrybucji
- **Wymaga ESP-IDF v5.3.2** (zalecane)
- **Wspiera role:** Coordinator (ZC), Router (ZR), End Device (ZED), Sleepy End Device, Green Power Device
- **Model dziaĹ‚ania:** Wymaga dedykowanego tasku FreeRTOS z pÄ™tlÄ… `esp_zb_main_loop_iteration()`

### 2.3 ObsĹ‚ugiwane ZCL Clusters (51 klastrĂłw)

**General:** Basic (0x0000), Power Configuration (0x0001), Device Temp Config (0x0002), Identify (0x0003), Groups (0x0004), Scenes (0x0005), On/Off (0x0006), On/Off Switch Config (0x0007), Level Control (0x0008), Alarms (0x0009), Time (0x000A)

**Analog/Binary/Multistate I/O:** Analog Input/Output/Value (0x000C-0x000E), Binary Input/Output/Value (0x000F-0x0011), Multistate Input/Output/Value (0x0012-0x0014)

**Commissioning & OTA:** Commissioning (0x0015), OTA (0x0019), Poll Control (0x0020), Green Power (0x0021)

**Closures:** Shade Config (0x0100), Door Lock (0x0101), Window Covering (0x0102)

**HVAC:** Thermostat (0x0201), Fan Control (0x0202), Dehumidification Control (0x0203), Thermostat UI (0x0204)

**Lighting:** Color Control (0x0300)

**Measurement & Sensing:** Illuminance (0x0400), Temperature (0x0402), Pressure (0x0403), Flow (0x0404), Humidity (0x0405), Occupancy (0x0406), pH (0x0409), Electrical Conductivity (0x040A), Wind Speed (0x040B), COâ‚‚ (0x040D), PM2.5 (0x042A)

**Security (IAS):** IAS Zone (0x0500), IAS ACE (0x0501), IAS WD (0x0502)

**Smart Energy:** Price (0x0700), Metering (0x0702), Meter ID (0x0B01)

**Diagnostics:** Electrical Measurement (0x0B04), Diagnostics (0x0B05)

**Touchlink:** Touchlink Commissioning (0x1000)

**Custom Clusters:** PeĹ‚ne wsparcie przez ESP-Zigbee-SDK (dowolne cluster ID, atrybuty, komendy)

### 2.4 MicroPython na ESP32-C6

- Oficjalnie wspierany od wersji 1.24 (paĹşdziernik 2024), aktualna wersja: 1.27.0
- Budowany z ESP-IDF v5.x
- **Brak jakiegokolwiek wsparcia ZigBee** â€” ani oficjalnie, ani w projektach spoĹ‚ecznoĹ›ciowych
- Mechanizm rozszerzania: **User C Modules** â€” kod C kompilowany razem z firmware
- **Native .mpy files NIE dziaĹ‚ajÄ… z ESP-IDF API** â€” potwierdzone przez core developera MicroPython (dpgeorge). Dynamiczne Ĺ‚adowanie moduĹ‚Ăłw korzystajÄ…cych ze stosu ZigBee jest niemoĹĽliwe
- Konsekwencja: UĹĽytkownik MUSI flashowaÄ‡ customowy firmware

### 2.5 IstniejÄ…ce Referencje Architektoniczne

**Arduino ZigbeeCore** (esp32-arduino) â€” najlepsza referencja:
- Klasa `ZigbeeCore` (singleton) zarzÄ…dza sieciÄ…
- Klasy endpoint: `ZigbeeLight`, `ZigbeeSwitch`, `ZigbeeTempSensor`, etc.
- KaĹĽda klasa endpoint dziedziczy z `ZigbeeEP`
- Wzorzec: proste API wystawione uĹĽytkownikowi, zĹ‚oĹĽonoĹ›Ä‡ ukryta wewnÄ…trz

### 2.6 Analiza KompatybilnoĹ›ci z Zigbee2MQTT (Z2M)

Zigbee2MQTT to najszerzej uĹĽywany most ZigBeeâ†”MQTT, kluczowy element ekosystemu Home Assistant. Aby urzÄ…dzenia stworzone przez `uzigbee` dziaĹ‚aĹ‚y w Z2M â€žz automatu", muszÄ… poprawnie przejĹ›Ä‡ **proces interview**, ktĂłry Z2M wykonuje dla kaĹĽdego nowego urzÄ…dzenia.

#### 2.6.1 Proces Interview Z2M â€” Co Musi ObsĹ‚uĹĽyÄ‡ UrzÄ…dzenie

Gdy urzÄ…dzenie doĹ‚Ä…cza do sieci, Z2M wysyĹ‚a seriÄ™ zapytaĹ„ ZDO i ZCL:

| Krok | Zapytanie Z2M | Co musi zwrĂłciÄ‡ urzÄ…dzenie | KrytycznoĹ›Ä‡ |
|------|---------------|---------------------------|-------------|
| 1 | **Node Descriptor Request** | Typ urzÄ…dzenia (router/end device), manufacturer code, MAC capabilities | KRYTYCZNE â€” bez tego interview nie ruszy |
| 2 | **Active Endpoints Request** | Lista aktywnych endpoint IDs (np. `[1]` lub `[1, 2]`) | KRYTYCZNE |
| 3 | **Simple Descriptor Request** (per endpoint) | Profile ID, Device ID, lista input clusters, lista output clusters | KRYTYCZNE â€” Z2M na tej podstawie odkrywa funkcje |
| 4 | **Read Basic Cluster Attributes** | `manufacturer_name`, `model_identifier`, `sw_build_id`, `date_code`, `power_source`, `zcl_version`, `application_version`, `hardware_version` | KRYTYCZNE â€” `model_identifier` + `manufacturer_name` to klucz identyfikacji |
| 5 | **Configure Reporting** | UrzÄ…dzenie musi zaakceptowaÄ‡ configure reporting commands dla swoich klastrĂłw | WAĹ»NE â€” bez tego Z2M nie dostanie aktualizacji wartoĹ›ci |
| 6 | **Bind Request** | UrzÄ…dzenie musi zaakceptowaÄ‡ binding do koordynatora | WAĹ»NE â€” reporting wymaga bindingu |

#### 2.6.2 Trzy Poziomy Wsparcia Z2M

Z2M rozpoznaje urzÄ…dzenia na trzech poziomach:

1. **"native"** â€” urzÄ…dzenie ma definicjÄ™ w `zigbee-herdsman-converters` (peĹ‚ne, oficjalne wsparcie). Wymaga PR do repozytorium Z2M. Docelowo `uzigbee` devices powinny trafiÄ‡ do oficjalnych definicji.

2. **"generated"** â€” Z2M automatycznie odkrywa funkcje na podstawie standardowych klastrĂłw ZCL. **To jest nasz gĹ‚Ăłwny target na start.** JeĹ›li urzÄ…dzenie poprawnie implementuje standardowe klastry (On/Off, Level Control, Color Control, Temperature Measurement, itp.), Z2M automatycznie:
   - Rozpozna je jako obsĹ‚ugiwane
   - Wygeneruje wĹ‚aĹ›ciwe kontrolki w UI (przeĹ‚Ä…cznik, suwak, odczyt temperatury)
   - WyĹ›le dane do Home Assistant przez MQTT discovery
   - **Nie wymaga ĹĽadnej konfiguracji po stronie uĹĽytkownika**

3. **"unsupported"** â€” urzÄ…dzenie doĹ‚Ä…czyĹ‚o, interview siÄ™ udaĹ‚, ale Z2M nie rozumie jego klastrĂłw (np. custom/manufacturer-specific clusters). Wymaga external converter.

#### 2.6.3 Kluczowe Atrybuty Basic Cluster dla Z2M

Z2M identyfikuje urzÄ…dzenie przede wszystkim po parze `model_identifier` + `manufacturer_name`. Te wartoĹ›ci MUSZÄ„ byÄ‡ ustawione poprawnie:

```
manufacturer_name:  "uZigbee"          â† identyfikator naszej biblioteki
model_identifier:   "uzb_light_01"     â† unikalny model per typ urzÄ…dzenia
sw_build_id:        "1.0.0"            â† wersja firmware
date_code:          "20260205"         â† data kompilacji
power_source:       0x01/0x03          â† 0x01=mains, 0x03=battery
application_version: 1                 â† wersja aplikacji
hardware_version:    1                 â† wersja hardware
```

#### 2.6.4 Wymogi dla Auto-Discovery ("generated" support)

Aby Z2M poprawnie wygenerowaĹ‚ kontrolki, KAĹ»DY klaster musi:
- MieÄ‡ poprawny `cluster_id` (standardowy ZCL)
- ByÄ‡ wymieniony jako `input cluster` w Simple Descriptor (dla server role)
- ZawieraÄ‡ obowiÄ…zkowe atrybuty ze specyfikacji ZCL (np. On/Off cluster MUSI mieÄ‡ atrybut 0x0000)
- ObsĹ‚ugiwaÄ‡ `Read Attributes` command (0x00) â€” Z2M czyta atrybuty podczas interview
- ObsĹ‚ugiwaÄ‡ `Configure Reporting` command (0x06) â€” Z2M konfiguruje reporting
- ObsĹ‚ugiwaÄ‡ `Write Attributes` command (0x02) dla atrybutĂłw z access=write

#### 2.6.5 Mapowanie KlastrĂłw â†’ Kontrolki Z2M

| Klaster ZCL | Kontrolka Z2M | Expose w HA |
|------------|---------------|-------------|
| On/Off (0x0006) | Switch toggle | `switch` / `light` |
| Level Control (0x0008) | Brightness slider | `light` z `brightness` |
| Color Control (0x0300) | Color picker / temp slider | `light` z `color_xy` / `color_temp` |
| Temperature (0x0402) | Odczyt temperatury | `sensor` (temperature) |
| Humidity (0x0405) | Odczyt wilgotnoĹ›ci | `sensor` (humidity) |
| Pressure (0x0403) | Odczyt ciĹ›nienia | `sensor` (pressure) |
| Occupancy (0x0406) | Czujnik obecnoĹ›ci | `binary_sensor` (occupancy) |
| IAS Zone (0x0500) | Alarm/kontakt/ruch | `binary_sensor` |
| Door Lock (0x0101) | Zamek | `lock` |
| Window Covering (0x0102) | Rolety/zasĹ‚ony | `cover` |
| Thermostat (0x0201) | Termostat | `climate` |
| Power Config (0x0001) | Poziom baterii | `sensor` (battery) |
| Electrical Meas. (0x0B04) | Pomiar energii | `sensor` (power/voltage/current) |
| Metering (0x0702) | Licznik energii | `sensor` (energy) |

---

## 3. Architektura Biblioteki

### 3.1 OgĂłlna Architektura Warstwowa

```
â”Śâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚          Skrypt uĹĽytkownika (Python)         â”‚
â”‚  import uzigbee                             â”‚
â”‚  light = uzigbee.Light(endpoint=1)          â”‚
â”‚  uzigbee.start(role=uzigbee.END_DEVICE)     â”‚
â”‚  # â†’ automatycznie Ĺ‚Ä…czy siÄ™ z Z2M! âś“      â”‚
â”śâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚     Warstwa 4: Z2M Compatibility (Python)   â”‚  â† uzigbee/z2m.py
â”‚  Auto-konfiguracja Basic cluster attrs      â”‚
â”‚  Poprawne deskryptory ZDO                   â”‚
â”‚  Configure Reporting acceptance             â”‚
â”‚  External converter generator               â”‚
â”śâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚     Warstwa 3: High-Level API (Python)      â”‚  â† uzigbee/devices.py, uzigbee/sensors.py
â”‚  Gotowe klasy urzÄ…dzeĹ„ HA                   â”‚
â”‚  Automatyczna konfiguracja klastrĂłw         â”‚
â”śâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚     Warstwa 2: Core API (Python)            â”‚  â† uzigbee/__init__.py, uzigbee/zcl.py
â”‚  Klasy: Node, Endpoint, Cluster, Attribute  â”‚
â”‚  Tworzenie dowolnych konfiguracji ZCL       â”‚
â”śâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚     Warstwa 1: C Binding Module             â”‚  â† mod_uzigbee.c (kompilowany do firmware)
â”‚  MicroPython â†” ESP-Zigbee-SDK bridge        â”‚
â”‚  ZarzÄ…dzanie tasku ZigBee                   â”‚
â”‚  Callback dispatch do Pythona               â”‚
â”‚  Thread safety (mutex/lock)                 â”‚
â”śâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚     ESP-Zigbee-SDK (esp-zigbee-lib)         â”‚  â† Pre-built library (Apache 2.0)
â”śâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚     ZBOSS Stack (esp-zboss-lib)             â”‚  â† Pre-built binary (zamkniÄ™te ĹşrĂłdĹ‚o)
â”śâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚     IEEE 802.15.4 Radio Driver              â”‚
â”śâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚     ESP-IDF / FreeRTOS / Hardware           â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
```

### 3.2 Model WÄ…tkowy (Krytyczne Wyzwanie)

ZigBee stack ZBOSS wymaga:
1. Dedykowanego tasku FreeRTOS (typowo 4096 bajtĂłw stosu)
2. CiÄ…gĹ‚ego wywoĹ‚ywania `esp_zb_main_loop_iteration()` w tym tasku
3. WiÄ™kszoĹ›Ä‡ Zigbee API musi byÄ‡ wywoĹ‚ywana z kontekstem zigbee lock: `esp_zb_lock_acquire()`

MicroPython dziaĹ‚a w swoim wĹ‚asnym tasku. **Problem:** WywoĹ‚ania Python â†’ C â†’ Zigbee muszÄ… przechodziÄ‡ pomiÄ™dzy wÄ…tkami, a callbacki Zigbee â†’ Python muszÄ… byÄ‡ bezpieczne wÄ…tkowo.

**RozwiÄ…zanie: Kolejka zdarzeĹ„ + Scheduler Alarms**

```
MicroPython Task                    Zigbee Task
     â”‚                                   â”‚
     â”‚ â”€â”€ uzigbee.send_command() â”€â”€â–ş     â”‚
     â”‚    [acquire zigbee lock]           â”‚
     â”‚    [call esp_zb_zcl_*()]           â”‚
     â”‚    [release lock]                  â”‚
     â”‚                                   â”‚
     â”‚                                   â”‚ â—„â”€â”€ Callback z ZBOSS
     â”‚                                   â”‚    [wstaw event do ring buffer]
     â”‚                                   â”‚    [esp_zb_scheduler_alarm]
     â”‚ â—„â”€â”€ mp_sched_schedule() â”€â”€â”€â”€â”€     â”‚
     â”‚    [dispatch do Python callback]   â”‚
     â”‚                                   â”‚
```

**Mechanizm szczegĂłĹ‚owy:**
- Komenda z Pythona â†’ C wrapper acquires `esp_zb_lock`, wywoĹ‚uje API, releases lock
- Callback z ZBOSS â†’ C handler zapisuje event do thread-safe ring buffera â†’ `mp_sched_schedule()` wstawia wywoĹ‚anie Python callbacka do kolejki MicroPython schedulera
- Python callback jest wywoĹ‚ywany w kontekĹ›cie MicroPython tasku (bezpieczne)

### 3.3 ZarzÄ…dzanie PamiÄ™ciÄ…

**BudĹĽet RAM (pesymistyczny szacunek dla ESP32-C6 z 512 KB SRAM):**

| Komponent | Szacowany koszt RAM |
|-----------|-------------------|
| FreeRTOS kernel + idle task | ~20-30 KB |
| ZBOSS stack + bufory | ~80-120 KB |
| ESP-IDF system (NVS, flash driver) | ~20-30 KB |
| MicroPython heap (minimum) | ~64 KB (roĹ›nie dynamicznie) |
| Stack dla zigbee task | 4-8 KB |
| Stack dla MicroPython task | 16-20 KB |
| Ring buffer zdarzeĹ„ | ~2-4 KB |
| Tablica routingu (zaleĹĽy od roli) | 5-30 KB |
| **Razem** | **~210-310 KB** |
| **Wolne dla uĹĽytkownika** | **~200-300 KB** |

**Strategie oszczÄ™dzania pamiÄ™ci:**
1. Frozen modules â€” caĹ‚y kod Python wkompilowany we flash (nie zuĹĽywa RAM na kompilacjÄ™)
2. Const data w flash â€” definicje klastrĂłw, atrybutĂłw, ID jako staĹ‚e w C
3. Lazy initialization â€” alokacja buforĂłw dopiero przy uĹĽyciu
4. Konfigurowalny rozmiar tablicy routingu (koordynator potrzebuje wiÄ™cej)
5. Opcjonalne wyĹ‚Ä…czanie WiFi gdy nie jest potrzebne (oszczÄ™dnoĹ›Ä‡ ~40-70 KB)
6. MoĹĽliwoĹ›Ä‡ budowy firmware z podzbiorem klastrĂłw (sdkconfig)

### 3.4 KompatybilnoĹ›Ä‡ z Zigbee2MQTT â€” Architektura

#### 3.4.1 Jak Z2M rozpoznaje urzÄ…dzenie (proces interview)

Gdy nowe urzÄ…dzenie doĹ‚Ä…cza do sieci Z2M, koordynator przeprowadza **interview** â€” sekwencjÄ™ zapytaĹ„ ZDO i ZCL, ktĂłra determinuje czy urzÄ…dzenie pojawi siÄ™ w dashboard i jak bÄ™dzie prezentowane:

```
1. ZDO Node Descriptor Request       â†’ Typ urzÄ…dzenia (router/end device), capabilities
2. ZDO Active Endpoints Request       â†’ Lista aktywnych endpointĂłw (np. [1, 2])
3. ZDO Simple Descriptor Request      â†’ Dla KAĹ»DEGO endpointu: profile ID, device ID,
   (per endpoint)                       lista input clusters, lista output clusters
4. ZCL Read Attributes (Basic Cluster, 0x0000):
   â”śâ”€â”€ 0x0000: ZCL Version
   â”śâ”€â”€ 0x0001: Application Version
   â”śâ”€â”€ 0x0002: Stack Version
   â”śâ”€â”€ 0x0003: Hardware Version
   â”śâ”€â”€ 0x0004: Manufacturer Name      â† KLUCZOWY â€” identyfikacja producenta
   â”śâ”€â”€ 0x0005: Model Identifier        â† KLUCZOWY â€” dopasowanie do definicji urzÄ…dzenia
   â”śâ”€â”€ 0x0006: Date Code
   â”śâ”€â”€ 0x0007: Power Source            â† Typ zasilania (mains/battery)
   â””â”€â”€ 0x4000: SW Build ID
5. Konfiguracja reporting (dla sensorĂłw â€” bind + configure reporting)
```

**Trzy scenariusze rozpoznania w Z2M:**

| Scenariusz | Warunek | Efekt w Z2M |
|-----------|---------|-------------|
| **Supported (native)** | `modelId` pasuje do wbudowanej definicji w zigbee-herdsman-converters | PeĹ‚ne wsparcie, dedykowana ikona, testowane, poprawne exposes |
| **Generated** | Interview OK, standardowe klastry ZCL, ale brak definicji | Z2M automatycznie mapuje klastry na features (np. on/off â†’ switch, temperature â†’ sensor). DziaĹ‚a dobrze jeĹ›li device jest ZCL-compliant |
| **Unsupported** | Interview nie powiĂłdĹ‚ siÄ™ lub brak rozpoznawalnych klastrĂłw | UrzÄ…dzenie widoczne, ale bez kontroli. Wymaga external converter |

**Cel biblioteki: Wszystkie urzÄ…dzenia muszÄ… minimum przechodziÄ‡ scenariusz â€žGenerated" automatycznie, a docelowo dostarczymy external converters dla scenariusza â€žSupported".**

#### 3.4.2 Wymagania Z2M Compliance wbudowane w bibliotekÄ™

Aby urzÄ…dzenie poprawnie przeszĹ‚o interview i dziaĹ‚aĹ‚o w Z2M, nasza biblioteka MUSI zapewniÄ‡:

1. **Poprawne Basic Cluster attributes** â€” wszystkie obowiÄ…zkowe atrybuty muszÄ… zwracaÄ‡ sensowne wartoĹ›ci. Z2M czyta je natychmiast po join i jeĹ›li dostanie bĹ‚Ä…d lub puste odpowiedzi, interview koĹ„czy siÄ™ niepowodzeniem.

2. **Poprawne Simple Descriptor** â€” lista input/output clusters musi dokĹ‚adnie odpowiadaÄ‡ zarejestrowanym klastrom. Z2M na tej podstawie generuje listÄ™ features.

3. **Standardowe klastry zgodne z ZCL spec** â€” klastry muszÄ… implementowaÄ‡ obowiÄ…zkowe atrybuty w zgodzie ze specyfikacjÄ…. Z2M mapuje klastry na features (exposes) automatycznie:
   - On/Off (0x0006) â†’ `switch` expose (state: ON/OFF)
   - Level Control (0x0008) â†’ `brightness` expose (numeric 0-254)
   - Color Control (0x0300) â†’ `color_hs` / `color_temp` / `color_xy` exposes
   - Temperature Measurement (0x0402) â†’ `temperature` expose (numeric Â°C)
   - Humidity Measurement (0x0405) â†’ `humidity` expose (numeric %)
   - Pressure Measurement (0x0403) â†’ `pressure` expose (numeric hPa)
   - IAS Zone (0x0500) â†’ `occupancy` / `contact` / `smoke` / `water_leak` (w zaleĹĽnoĹ›ci od zone_type)
   - Power Configuration (0x0001) â†’ `battery` expose
   - Electrical Measurement (0x0B04) â†’ `power`, `voltage`, `current` exposes
   - Door Lock (0x0101) â†’ `lock` expose
   - Window Covering (0x0102) â†’ `cover` expose (position %)
   - Thermostat (0x0201) â†’ `climate` expose

4. **Attribute Reporting** â€” sensory MUSZÄ„ wysyĹ‚aÄ‡ attribute reports (nie tylko odpowiadaÄ‡ na read requests). Z2M konfiguruje reporting przez binding + configure_reporting. Biblioteka musi to poprawnie obsĹ‚ugiwaÄ‡.

5. **Identify Cluster** â€” Z2M uĹĽywa identify do â€žmigania" urzÄ…dzeniem w UI. Implementacja identify jest prosta ale widocznie poprawia UX.

#### 3.4.3 Predefiniowane Z2M-ready Manufacturer/Model IDs

Biblioteka bÄ™dzie definiowaÄ‡ spĂłjne identyfikatory dla urzÄ…dzeĹ„ tworzonych przez uĹĽytkownikĂłw:

```python
# DomyĹ›lne wartoĹ›ci Basic Cluster â€” gwarantujÄ… poprawny interview
Z2M_DEFAULTS = {
    "manufacturer_name": "uzigbee",     # SpĂłjny manufacturer dla all devices
    "model_id": None,                    # Auto-generowany z klasy: "uzb_Light", "uzb_TempSensor"
    "zcl_version": 8,
    "application_version": 1,
    "stack_version": 2,
    "hw_version": 1,
    "power_source": None,                # Auto: 0x01 (mains) lub 0x03 (battery) z roli
    "date_code": "20250205",
    "sw_build_id": "uzigbee-1.0.0",
}
```

UĹĽytkownik MOĹ»E nadpisaÄ‡ te wartoĹ›ci â€” ale domyĹ›lne zapewniajÄ… ĹĽe interview Z2M zawsze siÄ™ powiedzie.

#### 3.4.4 Dostarczanie External Converters dla Z2M

OprĂłcz scenariusza â€žgenerated" (ktĂłry dziaĹ‚a automatycznie dla standardowych klastrĂłw), biblioteka dostarczy **gotowe external converters** JavaScript dla zigbee-herdsman-converters, dajÄ…ce peĹ‚ne wsparcie â€žnative":

```
uzigbee/
â””â”€â”€ z2m_converters/
    â”śâ”€â”€ README.md                     # Instrukcja instalacji w Z2M
    â”śâ”€â”€ uzigbee_all.js                # Jeden plik z wszystkimi definicjami
    â”śâ”€â”€ uzigbee_lights.js             # Definicje lamp
    â”śâ”€â”€ uzigbee_sensors.js            # Definicje sensorĂłw
    â”śâ”€â”€ uzigbee_switches.js           # Definicje przeĹ‚Ä…cznikĂłw
    â””â”€â”€ uzigbee_custom.js             # Template dla custom devices
```

PrzykĹ‚adowy external converter:
```javascript
// uzigbee_all.js â€” External converter for Zigbee2MQTT
const {
    light, onOff, identify, temperature, humidity, pressure,
    battery, iasZoneAlarm, electricityMeter, windowCovering,
    doorLock, thermostat, occupancy, illuminance, co2, pm25
} = require('zigbee-herdsman-converters/lib/modernExtend');

const definitions = [
    {
        zigbeeModel: ['uzb_Light'],
        model: 'uzb_Light',
        vendor: 'uzigbee',
        description: 'MicroPython ZigBee On/Off Light',
        extend: [onOff(), identify()],
    },
    {
        zigbeeModel: ['uzb_DimmableLight'],
        model: 'uzb_DimmableLight',
        vendor: 'uzigbee',
        description: 'MicroPython ZigBee Dimmable Light',
        extend: [light({"colorTemp": {"range": undefined}})],
    },
    {
        zigbeeModel: ['uzb_ColorLight'],
        model: 'uzb_ColorLight',
        vendor: 'uzigbee',
        description: 'MicroPython ZigBee Color Light',
        extend: [light({"color": {"modes": ["hs", "xy"], "applyRedFix": false}})],
    },
    {
        zigbeeModel: ['uzb_TempSensor'],
        model: 'uzb_TempSensor',
        vendor: 'uzigbee',
        description: 'MicroPython ZigBee Temperature Sensor',
        extend: [temperature(), battery(), identify()],
    },
    {
        zigbeeModel: ['uzb_TempHumSensor'],
        model: 'uzb_TempHumSensor',
        vendor: 'uzigbee',
        description: 'MicroPython ZigBee Temp+Humidity Sensor',
        extend: [temperature(), humidity(), battery(), identify()],
    },
    {
        zigbeeModel: ['uzb_ClimateSensor'],
        model: 'uzb_ClimateSensor',
        vendor: 'uzigbee',
        description: 'MicroPython ZigBee Climate Sensor (T+H+P)',
        extend: [temperature(), humidity(), pressure(), battery(), identify()],
    },
    {
        zigbeeModel: ['uzb_MotionSensor'],
        model: 'uzb_MotionSensor',
        vendor: 'uzigbee',
        description: 'MicroPython ZigBee Motion Sensor',
        extend: [
            iasZoneAlarm({"zoneType": "occupancy", "zoneAttributes": ["alarm_1"]}),
            battery(), identify()
        ],
    },
    {
        zigbeeModel: ['uzb_ContactSensor'],
        model: 'uzb_ContactSensor',
        vendor: 'uzigbee',
        description: 'MicroPython ZigBee Door/Window Sensor',
        extend: [
            iasZoneAlarm({"zoneType": "contact", "zoneAttributes": ["alarm_1"]}),
            battery(), identify()
        ],
    },
    {
        zigbeeModel: ['uzb_PowerOutlet'],
        model: 'uzb_PowerOutlet',
        vendor: 'uzigbee',
        description: 'MicroPython ZigBee Smart Plug',
        extend: [onOff(), electricityMeter(), identify()],
    },
    {
        zigbeeModel: ['uzb_Thermostat'],
        model: 'uzb_Thermostat',
        vendor: 'uzigbee',
        description: 'MicroPython ZigBee Thermostat',
        extend: [thermostat(), identify()],
    },
];

module.exports = definitions;
```

**Cel dĹ‚ugoterminowy:** ZgĹ‚oszenie tych definicji upstream do zigbee-herdsman-converters, aby urzÄ…dzenia uzigbee byĹ‚y rozpoznawane natywnie bez external converters.

### 4.1 Warstwa 1: ModuĹ‚ C (`_uzigbee`)

ModuĹ‚ C eksportuje niskopoziomowe funkcje, nie jest przeznaczony do bezpoĹ›redniego uĹĽycia:

```python
# WewnÄ™trzne API moduĹ‚u C (_uzigbee)
_uzigbee.init(role, radio_config)        # Inicjalizacja stosu
_uzigbee.start(autostart)                # Start stosu ZigBee
_uzigbee.main_loop_step()                # Jeden krok pÄ™tli (jeĹ›li manual mode)

# ZarzÄ…dzanie urzÄ…dzeniem
_uzigbee.create_endpoint(ep_id, device_id, profile_id)
_uzigbee.add_cluster(ep_handle, cluster_id, role, attr_list)
_uzigbee.register_device(ep_list_handle)
_uzigbee.set_attribute(ep_id, cluster_id, attr_id, value)
_uzigbee.get_attribute(ep_id, cluster_id, attr_id)

# Komendy ZCL
_uzigbee.send_zcl_cmd(dst_addr, dst_ep, src_ep, cluster_id, cmd_id, payload)
_uzigbee.send_zcl_raw(dst_addr, frame_bytes)

# SieÄ‡
_uzigbee.form_network(channel_mask, pan_id)
_uzigbee.join_network(channel_mask)
_uzigbee.permit_joining(duration)
_uzigbee.leave_network()
_uzigbee.scan_networks()
_uzigbee.get_network_info()
_uzigbee.get_short_addr()
_uzigbee.get_ieee_addr()

# Binding
_uzigbee.bind_device(src_ep, dst_addr, dst_ep, cluster_id)
_uzigbee.unbind_device(src_ep, dst_addr, dst_ep, cluster_id)

# Callbacki (rejestracja)
_uzigbee.on_signal(callback)              # Stack signals (join, leave, etc.)
_uzigbee.on_attribute_change(callback)    # Attribute changed
_uzigbee.on_zcl_command(callback)         # ZCL command received
_uzigbee.on_device_announce(callback)     # New device joined
_uzigbee.on_bind_request(callback)        # Bind request received

# ZDO (Zigbee Device Object)
_uzigbee.zdo_find_device(cluster_id)       # Match descriptor request
_uzigbee.zdo_active_ep_req(addr)           # Active endpoints request
_uzigbee.zdo_simple_desc_req(addr, ep)     # Simple descriptor request
_uzigbee.zdo_node_desc_req(addr)           # Node descriptor request
_uzigbee.zdo_ieee_addr_req(short_addr)     # IEEE address request
_uzigbee.zdo_nwk_addr_req(ieee_addr)       # Network address request

# Security
_uzigbee.set_network_key(key_bytes)
_uzigbee.set_install_code(ieee_addr, code)
_uzigbee.get_network_key()

# OTA
_uzigbee.ota_start_server(image_path, file_version, hw_version)
_uzigbee.ota_start_client(callback)

# Power management
_uzigbee.set_ed_timeout(timeout)
_uzigbee.set_max_children(count)
_uzigbee.sleep_configure(sleep_mode)

# NVS / Persistent storage
_uzigbee.nvram_erase()
_uzigbee.factory_reset()

# Diagnostyka
_uzigbee.get_neighbor_table()
_uzigbee.get_routing_table()
_uzigbee.get_binding_table()
_uzigbee.get_channel()
_uzigbee.set_channel(channel)
_uzigbee.get_pan_id()
_uzigbee.get_ext_pan_id()
```

### 4.2 Warstwa 2: Core Python API

```python
# uzigbee/__init__.py â€” importy i staĹ‚e
from _uzigbee import *

# Role
COORDINATOR = 0
ROUTER = 1
END_DEVICE = 2
SLEEPY_END_DEVICE = 3

# Profile IDs
PROFILE_HA = 0x0104
PROFILE_ZLL = 0xC05E

# Cluster IDs (peĹ‚na lista jako staĹ‚e)
CLUSTER_BASIC = 0x0000
CLUSTER_POWER_CONFIG = 0x0001
CLUSTER_ON_OFF = 0x0006
CLUSTER_LEVEL_CONTROL = 0x0008
CLUSTER_COLOR_CONTROL = 0x0300
CLUSTER_TEMPERATURE = 0x0402
# ... (wszystkie 51 klastrĂłw)

# Cluster role
CLUSTER_SERVER = 0
CLUSTER_CLIENT = 1
```

```python
# uzigbee/core.py â€” Klasy bazowe

class ZigbeeStack:
    """Singleton zarzÄ…dzajÄ…cy stosem ZigBee."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self._started = False
        self._role = None
        self._endpoints = []
        self._signal_handlers = {}
        self._on_device_joined = None
        self._on_device_left = None

    def init(self, role=COORDINATOR, channel_mask=0x07FFF800):
        """Inicjalizuj stos ZigBee."""
        self._role = role
        _uzigbee.init(role, {"channel_mask": channel_mask})

    def add_endpoint(self, endpoint):
        """Dodaj endpoint do urzÄ…dzenia."""
        self._endpoints.append(endpoint)
        endpoint._register()

    def start(self, autostart=True):
        """Uruchom stos ZigBee i sieÄ‡."""
        _uzigbee.register_device(...)
        _uzigbee.on_signal(self._handle_signal)
        _uzigbee.start(autostart)
        self._started = True

    def permit_joining(self, duration=180):
        """PozwĂłl nowym urzÄ…dzeniom doĹ‚Ä…czyÄ‡ (tylko koordynator/router)."""
        _uzigbee.permit_joining(duration)

    def scan(self):
        """Skanuj dostÄ™pne sieci ZigBee."""
        return _uzigbee.scan_networks()

    def factory_reset(self):
        """Reset ustawieĹ„ sieciowych."""
        _uzigbee.factory_reset()

    @property
    def network_info(self):
        return _uzigbee.get_network_info()

    @property
    def short_address(self):
        return _uzigbee.get_short_addr()

    @property
    def ieee_address(self):
        return _uzigbee.get_ieee_addr()

    def on(self, event, handler):
        """Rejestruj handler zdarzeĹ„."""
        self._signal_handlers[event] = handler

    def _handle_signal(self, signal_type, data):
        if signal_type in self._signal_handlers:
            self._signal_handlers[signal_type](data)


class Endpoint:
    """Reprezentuje Zigbee Endpoint z klastrami."""

    def __init__(self, ep_id, device_id, profile_id=PROFILE_HA):
        self.ep_id = ep_id
        self.device_id = device_id
        self.profile_id = profile_id
        self.clusters = []
        self._handle = None

    def add_cluster(self, cluster):
        self.clusters.append(cluster)

    def _register(self):
        self._handle = _uzigbee.create_endpoint(
            self.ep_id, self.device_id, self.profile_id
        )
        for cluster in self.clusters:
            cluster._register(self._handle)


class Cluster:
    """Reprezentuje ZCL Cluster z atrybutami."""

    def __init__(self, cluster_id, role=CLUSTER_SERVER):
        self.cluster_id = cluster_id
        self.role = role
        self.attributes = []
        self._attr_handlers = {}

    def add_attribute(self, attr_id, attr_type, value=None, access=0x01):
        self.attributes.append({
            "id": attr_id, "type": attr_type,
            "value": value, "access": access
        })

    def set_attribute(self, ep_id, attr_id, value):
        _uzigbee.set_attribute(ep_id, self.cluster_id, attr_id, value)

    def get_attribute(self, ep_id, attr_id):
        return _uzigbee.get_attribute(ep_id, self.cluster_id, attr_id)

    def on_attribute_change(self, attr_id, handler):
        self._attr_handlers[attr_id] = handler

    def send_command(self, dst_addr, dst_ep, src_ep, cmd_id, payload=None):
        _uzigbee.send_zcl_cmd(
            dst_addr, dst_ep, src_ep,
            self.cluster_id, cmd_id, payload or b""
        )

    def _register(self, ep_handle):
        _uzigbee.add_cluster(
            ep_handle, self.cluster_id, self.role, self.attributes
        )
```

### 4.3 Warstwa 3: High-Level API (Gotowe UrzÄ…dzenia)

```python
# uzigbee/devices.py â€” Gotowe urzÄ…dzenia HA

class Light(Endpoint):
    """ZigBee Light â€” najprostsza lampka on/off.
    Z2M-compatible out of the box: przechodzi interview, wyĹ›wietla siÄ™ jako switch.

    UĹĽycie:
        light = uzigbee.Light(endpoint=1)
        zbstack.add_endpoint(light)
        zbstack.start()

        # Reaguj na komendy z sieci (w tym z Z2M):
        light.on_change(lambda state: led.value(state))
    """

    # Z2M Model ID â€” matchowany w external converter lub auto-discovered
    Z2M_MODEL_ID = "uzb_Light"

    def __init__(self, endpoint=10, manufacturer="uzigbee", model=None):
        super().__init__(endpoint, device_id=0x0100)
        self._on_off = False
        self._change_cb = None
        self._manufacturer = manufacturer
        self._model = model or self.Z2M_MODEL_ID
        # Automatycznie dodaje klastry: Basic, Identify, Groups, Scenes, On/Off
        # Z poprawnie wypeĹ‚nionymi atrybutami dla Z2M interview
        self._setup_clusters()

    def _setup_clusters(self):
        # Basic cluster â€” KRYTYCZNY dla Z2M interview
        # Wszystkie atrybuty ktĂłre Z2M czyta muszÄ… zwracaÄ‡ poprawne wartoĹ›ci
        basic = Cluster(CLUSTER_BASIC)
        basic.add_attribute(0x0000, ZCL_UINT8, 8)                  # ZCL version
        basic.add_attribute(0x0001, ZCL_UINT8, 1)                  # App version
        basic.add_attribute(0x0002, ZCL_UINT8, 2)                  # Stack version
        basic.add_attribute(0x0003, ZCL_UINT8, 1)                  # HW version
        basic.add_attribute(0x0004, ZCL_CHAR_STRING, self._manufacturer)  # Manufacturer
        basic.add_attribute(0x0005, ZCL_CHAR_STRING, self._model)         # Model ID
        basic.add_attribute(0x0006, ZCL_CHAR_STRING, "20250205")          # Date code
        basic.add_attribute(0x0007, ZCL_ENUM8, 0x01)               # Power source: mains
        basic.add_attribute(0x4000, ZCL_CHAR_STRING, "uzigbee-1.0")       # SW build
        self.add_cluster(basic)

        # Identify cluster â€” Z2M uĹĽywa go do "migania" urzÄ…dzeniem w UI
        identify = Cluster(CLUSTER_IDENTIFY)
        identify.add_attribute(0x0000, ZCL_UINT16, 0)  # Identify time
        self.add_cluster(identify)

        # Groups, Scenes â€” Z2M wymaga ich dla peĹ‚nego wsparcia lamp
        self.add_cluster(Cluster(CLUSTER_GROUPS))
        self.add_cluster(Cluster(CLUSTER_SCENES))

        # On/Off â€” Z2M mapuje to na "state" expose (ON/OFF toggle w dashboard)
        onoff = Cluster(CLUSTER_ON_OFF)
        onoff.add_attribute(0x0000, ZCL_BOOL, False)
        self.add_cluster(onoff)

    @property
    def state(self):
        return self._on_off

    @state.setter
    def state(self, value):
        self._on_off = bool(value)
        _uzigbee.set_attribute(self.ep_id, CLUSTER_ON_OFF, 0x0000, self._on_off)

    def on_change(self, callback):
        """Callback wywoĹ‚ywany gdy sieÄ‡ zmieni stan lampki."""
        self._change_cb = callback

    def toggle(self):
        self.state = not self.state


class DimmableLight(Light):
    """Ĺšciemnialna lampka z kontrolÄ… poziomu."""

    def __init__(self, endpoint=10):
        super().__init__(endpoint)
        self.device_id = 0x0101
        level = Cluster(CLUSTER_LEVEL_CONTROL)
        level.add_attribute(0x0000, ZCL_UINT8, 254)  # Current level
        self.add_cluster(level)

    @property
    def brightness(self):
        return _uzigbee.get_attribute(
            self.ep_id, CLUSTER_LEVEL_CONTROL, 0x0000
        )

    @brightness.setter
    def brightness(self, value):
        _uzigbee.set_attribute(
            self.ep_id, CLUSTER_LEVEL_CONTROL, 0x0000, max(0, min(254, value))
        )


class ColorLight(DimmableLight):
    """Kolorowa lampka RGB z peĹ‚nÄ… kontrolÄ… koloru."""

    def __init__(self, endpoint=10):
        super().__init__(endpoint)
        self.device_id = 0x0102
        color = Cluster(CLUSTER_COLOR_CONTROL)
        color.add_attribute(0x0000, ZCL_UINT8, 0)    # Hue
        color.add_attribute(0x0001, ZCL_UINT8, 0)    # Saturation
        color.add_attribute(0x0003, ZCL_UINT16, 0)   # CurrentX
        color.add_attribute(0x0004, ZCL_UINT16, 0)   # CurrentY
        color.add_attribute(0x0007, ZCL_UINT16, 250)  # Color temp mireds
        self.add_cluster(color)

    def set_color_hs(self, hue, saturation):
        """Ustaw kolor w przestrzeni Hue/Saturation (0-254)."""
        _uzigbee.set_attribute(self.ep_id, CLUSTER_COLOR_CONTROL, 0x0000, hue)
        _uzigbee.set_attribute(self.ep_id, CLUSTER_COLOR_CONTROL, 0x0001, saturation)

    def set_color_temp(self, mireds):
        """Ustaw temperaturÄ™ barwowÄ… w mireds (153-500)."""
        _uzigbee.set_attribute(
            self.ep_id, CLUSTER_COLOR_CONTROL, 0x0007, mireds
        )


class Switch(Endpoint):
    """PrzeĹ‚Ä…cznik ZigBee â€” wysyĹ‚a komendy do lamp."""

    def __init__(self, endpoint=10):
        super().__init__(endpoint, device_id=0x0000)
        self._setup_clusters()

    def _setup_clusters(self):
        self.add_cluster(Cluster(CLUSTER_BASIC))
        self.add_cluster(Cluster(CLUSTER_IDENTIFY))
        onoff = Cluster(CLUSTER_ON_OFF, role=CLUSTER_CLIENT)
        self.add_cluster(onoff)

    def send_on(self, dst_addr, dst_ep=10):
        _uzigbee.send_zcl_cmd(dst_addr, dst_ep, self.ep_id,
                              CLUSTER_ON_OFF, 0x01, b"")

    def send_off(self, dst_addr, dst_ep=10):
        _uzigbee.send_zcl_cmd(dst_addr, dst_ep, self.ep_id,
                              CLUSTER_ON_OFF, 0x00, b"")

    def send_toggle(self, dst_addr, dst_ep=10):
        _uzigbee.send_zcl_cmd(dst_addr, dst_ep, self.ep_id,
                              CLUSTER_ON_OFF, 0x02, b"")


class TemperatureSensor(Endpoint):
    """Sensor temperatury ZigBee. Z2M-compatible: wyĹ›wietla siÄ™ jako sensor z wartoĹ›ciÄ… Â°C.

    Z2M interview rozpoznaje cluster 0x0402 i automatycznie tworzy expose 'temperature'.
    Biblioteka automatycznie konfiguruje attribute reporting â€” Z2M dostaje
    aktualizacje bez pollowania.
    """

    Z2M_MODEL_ID = "uzb_TempSensor"

    def __init__(self, endpoint=10, min_val=-40, max_val=125,
                 battery_powered=True, manufacturer="uzigbee", model=None):
        super().__init__(endpoint, device_id=0x0302)
        self._battery = battery_powered
        self._manufacturer = manufacturer
        self._model = model or self.Z2M_MODEL_ID
        self._setup_clusters(min_val, max_val)

    def _setup_clusters(self, min_val, max_val):
        # Basic cluster â€” peĹ‚ny zestaw atrybutĂłw dla Z2M interview
        basic = Cluster(CLUSTER_BASIC)
        basic.add_attribute(0x0000, ZCL_UINT8, 8)
        basic.add_attribute(0x0001, ZCL_UINT8, 1)
        basic.add_attribute(0x0002, ZCL_UINT8, 2)
        basic.add_attribute(0x0003, ZCL_UINT8, 1)
        basic.add_attribute(0x0004, ZCL_CHAR_STRING, self._manufacturer)
        basic.add_attribute(0x0005, ZCL_CHAR_STRING, self._model)
        basic.add_attribute(0x0006, ZCL_CHAR_STRING, "20250205")
        basic.add_attribute(0x0007, ZCL_ENUM8,
                            0x03 if self._battery else 0x01)  # battery vs mains
        basic.add_attribute(0x4000, ZCL_CHAR_STRING, "uzigbee-1.0")
        self.add_cluster(basic)

        self.add_cluster(Cluster(CLUSTER_IDENTIFY))

        # Temperature Measurement â€” Z2M auto-mapuje na expose "temperature"
        temp = Cluster(CLUSTER_TEMPERATURE)
        temp.add_attribute(0x0000, ZCL_INT16, 2000)          # MeasuredValue (0.01Â°C)
        temp.add_attribute(0x0001, ZCL_INT16, min_val * 100) # MinMeasuredValue
        temp.add_attribute(0x0002, ZCL_INT16, max_val * 100) # MaxMeasuredValue
        # Attribute reporting config â€” Z2M skonfiguruje automatycznie,
        # ale ustawiamy sensowne defaults (min 10s, max 300s, change 50 = 0.5Â°C)
        temp.set_default_reporting(0x0000, min_interval=10,
                                   max_interval=300, change=50)
        self.add_cluster(temp)

        # Power Configuration â€” Z2M mapuje na expose "battery" (widoczny %)
        if self._battery:
            power = Cluster(CLUSTER_POWER_CONFIG)
            power.add_attribute(0x0021, ZCL_UINT8, 200)  # BatteryPercentageRemaining (200=100%)
            power.set_default_reporting(0x0021, min_interval=3600,
                                        max_interval=43200, change=2)
            self.add_cluster(power)

    def set_temperature(self, celsius):
        """Ustaw temperaturÄ™ (float, w Â°C). Konwersja automatyczna.
        WartoĹ›Ä‡ bÄ™dzie automatycznie zaraportowana do Z2M."""
        val = int(celsius * 100)
        _uzigbee.set_attribute(self.ep_id, CLUSTER_TEMPERATURE, 0x0000, val)

    def set_battery(self, percent):
        """Ustaw poziom baterii (0-100). Widoczny w Z2M jako expose 'battery'."""
        if self._battery:
            _uzigbee.set_attribute(self.ep_id, CLUSTER_POWER_CONFIG,
                                   0x0021, int(percent * 2))

    def report(self, celsius):
        """Ustaw i wyĹ›lij raport temperatury do bound devices (w tym Z2M)."""
        self.set_temperature(celsius)


class HumiditySensor(Endpoint):
    """Sensor wilgotnoĹ›ci ZigBee."""

    def __init__(self, endpoint=10):
        super().__init__(endpoint, device_id=0x0307)
        self._setup_clusters()

    def _setup_clusters(self):
        self.add_cluster(Cluster(CLUSTER_BASIC))
        self.add_cluster(Cluster(CLUSTER_IDENTIFY))
        hum = Cluster(CLUSTER_HUMIDITY)
        hum.add_attribute(0x0000, ZCL_UINT16, 5000)   # MeasuredValue (in 0.01%)
        hum.add_attribute(0x0001, ZCL_UINT16, 0)      # Min
        hum.add_attribute(0x0002, ZCL_UINT16, 10000)   # Max
        self.add_cluster(hum)

    def set_humidity(self, percent):
        """Ustaw wilgotnoĹ›Ä‡ (float, w %). Konwersja automatyczna."""
        _uzigbee.set_attribute(
            self.ep_id, CLUSTER_HUMIDITY, 0x0000, int(percent * 100)
        )


class PowerOutlet(Endpoint):
    """Gniazdko smart z pomiarem energii."""

    def __init__(self, endpoint=10, with_metering=False):
        super().__init__(endpoint, device_id=0x0009)
        self._setup_clusters(with_metering)

    def _setup_clusters(self, with_metering):
        self.add_cluster(Cluster(CLUSTER_BASIC))
        self.add_cluster(Cluster(CLUSTER_IDENTIFY))
        self.add_cluster(Cluster(CLUSTER_GROUPS))
        self.add_cluster(Cluster(CLUSTER_SCENES))
        onoff = Cluster(CLUSTER_ON_OFF)
        onoff.add_attribute(0x0000, ZCL_BOOL, False)
        self.add_cluster(onoff)
        if with_metering:
            meter = Cluster(CLUSTER_ELECTRICAL_MEASUREMENT)
            meter.add_attribute(0x0505, ZCL_UINT16, 0)  # RMS Voltage
            meter.add_attribute(0x0508, ZCL_UINT16, 0)  # RMS Current
            meter.add_attribute(0x050B, ZCL_INT16, 0)    # Active Power
            self.add_cluster(meter)


class DoorLock(Endpoint):
    """Zamek drzwiowy ZigBee."""
    def __init__(self, endpoint=10):
        super().__init__(endpoint, device_id=0x000A)
        # ... klastry Door Lock


class Thermostat(Endpoint):
    """Termostat ZigBee."""
    def __init__(self, endpoint=10):
        super().__init__(endpoint, device_id=0x0301)
        # ... klastry Thermostat


class WindowCovering(Endpoint):
    """Rolety/zasĹ‚ony ZigBee."""
    def __init__(self, endpoint=10):
        super().__init__(endpoint, device_id=0x0202)
        # ... klastry Window Covering


class OccupancySensor(Endpoint):
    """Czujnik obecnoĹ›ci ZigBee."""
    def __init__(self, endpoint=10):
        super().__init__(endpoint, device_id=0x0107)
        # ... klaster Occupancy Sensing


class IASZone(Endpoint):
    """Czujnik bezpieczeĹ„stwa (drzwi/okna, ruch, dym, woda)."""
    def __init__(self, endpoint=10, zone_type=0x0015):
        super().__init__(endpoint, device_id=0x0402)
        # zone_type: 0x000D=motion, 0x0015=contact, 0x0028=fire, 0x002A=water
        # ... klaster IAS Zone
```

### 4.4 PrzykĹ‚ady UĹĽycia â€” Dla PoczÄ…tkujÄ…cych (Z2M-ready)

```python
# ============================================
# PrzykĹ‚ad 1: Lampka widoczna w Z2M â€” 5 linii kodu
# Po flashowaniu i doĹ‚Ä…czeniu do sieci Z2M:
#   - Interview: "Successfully interviewed '0x...'"
#   - Dashboard: pojawia siÄ™ jako toggle switch ON/OFF
#   - Home Assistant (via Z2M MQTT): auto-discovery jako light.uzb_light
# ============================================
import uzigbee
from machine import Pin

led = Pin(8, Pin.OUT)
light = uzigbee.Light(endpoint=1)
light.on_change(lambda state: led.value(state))
uzigbee.start(role=uzigbee.END_DEVICE)
# GOTOWE â€” Z2M zobaczy urzÄ…dzenie, interview przejdzie automatycznie


# ============================================
# PrzykĹ‚ad 2: Sensor temperatury w Z2M
# Dashboard Z2M pokaĹĽe:
#   - Kafelek "temperature" z wartoĹ›ciÄ… w Â°C
#   - Kafelek "battery" z % baterii
#   - Automatyczne aktualizacje co zmianÄ™ / co 5 minut
# ============================================
import uzigbee
import time

temp_sensor = uzigbee.TemperatureSensor(endpoint=1)
uzigbee.start(role=uzigbee.END_DEVICE)

while True:
    # Odczytaj z fizycznego sensora (np. DHT22, BME280, itp.)
    reading = read_my_sensor()  # Twoja funkcja
    temp_sensor.set_temperature(reading)
    temp_sensor.set_battery(get_battery_percent())
    time.sleep(30)
# Z2M automatycznie wyĹ›wietli wartoĹ›ci i bÄ™dzie je logowaÄ‡


# ============================================
# PrzykĹ‚ad 3: Stacja pogodowa (T+H+P) â€” jeden endpoint, trzy sensory
# Z2M Dashboard pokaĹĽe 3 kafelki: temperature, humidity, pressure
# ============================================
import uzigbee

climate = uzigbee.ClimateSensor(endpoint=1)
uzigbee.start(role=uzigbee.END_DEVICE)

# ... w pÄ™tli:
climate.set_temperature(22.5)
climate.set_humidity(65.3)
climate.set_pressure(1013.25)


# ============================================
# PrzykĹ‚ad 4: Czujnik otwarcia drzwi (contact sensor)
# Z2M pokaĹĽe: "contact: true/false" + ikona drzwi
# Home Assistant: binary_sensor z device_class: door
# ============================================
import uzigbee
from machine import Pin

reed_switch = Pin(5, Pin.IN, Pin.PULL_UP)
contact = uzigbee.ContactSensor(endpoint=1)
uzigbee.start(role=uzigbee.END_DEVICE)

last_state = None
while True:
    state = reed_switch.value()
    if state != last_state:
        contact.set_contact(state == 0)  # 0 = zamkniÄ™te
        last_state = state
    time.sleep_ms(100)


# ============================================
# PrzykĹ‚ad 5: Smart plug z pomiarem energii
# Z2M Dashboard pokaĹĽe: toggle ON/OFF + power(W), voltage(V), current(A)
# ============================================
import uzigbee

plug = uzigbee.PowerOutlet(endpoint=1, with_metering=True)
plug.on_change(lambda state: relay.value(state))
uzigbee.start(role=uzigbee.END_DEVICE)

# Aktualizuj pomiary energii
plug.set_power(watts=45.2)
plug.set_voltage(volts=230.1)
plug.set_current(amps=0.196)


# ============================================
# PrzykĹ‚ad 6: WĹ‚asna nazwa urzÄ…dzenia w Z2M
# DomyĹ›lnie Z2M pokaĹĽe manufacturer "uzigbee", model "uzb_Light"
# MoĹĽesz to customizowaÄ‡:
# ============================================
import uzigbee

light = uzigbee.Light(
    endpoint=1,
    manufacturer="MojaFirma",        # Pojawi siÄ™ w Z2M jako "Vendor"
    model="SuperLampka-v2"            # Pojawi siÄ™ jako "Model"
)
# Uwaga: custom model nie bÄ™dzie pasowaĹ‚ do external convertera,
# Z2M uĹĽyje trybu "generated" (nadal dziaĹ‚a, ale mniej Ĺ‚adne UI)


# ============================================
# PrzykĹ‚ad 7: Koordynator z logowaniem â€” NIE dla Z2M
# (Z2M sam jest koordynatorem â€” ten tryb to standalone coordinator)
# ============================================
import uzigbee

def on_device_joined(info):
    print(f"Nowe urzÄ…dzenie: {info['ieee_addr']:016X}")

def on_device_left(info):
    print(f"UrzÄ…dzenie opuĹ›ciĹ‚o sieÄ‡: {info['ieee_addr']:016X}")

uzigbee.on("device_joined", on_device_joined)
uzigbee.on("device_left", on_device_left)
uzigbee.start(role=uzigbee.COORDINATOR)
uzigbee.permit_joining(180)  # PozwĂłl doĹ‚Ä…czaÄ‡ przez 3 minuty
```

### 4.5 PrzykĹ‚ady UĹĽycia â€” Dla Zaawansowanych

```python
# ============================================
# PrzykĹ‚ad 4: Custom device z wĹ‚asnymi klastrami
# ============================================
import uzigbee
from uzigbee.core import Endpoint, Cluster
from uzigbee import zcl

# StwĂłrz custom endpoint
ep = Endpoint(ep_id=1, device_id=0x0100, profile_id=uzigbee.PROFILE_HA)

# Dodaj Basic cluster z custom manufacturer name
basic = Cluster(zcl.CLUSTER_BASIC)
basic.add_attribute(0x0004, zcl.ZCL_CHAR_STRING, "MyCompany")
basic.add_attribute(0x0005, zcl.ZCL_CHAR_STRING, "SmartSensor v2")
ep.add_cluster(basic)

# Dodaj custom cluster (manufacturer specific)
custom = Cluster(0xFC00)  # Private cluster ID
custom.add_attribute(0x0000, zcl.ZCL_UINT16, 0)   # Custom reading
custom.add_attribute(0x0001, zcl.ZCL_INT32, 0)     # Custom counter
custom.on_attribute_change(0x0000, lambda val: print(f"Custom attr changed: {val}"))
ep.add_cluster(custom)

stack = uzigbee.ZigbeeStack()
stack.add_endpoint(ep)
stack.init(role=uzigbee.ROUTER, channel_mask=0x07FFF800)
stack.start()


# ============================================
# PrzykĹ‚ad 5: Gateway ZigBeeâ†”WiFi
# ============================================
import uzigbee
import network
import usocket
import json

# PoĹ‚Ä…cz z WiFi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect("SSID", "password")

# ZigBee coordinator
uzigbee.start(role=uzigbee.COORDINATOR)
uzigbee.permit_joining(0)  # Nie pozwalaj domyĹ›lnie

# HTTP API do sterowania
def handle_request(cmd):
    if cmd["action"] == "on":
        uzigbee.send_zcl_cmd(
            cmd["addr"], cmd["ep"], 1,
            uzigbee.CLUSTER_ON_OFF, 0x01, b""
        )
    elif cmd["action"] == "permit_join":
        uzigbee.permit_joining(cmd.get("duration", 60))


# ============================================
# PrzykĹ‚ad 6: Attribute reporting configuration
# ============================================
import uzigbee

temp = uzigbee.TemperatureSensor(endpoint=1)

# Konfiguruj automatyczny reporting
temp.configure_reporting(
    cluster_id=uzigbee.CLUSTER_TEMPERATURE,
    attr_id=0x0000,
    min_interval=10,     # Min 10 sekund
    max_interval=300,    # Max 5 minut
    reportable_change=50  # Zmiana o 0.5Â°C triggeruje raport
)
```

---

## 5. Struktura Projektu i Pliki

```
uzigbee/
â”śâ”€â”€ README.md
â”śâ”€â”€ LICENSE                          # Apache 2.0 (dla naszego kodu)
â”śâ”€â”€ docs/
â”‚   â”śâ”€â”€ getting-started.md
â”‚   â”śâ”€â”€ api-reference.md
â”‚   â”śâ”€â”€ building-firmware.md
â”‚   â”śâ”€â”€ examples/
â”‚   â””â”€â”€ architecture.md
â”‚
â”śâ”€â”€ firmware/                        # Build system dla custom firmware
â”‚   â”śâ”€â”€ Makefile
â”‚   â”śâ”€â”€ build.sh                     # Skrypt budujÄ…cy firmware
â”‚   â”śâ”€â”€ sdkconfig.defaults           # DomyĹ›lna konfiguracja ESP-IDF
â”‚   â”śâ”€â”€ partitions.csv               # Tabela partycji
â”‚   â”śâ”€â”€ manifest.py                  # MicroPython frozen modules manifest
â”‚   â””â”€â”€ boards/
â”‚       â”śâ”€â”€ ESP32_C6_GENERIC/
â”‚       â”śâ”€â”€ XIAO_ESP32C6/
â”‚       â””â”€â”€ FIREBEETLE_ESP32C6/
â”‚
â”śâ”€â”€ c_module/                        # ModuĹ‚ C (kompilowany do firmware)
â”‚   â”śâ”€â”€ micropython.cmake            # CMake integration z MicroPython
â”‚   â”śâ”€â”€ micropython.mk               # Make integration
â”‚   â”śâ”€â”€ mod_uzigbee.c                # GĹ‚Ăłwny plik moduĹ‚u â€” rejestracja
â”‚   â”śâ”€â”€ uzb_core.c                   # Inicjalizacja, start, stop
â”‚   â”śâ”€â”€ uzb_core.h
â”‚   â”śâ”€â”€ uzb_endpoint.c               # Endpoint management
â”‚   â”śâ”€â”€ uzb_cluster.c                # Cluster/attribute CRUD
â”‚   â”śâ”€â”€ uzb_zcl.c                    # ZCL command sending/receiving
â”‚   â”śâ”€â”€ uzb_zdo.c                    # ZDO requests/responses
â”‚   â”śâ”€â”€ uzb_network.c                # Network operations
â”‚   â”śâ”€â”€ uzb_security.c               # Security (keys, install codes)
â”‚   â”śâ”€â”€ uzb_ota.c                    # OTA update support
â”‚   â”śâ”€â”€ uzb_callbacks.c              # Callback bridge (Zigbeeâ†’Python)
â”‚   â”śâ”€â”€ uzb_callbacks.h
â”‚   â”śâ”€â”€ uzb_event_queue.c            # Thread-safe ring buffer
â”‚   â”śâ”€â”€ uzb_event_queue.h
â”‚   â””â”€â”€ uzb_types.h                  # Shared type definitions
â”‚
â”śâ”€â”€ python/                          # Kod Python (frozen do firmware)
â”‚   â”śâ”€â”€ uzigbee/
â”‚   â”‚   â”śâ”€â”€ __init__.py              # Publiczne API, staĹ‚e, convenience functions
â”‚   â”‚   â”śâ”€â”€ core.py                  # ZigbeeStack, Endpoint, Cluster klasy
â”‚   â”‚   â”śâ”€â”€ zcl.py                   # ZCL constants (cluster IDs, attribute IDs, types)
â”‚   â”‚   â”śâ”€â”€ z2m.py                   # Z2M-specific helpers (model IDs, defaults, reporting)
â”‚   â”‚   â”śâ”€â”€ devices.py               # High-level: Light, Switch, Sensor, etc.
â”‚   â”‚   â”śâ”€â”€ sensors.py               # Sensor-specific devices
â”‚   â”‚   â”śâ”€â”€ security.py              # Security helpers
â”‚   â”‚   â”śâ”€â”€ reporting.py             # Attribute reporting config
â”‚   â”‚   â”śâ”€â”€ groups.py                # Group management helpers
â”‚   â”‚   â”śâ”€â”€ scenes.py                # Scene management helpers
â”‚   â”‚   â”śâ”€â”€ ota.py                   # OTA update helpers
â”‚   â”‚   â””â”€â”€ gateway.py               # Gateway mode helpers
â”‚   â””â”€â”€ examples/                    # PrzykĹ‚ady (nie frozen, na filesystem)
â”‚       â”śâ”€â”€ z2m_light.py             # â… Lampka gotowa na Z2M
â”‚       â”śâ”€â”€ z2m_temp_sensor.py       # â… Sensor temperatury â†’ Z2M
â”‚       â”śâ”€â”€ z2m_climate_station.py   # â… T+H+P â†’ Z2M (3 exposes)
â”‚       â”śâ”€â”€ z2m_contact_sensor.py    # â… Czujnik drzwi â†’ Z2M
â”‚       â”śâ”€â”€ z2m_smart_plug.py        # â… Gniazdko z pomiarem â†’ Z2M
â”‚       â”śâ”€â”€ z2m_motion_sensor.py     # â… Czujnik ruchu â†’ Z2M
â”‚       â”śâ”€â”€ simple_light.py
â”‚       â”śâ”€â”€ simple_switch.py
â”‚       â”śâ”€â”€ coordinator.py
â”‚       â”śâ”€â”€ gateway_wifi.py
â”‚       â”śâ”€â”€ custom_device.py
â”‚       â””â”€â”€ ota_update.py
â”‚
â”śâ”€â”€ z2m_converters/                  # External converters dla Zigbee2MQTT
â”‚   â”śâ”€â”€ README.md                    # Instrukcja: jak zainstalowaÄ‡ w Z2M
â”‚   â”śâ”€â”€ uzigbee.js                   # Wszystkie definicje urzÄ…dzeĹ„ uzigbee
â”‚   â””â”€â”€ uzigbee_custom_template.js   # Template do tworzenia wĹ‚asnych definicji
â”‚
â”śâ”€â”€ tests/                           # Testy
â”‚   â”śâ”€â”€ test_zcl_types.py
â”‚   â”śâ”€â”€ test_cluster_creation.py
â”‚   â”śâ”€â”€ test_device_models.py
â”‚   â”śâ”€â”€ test_z2m_basic_attrs.py      # Weryfikacja atrybutĂłw Basic Cluster dla Z2M
â”‚   â”śâ”€â”€ test_z2m_reporting.py        # Weryfikacja attribute reporting
â”‚   â””â”€â”€ integration/
â”‚       â”śâ”€â”€ test_network_form.py
â”‚       â”śâ”€â”€ test_on_off.py
â”‚       â”śâ”€â”€ test_z2m_interview.py    # â… Test peĹ‚nego interview Z2M
â”‚       â”śâ”€â”€ test_z2m_exposes.py      # â… Test czy exposes odpowiadajÄ… oczekiwaniom
â”‚       â””â”€â”€ test_z2m_control.py      # â… Test sterowania przez Z2M MQTT
â”‚
â””â”€â”€ tools/
    â”śâ”€â”€ flash.sh                     # Skrypt do flashowania firmware
    â”śâ”€â”€ monitor.sh                   # Serial monitor
    â””â”€â”€ zigbee_sniffer.py            # Sniffer helper
```

---

## 6. Proces Budowania Firmware

### 6.1 Wymagania

- ESP-IDF v5.3.2 (zainstalowany i skonfigurowany)
- MicroPython source code (branch odpowiadajÄ…cy docelowej wersji)
- Python 3.8+
- esptool.py

### 6.2 Kroki Budowania

```bash
# 1. Sklonuj MicroPython
git clone https://github.com/micropython/micropython.git
cd micropython
git checkout v1.27.0
git submodule update --init

# 2. Zbuduj mpy-cross
make -C mpy-cross

# 3. Skonfiguruj ESP-IDF
source $IDF_PATH/export.sh

# 4. Skopiuj moduĹ‚ C do katalogu moduĹ‚Ăłw
cp -r /path/to/uzigbee/c_module micropython/ports/esp32/boards/uzigbee_module

# 5. Dodaj zaleĹĽnoĹ›ci ESP-Zigbee do idf_component.yml
# W ports/esp32/main/idf_component.yml dodaj:
#   espressif/esp-zigbee-lib: "~1.6.0"
#   espressif/esp-zboss-lib: "~1.6.0"

# 6. Zbuduj firmware
cd ports/esp32
make BOARD=ESP32_GENERIC_C6 \
     USER_C_MODULES=/path/to/uzigbee/c_module/micropython.cmake \
     FROZEN_MANIFEST=/path/to/uzigbee/firmware/manifest.py

# 7. Flash
esptool.py --port /dev/ttyUSB0 --baud 460800 write_flash 0 \
    build-ESP32_GENERIC_C6/firmware.bin
```

### 6.3 Konfiguracja Partycji (partitions.csv)

```csv
# Name,    Type, SubType, Offset,  Size,    Flags
nvs,       data, nvs,     0x9000,  0x6000,
phy_init,  data, phy,     0xf000,  0x1000,
factory,   app,  factory, 0x10000, 0x200000,
zb_storage,data, fat,     0x210000,0x10000,
zb_fct,    data, fat,     0x220000,0x1000,
vfs,       data, fat,     0x221000,0x1DF000,
```

**Uwagi:**
- `factory` zwiÄ™kszony do 2 MB (MicroPython + ZBOSS + binding code)
- `zb_storage` (64 KB) â€” NVRAM dla stosu ZigBee (kluczowe dla persist po reboot)
- `zb_fct` (4 KB) â€” factory data ZigBee
- `vfs` â€” filesystem MicroPython (zmniejszony, ale wystarczajÄ…cy)

### 6.4 sdkconfig.defaults

```ini
# ZigBee configuration
CONFIG_ZB_ENABLED=y
# Wybierz rolÄ™ (domyĹ›lnie coordinator+router)
CONFIG_ZB_ZCZR=y
# Albo: CONFIG_ZB_ZED=y dla end device only (mniejszy rozmiar)

# Radio 802.15.4
CONFIG_IEEE802154_ENABLED=y

# Memory optimizations
CONFIG_FREERTOS_PLACE_FUNCTIONS_INTO_FLASH=y
CONFIG_COMPILER_OPTIMIZATION_SIZE=y
CONFIG_LOG_DEFAULT_LEVEL_WARN=y

# WiFi (opcjonalnie, dla gateway)
# CONFIG_ESP_WIFI_ENABLED=y

# Partition table
CONFIG_PARTITION_TABLE_CUSTOM=y
CONFIG_PARTITION_TABLE_CUSTOM_FILENAME="partitions.csv"

# Stack sizes
CONFIG_ESP_MAIN_TASK_STACK_SIZE=8192
CONFIG_MICROPYTHON_TASK_STACK_SIZE=20480

# Zigbee network
CONFIG_ZB_INSTALLCODE_ENABLED=y
CONFIG_ZB_TRACE_ENABLED=n
```

---

## 7. TrudnoĹ›ci i Ryzyka

### 7.1 TrudnoĹ›ci Krytyczne

| # | TrudnoĹ›Ä‡ | WpĹ‚yw | Mitygacja |
|---|----------|-------|-----------|
| 1 | **PamiÄ™Ä‡ RAM** â€” 512 KB musi pomieĹ›ciÄ‡ MicroPython + ZBOSS + FreeRTOS | MoĹĽliwe OOM przy zĹ‚oĹĽonych aplikacjach | Frozen modules, lazy init, konfigurowalny ZBOSS, wyĹ‚Ä…czenie WiFi gdy nie potrzebne |
| 2 | **ZBOSS zamkniÄ™te ĹşrĂłdĹ‚o** â€” brak debugowania wewnÄ™trznych bĹ‚Ä™dĂłw stosu | Utrudnione diagnozowanie problemĂłw | Wykorzystanie trace logging (CONFIG_ZB_TRACE), analiza sygnaĹ‚Ăłw |
| 3 | **Model wÄ…tkowy** â€” ZBOSS wymaga wĹ‚asnego tasku, callback dispatch jest skomplikowany | Race conditions, deadlocki | Ring buffer, mp_sched_schedule(), staranne uĹĽycie mutexĂłw |
| 4 | **Custom firmware** â€” uĹĽytkownik musi flashowaÄ‡ specjalny firmware | Bariera wejĹ›cia, utrudnione aktualizacje | Dostarczanie pre-built binaries, automatyczny build CI/CD |
| 5 | **Rozmiar firmware** â€” MicroPython + ZBOSS + bindingi mogÄ… przekroczyÄ‡ domyĹ›lnÄ… partycjÄ™ | Nie zmieĹ›ci siÄ™ na 4 MB flash | Custom partition table, optymalizacja rozmiaru, warianty (ZED-only mniejszy) |

### 7.2 TrudnoĹ›ci WaĹĽne

| # | TrudnoĹ›Ä‡ | WpĹ‚yw | Mitygacja |
|---|----------|-------|-----------|
| 6 | **Garbage Collector pause** â€” GC MicroPython moĹĽe wstrzymaÄ‡ odpowiedzi ZigBee | Timeouty, utrata pakietĂłw | GC w osobnym wÄ…tku (nie blokuje ZBOSS), maĹ‚e alokacje, gc.threshold() |
| 7 | **Callback timing** â€” ZigBee wymaga odpowiedzi w okreĹ›lonym czasie | NiezgodnoĹ›Ä‡ ze specyfikacjÄ… | Krytyczne callbacki obsĹ‚ugiwane w C, tylko notyfikacje do Pythona |
| 8 | **OTA firmware** â€” aktualizacja firmware wymaga restart + reflash | Wymaga fizycznego dostÄ™pu | Wsparcie OTA update w ZigBee, dual partition scheme |
| 9 | **Testowanie** â€” wymaga minimum 2 urzÄ…dzeĹ„ ZigBee | Koszt, zĹ‚oĹĽonoĹ›Ä‡ CI | Simulatory ZBOSS (jeĹ›li dostÄ™pne), testy manualne, CI z hardware-in-the-loop |
| 10 | **Wersjonowanie ESP-IDF** â€” MicroPython i ESP-Zigbee-SDK mogÄ… wymagaÄ‡ rĂłĹĽnych wersji IDF | Konflikty zaleĹĽnoĹ›ci | Ĺšledzenie kompatybilnoĹ›ci, pinowanie wersji |

### 7.3 Ograniczenia Znane

1. **Nie da siÄ™ zaĹ‚adowaÄ‡ biblioteki dynamicznie** â€” native .mpy files nie majÄ… dostÄ™pu do ESP-IDF API. Zawsze potrzebny jest custom firmware
2. **Koordynator + WiFi = bardzo maĹ‚o wolnego RAM** â€” ta kombinacja moĹĽe nie dziaĹ‚aÄ‡ stabilnie z duĹĽÄ… liczbÄ… urzÄ…dzeĹ„
3. **Sleepy End Device + MicroPython** â€” deep sleep MicroPython i zarzÄ…dzanie energiÄ… ZBOSS wymagajÄ… precyzyjnej koordynacji
4. **Brak PSRAM** â€” w odrĂłĹĽnieniu od ESP32-S3, ESP32-C6 nie wspiera zewnÄ™trznej pamiÄ™ci RAM
5. **Throughput Pythona** â€” operacje wymagajÄ…ce duĹĽej czÄ™stotliwoĹ›ci (np. rapid attribute changes) mogÄ… byÄ‡ zbyt wolne w Pythonie

---

## 8. Plan Realizacji (Fazy)

### Faza 0: Proof of Concept (4-6 tygodni)
**Cel:** UdowodniÄ‡, ĹĽe MicroPython + ZBOSS mogÄ… wspĂłĹ‚istnieÄ‡ na ESP32-C6

- [x] ZbudowaÄ‡ MicroPython firmware z pustym C moduĹ‚em dla ESP32-C6
- [x] DodaÄ‡ esp-zigbee-lib i esp-zboss-lib jako zaleĹĽnoĹ›ci
- [x] ZaimplementowaÄ‡ `_uzigbee.init()`, `_uzigbee.start()` â€” sam start stosu
- [x] UruchomiÄ‡ koordynator formujÄ…cy sieÄ‡ z poziomu REPL
- [x] ZmierzyÄ‡ zuĹĽycie RAM po starcie stosu ZigBee
- [x] UdokumentowaÄ‡ znalezione problemy i ograniczenia

**Deliverable:** Firmware, w ktĂłrym `import _uzigbee; _uzigbee.init(0); _uzigbee.start(True)` formuje sieÄ‡ ZigBee.

### Faza 1: Minimalny ModuĹ‚ C (4-6 tygodni)
**Cel:** Podstawowe operacje ZigBee przez Python

- [x] Endpoint creation/registration
- [x] On/Off cluster (najprostszy)
- [x] Callback bridge (attribute change â†’ Python)
- [x] Event queue (ring buffer)
- [x] Permit joining
- [x] Network info queries

**Deliverable:** DziaĹ‚ajÄ…ca lampka on/off sterowana z innego urzÄ…dzenia ZigBee.

### Faza 2: Core Python API (3-4 tygodnie)
**Cel:** Pythonowe klasy opakowujÄ…ce moduĹ‚ C

- [x] `ZigbeeStack` singleton
- [x] `Endpoint`, `Cluster`, `Attribute` klasy
- [x] Stałe ZCL (cluster IDs, attribute IDs, typy danych)
- [x] Error handling i walidacja
- [x] Event system (`on()` / `off()`)

**Deliverable:** `uzigbee.core` module z peĹ‚nym Core API.

### Faza 3: High-Level Devices + Z2M Compliance (5-7 tygodni)
**Cel:** Gotowe klasy urzÄ…dzeĹ„ HA, ktĂłre przechodzÄ… Z2M interview out-of-the-box

- [x] `Light`, `DimmableLight`, `ColorLight` (Z2M: switch/light expose)
- [x] `Switch`, `DimmableSwitch` (Z2M: switch expose)
- [x] `TemperatureSensor`, `HumiditySensor`, `PressureSensor` (Z2M: numeric exposes)
- [x] `ClimateSensor` â€” combo T+H+P w jednym endpoincie
- [x] `PowerOutlet` z opcjonalnym pomiarem energii (Z2M: switch + power/voltage/current)
- [x] `DoorLock`, `DoorLockController` (Z2M: lock expose)
- [x] `Thermostat` (Z2M: climate expose)
- [x] `OccupancySensor` (Z2M: occupancy expose)
- [x] `ContactSensor`, `MotionSensor` (Z2M: binary exposes via IAS Zone)
- [x] `IASZone` generyczny (fire, water, gas â€” Z2M: alarm exposes)
- [x] `WindowCovering` (Z2M: cover expose z position)
- [x] **Z2M Interview Test Suite** â€” automatyczny test ĹĽe KAĹ»DE urzÄ…dzenie:
  - Przechodzi peĹ‚ny interview (status: SUCCESSFUL)
  - Ma poprawne exposes w dashboard
  - Odpowiada na read attribute requests
  - WysyĹ‚a attribute reports po zmianie wartoĹ›ci
- [x] **External converters** â€” pliki .js dla zigbee-herdsman-converters:
  - `uzigbee.js` z definicjami wszystkich predefiniowanych urzÄ…dzeĹ„
  - Dokumentacja instalacji convertera w Z2M
  - Template `uzigbee_custom_template.js` dla custom devices uĹĽytkownikĂłw
- [x] **ModuĹ‚ `uzigbee.z2m`** â€” Python helper:
  - `z2m.set_model_id(model)` â€” zmiana model ID
  - `z2m.set_manufacturer(name)` â€” zmiana manufacturer
  - `z2m.get_interview_attrs()` â€” debug: wyĹ›wietl co Z2M zobaczy
  - `z2m.validate()` â€” sprawdĹş czy konfiguracja przejdzie interview

**Deliverable:** Wszystkie podstawowe urzÄ…dzenia HA dziaĹ‚ajÄ…ce w Z2M out-of-the-box. UĹĽytkownik flashuje firmware, urzÄ…dzenie doĹ‚Ä…cza do Z2M, interview przechodzi, exposes siÄ™ pojawiajÄ…, sterowanie dziaĹ‚a.

### Faza 4: Zaawansowane Funkcje (6-8 tygodni)
**Cel:** PeĹ‚ne pokrycie funkcjonalnoĹ›ci ZigBee

- [x] Custom clusters (manufacturer-specific)
- [x] Attribute reporting configuration
- [x] Python helper `uzigbee.reporting` presets (doorlock/thermostat/occupancy/contact/motion)
- [x] Podpięcie presetów reporting do wrapperów HA (`configure_default_reporting`)
- [x] Group management
- [x] Scene management
- [x] Binding table management
- [x] ZDO commands (device discovery, descriptor requests)
- [x] ZDO Mgmt_Bind_req read path (`request_binding_table` + `get_binding_table_snapshot`)
- [x] ZDO Active_EP_req read path (`request_active_endpoints` + `get_active_endpoints_snapshot`)
- [x] ZDO Node_Desc_req read path (`request_node_descriptor` + `get_node_descriptor_snapshot`)
- [x] ZDO Simple_Desc_req read path (`request_simple_descriptor` + `get_simple_descriptor_snapshot`)
- [x] ZDO Power_Desc_req read path (`request_power_descriptor` + `get_power_descriptor_snapshot`)
- [x] Security (install codes, network key management)
- [x] OTA update (server & client)
- [x] Gateway mode (ZigBee â†” WiFi bridge)
- [x] Green Power Proxy/Sink
- [x] Touchlink commissioning
- [x] NCP/RCP mode

### Faza 4.5: High-Level Coordinator API + Auto Device Graph (4-6 tygodni)
**Cel:** API wysokiego poziomu, ktore automatyzuje discovery/mapowanie/sterowanie bez recznego operowania endpointami i klastrami.

**Wymagania produktowe Fazy 4.5:**
- Uzytkownik tworzy i uruchamia koordynator 3-5 wywolaniami.
- Uzytkownik wlacza parowanie jednym API (`permit_join`) i dostaje automatycznie odkryte urzadzenia.
- Uzytkownik steruje urzadzeniami przez obiekty (`device.on()`, `device.set_level(...)`, `device.read.temperature()`), bez znajomosci endpointow/cluster IDs.
- Biblioteka utrzymuje stan ostatnich wartosci (cache), preferuje reporty, a read robi tylko gdy cache brak/stary.
- API jest 100% kompatybilne wstecznie z aktualnym `ZigbeeStack`/`devices.*`.

**Architektura docelowa (warstwa Python):**
- `uzigbee.network.Coordinator`
  - lifecycle koordynatora (start, permit_join, auto discovery)
  - routing callbackow sygnal/atrybut
  - publiczny rejestr `coordinator.devices`
- `uzigbee.network.DeviceRegistry`
  - ograniczony pamieciowo registry urzadzen (bounded map + eviction policy)
  - dostep po short address (w kolejnym kroku takze po IEEE)
- `uzigbee.network.DiscoveredDevice`
  - smart mapowanie `cluster -> endpoint`
  - `features` (on_off, level, temperature, humidity, pressure, occupancy, lock, ...)
  - `state` cache ostatnich wartosci
  - `read`/`control` proxy dla ergonomii API
- `uzigbee.network.DeviceReadProxy`
  - `temperature()`, `humidity()`, `on_off()`, `occupancy()`, itd.
  - tryb `use_cache=True` default
- `uzigbee.network.DeviceControlProxy`
  - `on()`, `off()`, `toggle()`, `level(...)`, `lock()`, `unlock()`, itd.

**Docelowy UX API (target):**
1. `coordinator = uzigbee.Coordinator().start(form_network=True)`
2. `coordinator.permit_join(60)`
3. `device = coordinator.get_device(0x1234)` lub iteracja po `coordinator.devices`
4. `device.on()`, `device.read.temperature()`, `device.state[...]`
5. callbacki: `coordinator.on_device_added(...)`, `coordinator.on_attribute(...)`

**Inteligentne mapowanie urzadzen (target logic):**
- Discovery pipeline:
  - Active_EP -> Node_Desc -> Simple_Desc -> (opcjonalnie) Power_Desc.
- Inference:
  - `input_clusters` mapowane na capability set + endpoint routing.
  - priorytety endpointow (primary endpoint, fallback endpoint, cluster-specific endpoint).
- Identity:
  - model/manufacturer/profile/device_id/endpoint graph przechowywane w metadata.
- Persistent cache:
  - ostatni stan atrybutow z timestampem + quality marker (reported/read/assumed).

**Pelne pokrycie funkcji docelowego API (scope 4.5):**
- parowanie + auto re-discovery po join/update/authorized.
- automatyczne aktualizacje stanu po reportach.
- odczyt z cache + read-through.
- sterowanie i idempotentne update cache po command send.
- podstawowe scenariusze HA: light/switch/sensor/lock/thermostat/ias.
- introspekcja urzadzenia (`to_dict()`, feature flags, endpoint map).

**Niezbedne rozszerzenia C bridge dla 100% dokladnosci multi-device (zaplanowane):**
- Callback atrybutu musi niesc zrodlo (`src_short_addr`, `src_endpoint`), bo sam `endpoint` jest niejednoznaczny przy wielu urzadzeniach.
- Snapshot identity dla urzadzenia zdalnego (NodeDesc manufacturer code + Basic read helper).
- Opcjonalny bufor eventow "device left/offline".

**Plan realizacji Fazy 4.5 (kroki iteracyjne):**
- [x] 4.5.1 Bootstrap API: `Coordinator` + `DeviceRegistry` + `DiscoveredDevice`, bazowe mapowanie feature/endpoint, `device.read.*`, `device.on/off/level/lock`, host tests.
- [x] 4.5.2 Auto-discovery pipeline v2: join queue, debounce, retry/backoff, hardening timeoutow, host+HIL.
  - [x] 4.5.2a Python API + host tests.
  - [x] 4.5.2b HIL (celowo odlozone do etapu po domknieciu pelnego API high-level).
- [x] 4.5.3 Rich identity model: metadata urzadzenia (profile/device/version/manufacturer code), API `device.identity`.
- [x] 4.5.4 State engine: TTL cache + source-of-truth markers + stale-read policy.
- [x] 4.5.5 Capability matrix: thermostat/cover/ias/energy advanced read+control wrappers.
- [x] 4.5.6 Binding/reporting automation: auto-bind + auto-configure reporting presets per capability.
- [x] 4.5.7 C bridge extension: source address in attribute callback + Python integration.
  - [x] 4.5.7a Python integration (source-aware callback parsing + cache routing).
  - [x] 4.5.7b C bridge payload extension (`source_short_addr` / `source_endpoint`).
- [x] 4.5.8 Persistent device graph: optional save/restore registry across reboot (bounded flash writes).
- [x] 4.5.9 HIL full matrix: >=2 urzadzenia jednoczesnie, collision tests endpoint overlap, long-run stability.
- [x] 4.5.10 Dokumentacja API high-level: quickstart, patterns, anti-patterns, migration guide from low-level API.
- [x] 4.5.11 Registry query API: wyszukiwanie urzadzen po capability/identity (`feature`, `device_id`, `manufacturer_code`, `ieee`) + shortcuty IEEE.
- [x] 4.5.12 Device lifecycle API: `online/offline`, `last_seen`, filtrowanie aktywnych urzadzen i manualne markowanie statusu.
- [x] 4.5.13 Multi-endpoint capability API: selektory `device.feature(selector)`/`device.switch(n)` dla powtarzajacych sie endpointow + endpoint-aware cache routing.

### Faza 4.6: High-Level Router + EndDevice API (4-6 tygodni)
**Cel:** API wysokiego poziomu dla urzadzen lokalnych (Router i EndDevice), aby uzytkownik mogl tworzyc pelne urzadzenia ZigBee bez recznego skladania endpointow/klastrow.

**Wymagania produktowe Fazy 4.6:**
- Uzytkownik tworzy Router lub EndDevice w 3-5 wywolaniach.
- Uzytkownik podpina sensory i aktory (light/switch/doorlock/thermostat/occupancy/contact/motion itp.) jednym API bez znajomosci cluster IDs.
- Reporting i binding sa automatyczne domyslnie, z mozliwoscia override.
- API ma wspierac zarowno proste preset-y, jak i zaawansowane sterowanie (custom cluster, custom attr, custom policy).
- API jest kompatybilne z aktualnym `ZigbeeStack`, `devices.*` i nowa warstwa `Coordinator` (Faza 4.5).
- RAM-safe: brak ciezkich alokacji w hot path, profile i mapy stale zorientowane na ESP32-C6.

**Architektura docelowa (warstwa Python):**
- `uzigbee.node.Router`
  - lifecycle routera (init/start/rejoin), builder endpointow, auto-register.
  - automation: auto identity, auto reporting, auto bind to coordinator.
- `uzigbee.node.EndDevice`
  - lifecycle end-device (init/start/rejoin) + tryb sleepy (poll/keepalive policy).
  - automation: battery defaults, reporting profile for low-power, optional wake hooks.
- `uzigbee.node.EndpointBuilder`
  - declarative API: mapowanie capability -> endpoint/cluster/attr.
  - automatyczny assignment endpoint IDs + conflict resolution.
- `uzigbee.node.LocalDeviceGraph`
  - lokalny graph endpointow i capability lokalnego node.
  - introspekcja `to_dict()`, restore snapshot, runtime validation.
- `uzigbee.node.ReportingPolicy`
  - domyslne presety reporting per capability.
  - per-attribute override i rate-limit dla update path.
- `uzigbee.node.BindingPolicy`
  - auto-bind do koordynatora i opcjonalnie do konkretnych destination nodes.
  - IAS CIE enrollment helper.

**Docelowy UX API (target):**
1. `router = uzigbee.Router().add_light().add_switch().start(join_parent=True)`
2. `router.sensor("temperature").set(22.4)` albo `router.update("temperature", 22.4)`
3. `router.actor("light").on()` / `router.actor("light").set_level(128)`
4. `ed = uzigbee.EndDevice(sleepy=True).add_contact_sensor().add_battery().start(join_parent=True)`
5. `ed.update("contact", True)` i biblioteka sama robi reporting/buffering zgodnie z policy.

**Automatyzacja domyslna (target logic):**
- Auto identity:
  - sensowne defaulty Basic cluster (`manufacturer`, `model`, `sw_build_id`, `power_source`).
- Auto endpoint provisioning:
  - capability templates, deterministic endpoint IDs, profile/device-id mapping.
- Auto reporting:
  - predefiniowane profile dla sensorow i aktuatorow, bezpieczne interval/change defaults.
  - fallback i retry dla configure reporting.
- Auto binding:
  - bind krytycznych klastrow do coordinator endpoint.
  - opcjonalne bind plan-y dla specyficznych scenariuszy (groups/scenes/ias).
- Auto state model:
  - cache ostatnich lokalnych wartosci + metadata (source, ts, quality).
  - opcjonalna persistence lokalnego graphu i state.

**Pelne pokrycie funkcji docelowego API (scope 4.6):**
- role-local lifecycle: Router i EndDevice (w tym Sleepy EndDevice profile).
- local sensors: temperature/humidity/pressure/occupancy/contact/motion/ias/energy/battery.
- local actuators: on_off light, dimmable light, color light, switch, lock, cover, thermostat.
- push i pull model:
  - push (`update`) dla sensor values,
  - pull (`actor`/`read`) dla local state i mapowanych attr.
- sterowanie zdalne i lokalne:
  - command wrappers + local mirrors.
- advanced mode:
  - custom clusters/attributes/policies bez utraty prostego API.
- introspekcja i debug:
  - `node.describe()`, `node.endpoints()`, `node.capabilities()`, `node.health()`.

**Plan realizacji Fazy 4.6 (kroki iteracyjne):**
- [x] 4.6.1 Bootstrap Node API: `Router`, `EndDevice`, wspolny base node + lifecycle.
- [x] 4.6.2 EndpointBuilder v1: declarative capability templates + auto endpoint assignment.
- [x] 4.6.3 Sensor pipeline: `update(capability, value)` + walidacja, konwersje i local state cache.
- [x] 4.6.4 Actuator pipeline: `actor(name).on/off/level/lock/cover/...` + idempotent local mirror.
- [x] 4.6.5 Auto-reporting policy manager: presets per capability + override per endpoint/attr.
- [x] 4.6.6 Auto-binding policy manager: coordinator bind defaults + IAS enrollment automation.
- [x] 4.6.7 Sleepy EndDevice profile: poll/keepalive strategy, wake windows, low-power reporting defaults.
- [x] 4.6.8 Persistence local graph/state: `save_node_state` / `load_node_state` (bounded writes).
- [x] 4.6.9 Advanced extension path: custom clusters + custom attrs + policy hooks without breaking simple API.
- [x] 4.6.10 Test matrix host: unit + integration dla Router/EndDevice API, profile conflicts, state/reporting edge cases.
- [x] 4.6.11 HIL matrix: Router + EndDevice on real hardware (join/rejoin/reporting/control/long-run).
- [x] 4.6.12 Dokumentacja API 4.6: quickstart Router/EndDevice, recipes sensor/actuator, advanced policy cookbook.

### Faza 4.7: High-Level Auto Commissioning + Network Orchestration (2-4 tygodnie)
**Cel:** Usunac potrzebe hardcodowania `channel/pan_id/extended_pan_id` i zapewnic profesjonalne, w pelni automatyczne dolaczanie/fomowanie sieci ZigBee.

**Wymagania produktowe:**
- Router/EndDevice maja domyslnie dolaczac do sieci bez recznego ustawiania `channel/pan_id/extended_pan_id`.
- Koordynator ma domyslnie formowac siec automatycznie (kanal wybierany optymalnie), z opcjonalnym override.
- API ma pozostac wysokopoziomowe i stabilne wstecznie.
- Parametry sieci po utworzeniu musza byc trwale i odczytywalne z API.
- Musi byc strategia naprawcza na konflikty (`PAN ID conflict`, utrata sieci, steering timeout).

**Docelowy UX API (high-level):**
- Koordynator:
  - `coordinator = uzigbee.Coordinator(network_mode="auto")`
  - `coordinator.start(form_network=True)`  # auto kanal/PAN/extPAN na first boot
  - `coordinator.network_info()`            # runtime: channel/pan_id/ext_pan_id/short_addr/state
  - `coordinator.open_network(180)`         # alias permit join
- Koordynator z override:
  - `coordinator = uzigbee.Coordinator(network_mode="fixed", channel=20, pan_id=0x1A62, extended_pan_id="00124b0001c6c6c6")`
- Router/EndDevice:
  - `router = uzigbee.Router(commissioning_mode="auto").add_light().start(join_parent=True)`
  - `ed = uzigbee.EndDevice(commissioning_mode="auto", sleepy=True).add_contact_sensor().start(join_parent=True)`
  - bez recznego `channel/pan_id/ext_pan_id`, chyba ze uzytkownik swiadomie wybierze `commissioning_mode="fixed"`.

**Plan realizacji (iteracyjny):**
- [x] 4.7.1 Kontrakt API i kompatybilnosc:
  - dodac w `Coordinator/Router/EndDevice` jawne tryby `network_mode`/`commissioning_mode`:
  - `auto` (domyslny), `fixed` (pelny override), `guided` (priorytet + fallback).
  - zachowac obecne argumenty (`channel`, `channel_mask`, `pan_id`, `extended_pan_id`) jako kompatybilne aliasy.
- [x] 4.7.2 Model konfiguracji sieci:
  - nowy obiekt `NetworkProfile` (serializowalny): `channel_mask`, `pan_id`, `extended_pan_id`, `source` (`auto|fixed|restored`), `formed_at_ms`.
  - `Coordinator.network_info()` i `Node.network_info()` zwracaja runtime + profil.
- [x] 4.7.3 C bridge introspekcja sieci:
  - dodac read-only API C/Python do pobrania aktywnych parametrow NWK (channel, pan_id, ext_pan, joined/formed flag, short addr).
  - wymaganie: tylko lock-safe odczyt, bez alokacji Python po stronie taska ZigBee.
- [x] 4.7.4 Auto-kanal dla koordynatora (first boot):
  - dodac strategie wyboru kanalu:
  - wariant A: energy-scan API ZigBee (preferowane, jesli stabilne na ESP32-C6),
  - wariant B: deterministyczny fallback maski preferowanych kanalow.
  - wynik zapisywany jako aktywny profil sieci.
- [x] 4.7.5 Auto PAN/extPAN:
  - w trybie `auto` nie wymuszac `set_pan_id`/`set_extended_pan_id`; pozwolic stackowi wygenerowac wartosci.
  - po utworzeniu sieci odczytac i zapisac do `NetworkProfile`.
- [x] 4.7.6 Router/EndDevice auto-join:
  - domyslnie skanowanie przez bezpieczna maske kanalow (konfigurowalna) i steering retry/backoff.
  - brak wymogu podawania `channel/pan/extpan`.
- [x] 4.7.7 Guided mode:
  - dodac tryb `guided`: preferuje profile znane z poprzedniego dolaczenia, ale fallbackuje do pelnego steering.
  - ma przyspieszyc reconnect bez utraty kompatybilnosci.
- [x] 4.7.8 Obsługa konfliktow i self-heal:
  - sygnal `panid_conflict_detected` -> policy hook + kontrolowany reformation/rejoin.
  - steering timeout -> automatyczne retriggery z limitem i telemetryka powodow.
- [x] 4.7.9 Telemetria commissioning:
  - `commissioning_stats()` dla Coordinator/Node: liczba prob, sukcesy, timeouty, conflict events, czas do join/form.
  - logi przyjazne dla HIL i CI.
- [x] 4.7.10 Migracja przykladów:
  - usunac hardcoded `ZIGBEE_CHANNEL/PAN/EXTPAN` z high-level examples.
  - pozostawic tylko opcjonalne profile demonstracyjne (`fixed`) jako sekcja advanced.
- [x] 4.7.11 Testy host:
  - przypadki `auto/fixed/guided`, walidacja fallbackow, kompatybilnosc wsteczna argumentow.
  - testy serializacji `NetworkProfile`.
- [x] 4.7.12 Testy HIL:
  - dual-node auto commissioning bez hardcode na czystych partycjach runtime.
  - cold boot + reboot + rejoin + conflict simulation.
  - kryterium: stabilne `TEST_PASS` w min. 10 cyklach batch runnera.
- [x] 4.7.13 Dokumentacja:
  - `docs/API.md`: sekcja "Auto commissioning" + recipes `auto/fixed/guided`.
  - `docs/EXAMPLES.md`: runbook bez hardcode, troubleshooting i policy rekomendacje.

### Faza 5: Stabilizacja, Z2M Certification i Dokumentacja (5-7 tygodni)
**Cel:** Produkcyjne quality, peĹ‚na kompatybilnoĹ›Ä‡ Z2M

- [x] **Testy Z2M end-to-end** z aktualnÄ… wersjÄ… Z2M (2.x):
  - Pair â†’ Interview â†’ Dashboard â†’ Control â†’ Remove dla KAĹ»DEGO typu urzÄ…dzenia
  - Test z i bez external convertera (oba Ĺ›cieĹĽki muszÄ… dziaĹ‚aÄ‡)
  - Test â€žgenerated" mode (gdy uĹĽytkownik customizuje model ID)
  - Test attribute reporting â†’ Z2M live update wartoĹ›ci
  - Test grup i scen przez Z2M UI
- [x] **Testy Home Assistant integration** (via Z2M â†’ MQTT Discovery):
  - Auto-discovery entity w HA
  - Poprawne device_class (temperature, humidity, door, motion, etc.)
  - Poprawne units (Â°C, %, hPa, W, V, A)
  - Sterowanie z HA dashboard â†’ urzÄ…dzenie reaguje
- [ ] Optymalizacja pamiÄ™ci i wydajnoĹ›ci
- [x] PeĹ‚na dokumentacja API (Sphinx/MkDocs)
- [x] **Dedykowany poradnik "uzigbee + Zigbee2MQTT":**
  - Quick Start: od flashowania do widocznoĹ›ci w Z2M w 5 minut
  - Troubleshooting interview failures
  - Jak dodaÄ‡ custom device do Z2M
  - Jak stworzyÄ‡ wĹ‚asny external converter
- [x] Tutoriale i przykĹ‚ady (priorytet: Z2M use cases)
- [x] Pre-built firmware binaries w CI/CD (GitHub Actions)
- [x] Wsparcie dla popularnych pĹ‚ytek (XIAO ESP32C6, FireBeetle, ESP32-C6-DevKit)
- [ ] **PR do zigbee-herdsman-converters** â€” zgĹ‚oszenie definicji urzÄ…dzeĹ„ uzigbee upstream, aby byĹ‚y rozpoznawane natywnie w Z2M bez external converters

### Faza 6: Rozszerzenia (ongoing)
- [ ] Wsparcie ESP32-H2 (dedykowany chip ZigBee, bez WiFi â€” idealny dla end devices)
- [ ] Wsparcie ESP32-C5 (nowy chip z 802.15.4)
- [ ] Web-based configuration panel (przez WiFi w trybie gateway)
- [ ] Integration z Home Assistant (jako addon)
- [ ] Matter bridge mode
- [ ] Zigbee Direct (BLE commissioning)

---

## 9. Szacowany Harmonogram

| Faza | Czas trwania | Kumulatywnie |
|------|-------------|-------------|
| Faza 0: PoC | 4-6 tyg. | 4-6 tyg. |
| Faza 1: ModuĹ‚ C | 4-6 tyg. | 8-12 tyg. |
| Faza 2: Core API | 3-4 tyg. | 11-16 tyg. |
| Faza 3: Devices + Z2M | 5-7 tyg. | 16-23 tyg. |
| Faza 4: Advanced | 6-8 tyg. | 22-31 tyg. |
| Faza 4.5: High-Level Coordinator API | 4-6 tyg. | 26-37 tyg. |
| Faza 4.6: High-Level Router + EndDevice API | 4-6 tyg. | 30-43 tyg. |
| Faza 5: Stabilizacja + Z2M cert | 5-7 tyg. | 35-50 tyg. |

**Szacowany caĹ‚kowity czas: 8-11 miesiecy** (dla jednego doswiadczonego developera embedded z znajomoscia C, MicroPython internals i ESP-IDF). Dodatkowe ~4-6 tygodni wzgledem planu bazowego to koszt pelnego API 4.6 i testow E2E.

---

## 10. Wymagania Kompetencyjne

Do realizacji projektu potrzebna jest wiedza z zakresu:

1. **C (zaawansowany)** â€” pisanie moduĹ‚Ăłw MicroPython, zarzÄ…dzanie pamiÄ™ciÄ…, wskaĹşniki
2. **ESP-IDF** â€” build system (CMake), FreeRTOS, partycje, konfiguracja
3. **MicroPython internals** â€” mp_obj_t, MP_DEFINE_CONST_FUN_OBJ, gc, scheduler
4. **ProtokĂłĹ‚ ZigBee** â€” ZCL, ZDO, profile, clustery, atrybuty, komendy, binding, reporting
5. **802.15.4** â€” warstwa fizyczna/MAC (podstawy)
6. **Python** â€” projektowanie API, OOP, async patterns
7. **Embedded debugging** â€” JTAG, serial debugging, analiza crashĂłw, memory profiling

---

## 11. Rekomendacje Strategiczne

1. **Zacznij od PoC** â€” przed inwestowaniem czasu w peĹ‚ne API, sprawdĹş czy ZBOSS + MicroPython wspĂłĹ‚istniejÄ… stabilnie na 512 KB RAM. To jest kluczowe ryzyko go/no-go.

2. **Z2M jako primary target** â€” Zigbee2MQTT jest de facto standardem w spoĹ‚ecznoĹ›ci home automation. JeĹ›li urzÄ…dzenia uzigbee dziaĹ‚ajÄ… dobrze z Z2M, automatycznie dziaĹ‚ajÄ… teĹĽ z Home Assistant, Node-RED i wieloma innymi systemami. Testuj z Z2M od pierwszego dziaĹ‚ajÄ…cego prototypu.

3. **â€žGenerated" mode wystarczy na start** â€” Z2M od wersji 2.x potrafi automatycznie mapowaÄ‡ standardowe klastry ZCL na features. JeĹ›li biblioteka poprawnie implementuje klastry (z peĹ‚nym Basic Cluster), urzÄ…dzenia bÄ™dÄ… dziaĹ‚aÄ‡ w Z2M BEZ external convertera. External converter to "nice to have" dla lepszego UX, nie blocker.

4. **Basic Cluster to fundament** â€” 90% problemĂłw z interview w Z2M wynika z niepoprawnych atrybutĂłw w Basic Cluster. Biblioteka MUSI domyĹ›lnie wypeĹ‚niaÄ‡ WSZYSTKIE atrybuty 0x0000-0x0007 + 0x4000 sensownymi wartoĹ›ciami. To nie jest opcjonalne.

5. **Attribute Reporting jest obowiÄ…zkowy** â€” Z2M nie polluje urzÄ…dzeĹ„. JeĹ›li sensor nie wysyĹ‚a attribute reports, Z2M pokaĹĽe stare/puste wartoĹ›ci. KaĹĽdy sensor MUSI mieÄ‡ skonfigurowany reporting z sensownymi defaults (min/max interval + reportable change).

6. **Warianty firmware** â€” rozwaĹĽ dostarczanie osobnych binariĂłw:
   - `uzigbee-coordinator.bin` (z WiFi, dla gateway)
   - `uzigbee-router.bin` (bez WiFi, oszczÄ™dnoĹ›Ä‡ RAM)
   - `uzigbee-enddevice.bin` (minimalistyczny, CONFIG_ZB_ZED, najniĹĽsze zuĹĽycie RAM)

7. **Inspiruj siÄ™ Arduino ZigbeeCore** â€” ich architektura (ZigbeeCore singleton + klasy endpoint) jest sprawdzona i dobrze mapuje siÄ™ na Python.

8. **Krytyczne callbacki w C** â€” odpowiedzi na ZCL commands, ktĂłre muszÄ… byÄ‡ szybkie (np. read attribute response â€” Z2M odpytuje o atrybuty podczas interview), powinny byÄ‡ obsĹ‚ugiwane bezpoĹ›rednio w C, a Python dostaje tylko notyfikacjÄ™ post-factum. JeĹ›li interview timeout nastÄ…pi bo Python GC wstrzymaĹ‚ odpowiedĹş, Z2M oznaczy device jako FAILED.

9. **RozwaĹĽ wspĂłĹ‚pracÄ™ z Espressif** â€” jako ĹĽe nie ma oficjalnego MicroPython ZigBee, jest szansa na wsparcie od Espressif (mogÄ… udostÄ™pniÄ‡ examples, pomĂłc z integracjÄ… build system, a nawet potencjalnie wĹ‚Ä…czyÄ‡ do oficjalnego MicroPython ESP32 portu).

10. **PR do zigbee-herdsman-converters** â€” po ustabilizowaniu model IDs, zgĹ‚oĹ› definicje urzÄ…dzeĹ„ uzigbee upstream. Koenkk (maintainer Z2M) akceptuje definicje nowych urzÄ…dzeĹ„ jeĹ›li sÄ… dobrze opisane i testowane. To sprawi, ĹĽe urzÄ…dzenia uzigbee bÄ™dÄ… â€žnative supported" w Z2M.

11. **Licencja ZBOSS** â€” przed publikacjÄ… sprawdĹş dokĹ‚adnie warunki licencji esp-zboss-lib. Dystrybucja pre-built firmware zawierajÄ…cego ZBOSS binaries moĹĽe wymagaÄ‡ zgody Espressif.

---

## Progress Log (Execution)

- [x] 2026-02-08 Step 32: recovered COM3 Zigbee startup stability after reporting-NVRAM crash (`zb_nvram_read_zcl_reporting_dataset`) via full flash erase + reflash; validated HIL (`hil_zigbee_bridge_addr_smoke.py`, `hil_web_demo_startup_smoke.py`) on COM3.
- [x] 2026-02-09 Step 33: coordinator web demo switched to STA defaults (`STAR1` / `wodasodowa`) with startup order `WiFi -> Zigbee`; validated on COM3 with `hil_web_demo_sta_smoke.py` (PASS).
- [x] 2026-02-09 Step 34: stabilized web-demo runtime on COM3 (HTTP client timeout fix + STA watchdog + serial launcher `tools/run_web_demo_serial.py`); validated with 30/30 successful HTTP responses on `http://192.168.0.26/`.
- [x] 2026-02-09 Step 35: added auto-target path for joined devices (`get_last_joined_short_addr`) in C bridge + Python API + web demo signal handling; built/flashed `build-ESP32_GENERIC_C6-uzigbee-step35a`; validated HIL (`hil_zigbee_bridge_addr_smoke.py`, `hil_last_joined_short_smoke.py`, `hil_web_demo_startup_smoke.py`, `hil_web_demo_sta_smoke.py`) and runtime HTTP actions on COM3.
- [x] 2026-02-09 Step 36: implemented binding management commands (`send_bind_cmd`, `send_unbind_cmd`) in C core + MicroPython C module + `uzigbee.core`; built/flashed `build-ESP32_GENERIC_C6-uzigbee-step35a`; validated HIL (`hil_bind_cmd_smoke.py`, `hil_zigbee_bridge_addr_smoke.py`, `hil_last_joined_short_smoke.py`) on COM3.
- [x] 2026-02-09 Step 37: implemented ZDO Mgmt_Bind request read path (`request_binding_table`, `get_binding_table_snapshot`) in C core + MicroPython C module + `uzigbee.core`; built/flashed `build-ESP32_GENERIC_C6-uzigbee-step37a`; validated HIL (`hil_zigbee_bridge_addr_smoke.py`, `hil_bind_cmd_smoke.py`, `hil_binding_table_read_smoke.py`) on COM3.
- [x] 2026-02-09 Step 38: implemented ZDO Active_EP request read path (`request_active_endpoints`, `get_active_endpoints_snapshot`) in C core + MicroPython C module + `uzigbee.core`; built with WSL (`build-ESP32_GENERIC_C6-uzigbee-step38a`), flashed on COM3, validated HIL (`hil_zigbee_bridge_addr_smoke.py`, `hil_bind_cmd_smoke.py`, `hil_binding_table_read_smoke.py`, `hil_active_endpoints_read_smoke.py`).
- [x] 2026-02-09 Step 39: implemented ZDO Node_Desc request read path (`request_node_descriptor`, `get_node_descriptor_snapshot`) in C core + MicroPython C module + `uzigbee.core`; built with WSL (`build-ESP32_GENERIC_C6-uzigbee-step39a`), flashed on COM3, validated HIL (`hil_zigbee_bridge_addr_smoke.py`, `hil_active_endpoints_read_smoke.py`, `hil_node_desc_read_smoke.py`, `hil_binding_table_read_smoke.py`).
- [x] 2026-02-09 Step 40: implemented ZDO Simple_Desc request read path (`request_simple_descriptor`, `get_simple_descriptor_snapshot`) in C core + MicroPython C module + `uzigbee.core`; built with WSL (`build-ESP32_GENERIC_C6-uzigbee-step40a`), flashed on COM3, validated HIL (`hil_zigbee_bridge_addr_smoke.py`, `hil_active_endpoints_read_smoke.py`, `hil_node_desc_read_smoke.py`, `hil_simple_desc_read_smoke.py`, `hil_binding_table_read_smoke.py`).
- [x] 2026-02-09 Step 41: implemented ZDO Power_Desc request read path (`request_power_descriptor`, `get_power_descriptor_snapshot`) in C core + MicroPython C module + `uzigbee.core`; built with WSL (`build-ESP32_GENERIC_C6-uzigbee-step41a`), flashed on COM3, validated HIL (`hil_zigbee_bridge_addr_smoke.py`, `hil_active_endpoints_read_smoke.py`, `hil_node_desc_read_smoke.py`, `hil_simple_desc_read_smoke.py`, `hil_power_desc_read_smoke.py`, `hil_binding_table_read_smoke.py`).
- [x] 2026-02-09 Step 42: added composed descriptor discovery helper (`discover_node_descriptors`) in `uzigbee.core` that orchestrates Active_EP, Node_Desc, Simple_Desc and Power_Desc requests with timeout/polling and strict/non-strict modes; built with WSL (`build-ESP32_GENERIC_C6-uzigbee-step42a`), flashed on COM3, validated HIL (`hil_discover_node_descriptors_smoke.py` + descriptor regression batch).
- [x] 2026-02-09 Step 43: implemented Scene management command path (`send_scene_add_cmd`, `send_scene_remove_cmd`, `send_scene_remove_all_cmd`, `send_scene_recall_cmd`) in C core + MicroPython C module + `uzigbee.core`, plus helper module `uzigbee.scenes` and `Switch` scene wrappers; built with WSL (`build-ESP32_GENERIC_C6-uzigbee-step43a`), flashed on COM3, validated HIL (`hil_scenes_cmd_smoke.py` + descriptor regression batch).
- [x] 2026-02-09 Step 44: implemented Security command path (install-code policy and network-key management) in C core + MicroPython C module + `uzigbee.core`, plus helper module `uzigbee.security`; built with WSL (`build-ESP32_GENERIC_C6-uzigbee-step44a`), flashed on COM3, validated HIL (`hil_security_smoke.py` + groups/scenes/descriptor/address regression batch).
- [x] 2026-02-09 Step 45: implemented Custom Cluster path (`clear_custom_clusters`, `add_custom_cluster`, `add_custom_attr`, `send_custom_cmd`) in C core + MicroPython C module + `uzigbee.core`, plus helper module `uzigbee.custom`; built with WSL (`build-ESP32_GENERIC_C6-uzigbee-step45a`), flashed on COM3, validated host tests + HIL (`hil_custom_cluster_smoke.py` + regression batch).
- [x] 2026-02-09 Step 46: implemented OTA client control baseline (`ota_client_query_interval_set`, `ota_client_query_image_req`, `ota_client_query_image_stop`) in C core + MicroPython C module + `uzigbee.core`, plus helper module `uzigbee.ota`; finalized with WSL build `build-ESP32_GENERIC_C6-uzigbee-step46g`, flashed on COM3, validated host tests + HIL (`hil_ota_client_smoke.py` + regression batch). Due vendor Zigbee OTA assert (`zcl_general_commands.c:612`), OTA control methods are currently guarded and return `ESP_ERR_NOT_SUPPORTED` (`262`) instead of crashing; full OTA server/client flow remains open.
- [x] 2026-02-09 Step 47: added OTA control capability probe (`ota_client_control_supported`) in C core + MicroPython C module + `uzigbee.core`, plus helper `uzigbee.ota.is_control_supported`; validated with host tests (`test_core_api.py`, `test_ota_api.py`, `test_import.py`), WSL build `build-ESP32_GENERIC_C6-uzigbee-step47a`, flash on COM3, direct runtime probe (`cap_api True False False`) and HIL regression (`hil_ota_client_smoke.py`, `hil_zigbee_bridge_addr_smoke.py`, `hil_custom_cluster_smoke.py`, `hil_security_smoke.py`).
- [x] 2026-02-09 Step 48: added capability-gated OTA fallback helpers (`set_query_interval_if_supported`, `query_image_if_supported`, `stop_query_if_supported`) in `uzigbee.ota` and wired runtime visibility in `examples/coordinator_web_demo.py` (`ota control supported=<bool>`); validated by host tests (`test_ota_api.py`, `test_example_coordinator_web_demo.py`, `test_core_api.py`, `test_import.py`), WSL build `build-ESP32_GENERIC_C6-uzigbee-step48a`, flash on COM3, and HIL (`hil_ota_capability_fallback_smoke.py`, `hil_ota_client_smoke.py`, `hil_zigbee_bridge_addr_smoke.py`).
- [x] 2026-02-09 Step 49 (Faza 4.5.1): introduced high-level automation scaffold `uzigbee.network` (`Coordinator`, `DeviceRegistry`, `DiscoveredDevice`) with auto-discovery on join signals, inferred capability/endpoint map, device-level control (`on/off/level/lock`) and read proxy (`read.temperature()`, etc.), plus bounded state cache; exported in `uzigbee.__init__`; validated by host tests (`test_network_api.py` + regression: `test_import.py`, `test_ota_api.py`, `test_core_api.py`, `test_example_coordinator_web_demo.py`), WSL build `build-ESP32_GENERIC_C6-uzigbee-step49a`, flash on COM3, and HIL (`hil_network_coordinator_smoke.py`, `hil_zigbee_bridge_addr_smoke.py`, `hil_ota_capability_fallback_smoke.py`).
- [x] 2026-02-10 Step 50 (Build acceleration): replaced root `build_firmware.sh` with uzigbee-specific builder for `ESP32_GENERIC_C6` + `c_module/micropython.cmake` + `firmware/manifest.py` + `firmware/sdkconfig.defaults`, enforced ESP-IDF `v5.3.2`, added anti-collision locks and fast defaults (skip submodules, reuse newest completed `build-...-step*`); validated on WSL with default incremental run `./build_firmware.sh --skip-mpy-cross` selecting `build-ESP32_GENERIC_C6-uzigbee-step49a` and completing in `ELAPSED=1:45.98`.
- [x] 2026-02-10 Step 51 (Faza 4.5.2a): implemented auto-discovery pipeline v2 in `uzigbee.network.Coordinator` (join queue, debounce, retry/backoff, queue overflow handling, timeout/poll hardening) and added host coverage (`test_network_api.py`); validation: `python -m pytest tests/test_network_api.py tests/test_import.py tests/test_example_coordinator_web_demo.py -q` => `16 passed`. HIL for 4.5.2 remains intentionally deferred until full high-level API completion.
- [x] 2026-02-10 Step 52 (Faza 4.5.3): added rich identity model in high-level API (`uzigbee.network.DeviceIdentity`, `DiscoveredDevice.identity`, package export `uzigbee.DeviceIdentity`) with metadata from Node/Simple/Power descriptor snapshots (`manufacturer_code`, `profile_id`, `device_id`, `device_version`, endpoint map, power source); validated by host tests (`python -m pytest tests/test_network_api.py tests/test_import.py tests/test_example_coordinator_web_demo.py -q` => `18 passed`).
- [x] 2026-02-10 Step 53 (Faza 4.5.4): added state engine in high-level API (`state_ttl_ms`, `stale_read_policy`, `configure_state_engine`) with per-attribute source-of-truth markers (`source`, `authoritative`, `updated_ms`) and stale handling (`allow`/`refresh`/`raise`) in `device.read.*`; validated by host tests (`python -m pytest tests/test_network_api.py tests/test_import.py tests/test_example_coordinator_web_demo.py -q` => `21 passed`).
- [x] 2026-02-10 Step 54 (Faza 4.5.5): added capability matrix wrappers for `thermostat`, `cover`, `ias_zone`, `energy` in high-level API (`device.read.*`, `device.control.*`, `DiscoveredDevice` convenience setters) with normalized units and clamped writes; validated by host tests (`python -m pytest tests/test_network_api.py tests/test_import.py tests/test_example_coordinator_web_demo.py -q` => `23 passed`).
- [x] 2026-02-10 Step 55 (Faza 4.5.6): added automation layer in `Coordinator` (`auto_configure_reporting`, `auto_bind`, `local_endpoint`, `configure_automation`, `automation_stats`) that auto-applies reporting presets per capability and attempts auto-bind when IEEE is available; bind path safely degrades to skip (`missing_remote_ieee`) when remote IEEE is not present in discovery metadata; validated by host tests (`python -m pytest tests/test_network_api.py tests/test_import.py tests/test_example_coordinator_web_demo.py -q` => `26 passed`).
- [x] 2026-02-10 Step 56 (Faza 4.5.7a): integrated source-aware attribute callback path in Python layer (`Coordinator._handle_attribute`) with backward-compatible parsing for legacy/extended callback signatures and precise state routing by `source_short_addr`; state metadata now stores optional `source_short_addr`/`source_endpoint`/`attr_type`; validated by host tests (`python -m pytest tests/test_network_api.py tests/test_import.py tests/test_example_coordinator_web_demo.py -q` => `27 passed`).
- [x] 2026-02-10 Step 57 (Faza 4.5.8): added persistent device graph in high-level API (`dump_registry`, `restore_registry`, `save_registry`, `load_registry`) with optional write-throttling (`persistence_min_interval_ms`) to bound flash writes; included serialization roundtrip for `DiscoveredDevice` + `DeviceIdentity`; validated by host tests (`python -m pytest tests/test_network_api.py tests/test_import.py tests/test_example_coordinator_web_demo.py -q` => `29 passed`).
- [x] 2026-02-10 Step 58 (Faza 4.5.7b): extended C bridge event payload for attribute updates with source metadata (`has_source`, `source_short_addr`, `source_endpoint`), added `ESP_ZB_CORE_REPORT_ATTR_CB_ID` handling for report-driven updates, and made `_uzigbee` dispatcher source-aware with legacy fallback (7-arg -> 6-arg on `TypeError`) to preserve existing callback compatibility; API docs updated.
- [x] 2026-02-10 Step 59 (Faza 4.5.10): completed high-level API documentation additions in `docs/API.md` with coordinator quickstart, recommended patterns, anti-patterns, and migration guide from low-level `ZigbeeStack` usage to `Coordinator` registry/capability workflow.
- [x] 2026-02-10 Step 60 (Faza 4.5.11): added high-level registry query ergonomics in `uzigbee.network` (`get_device_by_ieee`, `find_devices`, `select_device`) and IEEE identity propagation (`DeviceIdentity.ieee_addr`, `DiscoveredDevice.ieee_addr/ieee_hex`) with persistence-compatible serialization; updated docs and host coverage.
- [x] 2026-02-10 Step 61 (Faza 4.5.12): added device lifecycle layer in `uzigbee.network` (`offline_after_ms`, `configure_lifecycle`, `device_status`, `mark_device_offline`, `mark_device_online`) and online-aware filtering in `get_device`/`list_devices`/`find_devices`/`select_device`; extended persistence payload with lifecycle fields and updated docs/examples.
- [x] 2026-02-10 Step 62 (Faza 4.6.1): introduced bootstrap local node API in `uzigbee.node` with `Router` and `EndDevice` classes, chainable `add_*` endpoint builders, auto endpoint allocation, role-specific lifecycle (`register/start/on_signal/status`) and sleepy profile metadata for EndDevice; exported in package root, documented in `docs/API.md` and `docs/EXAMPLES.md`, and covered by host tests.
- [x] 2026-02-10 Step 63 (Faza 4.6.2): implemented `EndpointBuilder v1` in `uzigbee.node` with declarative capability templates, alias-based capability resolution, option-driven template expansion (`light`/`switch` variants, `power_outlet`, `ias_zone`), and batched `add_all(...)` definitions while preserving existing `add_*` compatibility; updated API/examples docs and expanded host tests for declarative add, aliases, and validation errors.
- [x] 2026-02-10 Step 64 (Faza 4.6.3): implemented local sensor update pipeline in `uzigbee.node` (`update`, `sensor_state`, `sensor_states`) with capability aliasing, endpoint auto-selection/ambiguity guard, strict value validation and raw conversion for temperature/humidity/pressure/binary/IAS, plus climate payload fan-out into per-sensor cache keys; updated docs/examples and host tests.
- [x] 2026-02-10 Step 65 (Faza 4.6.4): implemented actuator pipeline in `uzigbee.node` via `actor(name)` facade (`on/off/toggle`, `level`, `lock/unlock`, `cover*`, thermostat mode/setpoint) with idempotent local mirror cache (`actuator_state`, `actuator_states`) and strict per-kind action validation; updated docs/examples and host tests.
- [x] 2026-02-10 Step 66 (Faza 4.6.5): implemented endpoint-level reporting policy manager in `uzigbee.node` (`configure_reporting_policy`, `reporting_policies`, `apply_reporting_policy`, `clear_reporting_policy`) with default presets per capability/kind, override merge per `(cluster_id, attr_id)`, and apply path via `stack.configure_reporting`; updated docs/examples and host tests.
- [x] 2026-02-10 Step 67 (Faza 4.6.6): implemented endpoint-level binding policy manager in `uzigbee.node` (`configure_binding_policy`, `binding_policies`, `apply_binding_policy`, `clear_binding_policy`) with default bind clusters per capability/kind, destination/source IEEE handling, bind apply path via `stack.send_bind_cmd`, and IAS enrollment automation (`IAS CIE Address` update); updated docs/examples and host tests.
- [x] 2026-02-10 Step 68 (Faza 4.6.7): extended `uzigbee.EndDevice` with sleepy runtime profile (`wake_window_ms`, `checkin_interval_ms`, `low_power_reporting`) and timer helpers (`should_poll`, `should_keepalive`, `next_*_due_ms`, wake/poll/keepalive markers), plus low-power reporting tuning in EndDevice policy path (`min_interval >= 30`, `max_interval >= 900`); updated docs/examples and host tests.
- [x] 2026-02-10 Step 69 (Faza 4.6.8): implemented local node persistence API in `uzigbee.node` (`configure_persistence`, `dump_node_state`, `restore_node_state`, `save_node_state`, `load_node_state`) with bounded writes (`min_interval_ms` throttle), JSON serialization for endpoint graph/sensor+actuator caches/reporting+binding policies, and EndDevice sleepy profile roundtrip; updated docs/examples and host tests.
- [x] 2026-02-10 Step 70 (Faza 4.6.9): implemented advanced extension path in `uzigbee.node` with runtime custom capability templates (`register_capability`/`custom_capabilities`) wired into declarative `add(...)`, plus non-blocking policy hooks (`register_policy_hook`) for sensor/actuator/reporting/binding events; persisted custom capability metadata in node snapshots; updated docs/examples and host tests.
- [x] 2026-02-10 Step 71 (Faza 4.6.10): added dedicated host matrix suite for Router/EndDevice API (`tests/test_node_matrix_api.py`) covering builder variants, profile conflicts, state/reporting/binding edge cases, sleepy profile transitions, and integration snapshot roundtrip with hooks; added matrix runner (`tools/run_node_host_matrix.py`) and updated API/examples docs.
- [x] 2026-02-10 Step 72 (Faza 4.6.11): executed Router/EndDevice HIL matrix on ESP32-C6 (`COM3`) after rebuilding and flashing firmware from `build-ESP32_GENERIC_C6-uzigbee-step49a`; added HIL scripts (`hil_node_router_smoke.py`, `hil_node_enddevice_sleepy_smoke.py`, `hil_node_binding_reporting_smoke.py`, `hil_node_longrun_smoke.py`) and validated via `tools/hil_runner.py` (PASS 4/4). Observed runtime constraints captured in tests: reporting apply can return `ESP_ERR_INVALID_STATE (259)` in non-joined context, and IAS enroll attribute write currently degrades to partial status on this firmware.
- [x] 2026-02-10 Step 73 (Faza 4.6.12): completed Router/EndDevice API documentation closure with dedicated quickstart and cookbook coverage in `docs/API.md` and `docs/EXAMPLES.md` (sensor/actuator recipes, reporting/binding automation patterns, sleepy EndDevice usage, policy hooks and persistence workflow), aligned to implemented `uzigbee.node` behavior.
- [x] 2026-02-10 Step 74 (Faza 4, Gateway mode): added transport-agnostic gateway bridge module `uzigbee.gateway` with runtime command dispatcher (`ping`/`permit_join`/`list_devices`/`discover`/`read`/`control`), bounded event queue (`signal`/`attribute`/`device_added`/`device_updated`), JSON frame helpers (`decode_frame`/`encode_frame`/`process_frame`), custom operation hooks, and package export as `uzigbee.Gateway`; updated API/examples docs.
- [x] 2026-02-10 Step 75 (Faza 4, OTA update): expanded `uzigbee.ota` from minimal client helpers to full OTA API surface with capability model (`capabilities`, `is_server_supported`), safe start/stop controls for client/server (`start_client`, `stop_client`, `start_server`, `stop_server` with `strict` mode), and stateful `uzigbee.OtaManager`; preserved no-crash fallback behavior on unsupported firmware and updated docs/examples.
- [x] 2026-02-10 Step 76 (Faza 4, Green Power): added `uzigbee.greenpower` with `GreenPowerManager`, GP signal helpers (`gp_signal_ids`, `is_gp_signal`), capability detection for Proxy/Sink/commissioning controls, signal-driven event queue (`install_signal_handler`, `process_signal`, `poll_event`, `drain_events`) and strict/non-strict control methods (`set_proxy`, `set_sink`, `set_commissioning`) for safe fallback on unsupported firmware.
- [x] 2026-02-10 Step 77 (Faza 4, Touchlink): added `uzigbee.touchlink` with `TouchlinkManager`, touchlink signal helpers (`touchlink_signal_ids`, `is_touchlink_signal`), capability detection for initiator/target/factory-reset controls, signal-driven event queue (`install_signal_handler`, `process_signal`, `poll_event`, `drain_events`) and strict/non-strict control methods (`start_initiator`, `stop_initiator`, `set_target_mode`, `factory_reset`) with safe fallback on unsupported firmware.
- [x] 2026-02-10 Step 78 (Faza 4, NCP/RCP): added `uzigbee.ncp` with `NcpRcpManager`, runtime mode configuration (`ncp`/`rcp`/`disabled`), capability detection for mode control/frame TX hooks, signal/event bridge, frame codec helpers (`encode_frame_hex`/`decode_frame_hex`) and strict/non-strict lifecycle (`start`/`stop`/`send_host_frame`) with safe fallback on unsupported firmware.
- [x] 2026-02-10 Step 79 (Faza 5, CI artifacts): added GitHub Actions workflow `.github/workflows/firmware-artifacts.yml` for ESP32-C6 firmware build + artifact upload, plus packaging helper `tools/package_firmware_artifacts.sh` producing release-ready bundle (`bootloader.bin`, `partition-table.bin`, `micropython.bin`, `flash_args`, optional `sdkconfig`, `metadata.txt`, `SHA256SUMS.txt`); updated `docs/BUILD.md`.
- [x] 2026-02-10 Step 80 (Faza 5, board support): added hardware profile layer for popular ESP32-C6 boards (`esp32-c6-devkit`, `xiao-esp32c6`, `firebeetle-esp32c6`) via `firmware/boards/*.env` and extended `build_firmware.sh` with `--profile`, `--list-profiles`, `--sdkconfig-defaults`; kept single unified firmware target with profile-driven defaults; documented usage in `docs/BUILD.md`.
- [x] 2026-02-10 Step 81 (Faza 5, Zigbee2MQTT guide): added dedicated handbook `docs/Z2M_GUIDE.md` covering 5-minute quick start, interview troubleshooting, custom device flow, and external converter workflow with repo-specific automation paths (`tools/hil_runner.py`, `tools/z2m_interview_suite.py`); linked from `docs/README.md`.
- [x] 2026-02-10 Step 82 (Faza 5, tutorials): added `docs/Z2M_TUTORIALS.md` with practical high-level API scenarios for Coordinator/Router/EndDevice and Z2M validation commands; linked in `docs/README.md`.
- [x] 2026-02-10 Step 83 (Faza 5, API docs packaging): added MkDocs structure (`mkdocs.yml`, `docs/index.md`) and integrated navigation for build/API/examples/Z2M guides, completing documentation packaging path for publishing static API docs.
- [x] 2026-02-10 Step 84 (Faza 5, Z2M + HA integration): executed full interview-oriented Z2M HIL suite on device (`tools/z2m_interview_suite.py`, COM3, PASS 22/22, report `docs/z2m_interview_report.json`) and added HA discovery validation suite (`tools/ha_discovery_suite.py`) with strict converter compatibility checks for domain/device-class/unit coverage (PASS 18/18, report `docs/ha_discovery_report.json`); added integration docs `docs/HA_INTEGRATION.md` and linked it in docs/MkDocs navigation.
- [x] 2026-02-10 Step 85 (Faza 4.5.2b HIL): added on-device discovery pipeline smoke `tests/hil_network_autodiscovery_v2_smoke.py` validating queue debounce, retry/backoff requeue flow, and timing hardening (`discover_timeout_ms >= 2 * discover_poll_ms`), executed with `tools/hil_runner.py` on `COM3` (PASS).
- [x] 2026-02-10 Step 86 (Faza 4.5.13): extended high-level coordinator API for devices with duplicated same-type endpoints: endpoint/feature selectors (`device.endpoint(ep)`, `device.feature(name, selector)`, `device.switch(n)`, `device.temperature_sensor(n)`), endpoint-aware state cache and attribute routing, plus multi-endpoint auto-bind/auto-reporting fanout; validated by host tests (`python -m pytest tests/test_network_api.py tests/test_import.py tests/test_example_coordinator_web_demo.py tests/test_node_api.py tests/test_node_matrix_api.py -q` => `69 passed`), with docs updates in `docs/API.md` and `docs/EXAMPLES.md`.
- [x] 2026-02-10 Step 87 (Faza 4.5.9/4.6.11 extension): implemented high-level color-control path end-to-end (`send_color_move_to_color*` in C bridge + Python wrappers), added `coordinator_web_portal_color_highlevel.py`, `router_neopixel_color_light_highlevel.py`, and robust host runner `tools/hil_highlevel_color_portal_runner.py`; added compatibility hardening for older frozen API (`Coordinator` kwarg fallback, router attribute-callback fallback, coordinator permit-join retry, router rejoin retry), plus host verification (`69 passed`).
- [x] 2026-02-10 Step 88 (blokada HIL color dual-node): issue captured and root-caused; resolved later by firmware/API hardening and validated in Step 95 (`TEST_PASS` in `tools/hil_highlevel_color_portal_runner.py`).
- [x] 2026-02-10 Step 89 (firmware unification + flash): built latest uzigbee firmware in WSL (`build_firmware.sh`, profile `esp32-c6-devkit`, build dir `build-ESP32_GENERIC_C6-uzigbee-step49a`) including new frozen high-level modules and C bridge, then flashed identical image to both nodes (`COM3`, `COM6`) and erased Zigbee state partitions (`nvs`, `zb_storage`, `zb_fct`) on both boards.
- [x] 2026-02-10 Step 90 (HIL color E2E after reflash): historical unstable run documented; later stabilized and closed by Step 95 with deterministic dual-node pass.
- [x] 2026-02-10 Step 87 (High-level demo scripts): added high-level-only dual-device examples `examples/coordinator_web_portal_highlevel.py` and `examples/router_sensor_switch_sim_highlevel.py` (no direct `ZigbeeStack` usage in user script), updated `docs/EXAMPLES.md` runbook, and validated startup on hardware (`COM3` coordinator + web portal, `COM6` router simulator) with router `steering` and coordinator signal stream; pairing/discovery is environment-dependent in multi-network conditions and may require explicit channel/target alignment for deterministic end-to-end smoke control.
- [x] 2026-02-10 Step 91 (join reliability API): added explicit commissioning retrigger path `start_network_steering` across C core (`uzb_core_start_network_steering`), MicroPython C module (`_uzigbee.start_network_steering`), Python core (`ZigbeeStack.start_network_steering`) and high-level node API (`Router/EndDevice.start(join_parent=True)` now calls `join_parent()`, plus new `join_parent()` method); also hardened auto-discovery to ignore `0xFFFE` unknown short addresses.
- [x] 2026-02-10 Step 92 (host validation): expanded host coverage for the new commissioning path (`tests/test_core_api.py`, `tests/test_node_api.py`, `tests/test_network_api.py`) and executed regression suite `python -m pytest tests/test_core_api.py tests/test_network_api.py tests/test_node_api.py tests/test_node_matrix_api.py tests/test_import.py -q` -> `94 passed`.
- [x] 2026-02-10 Step 93 (firmware + HIL join/control): rebuilt and reflashed latest ESP32-C6 firmware on both nodes (`COM3`, `COM6`) including full `erase_flash`, then validated high-level two-node Zigbee flow without Wi-Fi portal using `tools/hil_highlevel_dual_toggle_runner.py` (`TEST_PASS`), confirming automatic join/discovery and coordinator->router control path is working.
- [x] 2026-02-10 Step 94 (web portal color E2E blocker): historical WLAN blocker documented; subsequently resolved on bench (`STAR1` join OK) and superseded by Step 95.
- [x] 2026-02-10 Step 95 (coordinator high-level commissioning/control hardening): removed unnecessary `s_device_registered` guard from read-only ZDO requests in `c_module/uzb_core.c` (`request_binding_table`, `request_active_endpoints`, `request_node_descriptor`, `request_simple_descriptor`, `request_power_descriptor`) and hardened high-level `Coordinator.start()` in `python/uzigbee/network.py` to auto-create/register local endpoint (`create_on_off_switch` + `register_device`) so control/discovery paths are valid without manual low-level setup.
- [x] 2026-02-10 Step 96 (dual-node web color E2E confirmation): rebuilt firmware in WSL (`build_firmware.sh`, profile `esp32-c6-devkit`), reflashed both boards (`COM3`, `COM6`), and reran `tools/hil_highlevel_color_portal_runner.py` -> `TEST_PASS`; confirmed full flow: `STAR1` Wi-Fi on coordinator, router join, auto-discovery (`device_added ... features=['color','level','on_off']`), and coordinator web control updating router NeoPixel (`cluster 0x0006/0x0008/0x0300` attrs observed).
- [x] 2026-02-10 Step 97 (Wi-Fi + Zigbee coexist fix for coordinator portal): added explicit coexist API hook across C bridge (`uzb_core_enable_wifi_i154_coex`, `_uzigbee.enable_wifi_i154_coex`) and Python (`ZigbeeStack.enable_wifi_i154_coex`, `Coordinator.start()` auto-call), fixed firmware build wiring by adding `esp_coex` dependency in `third_party/micropython-esp32/ports/esp32/esp32_common.cmake`, rebuilt/flashed latest firmware on `COM6`, and validated LAN reachability with real `curl` while Zigbee is running (`http://192.168.0.146/` -> portal HTML, `/permit?sec=120` -> `ok`).
- [x] 2026-02-10 Step 98 (web portal UX + dual-device manual control hardening): added full UI page for color control (`examples/portal_color.html`) and upgraded `examples/coordinator_web_portal_color_highlevel.py` with `/status` endpoint, external-HTML loader with embedded fallback, and safe cache-only `/probe` path (no forced reads) plus target-address discovery fallback for rejoin flows; reflashed both C6 boards (`COM6` coordinator, `COM3` router), started both demos, verified portal on `http://192.168.0.146/`, and confirmed coordinator web commands (`/on`, `/rgb`, `/off`) update router NeoPixel via high-level API (`cluster 0x0006/0x0008/0x0300` attrs observed).
- [x] 2026-02-10 Step 99 (HTTP reset + VFS closure): root-caused browser `ERR_CONNECTION_RESET` as socket close with unread request headers and partial-send risk; hardened coordinator HTTP server in `examples/coordinator_web_portal_color_highlevel.py` to fully drain request headers and send responses with robust `sendall` fallback loop; added explicit `vfs` partition to firmware (`firmware/partitions.csv`) and restored upstream ESP32 frozen boot helpers in manifest (`firmware/manifest.py` include of `$(PORT_DIR)/boards/manifest.py`), rebuilt+reflashed both boards (`COM6`, `COM3`), verified VFS read/write on-device (`boot.py` present, write/read `vfs_probe.txt`) and validated web stability from host with repeated `curl` (`/` and `/status` no reset failures).
- [x] 2026-02-10 Step 100 (Faza 4.5.9 prep): added dedicated dual-node high-level HIL matrix for endpoint-overlap + long-run stability (`tests/hil_highlevel_router_dual_switch_overlap.py`, `tests/hil_highlevel_coordinator_dual_switch_longrun.py`) and host orchestrator (`tools/hil_highlevel_overlap_longrun_runner.py`) with robust runtime-log parsing (no false PASS from paste-mode echo), plus docs update in `docs/EXAMPLES.md`.
- [x] 2026-02-10 Step 101 (commissioning hardening + blocker capture): hardened high-level node commissioning path to tolerate benign steering busy (`OSError(-1)`) in `uzigbee.node.join_parent()` and added host coverage (`test_router_join_parent_ignores_steering_busy_error` in `tests/test_node_api.py`); executed repeated HIL runs on COM6+COM3 and captured blocker for 4.5.9 closure: coordinator discovery consistently exposes only one remote `on_off` endpoint from test router (`feature_endpoints('on_off') -> (single endpoint)`), so endpoint-overlap HIL remains open until firmware-level multi-endpoint descriptor visibility is fixed.
- [x] 2026-02-10 Step 102 (Faza 4.5.9 closure): finalized overlap + long-run matrix validation on real dual-node setup (`COM6` coordinator + `COM3` router) by clearing runtime Zigbee state partitions (`nvs`, `zb_storage`, `zb_fct`) on both boards and rerunning `tools/hil_highlevel_overlap_longrun_runner.py` (`TEST_PASS`, endpoint hits `{10: 21, 11: 21}`, `120` rounds); host regression rechecked with `python -m pytest tests/test_node_api.py tests/test_network_api.py -q` (`66 passed`).
- [x] 2026-02-10 Step 103 (Faza 5 stress harness bootstrap): added dual-scenario stress orchestrator `tools/hil_stability_suite_runner.py` that runs overlap + color HIL flows in cycles with automatic runtime-state erase on both boards before each cycle; validated on hardware (`COM6` + `COM3`) with `python tools/hil_stability_suite_runner.py --coord-port COM6 --router-port COM3 --cycles 1 --overlap-timeout-s 620 --color-timeout-s 320` -> `TEST_PASS`.
- [x] 2026-02-11 Step 104 (Faza 4.7.1/4.7.2): implemented high-level auto-commissioning contract with explicit modes (`Coordinator.network_mode`, `Router/EndDevice.commissioning_mode`: `auto|fixed|guided`) and backward-compatible legacy-param upgrade to `fixed`; added serializable `uzigbee.NetworkProfile` model and runtime introspection (`Coordinator.network_info()`, `Node.network_info()`), persisted profile/mode in registry/node snapshots, updated API docs (`docs/API.md`), and validated host regressions (`python -m pytest tests/test_node_api.py tests/test_network_api.py tests/test_node_matrix_api.py tests/test_import.py -q` -> `80 passed`).
- [x] 2026-02-11 Step 105 (Faza 4.7.3): implemented lock-safe C bridge runtime snapshot (`uzb_core_get_network_runtime`) exposing active Zigbee `channel/pan_id/extended_pan_id/short_addr/formed/joined`, wired it to MicroPython module (`_uzigbee.get_network_runtime`) and Python API (`ZigbeeStack.get_network_runtime`), integrated runtime fields into high-level `Coordinator.network_info()` and `Node.network_info()`, and validated host regressions (`python -m pytest tests/test_core_api.py tests/test_network_api.py tests/test_node_api.py -q` -> `97 passed`).
- [x] 2026-02-11 Step 106 (Faza 4.7.4): implemented coordinator auto-channel selection in high-level API (`Coordinator(network_mode=\"auto\")`) with Wi-Fi-aware dynamic scoring (RSSI + channel-overlap), interoperability bias (`11/15/20/25` preferred, `26` penalized), blacklist/mask/preferred configuration knobs, deterministic fallback when Wi-Fi scan is unavailable, runtime decision telemetry in `network_info()[\"auto_channel\"]`, and host validation (`python -m pytest tests/test_network_api.py tests/test_core_api.py tests/test_node_api.py -q` -> `99 passed`).
- [x] 2026-02-11 Step 107 (Faza 4.7.5): implemented automatic runtime PAN/extPAN capture for coordinator auto mode by syncing `NetworkProfile` from runtime Zigbee parameters on successful commissioning signals (`formation/steering/first_start/reboot`) without requiring auto-discovery; in `network_mode=\"auto\"` profile now persists stack-generated `pan_id` and `extended_pan_id` (plus runtime channel mask) after network formation; added host coverage in `tests/test_network_api.py` and revalidated regressions (`python -m pytest tests/test_network_api.py tests/test_core_api.py tests/test_node_api.py -q` -> `101 passed`).
- [x] 2026-02-11 Step 108 (Faza 4.7.6): implemented Router/EndDevice auto-join hardening with configurable safe channel mask + steering retry/backoff in high-level API (`auto_join_channel_mask`, `join_retry_max`, `join_retry_base_ms`, `join_retry_max_backoff_ms`, `configure_auto_join()`), wired runtime profile sync on commissioning signals for nodes, persisted auto-join policy in node snapshots, and validated host regressions (`python -m pytest tests/test_network_api.py tests/test_core_api.py tests/test_node_api.py tests/test_node_matrix_api.py tests/test_import.py -q` -> `112 passed`).
- [x] 2026-02-11 Step 109 (Faza 4.7.7): completed guided commissioning mode behavior in high-level API: `Coordinator(network_mode=\"guided\")` now prefers restored profile identity (channel/PAN/extPAN) and falls back to dynamic channel selection when missing, while `Router/EndDevice(commissioning_mode=\"guided\")` now prefer restored profile and fallback to `auto_join_channel_mask` steering path on retry failure; added host coverage in `tests/test_network_api.py` and `tests/test_node_api.py`, updated docs (`docs/API.md`, `docs/EXAMPLES.md`), and revalidated regressions (`python -m pytest tests/test_network_api.py tests/test_core_api.py tests/test_node_api.py tests/test_node_matrix_api.py tests/test_import.py -q` -> `117 passed`).
- [x] 2026-02-11 Step 110 (Faza 4.7.8): implemented conflict/self-heal handling with high-level policy hooks and bounded retries: coordinator now reacts to `panid_conflict_detected` with controlled reform path and handles steering/formation failure signals with retrigger + telemetry; Router/EndDevice now auto-retrigger steering on conflict/failure signals (including guided fallback to `auto_join_channel_mask`), expose `configure_self_heal`, `on_commissioning_event`, and `self_heal` telemetry in `network_info/status`; persisted self-heal policy in registry/node snapshots, updated docs (`docs/API.md`, `docs/EXAMPLES.md`), and validated host regressions (`python -m pytest tests/test_network_api.py tests/test_core_api.py tests/test_node_api.py tests/test_node_matrix_api.py tests/test_import.py -q` -> `122 passed`).
- [x] 2026-02-11 Step 111 (Faza 4.7.9): implemented commissioning telemetry API on high-level coordinator and node layers: added `commissioning_stats(reset=False)` with counters for attempts/success/failure/timeout/conflict and `time_to_form_ms`/`time_to_join_ms`, wired stats updates to start paths, steering/form signals, and self-heal retriggers, and exposed telemetry in `network_info()`/`status()` for CI/HIL observability; updated docs (`docs/API.md`, `docs/EXAMPLES.md`) and revalidated host regressions (`python -m pytest tests/test_network_api.py tests/test_core_api.py tests/test_node_api.py tests/test_node_matrix_api.py tests/test_import.py -q` -> `126 passed`).
- [x] 2026-02-11 Step 112 (Faza 4.7.10/4.7.11): migrated high-level color examples to default auto/guided commissioning (removed hardcoded `ZIGBEE_CHANNEL/PAN/EXTPAN`, added optional advanced `FIXED_NETWORK_PROFILE` override in both scripts), updated runbook notes in `docs/EXAMPLES.md`, added regression guard `tests/test_example_highlevel_auto_commissioning.py`, and revalidated host suite (`python -m pytest tests/test_network_api.py tests/test_core_api.py tests/test_node_api.py tests/test_node_matrix_api.py tests/test_import.py tests/test_example_highlevel_auto_commissioning.py -q` -> `130 passed`).
- [x] 2026-02-11 Step 113 (Faza 4.7.12): migrated dual-node overlap HIL scripts to auto/guided commissioning (removed fixed `channel/pan_id`, added guided `auto_channel`/`auto_join_channel_mask`, self-heal telemetry hooks, and conflict-simulation trigger in coordinator loop), then executed full batch gate `python tools/hil_stability_suite_runner.py --coord-port COM6 --router-port COM3 --cycles 10 --overlap-timeout-s 620 --color-timeout-s 320` on clean runtime partitions each cycle -> `TEST_PASS cycles=10` (`total_elapsed=2204.3s`).
- [x] 2026-02-11 Step 114 (Faza 4.7.12 verification): rebuilt firmware (`build_firmware.sh`, profile `esp32-c6-devkit`, build `build-ESP32_GENERIC_C6-uzigbee-step49a`), reflashed both devices (`COM6`, `COM3`), reran stability batch (`cycles=2`) -> `TEST_PASS`, and confirmed overlap logs include runtime `network_info` in guided mode plus single conflict simulation event without runtime error.
- [x] 2026-02-11 Step 115 (Faza 4.7.13): finalized documentation runbook for auto-commissioning gate in `docs/EXAMPLES.md` (explicit 10-cycle command + conflict-simulation note), and completed API export consistency by exposing `SIGNAL_PANID_CONFLICT_DETECTED` in `python/uzigbee/__init__.py` with host regression recheck (`130 passed`).
- [x] 2026-02-11 Step 116 (Faza 5 progress, stress harness hardening): upgraded `tools/hil_stability_suite_runner.py` with strict API fallback detection (runtime-only `drop unsupported kwarg` markers), structured JSON reporting (`--report-json`), and richer per-scenario diagnostics (`TEST_PASS/FAIL`, timeout, traceback markers); added host tests `tests/test_hil_stability_suite_runner.py`, updated runbook in `docs/EXAMPLES.md`, revalidated host regressions (`132 passed`), and executed strict HIL batch on hardware (`COM6` + `COM3`, `cycles=2`) producing `docs/hil_stability_report.json` with `overall_pass=true` and zero compatibility-fallback hits.
- [x] 2026-02-11 Step 117 (Faza 5 progress, long-run strict batch): executed full strict stress gate with the hardened runner on real hardware (`python tools/hil_stability_suite_runner.py --coord-port COM6 --router-port COM3 --cycles 10 --overlap-timeout-s 620 --color-timeout-s 320 --report-json docs/hil_stability_report_10cycles.json`), result `TEST_PASS cycles=10`, `overall_pass=true`, `strict_api=true`, zero compatibility-fallback hits across all scenario entries (`compat_drop_count=0`), and total elapsed `1871.427s` (max overlap `141.469s`, max color `48.918s`).
- [x] 2026-02-11 Step 118 (Faza 5 progress, memory guardrail): added bounded per-device state cache in high-level API (`state_cache_max`, default `64`, range `8..512`) for both default and endpoint-aware cache maps in `uzigbee.network.DiscoveredDevice`; pruning now drops oldest entries by `updated_ms`, limits are configurable via `Coordinator(..., state_cache_max=...)` and `configure_state_engine(..., state_cache_max=...)`, restored snapshots are pruned to active cap; updated docs (`docs/API.md`, `docs/MEMORY.md`) and added host coverage (`test_state_cache_max_prunes_oldest_entries`) with regression run (`133 passed`).
- [x] 2026-02-11 Step 119 (repo publish readiness): cleaned repository metadata for GitHub publication (`LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, `CHANGELOG.md`), finalized docs (`docs/GETTING_STARTED.md`, `docs/BUILD.md`, `docs/LICENSE_NOTES.md`), and introduced reproducible third-party bootstrap flow (`tools/bootstrap_third_party.sh`, `tools/apply_vendor_overrides.sh`) with tracked vendor overrides under `firmware/vendor_overrides/` to keep repo lightweight and deterministic.
