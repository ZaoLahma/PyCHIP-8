#!/usr/bin/env python3

import sys
from emu import Emu

if "__main__" == __name__:
    debug = False
    romPath = None
    graphicsScale = 5
    print(str(sys.argv))
    if len(sys.argv) > 0:
        if '-db' in sys.argv:
            debug = True
        if '-r' in sys.argv:
            index = sys.argv.index('-r')
            romPath = sys.argv[index + 1]
        if '-s' in sys.argv:
            index = sys.argv.index('-s')
            graphicsScale =int(sys.argv[index + 1])

    emu = Emu(debug, graphicsScale)
    if None != romPath:
        emu.run(romPath)
    else:
        print("Provide rom path with -r Eg. python3 main.py -r Pong\ \(1\ player\).ch8")
