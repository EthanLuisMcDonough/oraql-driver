CC=clang
CF=-O3 -march=native -fopenmp -g -D__PRINT_NORM -D__COLLABORATIVE_THREADING=6 -D__TEST_MG_CONVERGENCE -D__USE_BICGSTAB -lm
SOURCES=box.c mg.c miniGMG.c solver.c timer.x86.c box.c

miniGMG_omptask: $(SOURCES) operators.omptask.o
	$(CC) $(CF) $^ -o $@

miniGMG_ompif: $(SOURCES) operators.ompif.o
	$(CC) $(CF) $^ -o $@

miniGMG_avx: $(SOURCES) operators.avx.o
	$(CC) $(CF) $^ -o $@

miniGMG_sse: $(SOURCES) operators.sse.o
	$(CC) $(CF) $^ -o $@
