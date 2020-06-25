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


def check_gps(gps, prev_gps, max_diff = 10):
    """ Returns True if gps position is within max_diff = 10m of prev value,  
    and within NZ boundaries of -35 to -45 Lat, 167 to 178 Long.
    Else returns False.
     """
    gps_check = True
    if abs(gps.distance(prev_gps) > max_diff):
        print("ERROR: GPS CHANGE = {} m".format(gps.distance(prev_gps)))
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
    centres = []
    if 0 < len(drones):
        centres.append(drones[0])
    if 1 < len(drones):
        centres.append(drones[1].add_x_offset(5))
        centres[1] = centres[1].add_y_offset(-5)
    if 2 < len(drones):
        centres.append(drones[2].add_x_offset(-5))
        centres[2] = centres[2].add_y_offset(-5)
    if 3 < len(drones):
        centres.append(drones[3].add_x_offset(5))
        centres[3] = centres[3].add_y_offset(5)
    if 4 < len(drones):
        centres.append(drones[4].add_x_offset(-5))
        centres[4] = centres[4].add_y_offset(5)
    return centres

def mean_centre(centres):
    """ Returns the mean average GPSCoord of the centres list, and returns the 
    error; the grestest distance in m from the mean to a value in centres """
    lat_sum = 0
    long_sum = 0
    error = 0
    n = 0
    for centre in centres:
        lat_sum += centre.lat
        long_sum += centre.long
        n += 1
    if lat_sum != 0 and long_sum != 0:
        mean_centre = GPSCoord(lat_sum / n, long_sum / n)
    
    # Find error in mean centre
    for centre in centres:
        if centre.distance(mean_centre) > error:
            error = centre.distance(mean_centre)
    
    return mean_centre, error


def check_formation(drones, est_centre, error):
    """ Checks positions of drones. Returns True if formation is adequate, False otherwise.
    Works for up to 5 drones. """
    formation = True
    
    # Check if est_centre is valid
    if error > 3:
        print("Warning: Error in centre estimate of {:.2f} m".format(error))
        formation = False
        
    # this section is useless as already done by checking error?
    #else:
        ## Check drone positions with respect to the estimated centre
        #for i in range(len(drones)):
            #desired_loc = update_loc(est_centre, i)
            #if desired_loc.distance(drones[i]) > 2:
                #formation = False
                #print("Drone {} out of formation".format(i))
    
    return formation

def critical_formation(drones):
    """ Checks positions of drones relative to each other, to detect if
    drones are in positions such that formation cannot be restored """
    formation = True
    
    # All drones must have at least 3 m between each other   
    for i in range(len(drones)):
        drone1 = drones[i]
        if drone1 != '':
            for n in range(len(drones) - i - 1):
                drone2 = drones[n + i + 1]
                if drone2 != '':
                    if drone1.distance(drone2) < 3:
                        print("ERROR: CRITICAL FORMATION")
                        formation = False
        
    # Drone 0 is known as checked by all others
    # Drone 1 left (lower long) of 0, 2, 4, and above (higher lat) 0, 3, 4
    if not(drones[1].long < drones[0].long and drones[1].long < drones[2].long and drones[1].long < drones[4].long):
        formation = False
    if not(drones[1].lat > drones[0].lat and drones[1].lat > drones[3].lat and drones[1].lat > drones[4].lat):
        formation = False
    # Drone 2 right of (higher long) 0, 3, and above (higher lat) 0, 3, 4
    if not(drones[2].long > drones[0].long and drones[2].long > drones[3].long):
        formation = False
    if not(drones[2].lat > drones[0].lat and drones[2].lat > drones[3].lat and drones[2].lat > drones[4].lat):
        formation = False    
    # Drone 3 left of (lower long) 0, 4, and below (lower lat) 0
    if not(drones[3].long < drones[0].long and drones[3].long < drones[4].long):
        formation = False
    if not(drones[3].lat < drones[0].lat):
        formation = False
    # Drone 4 right of (higher long) 0 and below (lower lat) 0
    if not(drones[4].long > drones[0].long):
        formation = False
    if not(drones[4].lat < drones[0].lat):
        formation = False 
    
    return formation
