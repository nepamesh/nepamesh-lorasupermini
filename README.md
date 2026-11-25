# NEPAMesh LoraSupermini

A small carrier PCB that joins an nRF52840 "supermini" (Nice!Nano clone) to a Seeed Wio-SX1262 LoRa module, with an off-board 18650 cell and a 3D-printable case.  Core parts come to about $10 per node.  Part of the [NEPAMesh](https://nepamesh.com) community Meshtastic network.

**Status: v0.1, early.**  Boards are fabricated and one is partly assembled.  The firmware builds but has not been run on hardware, and the case has not been sliced or printed.  Treat everything here as untested.

## What is in this repo

| Path | Contents |
|---|---|
| `nepamesh_lorasupermini.kicad_*` | KiCad 9 project: 2 layers, 32 x 55.5 mm |
| `lib/` | Project symbols and footprints (supermini, Wio-SX1262) |
| `gerbers/` | Gerber and drill files for JLCPCB (regenerated with the NEPAMesh LoraSupermini silkscreen and front logos; not fabricated in this form yet) |
| `tools/build.py` | Generates the KiCad project from code.  Edit the script, not the generated files |
| `tools/fill.py`, `tools/logo.py` | Zone fill and logo tracing |
| `case/build_case.py` | build123d script for the two-part case (62.2 x 87.8 mm).  Outputs in `case/out/` as STL |
| `firmware/meshtastic/` | Meshtastic variant (see its README) |
| `firmware/meshcore/` | MeshCore variant: repeater, room server, USB and BLE companion |
| `firmware/flash.sh` | Serial DFU flashing helper |


## Hardware summary

- Power: 18650 into a JST-PH connector, a PTC fuse, and a P-channel MOSFET for reverse-polarity protection, then the supermini battery input.  The module takes 3.3 V from the supermini VCC pin.
- No battery divider, button, GPS or I2C on the board.  The firmware variants map spare pins for bodge wiring.
- Pin map (Wio-SX1262 to nRF52840): SCK P0.02, MOSI P1.15, MISO P1.13, NSS P1.06, NRST P1.04, BUSY P0.31, DIO1 P0.29, RF_SW P1.11.  DIO2 switches TX inside the module, and DIO3 powers its TCXO at 1.8 V.

## Firmware

Build the Meshtastic variant by copying `firmware/meshtastic/variants/nrf52840/diy/nepamesh_lorasupermini` into a checkout of [meshtastic/firmware](https://github.com/meshtastic/firmware) and running `pio run -e nepamesh_lorasupermini`.  The MeshCore variant goes into `variants/` of a checkout of [meshcore-dev/MeshCore](https://github.com/meshcore-dev/MeshCore).  Tested against Meshtastic 2.8.3 and MeshCore commit 75b04ef, builds only.

Flash by double-tapping RST to GND so the bootloader drive appears, then copy the `.uf2` or use `firmware/flash.sh`.

Read before you flash:

- **Default credentials.**  The MeshCore repeater and room server builds ship with the admin password `password` and the room password `hello`.  The BLE companion build uses the pairing PIN `123456`.  Change them before putting a node on the air.  They are placeholders from upstream defaults, not secrets.
- **Set a region first.**  Meshtastic does not transmit until a region is set.
- **Fit the antenna before powering up.**  Transmitting into an open antenna port can damage the SX1262.
- **Licenses.**  The Meshtastic variant is a derivative of GPL-3.0 code and is distributed under GPL-3.0.  The MeshCore variant is MIT, and its `variant.h` retains a Seeed K.K. MIT header.  The Meshtastic hardware model reports as `PRIVATE_HW`.

## Known gaps

- Supermini hole drill and outline were assumed from photos and a datasheet.  Measure the real board before ordering more.
- The supermini VCC pin has not been checked against 125 mA transmit bursts.
- The first five boards were fabricated with the working name "meschoresupermini" on the silkscreen.  The files here use the new name and add two small NEPAMesh logos on the front.  The finest logo strokes are thinner than JLCPCB's usual 0.15 mm silkscreen minimum, so expect fuzzy detail.

## License

Original files outside `firmware/` are MIT (see `LICENSE`).  Firmware variants follow the licenses in `firmware/meshtastic/LICENSE` and `firmware/meshcore/LICENSE`.  The NEPAMesh logo is not covered.

*NEPAMesh is a community Meshtastic network covering Northeastern Pennsylvania's Wyoming Valley.  Live map at [map.nepamesh.com](https://map.nepamesh.com).  Questions in the [Discord](https://discord.com/invite/cSpfk6H2hz).*

*[Meshtastic](https://meshtastic.org) is a registered trademark of Meshtastic LLC.  No warranty is provided.  Use at your own risk.  This project is not endorsed by or affiliated with Meshtastic LLC.*
