export KMP_AFFINITY=compact
export OMP_NUM_THREADS=52
perf stat -r 10 ./lulesh-omp.initial -s 30
perf stat -r 10 ./lulesh-omp.final -s 30

perf stat -r 10 mpirun -n 8 ./lulesh-mpi.initial -s 30
perf stat -r 10 mpirun -n 8 ./lulesh-mpi.final -s 30

perf stat -r 10 ./lulesh.initial -s 30
perf stat -r 10 ./lulesh.final -s 30
