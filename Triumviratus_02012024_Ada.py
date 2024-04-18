import pygame
from pygame.locals import *
import zmq
import sys
import time
import math
import os
import numpy as np
import json
import pickle
# import pylsl
import random
import datetime
#import serial
import struct
import itertools
from pygame.locals import K_UP, K_DOWN, K_LEFT, K_RIGHT
import csv
import pymcc
import numpy as np
from scipy import signal
import pygame_textinput


# Record joystick values using Lab Streaming Layer (LSL)
# info = pylsl.StreamInfo("JoystickValues", 'Marker', 6, 0, 'string')
# outlet = pylsl.StreamOutlet(info)

# # Set up EMG communication
context = zmq.Context()
socketEMG = context.socket(zmq.SUB)
socketEMG.connect("tcp://localhost:5555")
socketEMG.setsockopt(zmq.SUBSCRIBE, b"")

# EMG_on = True

# if EMG_on == True:
#     # Initialize device parameters
#     sampleRate = 2*2048
#     samplesPerRead = 2*128
#     channels = (0, 3)
#     device = pymcc.MccDaq(sampleRate, samplesPerRead, channel_range = channels)
#     device.start()
    
#     # Butterworth filter
#     b, a = signal.butter(4, (10/(sampleRate/2), 500/(sampleRate/2)), btype='bandpass')

#     # Initialize parameters for code
#     currentChannelOne = []
#     currentChannelTwo = []
#     Flag = 0
#     standardDeviationChannelOne = np.zeros(4)
#     standardDeviationChannelTwo = np.zeros(4)
#     meanChannelOne = np.zeros(4)
#     meanChannelTwo = np.zeros(4)
#     MVC_ch1 = np.zeros(2)
#     MVC_ch2 = np.zeros(2)
#     thresholdChannelOne = 0
#     thresholdChannelTwo = 0
#     adjustConstantChannelOne = 4
#     adjustConstantChannelTwo = 4
#     muOne = 0
#     muTwo = 0
#     sigmaOne = 0
#     sigmaTwo = 0
#     leftLeg = 0
#     rightLeg = 0
#     outFlag = 0


# Set up haptic communication
socketHaptic = context.socket(zmq.PUB)
socketHaptic.bind("tcp://*:5558")
socketHaptic2 = context.socket(zmq.PUB)
socketHaptic2.bind("tcp://*:5559")
socketHaptic3 = context.socket(zmq.PUB)
socketHaptic3.bind("tcp://*:5560")

# ser = serial.Serial('/dev/ttyAMA0',baudrate=115200)

# Set up robot communication
socketRobot = context.socket(zmq.PUB)
socketRobot.bind("tcp://*:5557")

# Initialize screen colors and set up path to Bedford scale image
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
IMAGE_PATHS = ["BedfordScale.png"]
images = []
inputBox = pygame.Rect(560, 100, 41, 45)

SCREEN_WIDTH = 650 # can adjust this 1050 to make room for a side panel
SCREEN_HEIGHT = 650
for path in IMAGE_PATHS:
    image = pygame.image.load(path)
    image_width, image_height = image.get_size()
    scale_factor = min(SCREEN_WIDTH/image_width, SCREEN_HEIGHT/image_height)
    scaled_width = int(image_width*scale_factor)
    scaled_height = int(image_height*scale_factor)
    scaled_image = pygame.transform.scale(image, (scaled_width,scaled_height))
    images.append(image)

# Initialize pygame and joystick
pygame.init()
pygame.joystick.init()
joystick = pygame.joystick.Joystick(0)
pygame.display.set_caption("Triumviratus")

# control updates per second
clock = pygame.time.Clock()

# Sets up main display parameters for the GUI
surface_main = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
surface_game = pygame.Surface((650,650))
surface_panel = pygame.Surface((400,650))
IMAGE_PATHS = ["BedfordScale.png"]

# def TKEFilter(x):
#     y = []
#     for i in range(1, len(x) - 2):
#         y.append(x[i]**2 - x[i - 1]*x[i + 1])
#     return y


# def process_emg(dataCurrent):
#         # Sets which channels on the bridge board we're using as input (channels 1 and 3)
#         currentChannelOne = dataCurrent[0]
#         currentChannelTwo = dataCurrent[2]
#         #elapsedTime = pylsl.local_clock() - startTime
#         #myChunk = [[dataCurrent[0][i], dataCurrent[2][i]] for i in range(128)]
#         #outlet.push_chunk(myChunk, elapsedTime)
#         # Filter the signal and pass it through TKEfilter function
#         currentChannelOne = signal.lfilter(b, a, currentChannelOne)
#         currentChannelTwo = signal.lfilter(b, a, currentChannelTwo)
#         currentChannelTwo = TKEFilter(currentChannelTwo)
#         currentChannelOne = TKEFilter(currentChannelOne)

#         if Flag < 4:
#             # Take the mean of each channel     
#             meanChannelOne[Flag] = np.mean(currentChannelOne)
#             meanChannelTwo[Flag] = np.mean(currentChannelTwo)
#             # Take SD of each channel
#             standardDeviationChannelOne[Flag] = np.std(currentChannelOne)
#             standardDeviationChannelTwo[Flag] = np.std(currentChannelTwo)
#             Flag += 1

