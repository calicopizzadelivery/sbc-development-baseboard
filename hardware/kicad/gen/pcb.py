#!/usr/bin/env python3
"""Generate the board file from the schematic, the project and the layout directives (layout.py) with the
standard's placement engine, ecad-standards/tools/placer.py (the submodule at ../standards).

    ./pcb.py        # writes ../sbc-baseboard/sbc-baseboard.kicad_pcb (+ .kicad_dru), runs DRC
    ./pcb.py --route            # then FreeRouting (layout.FREEROUTING) over the locked lanes, hours
    ./pcb.py --copper           # (or alone, over the routed board) ground floods on the outer layers and stitching vias
    DEBUG_REF=C401 ./pcb.py     # and says where that part's candidate spots were refused
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.environ.get("STANDARDS_TOOLS") or os.path.join(HERE, "..", "standards", "tools"))   # STANDARDS_TOOLS: a working copy of ecad-standards/tools while the engine is being changed
sys.path.insert(0, HERE)
import placer, layout

if __name__ == "__main__":
    out = os.path.join(HERE, "..", "sbc-baseboard")
    if "--copper" not in sys.argv or "--route" in sys.argv:       # --copper alone works over the existing (routed) board: no new placement
        placer.main(layout, out, "sbc-baseboard", os.path.join(HERE, "..", "libs", "footprints"))
    if "--route" in sys.argv:                                     # then FreeRouting over the locked lanes (not reproducible: the board is the source of truth from here)
        import subprocess
        subprocess.run([sys.executable, os.path.join(os.path.dirname(placer.__file__), "autoroute.py"), os.path.join(out, "sbc-baseboard.kicad_pcb"),
                        layout.FREEROUTING, "--passes", str(getattr(layout, "FREEROUTING_PASSES", 30)),
                        "--plane-layers", *sorted({p[2] for p in layout.PLANES})], check=True)   # the router routes on no layer that carries a plane
    if "--copper" in sys.argv:                                    # then the ground floods and stitching over the routed board (idempotent)
        import subprocess
        subprocess.run([sys.executable, os.path.join(os.path.dirname(placer.__file__), "copper.py"), os.path.join(out, "sbc-baseboard.kicad_pcb"),
                        os.path.join(HERE, "layout.py")], check=True)
