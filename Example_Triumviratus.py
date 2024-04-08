import pygame
from pygame.locals import *
# import zmq
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
from gpiozero import PWMLED
from time import sleep 
import adafruit_mcp3xxx.mcp3008 as MCP
import board
import busio
import digitalio
import RPi.GPIO
from adafruit_mcp3xxx.analog_in import AnalogIn
SPI = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
MCP3008_CS = digitalio.DigitalInOut(board.D22)


mcp = MCP.MCP3008(SPI, MCP3008_CS)

foot_axis = AnalogIn(mcp, MCP.P0)

# Initialize screen colors and set up path to Bedford scale image
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
IMAGE_PATHS = ["BedfordScale.bmp"]
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

clock = pygame.time.Clock()

# Sets up main display parameters for the GUI
surface_main = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
surface_game = pygame.Surface((650,650))
surface_panel = pygame.Surface((400,650))

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

def process_numeric_data(filename): # this function reads the pickle file that's generated when the GUI runs containing x and y values from joystick and time 
    numeric_values = []
    with open(filename, 'rb') as picklefile:
        while True:
            try:
                numeric_value = pickle.load(picklefile)
                numeric_values.append(numeric_value)
            except EOFError:
                break
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

haptic_blocks = [2, 3, 4, 5] # this is really arbitraty since this gets changed later anyways
control_mapping_blocks = [1,2,3]
def HapticX (bulletTargetXDist, targetRadius,beepstarttime,ledx):
    if(3*targetRadius<bulletTargetXDist):
        xVibrate  = 3*targetRadius/bulletTargetXDist
        ledx.value = xVibrate
    elif (0.5*targetRadius<bulletTargetXDist<=3*targetRadius):
        current_time = time.time()
        if (current_time-beepstarttime>=0.1):
            ledx.value = 0 
            print("fuck")
            print(current_time)
            print(beepstarttime)
            beepstarttime =current_time
            print("hi")
            print(beepstarttime)
        else:
            ledx.value = 1
            print("bye")
            print(current_time)
    elif bulletTargetXDist<= 0.5* targetRadius:
        ledx.value = 1 

    return beepstarttime
def stop_HapticX(ledx):
    ledx.value = 0 
def HapticY (bulletTargetYDist, targetRadius,beepstarttime,ledy):
    if(3*targetRadius<bulletTargetYDist):
        yVibrate  = 3*targetRadius/bulletTargetYDist
        ledy.value = yVibrate
    elif (0.5*targetRadius<bulletTargetYDist<=3*targetRadius):
        current_time = time.time()
        if (current_time-beepstarttime>=0.1):
            ledy.value = 0 
            print("fuck")
            print(current_time)
            print(beepstarttime)
            beepstarttime =current_time
            print("hi")
            print(beepstarttime)
        else:
            ledy.value = 1
            print("bye")
            print(current_time)
    elif bulletTargetYDist<= 0.5* targetRadius:
        ledy.value = 1 

    return beepstarttime
def stop_HapticY(ledy):
    ledy.value = 0 
