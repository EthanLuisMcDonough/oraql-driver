export KMP_AFFINITY=compact
export OMP_NUM_THREADS=52
perf stat -r 10 ./miniGMG_sse.initial 5 2 2 2 1 1 1
perf stat -r 10 ./miniGMG_sse.final 5 2 2 2 1 1 1

perf stat -r 10 ./miniGMG_ompif.initial 5 2 2 2 1 1 1
perf stat -r 10 ./miniGMG_ompif.final 5 2 2 2 1 1 1

perf stat -r 10 ./miniGMG_omptask.initial 5 2 2 2 1 1 1
perf stat -r 10 ./miniGMG_omptask.final 5 2 2 2 1 1 1
