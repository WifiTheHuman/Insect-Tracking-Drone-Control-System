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

def centres_from_drones(drones):
    """ returns a list of the expected GPSCoords centre of the formation, 
    from the list of drone GPSCoords """
    centres = ['','','','','']
    centres[0] = drones[0]
    if drones[1] != '':
        centres[1] = drones[1].add_x_offset(5)
        centres[1] = centres[1].add_y_offset(-5)
    if drones[2] != '':
        centres[2] = drones[2].add_x_offset(-5)
        centres[2] = centres[2].add_y_offset(-5)
    if drones[3] != '':
        centres[3] = drones[3].add_x_offset(5)
        centres[3] = centres[3].add_y_offset(5)
    if drones[4] != '':
        centres[4] = drones[4].add_x_offset(-5)
        centres[4] = centres[4].add_y_offset(5)
    return centres

def mean_centre(centres):
    """ Returns the mean average GPSCoord of the centres list, or '' if list is empty
    Returns the error; the grestest distance in m from the mean to  """
    n = 0
    lat_sum = 0
    long_sum = 0
    error = 0
    for centre in centres:
        if centre != '':
            lat_sum += centre.lat
            long_sum += centre.long
            n += 1
    
    if n != 0:
        mean_centre = GPSCoord(lat_sum / n, long_sum / n)
    else:
        mean_centre = ''
        print("Warning: Empty centres list")
    
    # Find error in mean centre
    for centre in centres:
        if centre != '' and mean_centre != '' and centre.distance(mean_centre) > error:
            error = centre.distance(mean_centre)
    
    return mean_centre, error


def check_formation(drones):
    """ Checks positions of drones. Returns True if formation is adequate, False otherwise.
    Works for up to 5 drones. If formation is False, we need to check critical_formation(drones).  """
    
    formation = True
    
    # Estimate (mean) the centre of the formation
    centres = centres_from_drones(drones)
    est_centre, error = mean_centre(centres)
    
    # Check if est_centre is valid
    if error > 3:
        print("Warning: Invalid centre estimate, bad formation")
        formation = False
    else:
        # Check drone positions with respect to the estimated centre
        for i in range(len(drones)):
            if drones[i] != '' and est_centre != '':
                desired_loc = update_loc(est_centre, i)
                if desired_loc.distance(drones[i]) > 2:
                    formation = False
                    print("Drone {} out of formation".format(i))
        
    return formation

def critical_formation(drones):
    """ Checks positions of drones relative to each other, to detect if
    drones are in positions such that formation cannot be restored """
    # NEED TO DEFINE WHAT A CRITICAL FORMATION LOOKS LIKE
    # Drone 1 must be top left, 2 top right, 3 bottom left, 4 bottom right from Tx (centre)
    # All drones must have at least 3 m between each other
    