#         if Flag == 4:
#             # mean of the mean
#             muOne = np.mean(meanChannelOne)
#             muTwo = np.mean(meanChannelTwo)
#             # max of SD of each channel
#             sigmaOne = np.max(standardDeviationChannelOne)
#             sigmaTwo = np.max(standardDeviationChannelTwo)
#             # set the threshold by the following calculation
#             thresholdChannelOne = muOne + adjustConstantChannelOne * sigmaOne
#             thresholdChannelTwo = muTwo + adjustConstantChannelTwo * sigmaTwo
#             Flag += 2
#             print("I am the threshold One:", thresholdChannelOne)
#             print("I am the threshold Two:", thresholdChannelTwo)

#         temporary1 = np.sort(currentChannelOne)
#         temporary2 = np.sort(currentChannelTwo)
#         temporary1 = temporary1[::-1]
#         temporary2 = temporary2[::-1]

#         if(temporary1[10] > thresholdChannelOne):
#             outFlag = 1
#         elif(temporary2[10] > thresholdChannelTwo):
#             outFlag = 2
#         else:
#             outFlag = 0

#         return outFlag

# The following functions are used throughout the script - most of them if not all within the GUI definition
def get_unique_filename():
    current_number = 1
    while True:
        filename = f"events_{current_number}.pkl"
        if not os.path.exists(filename):
            return filename
        current_number += 1

def get_unique_filename_block():
    current_block_number = 1
    while True:
        block_filename = f"target_data_block{current_block_number}.json"
        if not os.path.exists(block_filename):
            return block_filename
        current_block_number += 1

def get_unique_filename_fam():
    current_number = 1
    while True:
        filename_fam = f"target_data_fam{current_number}.json"
        if not os.path.exists(filename_fam):
            return filename_fam
        current_number += 1

def get_unique_filename_position():
    current_number =1 
    while True:
        filename_position = f"events_{current_number}.csv"
        if not os.path.exists(filename_position):
            return filename_position
        current_number+=1

# def get_unique_filename_success():
#     current_number =1 
#     while True:
#         filename_position = f"events_{current_number}.csv"
#         if not os.path.exists(filename_position):
#             return filename_position
#         current_number+=1


def process_numeric_data(filename): # this function reads the pickle file that's generated when the GUI runs containing x and y values from joystick and time 
    numeric_values = []
    with open(filename, 'rb') as picklefile:
        while True:
            try:
                numeric_value = pickle.load(picklefile)
                numeric_values.append(numeric_value)
            except EOFError:
                break

    # print("Numeric Values:", numeric_values)

    # Now, you have a list of numeric values for further processing
    return numeric_values

def randomize_target_positions(): #this should be called as many times as there are blocks
    distance = 0.80
    depth = [0.025, 0.050, 0.150, 0.175] #idk how these were decided 
    pos = []
    grp_pos = []

    # Scaling parameters
    min_original = -1
    max_original = 1
    min_scaled = 0
    max_scaled = 650

    np.random.seed()	
    angles = [0, 45, 135, 180, 225, 315]

    for val in depth:
        for deg in angles:
            x = distance * np.sin(deg * np.pi/180)
            y = distance * np.cos(deg * np.pi/180)

            # Scaling
            scaled_x = min_scaled + (x - min_original) * (max_scaled - min_scaled) / (max_original - min_original)
            scaled_y = min_scaled + (y - min_original) * (max_scaled - min_scaled) / (max_original - min_original)
            scaled_val = 5 + (val - 0.025) * (30 - 7) / (0.175 - 0.025) #need to decide on this, I can change the 30 (max) and 7(min) to dictate radius of target

            # Scale and map val to fit within screen height
            pos.append((scaled_x, scaled_y, scaled_val, deg, distance))

    np.random.shuffle(pos)
    grp_pos.append(pos[0:24])
    #grp_pos.append(pos[12:24])

    return grp_pos

def calculate_coordination(filename,targetAngle):
    coord_xyzlist = process_numeric_data(filename)
    # print(coord_xyzlist)
    length_xyzlist = len(coord_xyzlist) #this lets us know how many "updates" were recorded in the time period
    # x-axis summation
    coord_x = sum(item[1] for item in coord_xyzlist)
    # y-axis summation
    coord_y = sum(item[2] for item in coord_xyzlist)
    # z-axis summation
    coord_z = sum(item[3] for item in coord_xyzlist)


    #this way of calculating score assumes that the order of angles and target distances is random and not known each block
    if targetAngle == 0 or targetAngle == 180:
        # for testing joystick, no accurate
        coord_score = ((coord_y + coord_x)/2)/length_xyzlist * 100
        #coord_score = ((coord_y + coord_z)/2)/length_xyzlist * 100
        rounded_coord_score = round(coord_score,2)
    else:
        # for testing joystick, no accurate
        coord_score = ((coord_y + coord_x)/2)/length_xyzlist * 100
        #coord_score = ((coord_x + coord_y + coord_z)/3)/length_xyzlist * 100
        rounded_coord_score = round(coord_score,2)
        
    return rounded_coord_score

    
# Create an array of these blocks (excluding block 1 because that condition gets repeated at the beginning and end of the experiment)
haptic_blocks = [2, 3, 4, 5] # this is really arbitraty since this gets changed later anyways

sendInterval = 0.2
lastSentTime = 0.0
lastSentTime1 = 0.0
lastSentTime2 = 0.0
lastSentTime3 = 0.0


