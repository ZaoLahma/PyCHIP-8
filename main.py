#!/usr/bin/env python3

import sys
from emu import Emu

if "__main__" == __name__:
    debug = False
    romPath = None
    if len(sys.argv) == 3:
        if "db" in sys.argv:
            debug = True
        if "-r" in sys.argv:
            index = sys.argv.index("-r")
            romPath = sys.argv[index + 1]

    emu = Emu(debug)
    if None != romPath:
        emu.run(romPath)
    else:
        print("Provide rom path with -r Eg. python3 main.py -r Pong\ \(1\ player\).ch8")
