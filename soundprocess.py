from os.path import exists
from array import array
from struct import unpack, pack

import math
import pyaudio
import wave
import sys
import numpy
from numpy import *
import scikits.audiolab as pya
import matplotlib.pyplot as pyplot
import socket
import serial
import time
import sys

minloud = 3

#Socket parametters.
HOST = '127.0.0.1'    # The remote host
PORT = 6666           # The same port as used by the server

#Debug with plots.
debug=False

def get_wav(audiofilename):
    chunk = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    global RECORD_SECONDS 
    audiofilename

    p = pyaudio.PyAudio()
    
    stream = p.open(format = FORMAT,
                    channels = CHANNELS,
                    rate = RATE,
                    input = True,
                    frames_per_buffer = chunk)

    print("[Soundproc] Start recording")
    lrtn = array('h')

    all = []
    for i in range(0, RATE / chunk * RECORD_SECONDS):
        data = stream.read(chunk)
        all.append(data)
    
    print "[Soundproc] Done recording"
        
    stream.close()
    p.terminate()

    # write data to WAVE file
    data = ''.join(all)
    wf = wave.open(audiofilename, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(data)
    wf.close()
        
    print("[Soundproc] Sound recorded in: "+audiofilename)


###################
#      Main       #
###################
print("[Soundproc] ** Starting sound proc")

if(len(sys.argv)>2):
    if(sys.argv[1]=="--help"):
        print("* Usage: soundproc n(number of time divisions) s(record seconds) [audiofilename] or-s [prerecordwav]")
        exit(1)

    #capture micro to wav.
    RECORD_SECONDS=int(sys.argv[2])
    audiofilename='NoneYet'

    if(sys.argv[3]=="-s"):
        print("[Sound proc] Filename is pre-record, name:"+sys.argv[4])
        audiofilename=sys.argv[4]
        (snd, sampFreq, nBits) = pya.wavread(audiofilename)
        #get one channel
        #s1 = snd[:,0]
        s1 = snd[:]

    elif(sys.argv[3]=="-n"):
        print("[Soundproc] Will capture the sound.")
    
    # Soundproc in printer connected mode.
    if(sys.argv[5]=="-p"):
        print("[Soundproc] Printer connected mode")
        for portn in range(0,5):
            try:
                ser = serial.Serial(port="/dev/ttyACM"+str(portn),baudrate=115200)
                print("Connecting to port: "+str(portn))
                if(ser!=-1):
                    print("[Soundproc] Connected to port /dev/ttyACM"+str(portn))
                break
            
            except(serial.SerialException):
                print("[Soundproc]Cannot connect to the printer on port /dev/ttyACM"+str(portn)+" Doing it in the next...")
                if(portn == 4):
                    print("[Soundproc][Error] Cannot connect to the printer")
                    exit()
                portn = portn + 1
                continue

        try:
            time.sleep(3)
            print("[Soundproc] Waiting for press button...")
            while(1):
                data = ser.read(6)
                if(data.find("B01")!=-1):
                    print("[Soundproc] Received B01 from printer")
                    break

            ser.write("M903 \n")
            print("[Soundproc] Sending: M903. Read light ON")
            ser.write("M104 S220 \n")
            audiofilename=sys.argv[4]
            get_wav(audiofilename)
            ser.write("M904 \n")
            print("[Soundproc] Sending: M904 Read light OFF")
            ser.close()
        except(serial.SerialException):
            exit("[Soundprocess] Error the printer has been disconnected")

    #no printer mode
    elif(sys.argv[5]=="-np"):
        print("[Soundproc] Printer not connected mode")
        print("[Soundproc] Skinpping, no printer conected")
        audiofilename=sys.argv[4]
        print("[Soundproc] Capturing sound")
        get_wav(audiofilename)
        print("[Soundproc] Captured sound: "+audiofilename)

    print("[Soundproc] Opening the wav file")
    (snd, sampFreq, nBits) = pya.wavread(audiofilename)
    s1 = snd[:]

        
else:
    print("* Usage: soundproc n(number of time divisions) s(record seconds) [audiofilename] or-s [prerecordwav]")
    exit(1)


timeArray = numpy.arange(0,float(snd.shape[0]), 1) #time base
timeArray = timeArray / sampFreq
timeArray = timeArray * 1000  #scale to milliseconds

pyplot.figure(1)
###################### Plot time domain.
pyplot.subplot(211)

pyplot.plot(timeArray, s1, color='k')
pyplot.ylabel('Amplitude')
pyplot.xlabel('Time (ms)')

#################### Plot reduced time
pyplot.subplot(212)

# Absolute values
s2=[]
for index,data in enumerate(s1):
    if(abs(data) > 0.05):   #0.045
        s2.append(abs(data))
    else:
        s2.append(0)



#print('------ Sound Sample Data: --------')
divfact = len(s2)/256
radios = s2[::divfact]


for idx,radioact in enumerate(radios):
    radios[idx] = "%.7f" % radioact


print('[Soundproc] Connecting to '+HOST)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))

print('[Soundproc] Connection sucess!')
print('[Soundproc] Sending the vector')
s.send(str(radios))
print('[Soundproc] Vector sent')

##################### Plot segmented frecuency domain. 
pyplot.figure(2)
i=int(sys.argv[1])
n=len(s1)/i

stoprange=n
startrange=0

for a in range(i):
    #calculate subplot rows/col
    string=str(i)+'1'+str(a+1)
    #print(string)
    pyplot.subplot(int(string))

    stoprange=n*(a+1)

    if(startrange==stoprange):
        print("the same")
    else:
        p = numpy.fft.fft(s1[startrange:stoprange])
        
        nUniquePts = numpy.ceil((n+1)/2.0)
        p = p[0:nUniquePts]
        p = abs(p)
        p = p / float(n)  # scale by the number of points so that
                          # the magnitude does not depend on the length 
                          # of the signal or on its sampling frequency  
        p = p**2          # square it to get the power 

        if n % 2 > 0:     # we've got odd number of points fft
            p[1:len(p)] = p[1:len(p)] * 2
        else:
            p[1:len(p) -1] = p[1:len(p) - 1] * 2 # we've got even number of points fft
            
        freqArray = numpy.arange(0, nUniquePts, 1.0) #* (sampFreq / n)
        print("******************")
        freqpeak = p.argmax(axis=0)
        print(freqpeak)
        print("******************")
        pyplot.plot(freqArray/1000, 10*numpy.log10(p), color='k')
        pyplot.xlabel('Frequency (kHz)')
        pyplot.ylabel('Power (dB)')
        
        startrange=stoprange
        pyplot.draw()

if(debug==True):    
    pyplot.show(1)

time.sleep(2)

print("waiting for the cylmodeler to be ready")
s.send("asdasdasdasd")
s.close()
print('[Soundproc] Socket closed')

temporad = numpy.arange(0,float(len(radios)), 1)
pyplot.plot(temporad,radios, color='k')

exit(1)

    