def GUI(TRIAL, START_TIME, targetX, targetY, targetRadius, targetAngle, haptic_blocks,instruction,running,control_mapping_blocks):
    # Initialize all necessary parameters
    WHITE = (255, 255, 255)
    bulletRadius = 20
    bulletX = 325
    bulletY = 325
    startbulletX = 325
    startbulletY = 325 
    bulletColor = (102, 0 , 102)
    joyAxisValue = {0: 0, 1: 0, 2: 0, 3: 0}
    mapped_value = 0
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
    ledx = PWMLED(12)
    ledy = PWMLED(13)
    beepstarttime = time.time()
    trial_x = 0 
    print(haptic_blocks,control_mapping_blocks)
    # Initialize parameters for the bullet to hover over the target
    hover_threshold = 2.0 # in seconds, can adjust this time later
    hovering_over_target = False
    start_hover_time = 0
    hovering_X_Ins = False
    hovering_Y_Ins = False
    hovering_Z_Ins = False 
    
    # Initialize filename for each trial
    filename = get_unique_filename()
    with open (filename,'wb') as file:
        pass

    filename_position = get_unique_filename_position()
    with open (filename_position,'w') as file_position:
        pass
    # running = False
    
    # instruction = False
    # This is the main loop (Testing and Familirazation Session) that runs the GUI
    while running:
        bulletTargetDistance = math.dist([startbulletX,startbulletY],[targetX,targetY])
        bulletTargetDistance = math.dist([bulletX, bulletY], [targetX, targetY])
        bulletTargetXDist = math.dist([bulletX,0],[targetX,0])
        bulletTargetYDist = math.dist([0,bulletY],[0,targetY])
        current_time = time.time()
        surface_main.fill(WHITE)
        surface_game.fill(WHITE)
        surface_panel.fill((211,211,211))
        # if targetRadius >= 20:
        pygame.draw.circle(surface_game, (255, 102, 102), (targetX, targetY), targetRadius)  # need to modify this for no visual feedback trials
        # pygame.draw.circle(surface_game, (102, 0, 102), (bulletX,bulletY),bulletRadius)
        if haptic_blocks == 1:
			#print ('I am running condition 1!')
            bulletColor = (132, 0, 132)     
            pygame.draw.circle(surface_game, bulletColor, (bulletX, bulletY), bulletRadius)
            beepstarttime = HapticX(bulletTargetXDist, targetRadius,beepstarttime,ledx)
            beepstarttime = HapticY(bulletTargetYDist,targetRadius,beepstarttime,ledy)
			# HapticZ(startbulletX, startbulletY, targetX, targetY, bulletX, bulletY, targetRadius, bulletRadius,lastSentTime3)
        #Only Visual Information
        elif haptic_blocks == 2:
            bulletColor = (132, 0, 132)
            pygame.draw.circle(surface_game, bulletColor, (bulletX, bulletY), bulletRadius)
        #Two Visual Information w. One Haptic Feedback (z)
        elif haptic_blocks == 3:
			#print ('I am running condition 1!')
            bulletColor = (132, 0, 132)     
            pygame.draw.circle(surface_game, bulletColor, (bulletX, bulletY), 20)
			# HapticZ(startbulletX, startbulletY, targetX, targetY, bulletX, bulletY, targetRadius, bulletRadius,lastSentTime3)
        #Two Haptic Feedback w. One Visual Information (z)
        elif haptic_blocks == 4:
			#print ('I am running condition 1!')
            bulletColor = (132, 0, 132)     
            pygame.draw.circle(surface_game, bulletColor, (325, 325), bulletRadius)
            beepstarttime = HapticX(bulletTargetXDist, targetRadius,beepstarttime,ledx)
            beepstarttime = HapticY(bulletTargetYDist,targetRadius,beepstarttime,ledy)
        #Only Haptic Feedback
        elif haptic_blocks == 5:
			#print ('I am running condition 1!')
            bulletColor = (132, 0, 132)     
            pygame.draw.circle(surface_game, bulletColor, (325, 325), bulletRadius)
            beepstarttime = HapticX(bulletTargetXDist, targetRadius,beepstarttime,ledx)
            beepstarttime = HapticY(bulletTargetYDist,targetRadius,beepstarttime,ledy)
			# HapticZ(startbulletX, startbulletY, targetX, targetY, bulletX, bulletY, targetRadius, bulletRadius,lastSentTime3)

        # beepstarttime = HapticX(bulletTargetXDist, targetRadius,beepstarttime,ledx)
        # beepstarttime =HapticY(bulletTargetYDist,targetRadius,beepstarttime,ledy)
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
                sys.exit()
            if event.type == KEYDOWN:
                running = False
                sys.exit()
            if event.type == JOYAXISMOTION:
                # Assign coordination scores depending on which axes are active
                if event.axis <= 24:
                    joyAxisValue[event.axis] = event.value
                    xaxis_raw = joyAxisValue[3]
                    yaxis_raw = joyAxisValue[1]
                    
                # If we are onyl allowing a joystick to control either x or y
                if joyAxisValue[3] and joyAxisValue[1] is not 0:
                    joy_time = current_time
                    xaxis = 1
                    yaxis = 1 
                elif joyAxisValue[3] == 0 and joyAxisValue[1] is not 0:
                    joy_time = current_time
                    xaxis = 0
                    yaxis = 1
                elif joyAxisValue[3] is not 0 and joyAxisValue[1] == 0:
                    joy_time = current_time
                    xaxis = 1
                    yaxis = 0
                else:
                    joy_time = current_time
                    xaxis = 0
                    yaxis = 0 
        #This just zeros the value of the joystick movements if they're less than 0.1
        if abs(joyAxisValue[0]) < 0.1:
            joyAxisValue[0] = 0
        if abs(joyAxisValue[1]) < 0.1:
            joyAxisValue[1] = 0
        if abs(joyAxisValue[2]) < 0.1:
            joyAxisValue[2] = 0
        if abs(joyAxisValue[3]) < 0.1:
            joyAxisValue[3] = 0

        # for foot pedal front (toe) and rear (heel) control value mapping
        if (foot_axis.voltage>=0.02 and foot_axis.voltage <1.32):
            mapped_value = np.interp(foot_axis.voltage,[0.02,0.5],[-1,0])
        if (foot_axis.voltage>=2.0 and foot_axis.voltage<=3.30):
            mapped_value = np.interp(foot_axis.voltage,[2.0,3.3],[0,1])

        # Joystick control and foot pedal for X:left-thumb joystick  //
        # Y: right-thumb joystick & Z: Foot pedal#
        if abs(mapped_value)<0.3:
                mapped_value = 0 

        bulletX = max(0, min(bulletX, 640))
        bulletY = max(0, min(bulletY, 640))            
        if control_mapping_blocks == 1:
            if(mapped_value > 0):
                if bulletRadius + 1 < 38 and (bulletX + bulletRadius < 650) and (bulletX - bulletRadius > 0):
                    bulletRadius += 1
            elif(mapped_value < 0):
                if bulletRadius - 1 > 4:
                    bulletRadius -= 1
            if(joyAxisValue[1] > 0): 
                if (bulletY + bulletRadius * 2 + joyAxisValue[1] * 1 < 650):
                    bulletY += joyAxisValue[1]*constant_velocity_y
            if(joyAxisValue[1] < 0):
                if(bulletY + bulletRadius * 2 + joyAxisValue[1] * 1 >0):
                    bulletY += joyAxisValue[1]*constant_velocity_y
            if(joyAxisValue[3] > 0):                                            # x-axis = joystick 2
                if(bulletX + bulletRadius * 2 + joyAxisValue[3] * 1 < 650):
                    bulletX += joyAxisValue[3]*constant_velocity_x
                # if (0.5*targetRadius<bulletTargetXDist<=3*targetRadius):
                #     bulletX += joyAxisValue[3]*5
            if(joyAxisValue[3] < 0):
                if(bulletX - bulletRadius * 2 + joyAxisValue[3] * 1 > 0):
                    bulletX += joyAxisValue[3]*constant_velocity_x

        elif control_mapping_blocks == 2:
            if(mapped_value > 0):
                if(bulletX + bulletRadius*2 +mapped_value <650):
                # if bulletRadius + 1 < 38 and (bulletX + bulletRadius < 650) and (bulletX - bulletRadius > 0):
                    bulletX += 2
            elif(mapped_value < 0):
                if(bulletX - bulletRadius * 2 + mapped_value * 1 > 0):
                # if bulletRadius - 1 > 4:
                    bulletX -= 2
            if(joyAxisValue[1] > 0): 
                if bulletRadius + 1 < 38 and (bulletX + bulletRadius < 650) and (bulletX - bulletRadius > 0):
                    bulletRadius += 1
            if(joyAxisValue[1] < 0):
                if bulletRadius - 1 > 4:
                    bulletRadius -= 1
            if(joyAxisValue[3] > 0):                                            # x-axis = joystick 2
                if(bulletY + bulletRadius * 2 + joyAxisValue[3] * 1 < 650):
                    bulletY += joyAxisValue[3]*constant_velocity_y
                # if (0.5*targetRadius<bulletTargetXDist<=3*targetRadius):
                #     bulletX += joyAxisValue[3]*5
            if(joyAxisValue[3] < 0):
                if(bulletY - bulletRadius * 2 + joyAxisValue[3] * 1 > 0):
                    bulletY += joyAxisValue[3]*constant_velocity_y
            # if (0.5*targetRadius<bulletTargetXDist<=3*targetRadius):
            #     bulletX += joyAxisValue[3]*5
        surface_main.blit(surface_game,(0,0))
        surface_main.blit(surface_panel, (650, 0))
        pygame.display.update()
        clock.tick(120)
        if(bulletTargetDistance <= 10 and abs(bulletRadius - targetRadius) <= 1):
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
                # rounded_coord_score_success = calculate_coordination(filename,targetAngle)

				# Robot communication

				# Dispaly success message and coordination score measure
                Font1 = pygame.font.SysFont("timesnewroman", 30)
                Font2 = pygame.font.SysFont("timesnewroman", 60)
                textSurface1 = Font1.render("SUCCESS!", True, (0, 0, 0))
                # textSurface2 = Font2.render(f"Coordination: {rounded_coord_score_success} %",True, (0,0,0))
                surface_main.fill(WHITE)
                surface_main.blit(textSurface1, ((SCREEN_WIDTH - textSurface1.get_width())/2, (SCREEN_HEIGHT - textSurface1.get_height())/4))
                # surface_main.blit(textSurface2, ((SCREEN_WIDTH - textSurface2.get_width())/2, (SCREEN_HEIGHT - textSurface2.get_height())/2))
                pygame.display.update()
                time.sleep(3)
                return
            else:
                hovering_over_target = False

		# Trial times out after x seconds
        if(time.time() - START_TIME > 10): # you can change this number to shorten or extend how long the trials are for testing
            # rounded_coord_score_fail = calculate_coordination(filename, targetAngle)
			# Display fail message
            Font1 = pygame.font.SysFont("timesnewroman", 30)
            Font2 = pygame.font.SysFont("timesnewroman", 60)
            textSurface1 = Font1.render("Trial timed out!", True, (0, 0, 0))
            # textSurface2 = Font2.render(f"Coordination: {rounded_coord_score_fail} %",True, (0,0,0))
            surface_main.fill(WHITE)
            surface_main.blit(textSurface1, ((SCREEN_WIDTH - textSurface1.get_width())/2, (SCREEN_HEIGHT - textSurface1.get_height())/4))
            # surface_main.blit(textSurface2, ((SCREEN_WIDTH - textSurface2.get_width())/2, (SCREEN_HEIGHT - textSurface2.get_height())/2))
            pygame.display.update()
            time.sleep(3)
            return
        time.sleep(0.01)

