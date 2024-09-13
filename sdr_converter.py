import os
import argparse
import math
from typing import List, Tuple
import struct
import numpy as np
import wave
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SUPPORTED_PROTOCOLS = ['RAW', 'BinRAW']

def parse_sub(file: str) -> dict:
    try:
        with open(file, 'r') as f:
            sub_data = f.read()
    except Exception as e:
        logging.error(f'Cannot read input file: {e}')
        exit(-1)

    sub_chunks = [r.strip() for r in sub_data.split('\n') if r.strip()]
    info = {}
    data_start_line = 0
    for idx, row in enumerate(sub_chunks):
        if ':' in row:
            k, v = row.split(':', 1)
            info[k.lower()] = v.strip()
        else:
            data_start_line = idx
            break  # Header ends, data starts

    if info.get('protocol') not in SUPPORTED_PROTOCOLS:
        logging.error(f'Failed to parse {file}: Supported protocols are {", ".join(SUPPORTED_PROTOCOLS)} (found: {info.get("protocol")})')
        exit(-1)

    info['chunks'] = []
    for r in sub_chunks[data_start_line:]:
        if not r.strip():
            continue  # Skip empty lines
        chunk = []
        for value in r.strip().split():
            try:
                chunk.append(int(value, 10))  # Try to parse as decimal
            except ValueError:
                chunk.append(int(value, 16))  # If decimal parsing fails, parse as hexadecimal
        info['chunks'].append(chunk)

    return info

def parse_wav(file: str) -> dict:
    try:
        with wave.open(file, 'r') as wf:
            params = wf.getparams()
            framerate = params.framerate
            nframes = params.nframes
            audio_data = wf.readframes(nframes)
            info = {
                'sampling_rate': framerate,
                'chunks': np.frombuffer(audio_data, dtype=np.int16).tolist()
            }
            return info
    except Exception as e:
        logging.error(f'Cannot read WAV file: {e}')
        exit(-1)

def parse_iq(file: str) -> dict:
    try:
        with open(file, 'rb') as f:
            iq_data = f.read()
            info = {
                'chunks': np.frombuffer(iq_data, dtype=np.int16).tolist()
            }
            return info
    except Exception as e:
        logging.error(f'Cannot read IQ file: {e}')
        exit(-1)

def parse_bin(file: str) -> dict:
    try:
        with open(file, 'rb') as f:
            bin_data = f.read()
            info = {
                'chunks': np.frombuffer(bin_data, dtype=np.uint8).tolist()
            }
            return info
    except Exception as e:
        logging.error(f'Cannot read BIN file: {e}')
        exit(-1)

def write_hrf_file(file: str, buffer: bytes, frequency: str, sampling_rate: str) -> List[str]:
    paths = [f'{file}.{ext}' for ext in ['c16', 'txt']]
    try:
        with open(paths[0], 'wb') as f:
            f.write(buffer)
        with open(paths[1], 'w') as f:
            f.write(generate_meta_string(frequency, sampling_rate))
    except Exception as e:
        logging.error(f'Cannot write output file: {e}')
        exit(-1)
    return paths

def generate_meta_string(frequency: str, sampling_rate: str) -> str:
    meta = [['sample_rate', sampling_rate], ['center_frequency', frequency]]
    return '\n'.join('='.join(map(str, r)) for r in meta)

HACKRF_OFFSET = 0

def durations_to_bin_sequence(durations: List[int], sampling_rate: int, intermediate_freq: int, amplitude: int) -> List[Tuple[int, int]]:
    sequence = []
    for duration in durations:
        sequence.extend(us_to_sin(duration > 0, abs(duration), sampling_rate, intermediate_freq, amplitude))
    return sequence

def us_to_sin(level: bool, duration: int, sampling_rate: int, intermediate_freq: int, amplitude: int) -> List[Tuple[int, int]]:
    iterations = int(sampling_rate * duration / 1_000_000)
    if iterations == 0:
        return []

    data_step_per_sample = 2 * math.pi * intermediate_freq / sampling_rate
    hackrf_amplitude = (256 ** 2 - 1) * (amplitude / 100)

    return [
        (
            HACKRF_OFFSET + int(math.floor(math.cos(i * data_step_per_sample) * (hackrf_amplitude / 2))),
            HACKRF_OFFSET + int(math.floor(math.sin(i * data_step_per_sample) * (hackrf_amplitude / 2)))
        )
        if level else (HACKRF_OFFSET, HACKRF_OFFSET)
        for i in range(iterations)
    ]

def sequence_to_16le_buffer(sequence: List[Tuple[int, int]]) -> bytes:
    return np.array(sequence).astype(np.int16).tobytes()

