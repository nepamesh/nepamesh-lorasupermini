#ifndef _VARIANT_MESCHORESUPERMINI_
#define _VARIANT_MESCHORESUPERMINI_

/*
 * NEPAMesh LoraSupermini v0.1 carrier: nRF52840 supermini (Nice!Nano / Pro-micro clone) + Seeed Wio-SX1262 (114993390).
 * Pin map comes from tools/build.py (U1_NETS / U2_NETS) in the KiCad project. Based on nrf52_promicro_diy_tcxo.
 *
 * Supermini header, USB at top            Wio-SX1262
 * | Left  | Use            |  | Right | Use           |
 * | B-    | GND (JP1)      |  | B+    | battery in    |
 * | P0.06 | Serial2 RX     |  | RAW   | -             |
 * | P0.08 | Serial2 TX     |  | GND   |               |
 * | GND   |                |  | RST   |               |
 * | GND   |                |  | VCC   | Wio VCC (3V3) |
 * | P0.17 | I2C SDA (free) |  | P0.31 | BUSY          |  pin 11
 * | P0.20 | GPS TX  (free) |  | P0.29 | DIO1 / IRQ    |  pin 12
 * | P0.22 | GPS RX  (free) |  | P0.02 | SCK           |  pin 4
 * | P0.24 | GPS EN  (free) |  | P1.15 | MOSI          |  pin 3
 * | P1.00 | BUTTON  (free) |  | P1.13 | MISO          |  pin 2
 * | P0.11 | I2C SCL (free) |  | P1.11 | RF_SW = RXEN  |  pin 1
 * | P1.04 | NRST           |  | P0.10 | free (NFC)    |  pin 5
 * | P1.06 | NSS / CS       |  | P0.09 | free (NFC)    |  pin 6
 *
 * Internal: P0.15 LED, P0.13 enables the supermini VCC (3V3) rail, which powers the Wio module. It must stay high.
 * The PCB has no battery-voltage divider and every analog-capable header pin is used by the radio, so there is
 * no BATTERY_PIN: the node reports no battery level.
 * "(free)" pins have no PCB trace; the functions are only suggestions for bodge wiring.
 */

/** Master clock frequency */
#define VARIANT_MCK (64000000ul)

#define USE_LFRC // supermini clones: use the RC for LF (no reliance on a 32 kHz crystal)

#include "WVariant.h"

#ifdef __cplusplus
extern "C" {
#endif

#define PINS_COUNT (48)
#define NUM_DIGITAL_PINS (48)
#define NUM_ANALOG_INPUTS (1)
#define NUM_ANALOG_OUTPUTS (0)

// 3V3 rail for the Wio-SX1262 (supermini VCC pin)
#define PIN_3V3_EN (0 + 13) // P0.13

#define ADC_RESOLUTION 14

// LED
#define PIN_LED1 (0 + 15) // P0.15
#define LED_BLUE PIN_LED1
#define LED_STATE_ON 1

// Button (not on the PCB; wire a switch from P1.00 to GND if wanted)
#define BUTTON_PIN (32 + 0) // P1.00

// I2C (not on the PCB)
#define WIRE_INTERFACES_COUNT 1
#define PIN_WIRE_SDA (0 + 17) // P0.17
#define PIN_WIRE_SCL (0 + 11) // P0.11

// GPS (not on the PCB)
#define GPS_TX_PIN (0 + 20) // P0.20, data from the MCU
#define GPS_RX_PIN (0 + 22) // P0.22, data from the GNSS
#define PIN_GPS_EN (0 + 24) // P0.24
#define GPS_UBLOX

#define PIN_SERIAL1_TX GPS_TX_PIN
#define PIN_SERIAL1_RX GPS_RX_PIN
#define PIN_SERIAL2_RX (0 + 6) // P0.06
#define PIN_SERIAL2_TX (0 + 8) // P0.08

// SPI to the Wio-SX1262
#define SPI_INTERFACES_COUNT 1
#define PIN_SPI_SCK (0 + 2)    // P0.02 -> Wio pin 4
#define PIN_SPI_MOSI (32 + 15) // P1.15 -> Wio pin 3
#define PIN_SPI_MISO (32 + 13) // P1.13 <- Wio pin 2

#define LORA_SCK PIN_SPI_SCK
#define LORA_MOSI PIN_SPI_MOSI
#define LORA_MISO PIN_SPI_MISO
#define LORA_CS (32 + 6)     // P1.06 -> Wio pin 6 NSS
#define LORA_DIO0 (0 + 31)   // P0.31 <- Wio pin 11 BUSY
#define LORA_DIO1 (0 + 29)   // P0.29 <- Wio pin 12 DIO1
#define LORA_RESET (32 + 4)  // P1.04 -> Wio pin 5 NRST

#define USE_SX1262

#define SX126X_CS LORA_CS
#define SX126X_DIO1 LORA_DIO1
#define SX126X_BUSY LORA_DIO0
#define SX126X_RESET LORA_RESET
// Wio-SX1262: RF_SW high = RX path; TX path is switched inside the module from DIO2.
#define SX126X_RXEN (32 + 11) // P1.11 -> Wio pin 1 RF_SW
#define SX126X_TXEN RADIOLIB_NC
#define SX126X_DIO2_AS_RF_SWITCH
// On-module TCXO driven from DIO3
#define SX126X_DIO3_TCXO_VOLTAGE 1.8

#ifdef __cplusplus
}
#endif

#endif
