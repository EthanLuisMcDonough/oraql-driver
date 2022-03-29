import json
import dotmap
import oraql_settings
import sys
import os
import shutil
import logging as log
import subprocess as sp
import tempfile
import random
import re
from subprocess import PIPE
import tempfile

DEBUG_CONSOLE = True
ANNOTATE_SOURCE = True
REPORT_EVERY_NUM_TRIES = 10

# Use None to disable
DEBUG_TIME = '%b %d, %H:%M:%S'
DEBUG_FILE = 'debug.log'

try:
    import colorlog as logging
    if DEBUG_TIME:
        debug_string = ("%(asctime)s - %(log_color)s%(levelname)-8s%(reset)s "
                        "%(message)s")
    else:
        debug_string = "%(log_color)s%(levelname)-8s%(reset)s %(message)s"
    formatter = logging.ColoredFormatter(debug_string,
                                         reset=True,
                                         datefmt=DEBUG_TIME,
                                         log_colors={
                                             'DEBUG':    'cyan',
                                             'INFO':     'green',
                                             'WARNING':  'yellow',
                                             'ERROR':    'red',
                                             'CRITICAL': 'red,bg_white',
                                         },
                                         secondary_log_colors={},
                                         style='%')
except Exception:
    logging = log
    formatter = log.Formatter('%(asctime)s - %(levelname)-10s - %(message)s',
                              datefmt='%b %d, %H:%M:%S')

logger = logging.getLogger('')
logger.setLevel(log.DEBUG)

ch = log.StreamHandler()
ch.setLevel(log.DEBUG if DEBUG_CONSOLE else log.INFO)
ch.setFormatter(formatter)
logger.addHandler(ch)

def str_BinListAsHex(l):
    # pad list so it has at least length 1
    l += [0] * (1 - len(l))
    # interpret input list `l` as bits in a binary number
    num = int("".join([str(x) for x in l]), 2)
    # return as hex string
    return format(num, 'x')

def readBenchmarkFile(benchmark_file):
    if not os.path.isfile(benchmark_file):
        logger.error(f'Benchmark file @ {benchmark_file} does not exist')
        return None

    try:
        with open(benchmark_file, 'r') as fd:
            return dotmap.DotMap(json.load(fd))
    except Exception as e:
        logger.error(f'Failed to read benchmark file @ {benchmark_file}:\n'
                     f'{e}')
        return None

def compileFile(benchmark, source_file, seqfile):
    compiler = oraql_settings.clangcommand
    if source_file.path.endswith('.cc') or source_file.path.endswith('.cpp') or source_file.path.endswith('.cu'):
        compiler =  oraql_settings.clangppcommand
    if "compiler" in benchmark:
        compiler = benchmark.compiler
    try:
        run_result = sp.run(f'{compiler} @{seqfile.name} {source_file.path}', shell=True, stdout=PIPE, stderr=PIPE)

        if run_result.returncode is not 0:
            logger.debug(f'   - Compile error, exit code was {run_result.returncode} and command was:\n{compiler} @{seqfile.name} {source_file.path}')
            return False, 0
    except Exception as e:
        logger.warning(f'   - Compile error:\n'
                       f'     - Command: {cmd}\n'
                       f'     - {e!s}')
        return False, 0
    pattern_aacall = "(\d+) optimisticaa\s+- Number of optimisticAA alias calls"
    pattern_aacall_nocache = "(\d+) optimisticaa\s+- Number of optimisticAA answers not from cache"
    try:
      problemsize_total = int(re.search(pattern_aacall, run_result.stderr.decode('utf-8')).group(1))
      problemsize = int(re.search(pattern_aacall_nocache, run_result.stderr.decode('utf-8')).group(1))
      logger.debug(f' Optimistic compilation of file {source_file.path}. Responded to {problemsize} unique queries ({problemsize_total} total queries).')
    except Exception as e:
        logger.warning(f'Did not find optimistic AA statistics in compiler stderr. Did you build LLVM with OptimisticAA support?')
        return False, 0
    return True, problemsize

def linkExecutable(benchmark):
    executable_path = benchmark.executable
    if os.path.isfile(executable_path):
        logger.debug(f'  Delete existing executable @ {executable_path}')
        os.remove(executable_path)

    try: 
        cmd = [benchmark.make_cmd]
        run_result = sp.run(cmd, stdout=sp.DEVNULL, stderr=sp.DEVNULL, shell=True)
        if run_result.returncode is not 0:
            logger.warn(f'   - Make command error, exit code was '
                        f'{run_result.returncode}:\n'
                        f'     - Command: {" ".join(cmd)}')
            return False
    except Exception as e:
        logger.warn(f'   - Make command error:\n'
                    f'     - Command: {" ".join(cmd)}\n'
                    f'     - {e!s}')
        return False
    logger.debug(f' Making {executable_path}')
    return True

