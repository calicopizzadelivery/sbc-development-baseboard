#!/bin/sh
# Measure the mirrored reference boards and this board with the standard's harvest tool
# (hardware/kicad/standards/tools/harvest.py); writes docs/reference-boards.csv and prints the comparison.
cd "$(dirname "$0")/.."
exec python3 hardware/kicad/standards/tools/harvest.py --mirror reference-boards --board hardware/kicad/sbc-baseboard/sbc-baseboard.kicad_pcb --csv docs/reference-boards.csv "$@"
