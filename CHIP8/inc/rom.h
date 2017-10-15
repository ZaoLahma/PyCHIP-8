#ifndef HEADER_ROM
#define HEADER_ROM
#include <stdint.h>

#define ROM_LOAD_FAILED (-1)
#define ROM_LOAD_OK     (0)

int8_t ROM_load(char* binPath);

#endif