def HapticX(startbulletX, startbulletY, targetX, targetY, bulletX, bulletY, targetRadius,bulletTargetXDist,lastSentTime1):
    # here we control haptic feedback commands based on bullet distance to the target
    if(3*targetRadius<bulletTargetXDist):
        xVibrate  = 3*targetRadius/bulletTargetXDist
        currentTime = time.time()
        #print("xhaptic")
        #print(xVibrate)
        if currentTime - lastSentTime1 >=sendInterval:
            socketHaptic.send_pyobj(xVibrate)
            lastSentTime1 = currentTime
        hovering_over_target = False
    elif (0.5*targetRadius<bulletTargetXDist<=3*targetRadius):
        xVibrate = -1/(2.5*targetRadius)*(bulletTargetXDist-3*targetRadius)+1
        currentTime = time.time()
        #print("xhaptic")
        #print(xVibrate)
        if currentTime - lastSentTime1 >=sendInterval:
            socketHaptic.send_pyobj(xVibrate)
            lastSentTime1 = currentTime
        hovering_over_target = False
    elif (bulletTargetXDist<=0.5*targetRadius):
        xVibrate =2 
        currentTime = time.time()
        #print("xhaptic")
        #print(xVibrate)
        if currentTime - lastSentTime1 >=sendInterval:
            #print("in1")
            socketHaptic.send_pyobj(xVibrate)
            lastSentTime1 = currentTime 

def HapticY(startbulletX, startbulletY, targetX, targetY, bulletX, bulletY, targetRadius,bulletTargetYDist,lastSentTime2):
    if(3*targetRadius<bulletTargetYDist):
            yVibrate  =3*targetRadius/bulletTargetYDist
            currentTime = time.time()
            #print("yhaptic")
            #print(yVibrate)
            if currentTime - lastSentTime2 >=sendInterval:
                socketHaptic2.send_pyobj(yVibrate)
                lastSentTime2 = currentTime
            hovering_over_target = False
    elif(0.5*targetRadius<bulletTargetYDist<=3*targetRadius):
            yVibrate = -1/(2.5*targetRadius)*(bulletTargetYDist-3*targetRadius)+1
            currentTime = time.time()
            if currentTime - lastSentTime2 >=sendInterval:
                socketHaptic2.send_pyobj(yVibrate)
                lastSentTime2 = currentTime
            hovering_over_target = False
    elif(bulletTargetYDist<=0.5*targetRadius):
            yVibrate =2 
            currentTime = time.time()
            #print("yhaptic")
            #print(yVibrate)
            if currentTime - lastSentTime2 >=sendInterval:
                #print("in2")
                socketHaptic2.send_pyobj(yVibrate)
                lastSentTime2 = currentTime 

def HapticZ(startbulletX, startbulletY, targetX, targetY, bulletX, bulletY, targetRadius, bulletRadius,lastSentTime3):
    if (3/7*targetRadius<abs(bulletRadius-targetRadius)):
        zVibrate = (3/7)*targetRadius/abs(bulletRadius-targetRadius)
        currentTime= time.time()
        #print("zhaptic")
        #print(zVibrate)
        if currentTime - lastSentTime3 >= sendInterval:
            socketHaptic3.send_pyobj(zVibrate)
            lastSentTime3 = currentTime
        hovering_over_target = False       
    elif (1/7*targetRadius<abs(bulletRadius-targetRadius)<=3/7*targetRadius):
        zVibrate = -1/(2/7*targetRadius)*(abs(bulletRadius-targetRadius)-3/7*targetRadius)+1
        currentTime = time.time()
        #print("zhaptic")
        #print(zVibrate)
        if currentTime - lastSentTime3 >=sendInterval:
            socketHaptic3.send_pyobj(zVibrate)
            lastSentTime3 = currentTime
        hovering_over_target = False           
    elif(abs(bulletRadius-targetRadius)<=1/7*targetRadius):
        zVibrate =2 
        currentTime = time.time()
        #print("zhaptic")
        #print(zVibrate)
        if currentTime - lastSentTime3 >=sendInterval:
            #print("in3")
            socketHaptic3.send_pyobj(zVibrate)
            lastSentTime3 = currentTime          



