import json
import os
import sys
import time
from multiprocessing import Process, Queue, Lock, Manager

from champions import champions_size
from getch.getch import getch
from utils import get_comp, calc_synergy, validate_synergy, next_comp

PROCESSES = 80
MINIMUM_COMP_SIZE = 8
MAXIMUM_COMP_SIZE = 10
MAX_QUEUE_SIZE = 1000
INITIAL_COMP = 'initial_comp.tft'
COMPS_FILE = 'comps.tft'


def initial_comp():
    comp = [0] * MAXIMUM_COMP_SIZE
    for i in range(MINIMUM_COMP_SIZE):
        comp[i] = i + 1
    if os.path.exists(INITIAL_COMP):
        with open(INITIAL_COMP, 'r') as file:
            lines = file.read().splitlines()
            if lines:
                last_line = lines[-1]
                comp = json.loads(last_line)

    return comp


def exit_gracefully(_signo, _stack_frame):
    sys.exit()


def producer(queue_comp: Queue):
    comp = initial_comp()
    while True:
        if queue_comp.qsize() > MAX_QUEUE_SIZE:
            time.sleep(0.01)
            continue
        comp = next_comp(comp)
        queue_comp.put(comp)


def consumer(queue_comp: Queue, queue_resp: Queue, processing: list):
    while True:
        if queue_resp.qsize() > MAX_QUEUE_SIZE:
            # time.sleep(0.1)
            continue
        comp = queue_comp.get()
        processing.append(comp)
        comp_names = get_comp(comp)
        synergy = calc_synergy(comp_names)
        remaining = validate_synergy(synergy)
        queue_resp.put((remaining == 0, comp))
        processing.remove(comp)


def monitor(queue_comp: Queue, queue_resp: Queue, processing: list):
    while True:
        print_info(processing, queue_comp, queue_resp)
        os.system('tput cuu 5')
        time.sleep(0.1)


def print_info(processing, queue_comp, queue_resp):
    print('Queue comp:', queue_comp.qsize(), '\x1b[K')
    print('Queue resp:', queue_resp.qsize(), '\x1b[K')
    print('Queue processing:', len(processing), '\x1b[K')
    processing_copy = processing[:]
    remaining = []
    remaining_count = 0
    if processing_copy:
        min_processing_copy = get_min_comp(processing_copy)
        write_initial_comp(min_processing_copy)
        processing_comp = ["%0.2d" % c for c in min_processing_copy if c > 0]
        remaining_count = \
            sum((champions_size - c) * (champions_size ** min_processing_copy.index(c) + 1)
                for c in min_processing_copy if c > 0)
        remaining = ["%0.2d" % (champions_size - c) for c in min_processing_copy if c > 0]
    else:
        processing_comp = ['-']
    print('Processing %0.2d' % len(processing_comp), processing_comp, '\x1b[K')
    if remaining:
        print('Remaining    ', remaining, '\x1b[K', f'Remaining ~{remaining_count:,}'.replace(',', '.'), '\x1b[K')
        # print(f'Remaining {remaining:,}'.replace(',', '.'), '\x1b[K')
    else:
        print()


def write_initial_comp(comp):
    with open(INITIAL_COMP, 'w') as file:
        file.write(str(comp) + '\n')


def process_resp(queue_resp: Queue, lock: Lock):
    while True:
        valid, comp = queue_resp.get()
        if valid:
            comp_names = get_comp(comp)
            synergy = calc_synergy(comp_names)
            print(comp_names, synergy)
            lock.acquire()
            with open(COMPS_FILE, 'a+') as f:
                f.write(
                    json.dumps(comp_names) +
                    json.dumps(synergy) + '\n'
                )
            lock.release()


def main():
    queue_comp = Queue()
    queue_resp = Queue()

    processing = Manager().list()
    lock = Lock()
    consumers = []

    producer_process = Process(target=producer, args=(queue_comp,))

    for i in range(PROCESSES):
        consumers.append(Process(target=consumer, args=(queue_comp, queue_resp, processing)))

    read_resp_process = Process(target=process_resp, args=(queue_resp, lock))

    monitor_process = Process(target=monitor, args=(queue_comp, queue_resp, processing))

    [p.start() for p in consumers + [monitor_process, producer_process, read_resp_process]]
    while True:
        if getch(False) == "q":
            os.system('tput cuu 1')
            break

    print()
    print('Terminating monitor...', end='')
    monitor_process.terminate()
    monitor_process.join()
    print('done\x1b[K')

    print('Terminating producer...', end='')
    producer_process.terminate()
    producer_process.join()
    print('done\x1b[K')

    print('Terminating consumers...', end='')
    [p.terminate() for p in consumers]
    [p.join() for p in consumers]
    print('done\x1b[K')

    print('Emptying queue resp...', end='')
    while not queue_resp.empty():
        time.sleep(0.1)
    print('done\x1b[K')

    print('Terminating read_resp_process...', end='')
    read_resp_process.terminate()
    read_resp_process.join()
    print('done\x1b[K')

    print_info(processing, queue_comp, queue_resp)


def get_min_comp(processing_comps):
    return list(reversed(min(list(reversed(c)) for c in processing_comps)))


def debug():
    comp = initial_comp()
    while True:
        last = comp
        comp = next_comp(comp)
        print(comp, get_min_comp([comp, last]))


# debug()
os.system('setterm -cursor off')
try:
    main()
finally:
    os.system('setterm -cursor on')
