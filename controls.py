# -*- coding: utf-8 -*-

import serial
import time
import datetime

DEBUG_OUTPUT = 1
output_file = None

def debug_print(msg):
    if DEBUG_OUTPUT:
        print('(' + str(datetime.datetime.now())[:-7:]+ ')', msg, flush = True, file = output_file)

class Controls:
    def __init__(self, port, out_file = None):
        """ Opening the serial port """
        self.started = False
        try:
            self.ser = serial.Serial(port, timeout=.1)
            self.started = True
            time.sleep(2)
        except Exception as e:
            debug_print(str(e))
            
        # Variables for Horizontal / Vertical / Camera / Canvas motor
        # Units are cm / cm / deg / cm
        self.units  = [2500, 371.5, 1600 / 360, 410]    # 1 unit = ? steps
        self.accels = [800, 1600, 900, 500]
        self.speeds = [1200, 800, 300, 1700]
        self.higherCameraSpeed = 300
        self.lowerCameraSpeed = 10
        # Time needed to accelerate and decelerate to maximum speed
        self.delay = [2 * self.speeds[i] / self.accels[i] for i in range(4)]
        
        # Current position of the motor from the last query
        self.lastReadHome = ""

        # Debug output file
        global output_file
        output_file = out_file
             
    def ReadValues(self):
        """ Reads all the values sent through Serial and returns
        True - in case metal pin was activated
        False - otherwise """
        
        lines = self.ser.readlines()
        lines = list(map(bytes.decode, lines))
        isMetal = False
        
        for l in lines:
            d = l.find('$')
            if l[:d:] == 'Metal':
                isMetal = True
                debug_print('* Metal is detected *')
            elif l[:d:] == 'Home':
                self.lastReadHome = l[d + 1::]
                
        return isMetal
                
    def Close(self):
        """ Closing the serial port """
        self.ser.close()
    
    def AskPosition(self, motor):
        """ Returns current position of the motor in its unit (cm or deg) """
        send = 'M' + str(motor) + 'H' + '\0#'
        self.ser.write(bytes(send, encoding="utf8"))
        
        # Waiting for the response from Arduino
        time.sleep(1)
        self.ReadValues()
        home = int(self.lastReadHome) / self.units[motor]
        debug_print('Current position for motor' + str(motor) + ' is ' + str(home))
        
        return home
    
    def Move(self, motor, command, step = 0, wait = False):
        """ Sends a command to a motor
        Possible values for motor:
            0 - Horizontal motor
            1 - Vertical motor
            2 - Camera motor
            3 - Canvas motor
        Possible values for command
            'M' - Move
            'S' - Stop
            'H' - Home
        step - number of centimeters (degrees in case of camera) to move
        wait - True / False for waiting until the command finishes """
        
        step = round(step * self.units[motor])
        send = 'M' + str(motor) + command + ('$' + str(step) if step != 0 else '') + '\0#'
        self.ser.write(bytes(send, encoding="utf8"))
        debug_print('COMMAND: ' + str(send))
        
        if command == 'H':
            # Waiting for the response from Arduino
            time.sleep(1)
            self.ReadValues()
            home = int(self.lastReadHome) / self.units[motor]
            debug_print('Current position:' + str(home))
            self.Move(motor, 'M', -1 * home, wait = True)
            
        sleep_time = abs(step) / self.speeds[motor] + self.delay[motor]
        if wait == True:
            debug_print('Waiting: ' + str(sleep_time))
            time.sleep(sleep_time)
            
        return sleep_time

    def Lights(self, val):
        """ Sends command 'L0' or 'L1' for toggling the lights.
        Possible values for val:
            0 - OFF
            1 - ON """
        
        self.ser.write(bytes('L' + str(val) + '\0#', encoding="utf8"))
        
    def CameraSpeed(self, val):
        """ Sends command 'C0' or 'C1' for changing the camera speed.
        Possible values for val:
            0 - Lower speed
            1 - Higher speed """
        
        self.ser.write(bytes('C' + str(val) + '\0#', encoding="utf8"))
        self.speeds[2] = self.higherCameraSpeed if val else self.lowerCameraSpeed

if __name__ == "__main__":
    C = Controls("/dev/ttyACM0")
    print(C.started)
    if C.started:
        print(C.ser)
        C.Close() 
