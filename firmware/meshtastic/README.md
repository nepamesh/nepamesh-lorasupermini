# Meshtastic on NEPAMesh LoraSupermini v0.1

The v0.1 PCB pinout does not match the stock "NRF52 Pro-micro DIY" firmware, so it needs this custom variant.
Stock Pro-micro firmware will NOT talk to the radio on this board.

## Build

```
git clone --recursive https://github.com/meshtastic/firmware.git
cp -r variants/nrf52840/diy/nepamesh_lorasupermini firmware/variants/nrf52840/diy/
cd firmware
pio run -e nepamesh_lorasupermini
```

Output: `.pio/build/nepamesh_lorasupermini/firmware-nepamesh_lorasupermini-*.uf2` (also a DFU `.zip`).

## Flash

1. The supermini ships with the Adafruit nRF52 UF2 bootloader (Nice!Nano style). Double-tap RST to GND: a USB drive appears.
2. Copy the `.uf2` onto it. The board reboots into Meshtastic.
3. Connect with the app or `meshtastic --port /dev/ttyACM0`. Set the region first (`meshtastic --set lora.region EU_868`/`US`, etc.). The radio does not transmit until a region is set.

Before first power-up: fit the antenna (IPEX pigtail). Transmitting without one can damage the SX1262.

## Pin map (from tools/build.py)

| Wio-SX1262 | nRF52840 | Firmware define |
|---|---|---|
| 4 SCK | P0.02 | PIN_SPI_SCK |
| 3 MOSI | P1.15 | PIN_SPI_MOSI |
| 2 MISO | P1.13 | PIN_SPI_MISO |
| 6 NSS | P1.06 | SX126X_CS |
| 11 BUSY | P0.31 | SX126X_BUSY |
| 12 DIO1 | P0.29 | SX126X_DIO1 |
| 5 NRST | P1.04 | SX126X_RESET |
| 1 RF_SW | P1.11 | SX126X_RXEN (TX switched internally by DIO2) |
| 8 VCC | supermini VCC (P0.13 enable kept high) | PIN_3V3_EN |

TCXO: DIO3 at 1.8 V. LED P0.15.

## Limitations

- No battery level: the PCB has no divider, and every analog-capable header pin (P0.02, P0.29, P0.31) is used by the radio.
- No button, GPS or I2C on the PCB. The variant puts them on spare pins (button P1.00, I2C SDA P0.17 / SCL P0.11,
  GPS TX P0.20 / RX P0.22 / EN P0.24, Serial2 P0.06 / P0.08) for bodge wiring.
- Hardware model reports as PRIVATE_HW.
- Flashed on one assembled board (Meshtastic 2.8.3): it sends and receives messages.  Range, battery and the bodge-wired extras are untested.
