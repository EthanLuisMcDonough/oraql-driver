SHELL = /bin/sh

SERCXX = clang++ -DUSE_MPI=0
MPICXX = mpicxx -DUSE_MPI=1
CXX = $(SERCXX)

SOURCES2.0 = \
	lulesh-comm.cc \
	lulesh-viz.cc \
	lulesh-util.cc \
	lulesh-init.cc

CXXFLAGS = -g -O3 -I. -Wall

lulesh-mpi-omp: $(SOURCES2.0) lulesh.o
	@echo "Linking"
	$(MPICXX) $^ $(CXXFLAGS) -fopenmp -lm -o $@

lulesh-mpi: $(SOURCES2.0) lulesh.o
	@echo "Linking"
	$(MPICXX) $^ $(CXXFLAGS) -lm -o $@

lulesh-omp: $(SOURCES2.0) lulesh.o
	@echo "Linking"
	$(SERCXX) $^ $(CXXFLAGS) -fopenmp -lm -o $@

lulesh: $(SOURCES2.0) lulesh.o
	@echo "Linking"
	$(SERCXX) $^ $(CXXFLAGS) -lm -o $@

clean:
	/bin/rm -f *.o *~ $(OBJECTS) $(LULESH_EXEC)
	/bin/rm -rf *.dSYM