def copyExecutable(benchmark, version, seqfile=None):
    executable_path = benchmark.executable
    if not os.path.isfile(executable_path):
        logger.debug(f'  Trying to keep executable as {version}, but {executable_path} did not exist.')
    else:
        shutil.copy(executable_path, f'{executable_path}.{version}')
        logger.debug(f'  Keeping {executable_path}.{version}')
        if seqfile:
            shutil.copy(seqfile, f'{executable_path}.{version}.sequence.txt')
    

def runAndVerify(benchmark, io_pair):
    cmd = [benchmark.executable]+io_pair.input
    logger.debug(f'    - Run command "{" ".join(cmd)}"')
    try:
        run_result = sp.run(cmd, timeout=io_pair.timeout, stdout=PIPE, stderr=PIPE)
    except sp.TimeoutExpired:
        logger.debug(f'     - Run failed due to time out ({io_pair.timeout}s)')
        return False
    except Exception as e:
        logger.warn(f'     - Run failed due to unknown error:\n{e!s}')
        return False

    logger.debug(f'    - Check return value')
    if run_result.returncode is not io_pair.returncode:
        logger.debug(f'  Run failed due to exit code mismatch, expected '
                     f'{io_pair.returncode} got {run_result.returncode}')
        return False

    logger.debug(f'    - Collect run output')
    run_output = ''
    if os.path.isfile('output.txt'):
        with open('output.txt', 'r') as fd:
            run_output = fd.read()
    else:
        if io_pair.use_stdout:
            run_output += run_result.stdout.decode('utf8')
        if io_pair.use_stderr:
            run_output += run_result.stderr.decode('utf8')

    logger.debug(f'    - Try to match output with expected pattern')
    expected_output = io_pair.output
    if os.path.isfile(io_pair.output):
        with open(io_pair.output, 'r') as fd:
            expected_output = fd.read()

    match = re.fullmatch(expected_output, run_output)
    if match:
        logger.debug(f'    - Output matched expected pattern '
                     f'{len(expected_output)} vs {len(run_output)}')
        return True

    for pair in zip(expected_output.splitlines(), run_output.splitlines()):
        match = re.fullmatch(*pair)
        if not match:
            logger.debug(f'    - Output "%s" did not match expected pattern "%s"'%(pair))
    return False

import hashlib
def md5(fname):
  hash_md5 = hashlib.md5()
  with open(fname, "rb") as f:
    for chunk in iter(lambda: f.read(4096), b""):
      hash_md5.update(chunk)
  return hash_md5.hexdigest()

_seen_before = dict()
def compileAndRunOneConfiguration(benchmark, seqs, problemsizes, initialBuild = False):
    global _seen_before
    # compile individual files into object files
    with tempfile.NamedTemporaryFile() as fp:
      for source_file in benchmark.source_files:
          logger.debug(f'- Compiling {source_file.path} with seq {str_BinListAsHex(seqs[source_file.path])}')
          seqstr = " ".join([str(s) for s in seqs[source_file.path]])
          options = source_file.options + benchmark.options
          cmd = " ".join([*options, '-O3', '-mllvm', '-stats', '-v', '-mllvm', f'-opt-aa-seq="{seqstr}"', '-flegacy-pass-manager'])
          if(initialBuild):
              cmd += ' -mllvm -opt-aa-target="pessimisticAA"' # by supplying a target that does not exist, we disable optimism
          fp.write(bytes(cmd, 'utf-8'))
          fp.flush()
          success, thisproblemsize = compileFile(benchmark, source_file, fp)
          problemsizes[source_file.path] = max(thisproblemsize, problemsizes[source_file.path])
          if not success:
              logger.debug(f'tmpfile content was: {cmd}')
              logger.info(f'Failed compilation with seq {str_BinListAsHex(seqs[source_file.path])}')
              return False, problemsizes

      # link object files into executable
      success = linkExecutable(benchmark)
      if not success:
          logger.info(f'Failed linking with seq {seqs}')
          return False, problemsizes
      logger.debug(f'    Compiled. Compare executable file to previously seen files')
      md5sum = md5(benchmark.executable)
      if(md5sum in _seen_before):
          if not _seen_before[md5sum]["res"]:
              logger.debug(f'   We have seen this executable previously, and it was a failure.')
              return False, _seen_before[md5sum]["problemsizes"]
          else:
              logger.debug(f'   We have seen this executable previously, and it was a success.')
              copyExecutable(benchmark, 'final', fp.name)
              return True, _seen_before[md5sum]["problemsizes"]
      logger.debug(f'    This is a new executable, continue with verification.')

      # run the generated executable for each input/output pair
      for iop in benchmark.input_output_pairs:
          success = runAndVerify(benchmark, iop)
          if not success:
              logger.debug(f'    unsuccessful execution.')
              _seen_before[md5sum] = {"res": False, "problemsizes": problemsizes}
              logger.info(f'Failed execution with seq {[(seq,str_BinListAsHex(seqs[seq])) for seq in seqs]}')
              return False, problemsizes

      # if we made it here, it means that all object files compiled, the
      # executable linked and executed, and the results were correct for every
      # input/output pair. Success!
      logger.info(f'Successful test for all i/o pairs with seq {[(seq,str_BinListAsHex(seqs[seq])) for seq in seqs]}')
      _seen_before[md5sum] = {"res": True, "problemsizes": problemsizes}
      copyExecutable(benchmark, 'final', fp.name)
    return True, problemsizes

