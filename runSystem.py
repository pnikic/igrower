# -*- coding: utf-8 -*-

from controls import Controls
import cv2
import datetime
import numpy as np
import os
import threading
import time
import subprocess

DEBUG_OUTPUT = 1
output_file = None
def debug_print(msg):
    if DEBUG_OUTPUT:
        print('(' + str(datetime.datetime.now())[:-7:]+ ')', msg, flush = True, file = output_file)

def extractColor(image, color):
    """ Extracts the given BGR color from image
    and returns the masked image """
    
    (lower, upper) = color
    lower = np.array(lower, dtype = "uint8")
    upper = np.array(upper, dtype = "uint8")

    mask = cv2.inRange(image, lower, upper)
    output = cv2.bitwise_and(image, image, mask = mask)
    return output

def middleSquare(image, strideH, strideV, centerH, centerV):
    """ Returns the number of nonzero elements of the image
        in the middle square (sides: 2 * strideH, 2 * strideV)
        centered in (rows * centerH, cols * centerV) """
    
    rows, cols, channels = image.shape;
    centerV = round(rows * centerV)
    centerH = round(cols * centerH)

    strideV = min([rows - centerV, centerV, strideV])
    strideH = min([cols - centerH, centerH, strideH])
    
    # Subimage
    ret = image[(centerV - strideV) : (centerV + strideV), (centerH - strideH) : (centerH + strideH)]
    # (1 / 3) because count_nonzero counts pixels in all 3 channels
    nnz = (1 / 3) * np.count_nonzero(ret) / (4 * strideV * strideH)
      
    # Draw the rectangle on original image
    cv2.rectangle(image, (centerH - strideH, centerV - strideV), (centerH + strideH - 1, centerV + strideV - 1), (150,150,30))
    # Draw the percentage of nonzero pixels in bottom-left corner
    cv2.putText(image, 'Mask: %.2f %%' % (100 * nnz), (15, rows - 15), 1, 1, (255, 255, 255))
    
    return nnz 

def cameraLoop(cam, signals):
    """ Takes pictures while recognizing red, green and blue objects
        until the user hits the 'q' key """
    
    # Color boundaries ([B_low, G_low, R_low], [B_high, G_high, R_high])
    red = ([0, 0, 120], [60, 120, 255])
    green = ([0, 50, 0], [30, 255, 140])
    blue = ([95, 65, 70], [170, 110, 95])
    
    # Utils
    # https://www.rapidtables.com/web/color/RGB_Color.html
    # https://www.ginifab.com/feeds/pms/pms_color_in_image.php
    
    # Read until video is completed
    while(not signals['finish'] and cam.isOpened()):
        # Capture frame-by-frame
        ret, frame = cam.read()
    
        if ret != True:
            #signals['stop'] = True
            debug_print('Camera loop skipped a frame.')
            time.sleep(1)
            continue
        
        # (Optional) Resizing the image
        # frame = cv2.resize(frame, (0,0), fx=0.82, fy=0.82)
        
        # Capturing red color
        redMask = extractColor(frame, red)
        cntRed = middleSquare(redMask, 15, 100000, 0.5, 0.5)
        
        if cntRed > .01:
            signals['red'] = True
                   
        # Capturing green color
        medBlur = cv2.medianBlur(frame, 5)
        greenMask = extractColor(medBlur, green)
        cntGreen = middleSquare(greenMask, 100, 30, 0.5, 0.5)
        
        if cntGreen > .03:
            signals['green'] = True

        # Capturing blue color
        blueMask = extractColor(frame, blue)
        cntBlueV = middleSquare(blueMask, 70, 70, 0.5, 0.4)
        
        if cntBlueV > .025:
            signals['blue'] = True
         
        # Display the resulting frames
        row1 = np.hstack([frame, redMask])
        row2 = np.hstack([greenMask, blueMask])
        cv2.imshow('Frame', np.vstack([row1, row2]))

        # Press Q on keyboard to  exit
        if cv2.waitKey(25) & 0xFF == ord('q'):
            signals['stop'] = True

    cam.release()               # When the loop is done, release the video capture object
    cv2.destroyAllWindows()     # Close all the frames
    
def findRedObject(S, sgn, signals, maxTime = 10 * 60):
    """ Searching for red object in horizontal direction '+' or '-' 
    Maximum duration of this function is maxTime seconds """
    
    debug_print('Finding red in direction ' + ('+' if sgn == 1 else '-') + '.')
    signals['red'] = False

    start = time.time()
    now = time.time()
    
    S.Move(0, 'M', sgn * 1000)
    
    while now - start < maxTime and not any([signals['stop'], signals['red'], signals['metal']]):
        time.sleep(.1)
        now = time.time()

    if now - start >= maxTime:
        debug_print('Maximum time for finding red expired. Aborting operation.')
        signals['maxTime'] = True
        
    if any([signals['stop'], signals['red'], signals['metal'], signals['maxTime']]):
        S.Move(0, 'S')
            
    debug_print('Finding red done.')
        