# This is the main definition for the experiment, we make a lot of adjustments here to control what appears on the screen, feedback, what data is recorded, etc.
def GUI(TRIAL, START_TIME, targetX, targetY, targetRadius, targetAngle, haptic_blocks):
    # Initialize all necessary parameters
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    bulletRadius = 20
    bulletX = 325
    bulletY = 325
    startbulletX = 325
    startbulletY = 325 
    bulletColor = (102, 0 , 102)
    joyAxisValue = {0: 0, 1: 0, 2: 0, 3: 0}
    lastSentTime1 = 0.0
    lastSentTime2 = 0.0
    lastSentTime3 = 0.0
    sendInterval = 0.01
    radiusFlag = 0
    clock = pygame.time.Clock()
    joy_time = []
    xaxis = 0
    yaxis = 0
    zaxis = 0
    xaxis_raw = []
    yaxis_raw = []
    zaxis_raw = []
    position_append = []
    targets_2D = [0, 3, 6, 13, 17, 19, 20, 22] 
    constant_velocity_x = 2.0
    constant_velocity_y = 2.0
    a = True 

    # Initialize parameters for the bullet to hover over the target
    hover_threshold = 1.0 # in seconds, can adjust this time later
    hovering_over_target = False
    start_hover_time = 0

    # Initialize filename for each trial
    filename = get_unique_filename()
    with open (filename,'wb') as file:
        pass

    filename_position = get_unique_filename_position()
    with open (filename_position,'w') as file_position:
        pass
    # print("I am in GUI")
    # dataCurrent = device.read()
    # radiusFlag = process_emg(dataCurrent)
    # This is the main loop that runs the GUI
            # Polling for EMG input


    while True:
        
        bulletTargetDistance = math.dist([startbulletX,startbulletY],[targetX,targetY])
        bulletTargetDistance = math.dist([bulletX, bulletY], [targetX, targetY])

        # what are these two for?
        sbulletTargetXDist = math.dist([startbulletX,0],[targetX,0])
        sbulletTargetYDist = math.dist([0,startbulletY],[0,targetY])


        bulletTargetXDist = math.dist([bulletX,0],[targetX,0])
        bulletTargetYDist = math.dist([0,bulletY],[0,targetY])

        # Initialize the user interface
        current_time = time.time()
        surface_main.fill(WHITE)
        surface_game.fill(WHITE)
        surface_panel.fill((211,211,211))

        # this determines if the cursor is in front or behind the target based on the target size
        if targetRadius >= 20:
            pygame.draw.circle(surface_game, (255, 102, 102), (targetX, targetY), targetRadius)  # need to modify this for no visual feedback trials
        
        position_data = {"bulletX": bulletX, "bulletY": bulletY, "bulletRadius": bulletRadius}
        
        # Receives input from EMG script
        
        # # Robot communication
        # socketRobot.send_pyobj(radiusFlag)
        # # Arrow key handling
        # for event in pygame.event.get():
        # 	if event.type == QUIT:
        # 		pygame.quit()
        # 		sys.exit()
        # 	keys = pygame.key.get_pressed()
        # keys = pygame.key.get_pressed()
        # if keys[K_UP]:
        # 		bulletY -= constant_velocity_y
        # if keys[K_DOWN]:
        # 		bulletY += constant_velocity_y
        # if keys[K_LEFT]:
        # 	bulletX -= constant_velocity_x
        # if keys[K_RIGHT]:
        # 	bulletX += constant_velocity_x
        # if keys[K_KP0]:
        # 	if bulletRadius + 1 < 38 and (bulletX + bulletRadius < 650) and (bulletX - bulletRadius > 0):
        # 		bulletRadius += 1
        # if keys[K_KP1]:
        # 	if bulletRadius - 1 > 4:
        # 		bulletRadius -= 1

        # Poll joystick for events and receive values
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit()

            if event.type == JOYAXISMOTION:
                # Assign coordination scores depending on which axes are active
                if event.axis <= 2:
                    joyAxisValue[event.axis] = event.value
                    xaxis_raw = joyAxisValue[2]
                    yaxis_raw = joyAxisValue[1]
                    velocity_x = xaxis_raw*constant_velocity_x
                    velocity_y = yaxis_raw*constant_velocity_y

                # If we are onyl allowing a joystick to control either x or y
                if joyAxisValue[2] and joyAxisValue[1] is not 0:
                        joy_time = current_time
                        xaxis = 1
                        yaxis = 1 
                elif joyAxisValue[2] == 0 and joyAxisValue[1] is not 0:
                        joy_time = current_time
                        xaxis = 0
                        yaxis = 1
                elif joyAxisValue[2] is not 0 and joyAxisValue[1] == 0:
                        joy_time = current_time
                        xaxis = 1
                        yaxis = 0
                else:
                        joy_time = current_time
                        xaxis = 0
                        yaxis = 0 
        poller = zmq.Poller()
        poller.register(socketEMG, zmq.POLLIN)
        events = dict(poller.poll(timeout = 0.02))
        radiusFlag = 0
        if socketEMG in events and events[socketEMG] == zmq.POLLIN:
            radiusFlag = socketEMG.recv_pyobj()
            # print(radiusFlag)
            if radiusFlag is not 0: 
                zaxis = 1
            else:
                zaxis = 0
            radiusFlag = int(radiusFlag)

           
        # Depending on flag (i.e. contract with one leg or the other), the radius for the cursor (or "bullet") will increase or decrease)
        if(radiusFlag == 1):
            if(bulletY + bulletRadius * 2  < 650):     # y-axis = joystick 1
                bulletY +=  4#radiusFlag * 6
            # if bulletRadius + 1 < 38 and (bulletX + bulletRadius < 650) and (bulletX - bulletRadius > 0):
            #     bulletRadius += 1
        elif(radiusFlag == 2):
            if(bulletY - bulletRadius * 2 > 0):
                bulletY -= 4 #0.5*radiusFlag * 6
        zaxis_raw = bulletRadius
        # # Polling for EMG input
        # poller = zmq.Poller()
        # poller.register(socketEMG, zmq.POLLIN)
        # events = dict(poller.poll(timeout = 0.02))
        # radiusFlag = 0
        
 
        # # Receives input from EMG script
        # if socketEMG in events and events[socketEMG] == zmq.POLLIN:
        #     radiusFlag = socketEMG.recv_pyobj()
        #     # print(radiusFlag)
        #     if radiusFlag is not 0: 
        #             zaxis = 1
        #     else:
        #         zaxis = 0
        #     radiusFlag = int(radiusFlag)
            
        #     # Robot communication
        #     socketRobot.send_pyobj(radiusFlag)

    #     # Depending on flag (i.e. contract with one leg or the other), the radius for the cursor (or "bullet") will increase or decrease)
    #     if(radiusFlag == 1):
    #         if(bulletY + bulletRadius * 2  < 650):     # y-axis = joystick 1
    #             bulletY += radiusFlag * 6
    #         # if bulletRadius + 1 < 38 and (bulletX + bulletRadius < 650) and (bulletX - bulletRadius > 0):
    #         #     bulletRadius += 1
    #     elif(radiusFlag == 2):
    #         # if bulletRadius - 1 > 4:
    # #     bulletRadius -= 1
    #         if(bulletY - bulletRadius * 2 > 0):
                
    #             bulletY -= 0.5*radiusFlag * 6
    #     zaxis_raw = bulletRadius

        # # open a pickle file to store the values
        # with open (filename,'ab') as file:
        # 	pickle.dump((joy_time, xaxis, yaxis, zaxis, xaxis_raw, yaxis_raw, zaxis_raw), file)
        # 	#for testing joystick control 
        # 	#pickle.dump((joy_time, xaxis, yaxis), file)  
        # with open (filename_position,'a',newline='') as file_position:
        # 	# json.dump(columns_data,file_position,indent=3)
        # 	csv_writer = csv.writer(file_position)
        # 	if file_position.tell() == 0:
        # 		csv_writer.writerow([bulletX,bulletY,bulletRadius])
        # 	csv_writer.writerow([bulletX, bulletY, bulletRadius])

        #This just zeros the value of the joystick movements if they're less than 0.1
        if abs(joyAxisValue[0]) < 0.1:
            joyAxisValue[0] = 0
        if abs(joyAxisValue[1]) < 0.1:
            joyAxisValue[1] = 0
        if abs(joyAxisValue[2]) < 0.1:
            joyAxisValue[2] = 0
        if abs(joyAxisValue[3]) < 0.1:
            joyAxisValue[3] = 0
        
    
        ##### JOYSTICK CONTROL WITH CONSTANT VELOCITY#################################
        bulletX = max(0, min(bulletX, 640))
        bulletY = max(0, min(bulletY, 640))

        # # Uncomment this for keyboard control
        # if keys[K_UP]:
        # 	if bulletY - bulletRadius * 2 > 0:
        # 		bulletY -= constant_velocity_y
        # if keys[K_DOWN]:
        # 	if bulletY + bulletRadius * 2 < 650:
        # 		bulletY += constant_velocity_y
        # if keys[K_LEFT]:
        # 	if bulletX - bulletRadius * 2 > 0:
        # 		bulletX -= constant_velocity_x
        # if keys[K_RIGHT]:
        # 	if bulletX + bulletRadius * 2 < 650:
        # 		bulletX += constant_velocity_x
        
        # Uncomment this for joystick control 
        if(joyAxisValue[1] > 0):
            # if(bulletY + bulletRadius * 2 + joyAxisValue[1] * 1 < 650):     # y-axis = joystick 1
            #     bulletY += joyAxisValue[1] * constant_velocity_y
            if bulletRadius + 1 < 38 and (bulletX + bulletRadius < 650) and (bulletX - bulletRadius > 0):
                bulletRadius += 0.75
        if(joyAxisValue[1] < 0):
            if bulletRadius - 1 > 4:
                bulletRadius -= 0.75
            # if(bulletY - bulletRadius * 2 + joyAxisValue[1] * 1 > 0):
            #     bulletY += joyAxisValue[1] * constant_velocity_y
        if(joyAxisValue[2] > 0):                                            # x-axis = joystick 2
            if(bulletX + bulletRadius * 2  < 650):
                #bulletX +=1
                bulletX += joyAxisValue[2] * constant_velocity_x
        if(joyAxisValue[2] < 0):
            if(bulletX - bulletRadius * 2  > 0):
                # bulletX -=1
                bulletX +=joyAxisValue[2] * constant_velocity_x
        # Haptic conditions
        # Haptic and visual for all
        if haptic_blocks == 1:
            print ('I am running condition 1!')
            bulletColor = (132, 0, 132)     
            pygame.draw.circle(surface_game, bulletColor, (bulletX, bulletY), bulletRadius)
            HapticX(startbulletX, startbulletY, targetX, targetY, bulletX, bulletY, targetRadius,bulletTargetXDist,lastSentTime1)
            HapticY(startbulletX, startbulletY, targetX, targetY, bulletX, bulletY, targetRadius,bulletTargetYDist,lastSentTime2)
            HapticZ(startbulletX, startbulletY, targetX, targetY, bulletX, bulletY, targetRadius, bulletRadius,lastSentTime3)

        # Visual for all
        elif haptic_blocks == 2:
            print ('I am running condition 2!')
            bulletColor = (132, 0, 132)
            pygame.draw.circle(surface_game, bulletColor, (bulletX, bulletY), bulletRadius)


        # Visual for depth and haptic for translation   
        elif haptic_blocks== 3:
            print ('I am running condition 3!')
            bulletColor = (132, 0, 132)
            distance_to_target = ((bulletX - targetX)**2 + (bulletY - targetY)**2)**0.5
            size_change_factor = 0.1 
            new_bullet_radius = int(bulletRadius + size_change_factor * (distance_to_target - 100))
            new_bullet_radius = max(10, min(50, new_bullet_radius))
            zaxis_raw = new_bullet_radius
            pygame.draw.circle(surface_game, bulletColor, (325, 325), bulletRadius)
            HapticX(startbulletX, startbulletY, targetX, targetY, bulletX, bulletY, targetRadius,bulletTargetXDist,lastSentTime1)
            HapticY(startbulletX, startbulletY, targetX, targetY, bulletX, bulletY, targetRadius,bulletTargetYDist,lastSentTime2)
        
        # Visual for translation & Haptic for radius
        elif haptic_blocks == 4:
            print ('I am running condition 4!')
            bulletColor = (132, 0, 132)
            pygame.draw.circle(surface_game, bulletColor, (bulletX, bulletY), 20)
            HapticZ(startbulletX, startbulletY, targetX, targetY, bulletX, bulletY, targetRadius, bulletRadius,lastSentTime3)

        # Haptic only
        elif haptic_blocks== 5:
            print ('I am running condition 5!')
            bulletColor = (132, 0, 132)
            pygame.draw.circle(surface_game, bulletColor, (325, 325), 20) 
            HapticX(startbulletX, startbulletY, targetX, targetY, bulletX, bulletY, targetRadius,bulletTargetXDist,lastSentTime1)
            HapticY(startbulletX, startbulletY, targetX, targetY, bulletX, bulletY, targetRadius,bulletTargetYDist,lastSentTime2)
            HapticZ(startbulletX, startbulletY, targetX, targetY, bulletX, bulletY, targetRadius, bulletRadius,lastSentTime3)

        
        if targetRadius < 20:
            pygame.draw.circle(surface_game, (255, 102, 102), (targetX, targetY), targetRadius)  # need to modify this for no visual feedback trials
        
        surface_main.blit(surface_game,(0,0))
        pygame.display.update()
        clock.tick(60)
    
        # Question here - is this code still relevant?		
        if(bulletTargetDistance <= 10 and abs(bulletRadius - targetRadius) <= 1):
            shouldIVibrate = 1/(3*targetRadius)*(3*targetRadius-bulletTargetDistance)+1
            if not hovering_over_target:
                start_hover_time = time.time()
                hovering_over_target = True
            
            current_time = time.time()    
            hover_duration = current_time - start_hover_time
            
            # if subject hovers over target position long enough (meets success criteria)
            if hover_duration >= hover_threshold:
                radiusFlag = 0
                #duration of trial
                duration = current_time - START_TIME
                
                # Coordination
                rounded_coord_score_success = calculate_coordination(filename,targetAngle)

                # Robot communication
                socketRobot.send_pyobj(radiusFlag)

                success = 1
                # Dispaly success message and coordination score measure
                Font1 = pygame.font.SysFont("timesnewroman", 30)
                Font2 = pygame.font.SysFont("timesnewroman", 60)
                textSurface1 = Font1.render("SUCCESS!", True, (0, 0, 0))
                textSurface2 = Font2.render(f"Coordination: {rounded_coord_score_success} %",True, (0,0,0))
                surface_main.fill(WHITE)
                surface_main.blit(textSurface1, ((SCREEN_WIDTH - textSurface1.get_width())/2, (SCREEN_HEIGHT - textSurface1.get_height())/4))
                surface_main.blit(textSurface2, ((SCREEN_WIDTH - textSurface2.get_width())/2, (SCREEN_HEIGHT - textSurface2.get_height())/2))
                pygame.display.update()
                time.sleep(3)
                break
        else:
            hovering_over_target = False

        # Trial times out after x seconds
        if(time.time() - START_TIME > 30): # you can change this number to shorten or extend how long the trials are for testing
            rounded_coord_score_fail = calculate_coordination(filename, targetAngle)
            success = 0
            # Display fail message
            Font1 = pygame.font.SysFont("timesnewroman", 30)
            Font2 = pygame.font.SysFont("timesnewroman", 60)
            textSurface1 = Font1.render("Trial timed out!", True, (0, 0, 0))
            textSurface2 = Font2.render(f"Coordination: {rounded_coord_score_fail} %",True, (0,0,0))
            surface_main.fill(WHITE)
            surface_main.blit(textSurface1, ((SCREEN_WIDTH - textSurface1.get_width())/2, (SCREEN_HEIGHT - textSurface1.get_height())/4))
            surface_main.blit(textSurface2, ((SCREEN_WIDTH - textSurface2.get_width())/2, (SCREEN_HEIGHT - textSurface2.get_height())/2))
            pygame.display.update()
            time.sleep(3)
            break
        time.sleep(0.01)

        # open a pickle file to store the values
        with open (filename,'ab') as file:
            pickle.dump((joy_time, xaxis, yaxis, zaxis, xaxis_raw, yaxis_raw, zaxis_raw), file)
            #for testing joystick control 
            #pickle.dump((joy_time, xaxis, yaxis), file)  
        with open (filename_position,'a',newline='') as file_position:
            # json.dump(columns_data,file_position,indent=3)
            csv_writer = csv.writer(file_position)
            if file_position.tell() == 0:
                csv_writer.writerow([bulletX,bulletY,bulletRadius,joy_time,xaxis,yaxis,zaxis])
            csv_writer.writerow([bulletX, bulletY, bulletRadius,joy_time,xaxis,yaxis,zaxis])


    # success_values_filename = "trial_success_coord.txt"
    # with open(success_values_filename, 'a') as success_file:
    #     if success == 0:
    #         success_file.write(f"{success}, {rounded_coord_score_fail}\n")
    #     if success == 1:
    #         success_file.write(f"{success}, {rounded_coord_score_success}\n")
            
    with open ('trial_success_coord.csv','a',newline='') as file_trial_metrics:
            # json.dump(columns_data,file_position,indent=3)
            csv_writer = csv.writer(file_trial_metrics)
            if file_trial_metrics.tell() == 0:
                header = ['Success or Fail','Coordination Score']
                csv_writer.writerow(header)
            if success == 0:
                csv_writer.writerow([success, rounded_coord_score_fail])
            if success == 1:
                csv_writer.writerow([success,rounded_coord_score_success])

    


