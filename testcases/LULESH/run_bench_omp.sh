export KMP_AFFINITY=compact
export OMP_NUM_THREADS=52
perf stat -r 10 ./lulesh-omp.initial -s 30
perf stat -r 10 ./lulesh-omp.final -s 30