def auto_detect_parameters(file: str) -> Tuple[int, int, int]:
    file_ext = os.path.splitext(file)[1].lower()
    
    # Default values
    default_sampling_rate = 500000
    default_intermediate_freq = 5000
    default_amplitude = 100

    logging.info(f"Auto-detecting parameters for file: {file}")
    
    if file_ext == '.sub':
        try:
            info = parse_sub(file)
            frequency = int(info.get('frequency', '418000000'))  # Example frequency in Hz
            sampling_rate = default_sampling_rate
            intermediate_freq = min(frequency // 100, default_intermediate_freq)
            amplitude = default_amplitude
        except Exception as e:
            logging.error(f"Error parsing .sub file: {e}")
            return (default_sampling_rate, default_intermediate_freq, default_amplitude)

    elif file_ext == '.wav':
        try:
            with wave.open(file, 'r') as wf:
                sampling_rate = wf.getframerate()
            intermediate_freq = min(sampling_rate // 100, default_intermediate_freq)
            amplitude = default_amplitude
        except Exception as e:
            logging.error(f"Error reading .wav file: {e}")
            return (default_sampling_rate, default_intermediate_freq, default_amplitude)

    elif file_ext == '.iq' or file_ext == '.bin':
        sampling_rate = default_sampling_rate
        intermediate_freq = default_intermediate_freq
        amplitude = default_amplitude

    else:
        logging.warning(f"Unsupported file format: {file_ext}. Using default parameters.")
        sampling_rate = default_sampling_rate
        intermediate_freq = default_intermediate_freq
        amplitude = default_amplitude

    logging.info(f"Detected parameters - Sampling Rate: {sampling_rate}, Intermediate Frequency: {intermediate_freq}, Amplitude: {amplitude}")
    return (sampling_rate, intermediate_freq, amplitude)

def parse_args() -> dict:
    parser = argparse.ArgumentParser(description="SDR-based file processing script")
    parser.add_argument('file', help="Input file path or folder.")
    parser.add_argument('-o', '--output', help="Output file or folder path. If not specified, the input file name will be used.")
    parser.add_argument('-sr', '--sampling_rate', type=int, help="Sampling rate for the output file.")
    parser.add_argument('-if', '--intermediate_freq', type=int, help="Intermediate frequency.")
    parser.add_argument('-a', '--amplitude', type=int, help="Amplitude percentage.")
    parser.add_argument('--auto', action='store_true', help='Automatically detect parameters.')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output.')
    return vars(parser.parse_args())

def process_file(file: str, output: str, sampling_rate: int, intermediate_freq: int, amplitude: int, verbose: bool):
    if verbose:
        logging.info(f'Parsing file: {file}')
    
    file_ext = os.path.splitext(file)[1].lower()
    if file_ext == '.sub':
        info = parse_sub(file)
    elif file_ext == '.wav':
        info = parse_wav(file)
    elif file_ext == '.iq':
        info = parse_iq(file)
    elif file_ext == '.bin':
        info = parse_bin(file)
    else:
        logging.error(f'Unsupported file format: {file_ext}')
        exit(-1)

    if verbose:
        logging.info(f'File information: {info}')

    chunks = [item for sublist in info.get('chunks', []) for item in sublist]  # Flatten the list of chunks

    if verbose:
        logging.info(f'Found {len(chunks)} pure data chunks')

    IQSequence = durations_to_bin_sequence(chunks, sampling_rate, intermediate_freq, amplitude)
    buff = sequence_to_16le_buffer(IQSequence)
    outFiles = write_hrf_file(output, buff, info.get('frequency', 'unknown'), sampling_rate)

    if verbose:
        logging.info(f'Written {round(len(buff) / 1024)} kiB, {len(IQSequence) / sampling_rate} seconds in files {", ".join(outFiles)}')

def main():
    args = parse_args()

    file = args.get('file')
    output = args.get('output')
    sampling_rate = args.get('sampling_rate')
    intermediate_freq = args.get('intermediate_freq')
    amplitude = args.get('amplitude')
    auto = args.get('auto')
    verbose = args.get('verbose', False)

    if auto:
        sampling_rate, intermediate_freq, amplitude = auto_detect_parameters(file)
    else:
        sampling_rate = sampling_rate or 500000
        intermediate_freq = intermediate_freq or sampling_rate // 100
        amplitude = amplitude or 100

    current_dir = os.getcwd()
    file = os.path.join(current_dir, file)
    if output:
        output = os.path.join(current_dir, output)

    if os.path.isdir(file):
        sub_files = [f for f in os.listdir(file) if f.endswith(('.sub', '.wav', '.iq', '.bin'))]
        total_files = len(sub_files)
        if not os.path.exists(output):
            os.makedirs(output)
        for sub_file in sub_files:
            input_path = os.path.join(file, sub_file)
            output_path = os.path.join(output, os.path.splitext(sub_file)[0])
            process_file(input_path, output_path, sampling_rate, intermediate_freq, amplitude, verbose)
    else:
        if output is None:
            output = os.path.splitext(file)[0]
        process_file(file, output, sampling_rate, intermediate_freq, amplitude, verbose)

if __name__ == "__main__":
    main()
