from os.path import exists
from array import array
from struct import unpack, pack

import socket
import math
import pyaudio
import wave
import sys
import numpy
from numpy import log10

import scikits.audiolab as pya
import matplotlib.pyplot as pyplot
import socket
import serial
import time
import sys

##### Global vars #####
s1=0
s2=0
snd=0
sampleFreq = 0
radios=0
freqArray=0
p=0

###### Functions #######
def get_wav(audiofilename,seconds):    
    chunk = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100


    p = pyaudio.PyAudio()
    
    stream = p.open(format = FORMAT,
                    channels = CHANNELS,
                    rate = RATE,
                    input = True,
                    frames_per_buffer = chunk)

    print("[Soundserver] Start recording")
    lrtn = array('h')

    all = []
    for i in range(0, RATE / chunk * seconds):
        data = stream.read(chunk)
        all.append(data)
    
    print "[Soundserver] Done recording"
        
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
        
    print("[Soundserver] Sound recorded in: "+audiofilename)


def record(audiofilename,seconds,prerecord=False):
    global snd,s1,s2,sampleFreq,radios,freqArray,p

    if(printermode==True):
        print("[Soundserver] Printer connected mode")
        for portn in range(0,5):
            try:
                ser = serial.Serial(port="/dev/ttyACM"+str(portn),baudrate=115200)
                print("Connecting to port: "+str(portn))
                if(ser!=-1):
                    print("[Soundserver] Connected to port /dev/ttyACM"+str(portn))
                break
            
            except(serial.SerialException):
                print("[Soundserver]Cannot connect to the printer on port /dev/ttyACM"+str(portn)+" Doing it in the next...")
                if(portn == 4):
                    print("[Soundserver][Error] Cannot connect to the printer")
                    exit()
                portn = portn + 1
                continue

        try:
            time.sleep(3)
            print("[Soundserver] Waiting for press button...")
            while(1):
                data = ser.read(6)
                if(data.find("B01")!=-1):
                    print("[Soundserver] Received B01 from printer")
                    break

            ser.write("M903 \n")
            print("[Soundserver] Sending: M903. Read light ON")
            ser.write("M104 S220 \n")
            
            if(prerecord==False):
                get_wav(audiofilename)
                

            ser.write("M904 \n")
            print("[Soundserver] Sending: M904 Read light OFF")
            ser.close()
        except(serial.SerialException):
            exit("[Soundserveress] Error the printer has been disconnected")
    
    #printermode=False
    else:
        print("[Soundserver] Printer not connected mode")
        print("[Soundserver] Capturing sound")
        if(prerecord==False):
            get_wav(audiofilename,seconds)
        print("[Soundserver] Captured sound: "+audiofilename)

    #general process the file
    print("[Soundserver] Opening the wav file")
    (snd, sampleFreq, nBits) = pya.wavread(audiofilename)
    s1 = snd[:]
    s2=[]
    
    #processing sound wave
    for index,data in enumerate(s1):
        if(abs(data) > 0.05):
            s2.append(abs(data))
        else:
            s2.append(0)

    divfact = len(s2)/256
    radios = s2[::divfact]
    for idx,radioact in enumerate(radios):
        radios[idx] = "%.7f" % radioact

    #fourier transform
    n=len(s1)
    p = numpy.fft.fft(s1)
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
            
    freqArray = numpy.arange(0, nUniquePts, 1.0) #* (samppleFreq / n)
    freqpeak = p.argmax(axis=0)
    
    return(radios,freqpeak)

#plot waves
def plotwaves():
    global snd,s1,s2,sampleFreq,radios,freqArray,p
    
    timeArray = numpy.arange(0,float(snd.shape[0]), 1) #time base
    timeArray = timeArray / sampleFreq
    timeArray = timeArray * 1000  #scale to milliseconds
    pyplot.figure(1)
    
    pyplot.subplot(211)
    pyplot.plot(timeArray, s1, color='K')
    pyplot.ylabel('Amplitude')
    pyplot.xlabel('Time (ms)')
    
    timeArray2 = numpy.arange(0,len(radios), 1) #time base
    pyplot.subplot(212)
    pyplot.plot(timeArray2, radios, color='C')
    pyplot.ylabel('Amplitude')
    pyplot.xlabel('Time (ms)')
    
    pyplot.figure(2)
    pyplot.subplot(111)
    pyplot.plot(freqArray/1000, 10*numpy.log10(p), color='C')

    pyplot.draw()
    pyplot.show()
    return

###### Main #######
ssocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
printermode = False

ssocket.bind (( '', 2727 ))
print("[Soundserver] Waiting for connection")
ssocket.listen(1)


while True:
    channel, details = ssocket.accept()
    print("[Soundserver] Connection open: ", details)
    
    while True:
        action = channel.recv(255)
        if("record" in action):
            audiofilename = action[action.find("[")+1:action.find("]")]
            print("[Soundserver] Recording")
            radios,frec = record(audiofilename,4)
            channel.send(str(radios)+"("+str(frec)+")")
            print("[Soundserver] The sound and frec has been sent")

        elif("primode=true" in action):
            printermode = True
            print("recived")
            channel.send("done")

        elif("primode=false" in str(action)):
            printermode = False
            print("recived")
            channel.send("done")

        elif(str(action)=="premode=true"):
            prerecord = True
            print("recived")
            channel.send("done")

        elif(str(action)=="premode=false"):
            prerecord = False
            print("recived")
            channel.send("done")

        elif(action=="showplots"):
            print("[Soundserver] Ploting...")
            plotwaves()
            channel.send("done")
            if(printermode == False):
                ssocket.close()
                exit(1)

        elif(action=="exit"):
            print("Closing the socket and exiting...bye")
            channel.send("done")
            channel.close()
            exit(1)
        action=0
