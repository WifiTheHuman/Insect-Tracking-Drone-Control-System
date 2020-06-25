"""
tx_swarm.py 
Transmitter drone swarming logic (mothership)
With the input of a target location (currently from target_positions_gps.txt),
outputs the desired drone location
"""
import time
import swarming_logic
from gps import GPSCoord

# assign the drone a number
drone_num = 0



drones = [GPSCoord(-43.520508, 172.583089),
          GPSCoord(-43.520363, 172.583027),
          GPSCoord(-43.520463, 172.583151),
          GPSCoord(-43.520553, 172.583027),
          GPSCoord(-43.520553, 172.583151)]

# Drone positions in formation about the first point in target_positions_gps.txt
#drones = [GPSCoord(-43.520508, 172.583089),
          #GPSCoord(-43.520463, 172.583027),
          #GPSCoord(-43.520463, 172.583151),
          #GPSCoord(-43.520553, 172.583027),
          #GPSCoord(-43.520553, 172.583151)]
    
def swarming_checks(drones, target_coords, previous_target_coords):
    """ Return the desired centre position of the formation. If formation is
    fine, output the target position, otherwise output the Tx position to reset
    the formation. """
    
    # Estimate (mean) the centre of the formation   
    centres = swarming_logic.centres_from_drones(drones)
    est_centre, error = swarming_logic.mean_centre(centres)
    
    # Check the target position is valid 
    if not(swarming_logic.check_gps(target_coords, previous_target_coords)):
        # Replace target with previous_target if target is bad
        target_coords = previous_target_coords
        print("ERROR: BAD TARGET GPS COORD")
        # TODO: for consecutinve bad readings, stop the drones / move back home
    
    if not(swarming_logic.critical_formation(drones)):
        # If formation is critical stop the drones
        #TODO: Stop the drones moving if critical
        output_dest = None
        print("ERROR: CRITICAL - STOP THE DRONES")
    elif not(swarming_logic.check_formation(drones, est_centre, error)):
        # Output the average centre of the drones as the destination to reset the formation        
        output_dest = est_centre
        print("RESET FORMATION")
    else:
        # Output target position as the destination
        print("UPDATE TARGET")
        output_dest = target_coords 
    
    return output_dest    


def main():
    target_file = open("target_positions_gps.txt")
    # Recieve GPS target position
    line = target_file.readline()
    if line != "":
        t, lat, long = line.split(",")
    target_loc = GPSCoord.from_nmea(lat.strip(), long.strip())
    
    while True:
        time.sleep(1)
        
        # Recieve GPS target position
        line = target_file.readline()
        if line != "":
            t, lat, long = line.split(",")
        else:
            target_file.close
            break
        prev_target_loc = target_loc
        target_loc = GPSCoord.from_nmea(lat.strip(), long.strip())
        
        dest = swarming_checks(drones, target_loc, prev_target_loc)
        if dest != None:
            print("target lat:{} long:{} dest lat:{} long:{}".format(target_loc.lat, target_loc.long, dest.lat, dest.long))


main()