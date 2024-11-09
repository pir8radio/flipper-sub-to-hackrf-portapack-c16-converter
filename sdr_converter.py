import sys
import logging
import subprocess

# Configure logging
logging.basicConfig(level=logging.CRITICAL, format='%(asctime)s - %(levelname)s - %(message)s')

# List of required packages
REQUIRED_PACKAGES = ['numpy', 'alive-progress', 'psutil']

def install_packages():
    """Install required packages using pip."""
    for package in REQUIRED_PACKAGES:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            logging.info(f'{package} installed successfully.')
        except subprocess.CalledProcessError as e:
            logging.error(f'Failed to install {package}: {e}')

# Check and install required packages
install_packages()

import threading
import os
import argparse
import math
import shutil
import numpy as np
from alive_progress import alive_bar
import psutil
import gc
import time


print("\n\n\n\n\n\n") 
print("Some conversions will take a long time and appear to freeze. Let it run. To quit hit CTRL+C and wait some more... ")
print("\n\n\n") 

# Updated supported protocols
SUPPORTED_PROTOCOLS = [
    'RAW', 'BinRAW', 'CAME', 'Holtek_HT12X', 'PT2262', 
    'FSK', 'Keeloq', 'RC522', '1-Wire', 'DHT'
]

def check_memory_and_clear():
    """Check memory usage and clear memory if usage exceeds 80%."""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    memory_usage_percentage = (memory_info.rss / psutil.virtual_memory().total) * 100

    if memory_usage_percentage > 40:
        logging.warning(f'Memory usage is at {memory_usage_percentage:.2f}%. Clearing memory...')
        gc.collect()

def parse_sub(file: str) -> dict:
    try:
        with open(file, 'r') as f:
            lines = f.readlines()
    except Exception as e:
        logging.error(f'Cannot read input file: {e}')
        return None

    info = {}
    data_started = False
    data_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith('RAW_Data:'):
            data_started = True
            data_lines.append(line[len('RAW_Data:'):].strip())
        elif data_started:
            data_lines.append(line)
        elif ':' in line:
            k, v = line.split(':', 1)
            info[k.lower()] = v.strip()
        else:
            continue

    if info.get('protocol') not in SUPPORTED_PROTOCOLS:
        logging.error(f'Failed to parse {file}: Supported protocols are {", ".join(SUPPORTED_PROTOCOLS)} (found: {info.get("protocol")})')
        return None

    info['chunks'] = []
    for line in data_lines:
        if not line:
            continue
        chunk = []
        for value in line.strip().split():
            try:
                chunk.append(int(value, 10))
            except ValueError:
                try:
                    chunk.append(int(value, 16))
                except ValueError:
                    logging.error(f"Invalid value in data: {value}")
                    return None
        info['chunks'].append(chunk)

    return info

def process_with_timeout(func, args, timeout):
    """Run a function with a timeout."""
    result = [None]
    
    def target():
        result[0] = func(*args)

    thread = threading.Thread(target=target)
    thread.start()
    thread.join(timeout)

    if thread.is_alive():
        logging.warning(f'Skipped processing due to timeout after {timeout} seconds.')
        return None
    return result[0]

def process_raw(info: dict) -> list:
    logging.info("Processing RAW protocol data")
    processed_chunks = []
    for chunk in info['chunks']:
        processed_chunks.extend(chunk)
    return processed_chunks

def process_binraw(info: dict) -> list:
    logging.info("Processing BinRAW protocol data")
    processed_chunks = []
    for chunk in info['chunks']:
        for value in chunk:
            processed_chunks.append(format(value, '08b'))
    return processed_chunks

def process_came(info: dict) -> list:
    logging.info("Processing CAME protocol data")
    processed_chunks = []
    for chunk in info['chunks']:
        for value in chunk:
            processed_chunks.append(format(value, '08b'))
    return processed_chunks

def process_holtek(info: dict) -> list:
    logging.info("Processing Holtek_HT12X protocol data")
    processed_chunks = []
    for chunk in info['chunks']:
        for value in chunk:
            address_command = format(value, '012b')
            processed_chunks.append(address_command)
    return processed_chunks

def process_pt2262(info: dict) -> list:
    logging.info("Processing PT2262 protocol data")
    processed_chunks = []
    for chunk in info['chunks']:
        for value in chunk:
            processed_chunks.append(format(value, '08b'))
    return processed_chunks

def process_fsk(info: dict) -> list:
    logging.info("Processing FSK protocol data")
    processed_chunks = []
    for chunk in info['chunks']:
        for value in chunk:
            processed_chunks.append(format(value, '08b'))
    return processed_chunks

def process_keeloq(info: dict) -> list:
    logging.info("Processing Keeloq protocol data")
    processed_chunks = []
    for chunk in info['chunks']:
        for value in chunk:
            processed_chunks.append(format(value, '08b'))
    return processed_chunks

def process_rc522(info: dict) -> list:
    logging.info("Processing RC522 protocol data")
    processed_chunks = []
    for chunk in info['chunks']:
        for value in chunk:
            processed_chunks.append(format(value, '08b'))
    return processed_chunks

def process_one_wire(info: dict) -> list:
    logging.info("Processing 1-Wire protocol data")
    processed_chunks = []
    for chunk in info['chunks']:
        for value in chunk:
            processed_chunks.append(format(value, '08b'))
    return processed_chunks

def process_dht(info: dict) -> list:
    logging.info("Processing DHT protocol data")
    processed_chunks = []
    for chunk in info['chunks']:
        for value in chunk:
            processed_chunks.append(format(value, '08b'))
    return processed_chunks

