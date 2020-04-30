# swarming_logic.py
# Inputs: GPS coordinates of drones and target
# Output: Desired GPS location of the individual drone

# Drone positions in formation
#  1          2
#
#       0
#
#  3          4       

import time
import math
from gps import GPSCoord

# assign the drone a number
drone = 0

# make up data
TARGET_FILE = "target_positions_gps.txt"
drones = [GPSCoord(-43.520531, 172.583067), 
          GPSCoord(-43.520533, 172.583065), 
          GPSCoord(-43.520534, 172.583064)]


def gps_buffer(buffer, gps, prev_avg):
    """ Given a list of GPSCoords, a new GPSCoord value, and the previous buffer average
    the circular buffer is checked for errors and updated. 
    The updated gps average and buffer are outputed """
    tot_lat = 0
    tot_long = 0
    value = gps_bound(gps, prev_avg)
    if value == -1:
        print("GPS_BOUNDARY_ERROR")
    else:
        buffer.append(value)
        buffer.pop(0)
        for gps in buffer:
            tot_lat += gps.lat
            tot_long += gps.long
        gps_avg = GPSCoord(tot_lat / len(buffer), tot_long / len(buffer))
    return gps_avg, buffer


def gps_bound(gps, prev_gps):
    """ Returns gps if position is acceptable; within lat 50m, long 40m (0.0005),  
    within -35 to -45 Lat, 167 to 178 Long Boundaries of NZ.
    Else returns -1.
     """
    if (abs(gps.lat - prev_gps.lat) < 0.0005 and abs(gps.long - prev_gps.long) < 0.0005 and -45 < gps.lat < -35 and 167 < gps.long < 178):
        return gps
    else:
        return -1
        
        
#def set_formation():

def check_formation(drones):
    """ Given a list of drone GPSCoords, check the distance between each drone
    """

def check_formation(drones):
    """ check positions of drones. Returns True if formation is adequate,
    False otherwise """
    formation = True
    for drone in drones[1:-1]:
        if drones[0].distance(drone) < 6:
            formation = False
    if drone[1].distance(drone[2]) < 9 or drone[1].distance(drone[3]) < 9 or drone[4].distance(drone[2]) < 9 or drone[4].distance(drone[3]) < 9:
        formation = False
    return formation
            
def reset_formation(drones):
    """ Set the location of each drone to be thier position relative 
    to the mothership position """
    update_loc(drones[0])
        

def update_loc(target):
    """ returns the desired GPSCoord of the drone, from the target GPSCoord """
    if drone == 0:
        pos = target.add_x_offset(0)
        pos = target.add_y_offset(0)
    elif drone == 1:
        pos = target.add_x_offset(-5)
        pos = target.add_y_offset(5)
    elif drone == 2:
        pos = target.add_x_offset(5)
        pos = target.add_y_offset(5)
    elif drone == 3:
        pos = target.add_x_offset(-5)
        pos = target.add_y_offset(-5)
    elif drone == 4:
        pos = target.add_x_offset(5)
        pos = target.add_y_offset(-5)
    return pos

def reset_formation(target):
    """ Stop the drones moving, then move each to their position with respect 
    to themothership"""
    #TODO: set drone mode to hold or set the drones current position as its location
    update_loc(target)
    #TODO: may need to rotate the drones to face their next target here for follow me mode

def main():
    target_file = open(TARGET_FILE)
    buffer_length = 4
    n = 0
    target_sum_lat = 0
    target_sum_long = 0
    target_buffer = []
    while n < buffer_length:
         #Fill the buffer
        t, lat, long = target_file.readline().split(",")
        target = GPSCoord.from_nmea(lat.strip(), long.strip())
        target_buffer.append(target)
        target_sum_lat += target.lat
        target_sum_long += target.long
        n += 1
    target_avg = GPSCoord(target_sum_lat / buffer_length, target_sum_long / buffer_length)
    while True:
        time.sleep(1)
        line = target_file.readline()
        if line != "":
            t, lat, long = line.split(",")
        else:
            target_file.close
            break
        target_avg, target_buffer = gps_buffer(target_buffer, GPSCoord.from_nmea(lat.strip(), long.strip()), target_avg)
        desired_loc = update_loc(target_avg)
        print(desired_loc)

main()