# This is the instruction session loop that runs the GUI
    while instruction:
        current_time = time.time()
        surface_main.fill(WHITE)
        surface_game.fill(WHITE)
        surface_panel.fill(WHITE)
        bulletTargetXDist = math.dist([bulletX,0],[targetX,0])
        bulletTargetYDist = math.dist([0,bulletY],[0,targetY])
        pygame.draw.circle(surface_game, (255, 102, 102), (targetX, targetY), targetRadius)  # need to modify this for no visual feedback trials
        pygame.draw.circle(surface_game, (102, 0, 102), (bulletX,bulletY),bulletRadius)   
        if haptic_blocks == 1:
            if bulletTargetXDist <= 1:
                bulletX += 0
                if not hovering_X_Ins:
                    start_hover_time = time.time()
                    hovering_X_Ins = True
                current_time = time.time()    
                hover_duration = current_time - start_hover_time
                if hover_duration >= hover_threshold:
                    stop_HapticX(ledx)
                    if bulletTargetYDist <=1:
                        bulletY += 0 
                        if not hovering_Y_Ins:
                            start_hover_timeY = time.time()
                            hovering_Y_Ins = True
                        current_timeY = time.time()
                        hover_durationY =current_timeY - start_hover_timeY
                        if hover_durationY >= hover_threshold:
                            stop_HapticY(ledy)
                            if abs(targetRadius-bulletRadius) <= 1:
                                bulletRadius += 0 
                                if not hovering_Z_Ins:
                                    start_hover_timeZ = time.time()
                                    hovering_Z_Ins = True
                                current_timeZ = time.time()
                                hover_durationZ = current_timeZ - start_hover_timeZ
                                if hover_durationZ >= hover_threshold:
                                    Font1 = pygame.font.SysFont("timesnewroman", 30)
                                    textSurface1 = Font1.render("Instruction Finished!", True, (0, 0, 0))
                                    surface_main.fill(WHITE)
                                    surface_main.blit(textSurface1, ((SCREEN_WIDTH - textSurface1.get_width())/2, (SCREEN_HEIGHT - textSurface1.get_height())/4))
                                    pygame.display.update()
                                    time.sleep(3)
                                    return
                            else: 
                                bulletRadius +=1   
                    else:
                        bulletY += constant_velocity_y
                        beepstarttime = HapticY(bulletTargetYDist,targetRadius,beepstarttime,ledy)
            else:
                bulletX += 1
                hovering_over_target = False
                beepstarttime = HapticX(bulletTargetXDist, targetRadius,beepstarttime,ledx)
       #No Haptic feedback blocks
        if haptic_blocks == 2:
            if bulletTargetXDist <= 1:
                bulletX += 0
                if not hovering_X_Ins:
                    start_hover_time = time.time()
                    hovering_X_Ins = True
                current_time = time.time()    
                hover_duration = current_time - start_hover_time
                if hover_duration >= hover_threshold:
                    if bulletTargetYDist <=1:
                        bulletY += 0 
                        if not hovering_Y_Ins:
                            start_hover_timeY = time.time()
                            hovering_Y_Ins = True
                        current_timeY = time.time()
                        hover_durationY =current_timeY - start_hover_timeY
                        if hover_durationY >= hover_threshold:
                            if abs(targetRadius-bulletRadius) <= 1:
                                bulletRadius += 0 
                                if not hovering_Z_Ins:
                                    start_hover_timeZ = time.time()
                                    hovering_Z_Ins = True
                                current_timeZ = time.time()
                                hover_durationZ = current_timeZ - start_hover_timeZ
                                if hover_durationZ >= hover_threshold:
                                    Font1 = pygame.font.SysFont("timesnewroman", 30)
                                    textSurface1 = Font1.render("Instruction Finished!", True, (0, 0, 0))
                                    surface_main.fill(WHITE)
                                    surface_main.blit(textSurface1, ((SCREEN_WIDTH - textSurface1.get_width())/2, (SCREEN_HEIGHT - textSurface1.get_height())/4))
                                    pygame.display.update()
                                    time.sleep(3)
                                    return
                            else: 
                                bulletRadius +=1   
                    else:
                        bulletY += constant_velocity_y
            else:
                bulletX += 1
                hovering_over_target = False
        # Two visual and one haptic (z direction)
        if haptic_blocks == 3:
            if bulletTargetXDist <= 1:
                bulletX += 0
                if not hovering_X_Ins:
                    start_hover_time = time.time()
                    hovering_X_Ins = True
                current_time = time.time()    
                hover_duration = current_time - start_hover_time
                if hover_duration >= hover_threshold:
                    if bulletTargetYDist <=1:
                        bulletY += 0 
                        if not hovering_Y_Ins:
                            start_hover_timeY = time.time()
                            hovering_Y_Ins = True
                        current_timeY = time.time()
                        hover_durationY =current_timeY - start_hover_timeY
                        if hover_durationY >= hover_threshold:
                            if abs(targetRadius-bulletRadius) <= 1:
                                bulletRadius += 0 
                                if not hovering_Z_Ins:
                                    start_hover_timeZ = time.time()
                                    hovering_Z_Ins = True
                                current_timeZ = time.time()
                                hover_durationZ = current_timeZ - start_hover_timeZ
                                if hover_durationZ >= hover_threshold:
                                    Font1 = pygame.font.SysFont("timesnewroman", 30)
                                    textSurface1 = Font1.render("Instruction Finished!", True, (0, 0, 0))
                                    surface_main.fill(WHITE)
                                    surface_main.blit(textSurface1, ((SCREEN_WIDTH - textSurface1.get_width())/2, (SCREEN_HEIGHT - textSurface1.get_height())/4))
                                    pygame.display.update()
                                    time.sleep(3)
                                    return
                            else: 
                                bulletRadius +=1   
                    else:
                        bulletY += constant_velocity_y
            else:
                bulletX += 1
                hovering_over_target = False
       #Two Haptic feedback and one visaul (z)
        if haptic_blocks == 4:
            if bulletTargetXDist <= 1:
                bulletX += 0
                if not hovering_X_Ins:
                    start_hover_time = time.time()
                    hovering_X_Ins = True
                current_time = time.time()    
                hover_duration = current_time - start_hover_time
                if hover_duration >= hover_threshold:
                    stop_HapticX(ledx)
                    if bulletTargetYDist <=1:
                        bulletY += 0 
                        if not hovering_Y_Ins:
                            start_hover_timeY = time.time()
                            hovering_Y_Ins = True
                        current_timeY = time.time()
                        hover_durationY =current_timeY - start_hover_timeY
                        if hover_durationY >= hover_threshold:
                            stop_HapticY(ledy)
                            if abs(targetRadius-bulletRadius) <= 1:
                                bulletRadius += 0 
                                if not hovering_Z_Ins:
                                    start_hover_timeZ = time.time()
                                    hovering_Z_Ins = True
                                current_timeZ = time.time()
                                hover_durationZ = current_timeZ - start_hover_timeZ
                                if hover_durationZ >= hover_threshold:
                                    Font1 = pygame.font.SysFont("timesnewroman", 30)
                                    textSurface1 = Font1.render("Instruction Finished!", True, (0, 0, 0))
                                    surface_main.fill(WHITE)
                                    surface_main.blit(textSurface1, ((SCREEN_WIDTH - textSurface1.get_width())/2, (SCREEN_HEIGHT - textSurface1.get_height())/4))
                                    pygame.display.update()
                                    time.sleep(3)
                                    return
                            else: 
                                bulletRadius +=1   
                    else:
                        bulletY += constant_velocity_y
                        beepstarttime = HapticY(bulletTargetYDist,targetRadius,beepstarttime,ledy)
            else:
                bulletX += 1
                hovering_over_target = False
                beepstarttime = HapticX(bulletTargetXDist, targetRadius,beepstarttime,ledx)
       #all haptic feedback (z)
        if haptic_blocks == 5:
            if bulletTargetXDist <= 1:
                bulletX += 0
                if not hovering_X_Ins:
                    start_hover_time = time.time()
                    hovering_X_Ins = True
                current_time = time.time()    
                hover_duration = current_time - start_hover_time
                if hover_duration >= hover_threshold:
                    stop_HapticX(ledx)
                    if bulletTargetYDist <=1:
                        bulletY += 0 
                        if not hovering_Y_Ins:
                            start_hover_timeY = time.time()
                            hovering_Y_Ins = True
                        current_timeY = time.time()
                        hover_durationY =current_timeY - start_hover_timeY
                        if hover_durationY >= hover_threshold:
                            stop_HapticY(ledy)
                            if abs(targetRadius-bulletRadius) <= 1:
                                bulletRadius += 0 
                                if not hovering_Z_Ins:
                                    start_hover_timeZ = time.time()
                                    hovering_Z_Ins = True
                                current_timeZ = time.time()
                                hover_durationZ = current_timeZ - start_hover_timeZ
                                if hover_durationZ >= hover_threshold:
                                    Font1 = pygame.font.SysFont("timesnewroman", 30)
                                    textSurface1 = Font1.render("Instruction Finished!", True, (0, 0, 0))
                                    surface_main.fill(WHITE)
                                    surface_main.blit(textSurface1, ((SCREEN_WIDTH - textSurface1.get_width())/2, (SCREEN_HEIGHT - textSurface1.get_height())/4))
                                    pygame.display.update()
                                    time.sleep(3)
                                    return
                            else: 
                                bulletRadius +=1   
                    else:
                        bulletY += constant_velocity_y
                        beepstarttime = HapticY(bulletTargetYDist,targetRadius,beepstarttime,ledy)
            else:
                bulletX += 1
                hovering_over_target = False
                beepstarttime = HapticX(bulletTargetXDist, targetRadius,beepstarttime,ledx)

        # beepstarttime = HapticX(bulletTargetXDist, targetRadius,beepstarttime,ledx)
        surface_main.blit(surface_game,(0,0))
        surface_main.blit(surface_panel, (650, 0))
        pygame.display.update()
        clock.tick(120)
        time.sleep(0.01)

