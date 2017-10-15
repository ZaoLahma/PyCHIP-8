#include "rom.h"
#include <stdio.h>

int8_t ROM_load(char* binPath)
{
  (void) printf("ROM_load called\n");

  return ROM_LOAD_FAILED;
}
