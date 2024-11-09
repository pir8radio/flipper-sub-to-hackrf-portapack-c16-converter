# .sub, .wav, .iq, .bin to .c16 Converter for HackRF PortaPack (not currently working)

Made by RockGod, trying to be fixed by "me" (gpt 4O). This project contains a Python script that helps convert .sub (and possibily .wav, .iq, .bin)  files (Flipper SubGhz RAW File) to .c16 files for use with HackRF PortaPack. This project is a fork from broken code and has been fixed and improved. I fixed this using chatgpt, I know nothing. Supports two protocols: RAW and BinRAW.

## What You Need

- A computer with Python installed. 
- The NumPy library for Python. (This library helps with math operations.)

## Steps to Get Ready

### 1. Install Python

If you don't have Python, you can download and install it from [python.org](https://www.python.org/).


### How to Use the Script

Get Your Files Ready

### How To Run the Script
Open the command prompt or terminal on your computer.

Go to the folder where you saved the script. For example, if it's saved in C:\Users\YourName\Documents, type:

```sh
cd C:\Users\YourName\Documents
```
Now, run the script with the following command:

```sh
python sdr_converter.py "input_file.sub" -o "output_file"
```
## Important Parameters



## What the Commands Do
python sdr_converter.py runs the script.

input_folder_name is the name of the folder of subfolders and files you want to convert.

-o output_file tells the script to save the new files with the name output_file.

-v enables verbose mode, which means the script will tell you what it's doing step by step.


### Check the New Files
After you run the command, the script creates two new files:

##### output_file.c16: This is the main file you need.

##### output_file.txt: This file has extra information like the sample rate and frequency.


## Default Output:

If the output folder is not specified, the converted files will be saved in the same location as the input files with the default naming convention.

## Example Commands
Here's an example of how to run the script:

Single File with Automatic Detection:

```sh
python sdr_converter.py "input_folder" -o "output_folder"
```

#### File Names with Spaces:

Ensure that file names with spaces are enclosed in quotes ("input folder").

## Extra Info

Sample Rate: This tells how many samples per second are used.

Intermediate Frequency: This helps adjust the signal.

Amplitude: This tells how strong the signal is.

Remove any comments from the top of the .sub files, such as "# generated with ook_to_sub.py", it will not see the protocol. Can handle large .sub files such as [CVS Chaos](https://github.com/jimilinuxguy/customer-assistance-buttons-sdr/blob/main/cvs/flipper_zero/CVS_Chaos.sub#L3C18-L3C28)




# ORIGINAL README - WAS LABELED AS "BROKEN"


Welcome to the flipper-sub-to-hackrf-portapack-c16-converter repository. This project aims to convert .sub files to HackRF Portapack .c16 files using a Python script.

The primary script used here is heavily inspired by the JS files found at this [repository](https://github.com/rascafr/sub-to-c16). 
Thanks François for the initial work!

The main goal of this project is to convert all .sub files from [https://github.com/RocketGod-git/Flipper_Zero](https://github.com/RocketGod-git/Flipper_Zero) 
and load them into the HackRF repository [https://github.com/RocketGod-git/HackRF-Treasure-Chest](https://github.com/RocketGod-git/HackRF-Treasure-Chest).

If you have the time and skills to help improve this project, please don't hesitate to contribute. 
Feel free to PR fixes or additions.

RocketGod

![RocketGod](https://github.com/RocketGod-git/flipper-sub-to-hackrf-portapack-c16-converter/assets/57732082/acaadb30-214c-4b42-b893-33de68230083)