def instruction(haptic_blocks):

    distance = 0.80
    depth = [0.025, 0.050, 0.150, 0.175]
    min_original = -1
    max_original = 1
    min_scaled = 0
    max_scaled = 650
    x = distance * np.sin(45 * np.pi/180)
    y = distance * np.cos(45 * np.pi/180)
    TRIAL = 0
     
    # haptic_blocks = 0
    # Scaling
    scaled_x = min_scaled + (x - min_original) * (max_scaled - min_scaled) / (max_original - min_original)
    scaled_y = min_scaled + (y - min_original) * (max_scaled - min_scaled) / (max_original - min_original)
    scaled_val = 5 + (0.175- 0.025) * (30 - 7) / (0.175 - 0.025) #need to decide on this, I can change the 30 (max) and 7(min) to dictate radius of target

    Font = pygame.font.SysFont("timesnewroman", 30)
    textsurface1 = Font.render("Start of Instructions!", True, (0, 0, 0))
    surface_main.fill(WHITE)
    surface_main.blit(textsurface1, ((SCREEN_WIDTH - textsurface1.get_width())/2, (SCREEN_HEIGHT - textsurface1.get_height())/2))
    pygame.display.update()
    time.sleep(3)
    while TRIAL<2:
        running = False 
        instruction = True
        print("TRIAL")
        START_TIME = time.time()
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit()
            if event.type == pygame.JOYBUTTONDOWN or event.type == pygame.KEYDOWN and event.key == K_RETURN:        
                trial_targets = {
                    'target_x': scaled_x,
                    'target_y': scaled_y,
                    'target_z_initial': scaled_val,
                    'target_angle': 45 } #if we don't want to be testing EMG, then the Z axis value can be held constant
                surface_main.fill(WHITE)

                GUI (TRIAL,START_TIME, trial_targets['target_x'], trial_targets['target_y'], trial_targets['target_z_initial'],trial_targets['target_angle'],haptic_blocks,instruction,running)
                TRIAL +=1
                if TRIAL ==2:
                    done = False 
                    surface_main.fill(WHITE)
                    instruction = False
                    while not done:
                        
                        font = pygame.font.SysFont("timesnewrowman",30)
                        textSurface1 = font.render("Instruction Session Finished",True,(0,0,0))
                        surface_main.blit(textSurface1,((SCREEN_WIDTH - textSurface1.get_width())/2, (SCREEN_HEIGHT - textSurface1.get_height())/2))
                        pygame.display.flip()
                        done =True 
                        time.sleep(3)
                        
