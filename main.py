#!/usr/bin/env python3

import sys
from emu import Emu

if "__main__" == __name__:
    debug = False
    print("argv: " + str(sys.argv))
    if len(sys.argv) == 2:
        if "db" == sys.argv[1]:
            debug = True

    emu = Emu(debug)
    emu.run("./roms/games/Pong (1 player).ch8")
