miniGMG:  box.c mg.c miniGMG.c operators.ompif.o solver.c timer.x86.c box.c
	clang -O3 -march=native -fopenmp -g -D__PRINT_NORM -D__COLLABORATIVE_THREADING=6 -D__TEST_MG_CONVERGENCE -D__USE_BICGSTAB -lm -o $@ $^