# The following functions will be used to structure the experiment
def run_familiarization_trials(haptic_blocks):
    TRIAL = 0
    block = 'familiarization'
    # here we create the randomized trial target positions each time a new block is called
    grp_pos = randomize_target_positions()
    blocks = len(grp_pos)
    json_array = []

    for _ in range(len(grp_pos)):
        target_data = grp_pos[_]
        json_array.append(target_data)   

    # Initialize filename for each each block
    fam_filename = get_unique_filename_fam()
    with open (fam_filename,'w') as fam_file:
        json.dump(json_array,fam_file, indent=4)

    Font = pygame.font.SysFont("timesnewroman", 30)
    textSurface1 = Font.render("Start of Familiarization Trials!", True, (0, 0, 0))
    surface_main.fill(WHITE)
    surface_main.blit(textSurface1, ((SCREEN_WIDTH - textSurface1.get_width())/2, (SCREEN_HEIGHT - textSurface1.get_height())/2))
    pygame.display.update()
    time.sleep(1.5)
    
    # Main experiment loop
    while TRIAL < 1:
        # Initialize trial targets
        with open(fam_filename,"r") as file:
            target_data = json.load(file)
        START_TIME = time.time()
        Font = pygame.font.SysFont("timesnewroman", 30)
        textSurface1 = Font.render("Next trial, press A on joystick", True, (0, 0, 0))
        surface_main.fill(WHITE)
        surface_main.blit(textSurface1, ((SCREEN_WIDTH - textSurface1.get_width())/2, (SCREEN_HEIGHT - textSurface1.get_height())/2))
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit()
            if event.type == pygame.JOYBUTTONDOWN: #or event.type == pygame.KEYDOWN and event.key == K_RETURN:# press button a to advance between trials
                    surface_main.fill(WHITE)
                    data = target_data[0]
                    trial_targets = {
                        'target_x': data[TRIAL][0],
                        'target_y': data[TRIAL][1],
                        #'target_z_initial': 20, #if we don't want to be testing EMG, then the Z axis value can be held constant
                        'target_z_initial': data[TRIAL][2],
                        'target_angle': data[TRIAL][3],
                        'target_dist': data[TRIAL][4]
                        }
                    # trial_data = target_data[TRIAL]
                    # trial_targets = {
                    #         'target_x': trial_data['position'][0],
                    #         'target_y': trial_data['position'][1],
                    #         'target_z_initial': trial_data['position'][2],
                    #         'target_angle': trial_data['position'][3],
                    #         'target_dist': trial_data['position'][4]
                    #     }
                    
                    # print(trial_targets)


                    GUI(TRIAL, START_TIME, trial_targets['target_x'], trial_targets['target_y'], trial_targets['target_z_initial'],trial_targets['target_angle'], haptic_blocks) # here we call the main script to initiate the bullet/target trial screen
                    TRIAL += 1
                    
                    duration = time.time() - START_TIME
                    if TRIAL == 1:
                        done = False
                        surface_main.fill(WHITE)
                        socketHaptic.send_pyobj(0)
                        socketHaptic2.send_pyobj(0)
                        socketHaptic3.send_pyobj(0)

                        textinput = pygame_textinput.TextInputVisualizer()
                        font = pygame.font.SysFont("timesnewroman", 30)
                        textSurface = font.render("BREAK-input number from 1-10.", True, (0, 0, 0))
                        surface_main.blit(textSurface, ((SCREEN_WIDTH - textSurface.get_width())/6, (SCREEN_HEIGHT - textSurface.get_height())/6))
                        
                        while not done:
                            events = pygame.event.get()    
                            surface_main.blit(scaled_image, ((SCREEN_WIDTH-scaled_width)/1.5, (SCREEN_HEIGHT-scaled_height)/1.5))
                            pygame.draw.rect(surface_main, BLACK, inputBox, 2)
                            pygame.display.flip()

                            surface_main.fill(WHITE)
                            textinput.update(events)
                            surface_main.blit(textSurface, ((SCREEN_WIDTH - textSurface.get_width())/6, (SCREEN_HEIGHT - textSurface.get_height())/6))
                            surface_main.blit(scaled_image, ((SCREEN_WIDTH-scaled_width)/1.5, (SCREEN_HEIGHT-scaled_height)/1.5))
                            pygame.draw.rect(surface_main, BLACK, inputBox, 2)
                            surface_main.blit(textinput.surface, (inputBox.x + 5, inputBox.y + 5))
                            pygame.display.flip()

                            for event in events:
                                if event.type == pygame.QUIT:
                                    done = True
                                elif event.type == pygame.KEYDOWN:
                                    if event.key == pygame.K_ESCAPE:
                                        done = True
                                    elif event.key == pygame.K_RETURN:
                                        with open("bedford_fam.pkl", "ab") as file:
                                            pickle.dump(textinput.value, file)
                                        done = True
                            

