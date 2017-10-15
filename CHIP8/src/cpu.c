#include "cpu.h"

void CPU_init(CPU_ctxt* cpu)
{
  (void) printf("CPU initialized\n");
}

void CPU_exec(unsigned char* bin)
{
  (void) printf("CPU_exec called\n");
}
