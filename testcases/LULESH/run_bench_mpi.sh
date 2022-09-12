perf stat -r 10 mpirun -n 8 ./lulesh-mpi.initial -s 30
perf stat -r 10 mpirun -n 8 ./lulesh-mpi.final -s 30
