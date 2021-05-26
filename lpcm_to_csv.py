# Used for converting multi and single channel uncompressed
# audio to a single waveform for analog transcription.

import aifc # https://docs.python.org/3/library/aifc.html
import wave # https://docs.python.org/3/library/wave.html
import csv  # https://docs.python.org/3/library/csv.html
import math
import sys

# Variables for unpacking
import record_constant.samplingRate

supported_formats = ['.wav', '.wave', '.aifc', 'aiff']

if sys.argv.length != 2 :
  print('Wrong number of arguements.')
  quit()
  
filename = sys.argv[1]
if '.' not in filename:
  print('File extension must be provided.')
  quit()    
  
extension = filename.split(".")[1]
if extension not in supported_formats:
  print('Not a supported file format.')
  quit()  

with wave.open(fileName, 'rb') as w_file:
  channels = wave.getnchannels()
  number_of_frames = wave.getnframes()
  with open(fileName[:-4] + '.csv', 'w', newline='') as csvfile:
    csv_writer = csv.writer(csvfile, delimiter=' ')
    