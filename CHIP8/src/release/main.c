#include <stdio.h>
#include "emu.h"

int main(void)
{
  (void) printf("Main called\n");
  EMU_init();
  EMU_run("testPath");
}