def findGreenObject(S, signals):
    """ Searching for green object in vertical direction '-' """

    debug_print('Finding green.')
    signals['green'] = False
    # Maximum duration of this function is maxTime seconds
    maxTime = 8 * 60
    start = time.time()
    now = time.time()
           
    S.Move(1, 'M', -1000)
    
    while now - start < maxTime and not any([signals['stop'], signals['green'], signals['metal']]):
        time.sleep(.1)
        now = time.time()

    if now - start >= maxTime:
        debug_print('Maximum time for finding green expired. Aborting operation.')
        signals['stop'] = True
        
    if any([signals['stop'], signals['green'], signals['metal']]):
        S.Move(1, 'S')
            
    debug_print('Finding green done.')
        
def takePicture(cam, signals):
    """ Takes a picture with the camera cam and stores it with the given filename """
    
    # Test picture as the camera sometimes gives a black picture on startup
    ret, frame = cam.read()
    time.sleep(.5)
    
    tries = 10
    ret = False
    while cam.isOpened and tries > 0 and not ret:        
        # Calming the camera before taking a picture
        time.sleep(2)
        ret, frame = cam.read()
        tries -= 1
    
    if ret:
        cv2.imwrite(signals['path'] + 'img' + str(signals['pltCnt']) + '_' + str(signals['imgCnt']) + '.png', frame)
        signals['imgCnt'] += 1
        debug_print('The picture is saved.')
    else:
        debug_print('It was not possible to take a picture.')

def takeThreePictures(C, camera, signals, sgn):
    """ Takes three pictures of the target: one from the front side and one from each flank """
    
    takePicture(camera, signals)
    
    pathHalfLength = 15
    angleRotation = 25
           
    # Go in opposite direction
    centerPos = C.AskPosition(0)
    maxTime = C.Move(0, 'M', -1 * sgn * pathHalfLength) + 5
    start = time.time()
    now = time.time()
    
    while now - start < maxTime and not any([signals['stop'], signals['metal']]):
        time.sleep(.1)
        now = time.time()
        
    if signals['stop']:
        debug_print('Operation aborted due to stop signal.')
        C.Move(0, 'S')
        return
    elif signals['metal']:
        C.Move(0, 'S')
        debug_print('Metal encountered and skipped first side picture. Returning to the center.')
        # Try to take the picture from the other angle, first go back to the center
        C.Move(0, 'M', sgn * abs((C.AskPosition(0) - centerPos)), wait = True)
    else:
        # Rotate for picture
        C.Move(2, 'M', angleRotation, wait = True)
        takePicture(camera, signals)
        C.Move(2, 'M', -angleRotation, wait = True)
        # Head back to the center
        C.Move(0, 'M', sgn  * pathHalfLength, wait = True)

    debug_print('We are in the center again. Moving to the other side.')
    resetSignals(signals)
    maxTime = C.Move(0, 'M', sgn  * pathHalfLength) + 5
    start = time.time()
    now = time.time()
    
    while now - start < maxTime and not any([signals['stop'], signals['metal']]):
        time.sleep(.1)
        now = time.time()

    if signals['stop']:
        debug_print('Operation aborted due to stop signal.')
        C.Move(0, 'S')
        return
    elif signals['metal']:
        C.Move(0, 'S')
        # Return to the center
        debug_print('Metal encountered and skipped second side picture. Returning to the center.')
        C.Move(0, 'M', -1 * sgn * abs((C.AskPosition(0) - centerPos)), wait = True)
    else:
        C.Move(2, 'M', -angleRotation, wait = True)
        takePicture(camera, signals)
        C.Move(2, 'M', angleRotation, wait = True)
        # Return to the center
        C.Move(0, 'M', -1 * sgn * pathHalfLength, wait = True)

    resetSignals(signals)
    debug_print('Take three pictures procedure finished for plant #' + str(signals['pltCnt']) + '.')
    signals['pltCnt'] += 1
    signals['imgCnt'] = 1

def resetSignals(signals):
    targets = ['green', 'red', 'blue', 'stop', 'metal', 'maxTime', 'finish']
    for t in targets:
        signals[t] = False