def run_familiarization_trials(haptic_blocks,control_mapping_blocks):
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
    time.sleep(3)
    
    # Main experiment loop
    while TRIAL < 1:
        instruction = False 
        running = True
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
            if event.type == pygame.JOYBUTTONDOWN or event.type == pygame.KEYDOWN and event.key == K_RETURN:# press button a to advance between trials
                    surface_main.fill(WHITE)
                    data = target_data[0]
                    trial_targets = {
                        'target_x': data[TRIAL][0],
                        'target_y': data[TRIAL][1],
                        'target_z_initial': 20, #if we don't want to be testing EMG, then the Z axis value can be held constant
                        # 'target_z_initial': data[TRIAL][2],
                        'target_angle': data[TRIAL][3],
                        'target_dist': data[TRIAL][4]
                        }


                    GUI(TRIAL, START_TIME, trial_targets['target_x'], trial_targets['target_y'], trial_targets['target_z_initial'],trial_targets['target_angle'], haptic_blocks, instruction, running,control_mapping_blocks) # here we call the main script to initiate the bullet/target trial screen
                    TRIAL += 1
                    
                    duration = time.time() - START_TIME

                    if TRIAL == 1:
                        done = False
                        surface_main.fill(WHITE)
                        textInput = ''
                        while not done:
                            font = pygame.font.SysFont("timesnewroman", 30)
                            textSurface = font.render("BREAK-input number. For 1-9, type 0 first.", True, (0, 0, 0))
                            surface_main.blit(textSurface, ((SCREEN_WIDTH - textSurface.get_width())/6, (SCREEN_HEIGHT - textSurface.get_height())/6))
                            surface_main.blit(scaled_image, ((SCREEN_WIDTH-scaled_width)/1.5, (SCREEN_HEIGHT-scaled_height)/1.5))
                            pygame.draw.rect(surface_main, BLACK, inputBox, 2)
                            pygame.display.flip()
                            for event in pygame.event.get():
                                if event.type == pygame.QUIT:
                                    pygame.quit()
                                    sys.exit()
                                elif event.type == pygame.KEYDOWN:
                                    if event.unicode.isnumeric():
                                        textInput += event.unicode
                                        TEXT = font.render(textInput, True, BLACK)
                                        surface_main.fill(WHITE)
                                        surface_main.blit(textSurface, ((SCREEN_WIDTH - textSurface.get_width())/6, (SCREEN_HEIGHT - textSurface.get_height())/6))
                                        surface_main.blit(scaled_image, ((SCREEN_WIDTH-scaled_width)/1.5, (SCREEN_HEIGHT-scaled_height)/1.5))
                                        pygame.draw.rect(surface_main, BLACK, inputBox, 2)
                                        surface_main.blit(TEXT, (inputBox.x + 5, inputBox.y + 5))
                                        pygame.display.flip()
                                        #print("Current Input:", textInput)
                                    elif event.key == pygame.K_BACKSPACE:
                                        if len(textInput) > 0:
                                            textInput = textInput[:-1]
                                            TEXT = font.render(textInput, True, BLACK)
                                            surface_main.fill(WHITE)
                                            surface_main.blit(textSurface, ((SCREEN_WIDTH - textSurface.get_width())/6, (SCREEN_HEIGHT - textSurface.get_height())/6))
                                            surface_main.blit(scaled_image, ((SCREEN_WIDTH-scaled_width)/1.5, (SCREEN_HEIGHT-scaled_height)/1.5))
                                            pygame.draw.rect(surface_main, BLACK, inputBox, 2)
                                            surface_main.blit(TEXT, (inputBox.x + 5, inputBox.y + 5))

                                    elif event.key == pygame.K_RETURN:
										#if int(textInput) > 0 and int(textInput) <= 10:
                                        if textInput.isdigit() and 0 < int(textInput) <= 10:
                                            with open("user_input.pkl", "ab") as file:
                                                pickle.dump(textInput,file)
                                                done = True
                                        # elif int(textInput) <0 or int(textInput) >= 10:
                                        elif not textInput.isdigit() or int(textInput) < 0 or int(textInput) >= 10:
                                            print ('Input out of range!')
                                    
                            return TRIAL, duration                                    

