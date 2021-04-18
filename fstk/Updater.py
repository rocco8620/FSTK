import logging
import os
import subprocess
import sys


def install_package(package_name):
    logging.debug('Spawning pip to install update...')
    proc_handle = subprocess.Popen([sys.executable, "-m", "pip", "install", "--upgrade", package_name], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    # leggo lo standard output del processo, tenendo conto del timeout
    try:
        stdout, _ = proc_handle.communicate(timeout=10*60)
    except subprocess.TimeoutExpired:
        logging.warning('Pip killed during update beacuse of operation timeout expired')
        # se il timeout del processo scade, lo killo e leggo il suo stdout
        proc_handle.kill()
        # qui si può piantare solo nel caso che il processo stia eseguendo una system call piantata a causa di un fattore esterno.
        # un esempio è la lettura da un disco rimovibile rotto, o un modulo kernel buggato
        stdout, _ = proc_handle.communicate()

    if proc_handle.returncode == 0:
        logging.info('Pip update install completed successfully')
        logging.debug('Pip update install output: "{}"'.format(stdout))
        return True, None
    else:
        logging.error('An error occurred trying to install package update: pip exited with code {} and output: "{}"'.format(proc_handle.returncode, stdout))
        return False, 'Unknow error, see standard output'


def restart():
    # riavvia il software dopo aver installato una nuova versione
    # execv magic
    os.execv(sys.executable, ['python3', '-m', 'fstk'])