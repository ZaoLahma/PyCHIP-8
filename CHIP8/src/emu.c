#include "emu.h"
#include "rom.h"
#include "cpu.h"
#include <stdio.h>
#include <stdint.h>

static CPU_ctxt cpu;

void EMU_init(void)
{
    CPU_init(&cpu);
}

void EMU_run(char* binPath)
{
  (void) printf("EMU_run called\n");

  if(ROM_LOAD_OK != ROM_load(binPath))
  {
    (void) printf("Failed to load ROM: %s\n", binPath);
    return;
  }

  unsigned char* bin = 0u;
  CPU_exec(bin);
}