def plantIter(C, camera, direction, signals):
    """ One iteration of plant imaging """
    
    debug_print('Starting iteration in direction ' + direction + '.')
    time.sleep(2)
    resetSignals(signals)
    
    sgn = 1 if direction == '+' else -1
    
    while not signals['metal']:
        T_red = threading.Thread(target = findRedObject, args = (C, sgn, signals,))
        T_red.start()
        T_red.join()
        if signals['metal']:
            debug_print('Metal signal during first red search. Iteration finished.')
            C.Move(0, 'M', -1 * sgn * 5, wait = True)
            resetSignals(signals)
            return
        if signals['maxTime']:
            signals['stop'] = True
            debug_print('Operation aborted due to stop signal during first red search.')
            return
    
        T_green = threading.Thread(target = findGreenObject, args = (C, signals,))
        T_green.start()
        T_green.join()
        if signals['metal']:
            debug_print('Metal signal during green search. Returning to vertical home position.')
            C.Move(1, 'H', wait = True)
            ret = safeMove(C, 0, 'M', sgn * 15, signals)
            resetSignals(signals)
            if ret == False:
                return

            continue
        if signals['stop']:
            debug_print('Operation aborted due to stop signal during green search.')
            return

        C.Move(1, 'M', 15, wait = True)
        # Searching for red again, as the plant is perhaps not centered now
        centerPos = C.AskPosition(0)
        T_red = threading.Thread(target = findRedObject, args = (C, -1 * sgn, signals, 20))
        T_red.start()
        T_red.join()
        if signals['metal']:
            debug_print('Metal signal during second red search. Returning to latest best position.')
            C.Move(0, 'M', sgn * abs((C.AskPosition(0) - centerPos)), wait = True)
        if signals['maxTime']:
            debug_print('Stop signal during second red search. Returning to latest best position.')
            C.Move(0, 'M', sgn * abs((C.AskPosition(0) - centerPos)), wait = True)

        resetSignals(signals)
        
        # Go down before taking the pictures
        C.Move(1, 'M', -16, wait = True)
        takeThreePictures(C, camera, signals, sgn)
        if signals['stop']:
            return
            
        debug_print('Moving up over the plants.')
        safeMove(C, 1, 'M', 70, signals)
        if signals['stop']:
            return
            
        debug_print('Moving away from the plant and red wire.')
        ret = safeMove(C, 0, 'M', sgn * 15, signals)
        resetSignals(signals)
        if ret == False:
            return

def safeMove(C, motor, command, step, signals):
    """ Executes a motor command while monitoring the metal sensors.
    If metal is detected on the way, aborts the command and returns the motor back 5 cm's.
    Returns whether the command was successfull or not."""

    debug_print('Doing safe move for motor ' + str(motor) + ' (Command: ' + command + ', Step: ' + str(step)  + ').')
    # Clearing potential old metal signals
    signals['metal'] = False
    time.sleep(1)

    success = True
    start = time.time()
    now = time.time()

    maxTime = C.Move(motor, command, step) + 5

    while now - start < maxTime and not signals['metal']:
        time.sleep(.1)
        now = time.time()

    if signals['metal']:
        debug_print('Metal detected during safe move.')
        C.Move(motor, 'S')
        time.sleep(1)
        success = False

        sgn = step / abs(step)
        C.Move(motor, 'M', -1 * sgn * 5, wait = True)
        signals['metal'] = False

    debug_print('Safe move done.')
    return success

def metalCheck(C, signals):
    """Checking the metal sensor pin """
    
    while not signals['finish']:
        isMetal = C.ReadValues()
        if isMetal:
            signals['metal'] = True
            # Metal signal is ready to be processed
        
        time.sleep(0.25)
        
    debug_print('Metal check loop is done.')
        
def calibrateCamera(C, signals):
    """Searching the blue wire for camera calibration """
    
    resetSignals(signals)
    debug_print('Calibrating camera')
    time.sleep(2)
    if signals['blue']:
        return
    
    # Search on one side
    C.CameraSpeed(0)
    max_time = C.Move(2, 'M', 180) + 1
    now = time.time()
    while time.time() - now < max_time:
        if any([signals['stop'], signals['blue']]):
            C.Move(2, 'S')
            C.CameraSpeed(1)
            return
    
    # Return to the starting point
    C.CameraSpeed(1)
    C.Move(2, 'M', -180, wait = True)
    C.CameraSpeed(0)
    
    max_time = C.Move(2, 'M', -180) + 1
    
    # Search on the other side
    now = time.time()
    while time.time() - now < max_time:
        if any([signals['stop'], signals['blue']]):
            C.Move(2, 'S')
            C.CameraSpeed(1)
            return

    debug_print('Calibrating unsuccessful. Aborting operation.')
    signals['stop'] = True

