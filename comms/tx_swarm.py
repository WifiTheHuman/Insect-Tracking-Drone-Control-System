"""
rx_swarm.py 
Transmitter drone swarming logic (mothership)
With the input of a target location (currently from target_positions_gps.txt),
outputs the desired drone location
"""
import time
import swarming_logic
from gps import GPSCoord

# assign the drone a number
drone_num = 0

# Drone positions in formation about the first point in target_positions_gps.txt
drones = [GPSCoord(-43.520508, 172.583089),
          GPSCoord(-43.520463, 172.583027),
          GPSCoord(-43.520463, 172.583151),
          GPSCoord(-43.520553, 172.583027),
          GPSCoord(-43.520553, 172.583151)]


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
        
        # If formation is fine, output the target, otherwise output tx position to reset the formation
        if swarming_logic.check_formation(drones) and swarming_logic.check_gps(target_loc, prev_target_loc):
            # Output target location as the desired location
            desired_loc = target_loc
        else:
            # Output mothership position as the desired location, to reset formation
            desired_loc = drones[0]
            print("RESET FORMATION")
        print("Target Loc:", target_loc)
        print("Desired Loc:", desired_loc)


main()