def run_one_experiment_block(haptic_blocks):
    TRIAL = 0
    grp_pos = randomize_target_positions()
    blocks = len(grp_pos)
    trial = []
    json_array = []

    for _ in range(len(grp_pos)):
        target_data = grp_pos[_]
        json_array.append(target_data)   

    # Initialize filename for each each block
    block_filename = get_unique_filename_block()
    with open (block_filename,'w') as block_file:
        json.dump(json_array,block_file, indent=4)

    Font = pygame.font.SysFont("timesnewroman", 30)
    textSurface1 = Font.render("Start of Block!", True, (0, 0, 0))
    surface_main.fill(WHITE)
    surface_main.blit(textSurface1, ((SCREEN_WIDTH - textSurface1.get_width())/2, (SCREEN_HEIGHT - textSurface1.get_height())/2))
    pygame.display.update()
    time.sleep(1.5)
    
    # Main experiment loop
    while TRIAL < 24:
        # Initialize trial targets
        with open(block_filename,"r") as file:
            target_data = json.load(file)
        START_TIME = time.time()
        Font = pygame.font.SysFont("timesnewroman", 30)
        textSurface1 = Font.render("Next trial, press A on joystick", True, (0, 0, 0))
        surface_main.fill(WHITE)
        surface_main.blit(textSurface1, ((SCREEN_WIDTH - textSurface1.get_width())/2, (SCREEN_HEIGHT - textSurface1.get_height())/2))
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit()
            if event.type == pygame.JOYBUTTONDOWN or event.type == pygame.KEYDOWN and event.key == K_RETURN:# press button a to advance between trials
                    surface_main.fill(WHITE)
                    data = target_data[0]
                    trial_targets = {
                        'target_x': data[TRIAL][0],
                        'target_y': data[TRIAL][1],
                        #'target_z_initial': 20, #if we don't want to be testing EMG, then the Z axis value can be held constant
                        'target_z_initial': data[TRIAL][2],
                        'target_angle': data[TRIAL][3],
                        'target_dist': data[TRIAL][4]
                        }
                    # trial_data = target_data[TRIAL]
                    # trial_targets = {
                    #         'target_x': trial_data['position'][0],
                    #         'target_y': trial_data['position'][1],
                    #         'target_z_initial': trial_data['position'][2],
                    #         'target_angle': trial_data['position'][3],
                    #         'target_dist': trial_data['position'][4]
                    #     }
                    
                    # print(trial_targets)

                    GUI(TRIAL, START_TIME, trial_targets['target_x'], trial_targets['target_y'], trial_targets['target_z_initial'],trial_targets['target_angle'],  haptic_blocks) # here we call the main script to initiate the bullet/target trial screen
                    TRIAL += 1
                    duration = time.time() - START_TIME

                    if TRIAL == 24:
                        done = False
                        surface_main.fill(WHITE)
                        socketHaptic.send_pyobj(0)
                        socketHaptic2.send_pyobj(0)
                        socketHaptic3.send_pyobj(0)

                        textinput = pygame_textinput.TextInputVisualizer()
                        font = pygame.font.SysFont("timesnewroman", 30)
                        textSurface = font.render("BREAK-input number from 1-10.", True, (0, 0, 0))
                        surface_main.blit(textSurface, ((SCREEN_WIDTH - textSurface.get_width())/6, (SCREEN_HEIGHT - textSurface.get_height())/6))
                        
                        while not done:
                            events = pygame.event.get()    
                            surface_main.blit(scaled_image, ((SCREEN_WIDTH-scaled_width)/1.5, (SCREEN_HEIGHT-scaled_height)/1.5))
                            pygame.draw.rect(surface_main, BLACK, inputBox, 2)
                            pygame.display.flip()

                            surface_main.fill(WHITE)
                            textinput.update(events)
                            surface_main.blit(textSurface, ((SCREEN_WIDTH - textSurface.get_width())/6, (SCREEN_HEIGHT - textSurface.get_height())/6))
                            surface_main.blit(scaled_image, ((SCREEN_WIDTH-scaled_width)/1.5, (SCREEN_HEIGHT-scaled_height)/1.5))
                            pygame.draw.rect(surface_main, BLACK, inputBox, 2)
                            surface_main.blit(textinput.surface, (inputBox.x + 5, inputBox.y + 5))
                            pygame.display.flip()

                            for event in events:
                                if event.type == pygame.QUIT:
                                    done = True
                                elif event.type == pygame.KEYDOWN:
                                    if event.key == pygame.K_ESCAPE:
                                        done = True
                                    elif event.key == pygame.K_RETURN:
                                        with open("bedford_block.pkl", "ab") as file:
                                            pickle.dump(textinput.value, file)
                                        done = True
                                  

