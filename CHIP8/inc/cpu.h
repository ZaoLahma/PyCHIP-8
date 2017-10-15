#ifndef HEADER_CPU
#define HEADER_CPU
#include <stdint.h>

typedef struct
{

} CPU_ctxt;

void CPU_init(CPU_ctxt* cpu);
void CPU_exec(unsigned char* bin);

#endif
