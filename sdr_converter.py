import os
import argparse
import math
import numpy as np
import logging
import wave

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SUPPORTED_PROTOCOLS = ['RAW', 'BinRAW']

def parse_sub(file: str) -> dict:
    try:
        with open(file, 'r') as f:
            lines = f.readlines()
    except Exception as e:
        logging.error(f'Cannot read input file: {e}')
        return None  # Return None on error

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
            # All lines after RAW_Data: are considered data lines
            data_lines.append(line)
        elif ':' in line:
            k, v = line.split(':', 1)
            info[k.lower()] = v.strip()
        else:
            # Ignore any other lines before data starts
            continue

    if info.get('protocol') not in SUPPORTED_PROTOCOLS:
        logging.error(f'Failed to parse {file}: Supported protocols are {", ".join(SUPPORTED_PROTOCOLS)} (found: {info.get("protocol")})')
        return None  # Return None for unsupported protocols

    # Now parse the data lines
    info['chunks'] = []
    for line in data_lines:
        if not line:
            continue
        chunk = []
        for value in line.strip().split():
            try:
                chunk.append(int(value, 10))  # Try to parse as decimal
            except ValueError:
                try:
                    chunk.append(int(value, 16))  # Try to parse as hexadecimal
                except ValueError:
                    logging.error(f"Invalid value in data: {value}")
                    return None  # Return None on invalid value
        info['chunks'].append(chunk)

    return info

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
        # When the signal is low, output zeros (transmitter off)
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
        return []  # Return an empty list on error
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
        return  # Return to skip unsupported or invalid files

    if verbose:
        logging.info(f'File information: {info}')

    # Flatten the list of chunks
    chunks = [item for sublist in info.get('chunks', []) for item in sublist]

    if verbose:
        logging.info(f'Found {len(chunks)} pure data chunks')

    sampling_rate = 500000  # Example sampling rate (can be adjusted)
    intermediate_freq = min(int(info.get('frequency', '418000000')) // 100, 5000)  # Example
    amplitude = 100  # Example amplitude

    IQSequence = durations_to_bin_sequence(chunks, sampling_rate, intermediate_freq, amplitude)

    buff = sequence_to_16le_buffer(IQSequence)
    outFiles = write_hrf_file(output, buff, info.get('frequency', 'unknown'), sampling_rate)

    if verbose:
        duration_seconds = len(IQSequence) / sampling_rate
        logging.info(f'Written {round(len(buff) / 1024)} kiB, {duration_seconds:.2f} seconds in files {", ".join(outFiles)}')

def main():
    parser = argparse.ArgumentParser(description="Convert Flipper Zero .sub files to HackRF .c16 files.")
    parser.add_argument('input_folder', help="Input folder to recursively search for .sub files.")
    parser.add_argument('-o', '--output_folder', help="Output folder to maintain the recursive structure.")
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output.')
    
    args = parser.parse_args()

    input_folder = os.path.abspath(args.input_folder)
    output_folder = os.path.abspath(args.output_folder) if args.output_folder else input_folder

    for root, _, files in os.walk(input_folder):
        for sub_file in files:
            if sub_file.endswith('.sub'):
                input_path = os.path.join(root, sub_file)

                # Maintain the folder structure
                relative_path = os.path.relpath(input_path, input_folder)
                output_path = os.path.join(output_folder, os.path.splitext(relative_path)[0]) + '.c16'
                output_dir = os.path.dirname(output_path)
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                
                process_file(input_path, output_path, args.verbose)

if __name__ == "__main__":
    main()