'''
End of definitions.
****************************************************MAIN EXPERIMENT LOOP*************************************************************
This is where we combine all the definitions into one big while loop to create the experiment structure.'''


#targets_2D = [0, 3, 6, 13, 17, 19, 20, 22] #indices for "trial_counter" indicating which targets are on_axes or "2D"

# EXPERIMENT ORDER
# The scripts are run in the following order: initialize EMG.py, haptics py script. Then run the EMG_MVC.py code, then run the
# experiment code, and then finish by running EMG_MVC.py again.

# Run EMG_MVC.py before you start!

# run condition 1
haptic_blocks = 1
# # run_familiarization_trials(haptic_blocks)
run_familiarization_trials(haptic_blocks)
# run_familiarization_trials(haptic_blocks)
run_one_experiment_block(haptic_blocks)

# haptic_blocks=5
# run_one_experiment_block(haptic_blocks)
# now start random order of haptic conditions
haptic_blocks = [2,3,4,5]
random.shuffle(haptic_blocks)
with open('haptic_conditions.txt','a') as file_haptic_conditions:
    file_haptic_conditions.write(f"{haptic_blocks}\n")

# # random condition
run_familiarization_trials(haptic_blocks[0])
run_one_experiment_block(haptic_blocks[0])

# # # random condition
run_familiarization_trials(haptic_blocks[1])
run_one_experiment_block(haptic_blocks[1])

# # # random condition
run_familiarization_trials(haptic_blocks[2])
run_one_experiment_block(haptic_blocks[2])

# # # # # random condition
run_familiarization_trials(haptic_blocks[3])
run_one_experiment_block(haptic_blocks[3])

# # # back to condition 1
haptic_blocks = 1
run_familiarization_trials(haptic_blocks)
run_one_experiment_block(haptic_blocks)

# # # Run EMG_MVC.py again!

