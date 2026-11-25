/*
 * variant.h
 * NEPAMesh LoraSupermini v0.1 (nRF52840 supermini + Wio-SX1262), from MeshCore variants/promicro.
 * Pin numbers are indexes into g_ADigitalPinMap in variant.cpp.
 * Copyright (C) 2023 Seeed K.K.
 * MIT License
 */

 #pragma once

 #include "WVariant.h"

 ////////////////////////////////////////////////////////////////////////////////
 // Low frequency clock source

#define VARIANT_MCK       (64000000ul)

//#define USE_LFXO      // 32.768 kHz crystal oscillator
#define USE_LFRC    // 32.768 kHz RC oscillator

////////////////////////////////////////////////////////////////////////////////
// Power

#define PIN_EXT_VCC          (21)
#define EXT_VCC              (PIN_EXT_VCC)

// No battery sense on NEPAMesh LoraSupermini v0.1 (P0.31 is the radio BUSY line)
#define ADC_RESOLUTION       12

////////////////////////////////////////////////////////////////////////////////
// Number of pins

#define PINS_COUNT           (23)
#define NUM_DIGITAL_PINS     (23)
#define NUM_ANALOG_INPUTS    (3)
#define NUM_ANALOG_OUTPUTS   (0)

////////////////////////////////////////////////////////////////////////////////
// UART pin definition

#define PIN_SERIAL1_TX       (1)
#define PIN_SERIAL1_RX       (0)

////////////////////////////////////////////////////////////////////////////////
// I2C pin definition

#define WIRE_INTERFACES_COUNT 2

#define PIN_WIRE_SDA         (6)
#define PIN_WIRE_SCL         (7)
#define PIN_WIRE1_SDA        (13)
#define PIN_WIRE1_SCL        (14)

////////////////////////////////////////////////////////////////////////////////
// SPI pin definition

#define SPI_INTERFACES_COUNT 2

#define PIN_SPI_SCK          (2)
#define PIN_SPI_MISO         (3)
#define PIN_SPI_MOSI         (4)

#define PIN_SPI_NSS          (5)

#define PIN_SPI1_SCK         (18)
#define PIN_SPI1_MISO        (19)
#define PIN_SPI1_MOSI        (20)

////////////////////////////////////////////////////////////////////////////////
// Builtin LEDs

#define PIN_LED              (22)
#define LED_PIN              PIN_LED
#define LED_BLUE             PIN_LED
#define LED_BUILTIN          PIN_LED
#define LED_STATE_ON         1

////////////////////////////////////////////////////////////////////////////////
// Builtin buttons

#define PIN_BUTTON1          (6)
#define BUTTON_PIN           PIN_BUTTON1

//////////////////////////////////////////////////////////////////////////////
// LoRa

#define P_LORA_NSS                (9)       // P1.06
#define P_LORA_DIO_1              (16)      // P0.29
#define P_LORA_RESET              (8)       // P1.04
#define P_LORA_BUSY               (17)      // P0.31
#define P_LORA_MISO               (13)      // P1.13
#define P_LORA_SCLK               (15)      // P0.02
#define P_LORA_MOSI               (14)      // P1.15
#define SX126X_POWER_EN           (21)
#define SX126X_RXEN               (12)      // P1.11 -> Wio RF_SW
#define SX126X_TXEN               (-1)
#define SX126X_DIO2_AS_RF_SWITCH  true
#define SX126X_DIO3_TCXO_VOLTAGE  (1.8f)
