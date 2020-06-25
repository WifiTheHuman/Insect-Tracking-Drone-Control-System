"""
rx_swarm.py 
Reciever drone swarming logic
With the input of a target location (currently from target_positions_gps.txt),
outputs the desired drone location
"""
import time
import swarming_logic
from gps import GPSCoord

# assign the drone a number
drone_num = 1

def main():
    target_file = open("target_positions_gps.txt")
    while True:
        time.sleep(1)
        # Recieve GPS target position
        line = target_file.readline()
        if line != "":
            t, lat, long = line.split(",")
        else:
            target_file.close
            break
        # Output desired position
        target_loc = GPSCoord.from_nmea(lat.strip(), long.strip())
        desired_loc = swarming_logic.update_loc(target_loc, drone_num)
        print("Target Loc: {} Desired Loc: {}".format(target_loc , desired_loc))

main()