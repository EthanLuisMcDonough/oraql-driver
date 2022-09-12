module use /soft/modulefiles/
module load openmpi/4.1.1-llvm
source ../../path_setup.sh
export OMPI_CC=/home/jhuckelheim/llvm-project/build/bin/clang
export OMPI_CXX=/home/jhuckelheim/llvm-project/build/bin/clang

python3 ../../oraql_chunked.py benchmark-mpi.ot
python3 ../../oraql_chunked.py benchmark-omp.ot
python3 ../../oraql_chunked.py benchmark.ot