def stopRoutine(C, signals):
    """ A routine to be called upon finishing.
    Return all motors to their home positions and turns off the lights. """
    
    debug_print('Stop routine called.')
    for i in range(4):
        debug_print('Returning motor ' + str(i) + ' to home position.')
        homePos = C.AskPosition(i)
        safeMove(C, i, 'M', -1 * homePos, signals)
        homePos = C.AskPosition(i)
        
    C.Lights(0)
    
def uploadCloudFolder(folder):
    debug_print('Uploading to cloud folder started.')
    subprocess.call(['/home/pi/Dropbox-Uploader/dropbox_uploader.sh -q upload ' + folder + ' .'], shell = True)
    debug_print('Uploading to cloud folder completed.')

############################ Main program ############################
def run():
    signals = { 'green'  : False,
                'red'    : False,
                'blue'   : False,
                'stop'   : False,
                'metal'  : False,
                'maxTime': False,
                'finish' : False,
                'path'   : '/home/pi/Filakov/',
                'pltCnt': 1,
                'imgCnt' : 1 }
    
    start = time.time()
    
    # Make directory for the pictures
    directory = datetime.datetime.today().strftime('%Y-%m-%d_%H-%M-%S')
    signals['path'] += directory + '/'
    try:
        os.makedirs(signals['path'])
    except Exception as e:
        debug_print(str(e))
        debug_print('Folder for pictures was not created. Aborting program...')
        return

    global output_file
    output_file = open(signals['path'] + 'log.txt', 'w', encoding='utf-8')

    C = Controls("/dev/ttyACM0", output_file)
    if not C.started:
        debug_print("Controls of the motors are not started. Aborting program...")
        output_file.close()
        return
    
    cam = cv2.VideoCapture(0)
    time.sleep(1)
    if not cam.isOpened():
        debug_print("Camera is not opened. Aborting program...")
        output_file.close()
        return

    
    # Run the process
    T_metal = threading.Thread(target = metalCheck, args = (C, signals, ))
    T_cam = threading.Thread(target = cameraLoop, args = (cam, signals, ))
    T_metal.start()
    T_cam.start()

    # Canvas down
    C.Move(3, 'M', 250, wait = True)
    
    C.Lights(1)
    # Camera calibration
#    C.Move(2, 'M', 180, wait = True)
#    calibrateCamera(C, signals)
#    if signals['stop']:
#        stopRoutine(C, signals)
#        return

    C.Move(2, 'M', 180, wait = True)
#    debug_print('Camera calibrated successfully.')

    # First iteration of plant imaging
    plantIter(C, cam, '-', signals)
    if signals['stop']:
        stopRoutine(C, signals)
        signals['finish'] = True
        T_cam.join()
        T_metal.join()
        output_file.close()
        return

    # Second iteration of plant imaging
    debug_print('Preparing plant imaging on the other side.')
    C.Move(2, 'M', -180, wait = True)
    plantIter(C, cam, '+', signals)
    if signals['stop']:
        stopRoutine(C, signals)
        signals['finish'] = True
        T_cam.join()
        T_metal.join()
        output_file.close()
        return

    # Finishing routine
    debug_print('Vertical motor returning to home position.')
    C.Move(1, 'H', wait = True)
    debug_print('Job done: ' + str(time.time() - start) + ' secs')

    signals['finish'] = True
    T_cam.join()
    T_metal.join()
    C.Lights(0)
    # Canvas up
    C.Move(3, 'M', -250, wait = True)
    C.Close()
    
    uploadCloudFolder(signals['path'])
    output_file.close()

############################ End #####################################

############################ Temp program ############################
def temp_run():
    temp_signals = { 'green'  : False,
                    'red'    : False,
                    'blue'   : False,
                    'stop'   : False,
                    'metal'  : False,
                    'maxTime': False,
                    'finish' : False,
                    'path'   : '/home/pi/Filakov/',
                    'pltCnt': 1,
                    'imgCnt' : 1 }

    C = Controls("/dev/ttyACM0")
    if not C.started:
        debug_print("Controls of the motors are not started. Aborting program...")
        return
    
    time.sleep(3)
    cam = cv2.VideoCapture(0)
    time.sleep(1)
    if not cam.isOpened():
        debug_print("Camera is not opened. Aborting program...")
        return
    
       
    T_cam = threading.Thread(target = cameraLoop, args = (cam, temp_signals, ))
    T_cam.start()

#    calibrateCamera(C, temp_signals)
#    if temp_signals['stop']:
#        return
#

    C.Move(2, 'M', -90, wait = True)

    while True:
        time.sleep(.5)
        if temp_signals['stop']:
            temp_signals['finish'] = True
            break

    T_cam.join()
    C.Lights(0)
    C.Close()
    
############################ End #####################################

if __name__ == "__main__":
    run()
#    temp_run()
    
