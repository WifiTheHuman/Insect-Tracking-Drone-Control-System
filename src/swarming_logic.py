# swarming_logic.py
# Helper functions for rx_swarm.py, tx_swarm.py

# Drone positions in formation
#  1          2
#
#       0
#
#  3          4       

import time
import math
from gps import GPSCoord


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


def check_gps(gps, prev_gps):
    """ Returns gps if position is acceptable; within lat 50m, long 40m (0.0005),  
    within -35 to -45 Lat, 167 to 178 Long Boundaries of NZ.
    Else returns -1.
     """
    gps_check = True
    if abs(gps.distance(prev_gps) > 20):
        print("ERROR: GPS CHANGE > 20m")
        gps_check = False
    if not (-45 < gps.lat < -35 and 167 < gps.long < 178):
        print("ERROR: GPS OUTSIDE NZ")
        gps_check = False
    return gps_check
        

def update_loc(target, drone_num):
    """ returns the desired GPSCoord of the drone, from the target GPSCoord """
    if drone_num == 0:
        pos = target.add_x_offset(0)
        pos = pos.add_y_offset(0)
    elif drone_num == 1:
        pos = target.add_x_offset(-5)
        pos = pos.add_y_offset(5)
    elif drone_num == 2:
        pos = target.add_x_offset(5)
        pos = pos.add_y_offset(5)
    elif drone_num == 3:
        pos = target.add_x_offset(-5)
        pos = pos.add_y_offset(-5)
    elif drone_num == 4:
        pos = target.add_x_offset(5)
        pos = pos.add_y_offset(-5)
    return pos


def check_formation(drones):
    """ Check positions of drones. Returns True if formation is adequate,
    False otherwise. This assumes there are 5 drones """
    formation = True
    for drone in drones[1:-1]:
        if drones[0].distance(drone) < 6:
            formation = False
    if drones[1].distance(drones[2]) < 9 or drones[1].distance(drones[3]) < 9 or drones[4].distance(drones[2]) < 9 or drones[4].distance(drones[3]) < 9:
        formation = False
    return formation
