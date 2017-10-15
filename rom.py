#!/usr/bin/env python3
import struct

class rom(object):
    def __init__(self):
        self.romData = []

    def load(self, path):
        file = open(path, 'rb')
        while True:
            byte = file.read(1)
            if not byte:
                break
            self.romData.append(ord(byte))
