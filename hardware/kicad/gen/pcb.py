#!/usr/bin/env python3
"""Generate the board file from the schematic, the project and the layout directives (layout.py) with the
standard's placement engine, ecad-standards/tools/placer.py (the submodule at ../standards).

    ./pcb.py        # writes ../sbc-baseboard/sbc-baseboard.kicad_pcb (+ .kicad_dru), runs DRC
    DEBUG_REF=C401 ./pcb.py     # and says where that part's candidate spots were refused
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "standards", "tools"))
sys.path.insert(0, HERE)
import placer, layout

if __name__ == "__main__":
    placer.main(layout, os.path.join(HERE, "..", "sbc-baseboard"), "sbc-baseboard", os.path.join(HERE, "..", "libs", "footprints"))