# haptic_blocks =2 
# instruction(haptic_blocks=5)
haptic_blocks =1
control_mapping_blocks = 1
run_familiarization_trials(haptic_blocks,control_mapping_blocks)
#run_one_experiment_block(haptic_blocks)
# now start random order of haptic conditions
haptic_blocks = [2,3,4,5]
random.shuffle(haptic_blocks)

for i in range(4):
    control_mapping_blocks =1 
    run_familiarization_trials(haptic_blocks[i],control_mapping_blocks)

haptic_blocks =1
control_mapping_blocks =1 
run_familiarization_trials(haptic_blocks,control_mapping_blocks)

haptic_blocks =1
control_mapping_blocks = 2
run_familiarization_trials(haptic_blocks,control_mapping_blocks)
#run_one_experiment_block(haptic_blocks)
# now start random order of haptic conditions
haptic_blocks = [2,3,4,5]
random.shuffle(haptic_blocks)

for i in range(4):
    control_mapping_blocks =2 
    run_familiarization_trials(haptic_blocks[i],control_mapping_blocks)

haptic_blocks =1
control_mapping_blocks =2 
run_familiarization_trials(haptic_blocks,control_mapping_blocks)
# instruction(haptic_blocks[0])
# run_familiarization_trials(haptic_blocks[0])
#run_one_experiment_block(haptic_blocks[0])
# back to condition 1
# haptic_blocks = 1
# instruction(haptic_blocks)
# run_familiarization_trials(haptic_blocks)
#run_one_experiment_block(haptic_blocks)