def durations_to_bin_sequence(durations: list, sampling_rate: int, intermediate_freq: int, amplitude: int) -> list:
    sequence = []
    for duration in durations:
        samples = us_to_sin(duration > 0, abs(duration), sampling_rate, intermediate_freq, amplitude)
        sequence.extend(samples)
    return sequence

def us_to_sin(level: bool, duration: int, sampling_rate: int, intermediate_freq: int, amplitude: int) -> list:
    iterations = int(sampling_rate * duration / 1_000_000)
    if iterations <= 0:
        return []

    data_step_per_sample = 2 * math.pi * intermediate_freq / sampling_rate
    max_amplitude = int(32767 * (amplitude / 100))

    if level:
        return [
            (
                int(math.cos(i * data_step_per_sample) * max_amplitude),
                int(math.sin(i * data_step_per_sample) * max_amplitude)
            )
            for i in range(iterations)
        ]
    else:
        return [(0, 0)] * iterations

def sequence_to_16le_buffer(sequence: list) -> bytes:
    return np.array(sequence, dtype=np.int16).flatten().tobytes()

def write_hrf_file(file: str, buffer: bytes, frequency: str, sampling_rate: str) -> list:
    paths = [f'{file}.{ext}' for ext in ['c16', 'txt']]
    try:
        with open(paths[0], 'wb') as f:
            f.write(buffer)
        with open(paths[1], 'w') as f:
            f.write(generate_meta_string(frequency, sampling_rate))
    except Exception as e:
        logging.error(f'Cannot write output file: {e}')
        return []
    return paths

def generate_meta_string(frequency: str, sampling_rate: str) -> str:
    meta = [['sample_rate', sampling_rate], ['center_frequency', frequency]]
    return '\n'.join('='.join(map(str, r)) for r in meta)

def process_file(file: str, output: str, verbose: bool):
    if verbose:
        logging.info(f'Parsing file: {file}')
    
    info = parse_sub(file)
    if info is None:
        logging.error(f'Failed to process file: {file}. Skipping to the next file.')
        return

    if verbose:
        logging.info(f'File information: {info}')

    chunks = [item for sublist in info.get('chunks', []) for item in sublist]

    if info.get('protocol') == 'RAW':
        chunks = process_raw(info)
    elif info.get('protocol') == 'BinRAW':
        chunks = process_binraw(info)
    elif info.get('protocol') == 'CAME':
        chunks = process_came(info)
    elif info.get('protocol') == 'Holtek_HT12X':
        chunks = process_holtek(info)
    elif info.get('protocol') == 'PT2262':
        chunks = process_pt2262(info)
    elif info.get('protocol') == 'FSK':
        chunks = process_fsk(info)
    elif info.get('protocol') == 'Keeloq':
        chunks = process_keeloq(info)
    elif info.get('protocol') == 'RC522':
        chunks = process_rc522(info)
    elif info.get('protocol') == '1-Wire':
        chunks = process_one_wire(info)
    elif info.get('protocol') == 'DHT':
        chunks = process_dht(info)

    if verbose:
        logging.info(f'Found {len(chunks)} pure data chunks')

    sampling_rate = 500000  # Example sampling rate (can be adjusted)
    intermediate_freq = min(int(info.get('frequency', '418000000')) // 100, 5000)
    amplitude = 100  # Example amplitude

    IQSequence = durations_to_bin_sequence(chunks, sampling_rate, intermediate_freq, amplitude)

    buff = sequence_to_16le_buffer(IQSequence)
    outFiles = write_hrf_file(output, buff, info.get('frequency', 'unknown'), sampling_rate)

    if verbose:
        duration_seconds = len(IQSequence) / sampling_rate
        logging.info(f'Written {round(len(buff) / 1024)} kiB, {duration_seconds:.2f} seconds in files {", ".join(outFiles)}')

    # Check memory usage and clear if necessary
    check_memory_and_clear()

def remove_empty_folders(folder: str):
    """Remove empty folders and subfolders."""
    for dirpath, dirnames, filenames in os.walk(folder, topdown=False):
        for dirname in dirnames:
            dir_to_check = os.path.join(dirpath, dirname)
            if not os.listdir(dir_to_check):  # Check if the directory is empty
                print(f'Removing empty directory: {dir_to_check}')
                os.rmdir(dir_to_check)

def main():
    parser = argparse.ArgumentParser(description="Convert Flipper Zero .sub files to HackRF .c16 files.")
    parser.add_argument('input_folder', help="Input folder to recursively search for .sub files.")
    parser.add_argument('-o', '--output_folder', help="Output folder to maintain the recursive structure.")
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output.')
    
    args = parser.parse_args()

    input_folder = os.path.abspath(args.input_folder)
    output_folder = os.path.abspath(args.output_folder) if args.output_folder else input_folder

    # Collect all .sub files for processing
    sub_files = []
    for root, _, files in os.walk(input_folder):
        for sub_file in files:
            if sub_file.endswith('.sub'):
                sub_files.append(os.path.join(root, sub_file))

    # Process each file with a progress bar
    with alive_bar(len(sub_files), title="Processing files") as bar:
        for input_path in sub_files:
            relative_path = os.path.relpath(input_path, input_folder)
            output_path = os.path.join(output_folder, os.path.splitext(relative_path)[0]) + '.c16'
            output_dir = os.path.dirname(output_path)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # Process with a timeout for each individual file
            result = process_with_timeout(process_file, (input_path, output_path, args.verbose), 60)
            if result is None:
                logging.warning(f'Skipped processing of {input_path} due to timeout.')

            # Update the progress bar
            bar()

    # Remove empty folders in the output directory
    remove_empty_folders(output_folder)

if __name__ == "__main__":
    main()