def compileAndRunAllConfigurations(benchmark, problemsizes):
    seqs = {x.path:[0]*problemsizes[x.path] for x in benchmark.source_files}
    for source_file in benchmark.source_files:
        logger.debug(f'Optimistic probing for {source_file.path}')
        seqs, problemsizes = split_n_try(seqs, 0, -1, source_file, benchmark, problemsizes)
    return seqs

def split_n_try(seqs, start, orig_end, source_file, benchmark, problemsizes):
  '''
  Try if [start, end) is safe to add to the sequence. If yes, do so.
  If no, bisect.
  '''
  end = orig_end
  if(orig_end == -1):
    end = problemsizes[source_file.path]
  print(f"splitntry {start} {orig_end} {end}")
  previous_seq = seqs[source_file.path]
  success = False
  seqs[source_file.path] = [1 if (i >= start and i < end) else seqs[source_file.path][i] for i in range(len(seqs[source_file.path]))]
  success, problemsizes = compileAndRunOneConfiguration(benchmark, seqs, problemsizes)
  if success:
    return seqs, problemsizes
  else:
    seqs[source_file.path] = previous_seq
    middle = start + (end - start) // 2
    if(middle > start and middle < end):
      left, problemsize_l = split_n_try(seqs, start, middle, source_file, benchmark, problemsizes)
      right, problemsize_r = split_n_try(seqs, middle, orig_end, source_file, benchmark, problemsizes)
      problemsizes[source_file.path] = max(problemsize_l[source_file.path], problemsize_r[source_file.path])
      seqs[source_file.path] = [1 if left[source_file.path][i] == 1 else right[source_file.path][i] for i in range(len(seqs[source_file.path]))]
  return seqs, problemsizes

def runBenchmark(benchmark_file):
    benchmark = readBenchmarkFile(benchmark_file)
    logger.info(f'Start benchmark {benchmark.name}')
    benchmark_path = os.path.dirname(benchmark_file)

    success = False
    seqs = {x.path:[] for x in benchmark.source_files}
    problemsizes = {x.path:0 for x in benchmark.source_files}
    success, problemsizes = compileAndRunOneConfiguration(benchmark, seqs, problemsizes, True)
    if success:
        logger.info(f'- Initial build successful, proceed to '
                    f'optimistic optimization for '
                    f'{len(benchmark.source_files)} source files')
        copyExecutable(benchmark, 'initial')
        seqs = compileAndRunAllConfigurations(benchmark, problemsizes)
    else:
        logger.info(f'- Initial build of {benchmark.name} failed')

    logger.info(f'Finished benchmark {benchmark.name}, '
                f'{"" if success else "un"}successful')
    logger.info(f'Final sequence: {[(seq,str_BinListAsHex(seqs[seq])) for seq in seqs]}')

benchmark_files = ['./benchmark.ot']

if len(sys.argv) > 1:
    benchmark_files = sys.argv[1:]

base_path = os.path.abspath(os.curdir)
for benchmark_file in benchmark_files:
    os.chdir(base_path)
    try:
        runBenchmark(benchmark_file)
    except Exception as e:
        logger.error(f' The execution of {benchmark_file} ended in an '
                     f' uncaught exception:\n{e!s}', exc_info=True)
