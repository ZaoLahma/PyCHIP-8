#!/usr/bin/env python3

import sys
from emu import emu

if "__main__" == __name__:
    debug = False
    print("argv: " + str(sys.argv))
    if len(sys.argv) == 2:
        if "db" == sys.argv[1]:
            debug = True

    emu = emu(debug)
    emu.run("./roms/games/Pong (1 player).ch8")
