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
        

def update_loc(target, drone_num, drone_pos):
    """ returns the desired GPSCoord offset of the drone for formation, 
    given the target GPSCoord, and drone_num. If target is -1, showing a
    swarming error, returns the drones current location """
    if target.lat == -1 or target.long == -1:
        pos = drone_pos
    else:
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
    return formation


def critical_formation(drones):
    """ Checks positions of drones relative to each other, to detect if
    drones are in positions such that formation cannot be restored """
    formation = True
    
    # All drones must have at least 3 m between each other   
    for i in range(len(drones) - 1):
        drone1 = drones[i]
        for n in range(len(drones) - i - 1):
            drone2 = drones[n + i + 1]
            if drone1.distance(drone2) < 3:
                print("ERROR: CRITICAL FORMATION")
                formation = False
    
    # Check that all drones are the right direction relative to each other
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


def update_fsm(drone_positions, swarming_state):
    """ Update the swarming fsm for the drone formation given drone positions
    and current state. Sates are 0 (normal), 1 (reset formation), 2 (stop) """
    # Estimate (mean) the centre of the formation   
    centres = centres_from_drones(drone_positions)
    est_centre, error = mean_centre(centres)        
    
    # Check the drone formation and update the fsm state accordingly
    if not(critical_formation(drone_positions)):
        # Set state to 2 (stop) if there is a critical (unrecoverable) formation
        swarming_state = 2
        print("ERROR: CRITICAL - STOP THE DRONES")
    elif not(check_formation(drone_positions, est_centre, error)):
       # Set state to 1 (reset) if drones are out of formation (recoverable)
        swarming_state = 1
        print("RESET FORMATION")
    elif swarming_state == 1 and error >= 1:
        # Do not change from reset (1) to normal (0) until all drones are 
        # within 1m of their desired position
        print("RESET FORMATION")
    else:
        # if no formation errors, set state to 0 (normal)
        swarming_state = 0
    return swarming_state, est_centre

def destination(swarming_state, target_coords, est_centre):
    """ Ouput destination depending fsm state """
    if swarming_state == 0:
        output_dest = target_coords
    elif swarming_state == 1:
        # desination average centre of the drones to reset formation 
        output_dest = est_centre            
    elif swarming_state == 2:
        # If formation is critical stop the drones
        # TODO: Set drone mode to hold (pixhawk)            
        output_dest = GPSCoord(-1, -1)            
    return output_dest    
    