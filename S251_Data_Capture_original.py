import serial
import numpy as np
import matplotlib.pyplot as plt
import sys
from scipy.signal import savgol_filter

port = '/dev/tty.usbserial-1420'
smooth = True

def connect(port):
    try:
        print(f"\nTrying to open {port}")
        ser = serial.Serial(port,baudrate=9600)                     #Open the serial port
        ser.write(b'\x45')                                          #Send Romote Mode Command 0x45
    except:
        print('Serial port open failed')
        sys.exit()                                                  #If the serial port comm fail close the app
    return 0

def read_data(ser):
    reply = ser.read(13)                                            #Read the Anritsu reply
    reply = reply.decode("utf-8", "ignore")
    model = reply[2:7]                                              #The model and the version in ASCII
    version = reply[9:13]

    print(f"Successful connected to {ser.name}")
    print(f"Anritsu SiteMaster {model}  Version {version} ")
    ser.write(b'\x11\x00')                                          #Retreive the current trace data
    print(f"Retrieving the current trace")
    trace_data = ser.read(4364)
    ser.write(b'\xFF')                                              #Exit the remote mode and close the serial port
    ser.close()
    return trace_data

def calc_data(trace_data):

    temp = 0
    aux = 0
    measure_mode = hex(trace_data[15])                              #Measure Mode are = 00h : RL Frequency, 01h : SWR Frequency, 02h : Cable Loss Frequency
                                                                    #10h : RL Distance, 11h : SWR Distance, 21h : Insertion Loss, 22h : Insertion Gain
    data_points = hex(trace_data[54])                               #Read the number of datapoint (130, 259, or 517)
    if data_points == 0x0:
        data_points = 130
    elif data_points == 0x1:
        data_points = 259
    else:
        data_points = 517

    start_freq = int.from_bytes(trace_data[56:60],"big")  #Determine the start and stop frequency
    stop_freq = int.from_bytes(trace_data[60:64], "big")
    freq_step = (stop_freq - start_freq) / (data_points-1)
    frequency = [(start_freq + freq_step*i) for i in range(data_points)]
    frequency = np.array(frequency)                                #Create a array w/ frequency values in MHz
    frequency = np.round(frequency / 1e6, 3)

    trace_hex = trace_data[228:(data_points * 8 + 228)]            #Retreive trace values (gamma)
    trace_hex = [hex(i) for i in trace_hex]

    gamma =[0x00 for i in range(data_points * 4)]                  #Extract the 4 Bytes gamma value
    for i in range(data_points * 4):
        gamma[i] = trace_hex[temp]
        gamma[i] = format(int(gamma[i],16),'#04x')
        temp = temp + 1
        aux = aux + 1
        if aux == 4:
            temp = temp + 4
            aux = 0
    aux = 0

    gamma_dec = [0x00 for i in range(data_points)]               #Calculate the decimal values of gamma
    for i in range(data_points):
        value = gamma[aux] + gamma[aux+1] + gamma[aux+2] + gamma[aux+3]
        value = value.replace("0x", "")
        gamma_dec[i] = int(value, 16)
        aux = aux + 4
    gamma = np.array(gamma_dec)
    return measure_mode, start_freq, stop_freq, frequency, gamma

def plot_data(measure_mode, start_freq, stop_freq, frequency, gamma, smooth):
    match measure_mode:
        case "0x0":
            rl = np.round(20* np.log10(gamma/1000), 3)
            if smooth:
                rl_smooth = np.round(savgol_filter(rl, 51, 3), 3)
                plt.plot(frequency, rl_smooth)
            else:
                plt.plot(frequency, rl)
            plt.grid()
            plt.xlim(start_freq / 1e6, stop_freq / 1e6)
            plt.title("RETURN LOSS")
            plt.xlabel("Frequency [MHz]")
            plt.ylabel("Return Loss [dB]")
            plt.show()

        case "0x1":
            swr = np.round((1 + gamma/1000) / (1 - gamma/1000), 3)
            if smooth:
                swr_smooth = np.round(savgol_filter(swr, 51, 3), 3)
                plt.plot(frequency, swr_smooth)
            else:
                plt.plot(frequency, swr)
            plt.grid()
            plt.xlim(start_freq / 1e6, stop_freq / 1e6)
            plt.title("SWR")
            plt.xlabel("Frequency [MHz]")
            plt.ylabel("SWR")
            plt.show()

        case "0x2":
            il = np.round(20* np.log10(gamma/1000)/2, 3)
            if smooth:
                il_smooth = np.round(savgol_filter(il, 51, 5), 3)

                plt.plot(frequency, il_smooth)
            else:
                plt.plot(frequency, il)
            plt.grid()
            plt.xlim(start_freq / 1e6, stop_freq / 1e6)
            plt.title("CABLE LOSS")
            plt.xlabel("Frequency [MHz]")
            plt.ylabel("Cable Loss [dB]")
            plt.show()

        case "0x21":
            il = np.round( 20 * np.log10(gamma/10000000), 3)
            if smooth:
                il_smooth = np.round(savgol_filter(il, 51, 3), 3)
                plt.plot(frequency, il_smooth)
            else:
                plt.plot(frequency, il)
            plt.grid()
            plt.xlim(start_freq / 1e6, stop_freq / 1e6)
            plt.title("INSERTION LOSS")
            plt.xlabel("Frequency [MHz]")
            plt.ylabel("Insertion Loss [dB]")
            plt.show()

        case "0x22":
            il = np.round( 20 * np.log10(gamma/10000000), 3)
            if smooth:
                il_smooth = np.round(savgol_filter(il, 51, 3), 3)
                plt.plot(frequency, il_smooth)
            else:
                plt.plot(frequency, il)
            plt.grid()
            plt.xlim(start_freq / 1e6, stop_freq / 1e6)
            plt.title("INSERTION GAIN")
            plt.xlabel("Frequency [MHz]")
            plt.ylabel("insertion Gain [dB]")
            plt.show()

        case _:
            print("Measure Mode not supported")

def main():
    connect(port)
    trace_data = read_data(serial.Serial(port))
    measure_mode, start_freq, stop_freq, frequency, gamma = calc_data(trace_data)
    plot_data(measure_mode, start_freq, stop_freq, frequency, gamma, smooth)


if __name__ == '__main__':
    main()




