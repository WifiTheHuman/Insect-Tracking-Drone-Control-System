import time
import zmq
import sys
import matplotlib.pyplot as plt
import argparse

import multilateration
import swarming_logic
from gps import GPSCoord
from packets import RxUpdate, TxUpdate

# Must match the port numbers in rx.py
TX_STARTUP_PORT = 5554
TX_RECEIVE_PORT = 5555
TX_SEND_PORT = 5556

# This must match the value in rx.py, and be compatible with the swarming logic
# and the multilateration.
NUM_RXS = 4

# Tx starting position. This value must match the one in rx.py
TX_START_COORDS = GPSCoord(-43.520508, 172.583089)

# Latitude and logtitude limits for the expected drone and target coordinates.
# Used to define the boundaries of the plot.
MIN_LAT = -43.520833
MAX_LAT = -43.520333
MIN_LONG = 172.582833
MAX_LONG = 172.583167

# The drone ID of the transmitter drone.
TX_ID = 0

# How often the Tx should perform multilateration and send an update.
# TODO: not currently used, instead the Tx just performs multilateration
# whenever a new full group of readings has been received.
# UPDATE_PERIOD_S = 1

# Timeout period for receiving updates from Rxs.
TIMEOUT_S = 3

# The maximum allowed time difference in milliseconds between the timestamps of
# range readings belonging to the same group.
# TODO: once real SDR readings are used, this should be very small (e.g. 1 ms?)
SYNC_ACCURACY_S = 0.01


class TimeoutException(Exception):
    pass


class TimingException(Exception):
    pass


class UpdateStore:
    """ Stores all the updates received from the Rx's, grouping them by the
    sequence number of the reading they correspond to. Allows data from the most
    recent group of readings to be accessed for multilateration, swarming, etc.

    TODO: only store updates for some period of time then write them to a log file?
    """
    def __init__(self):
        # A list of lists, where updates[i][j] is the update with sequence
        # number i from the Rx with ID j + 1. The list is expanded every time an
        # update with a new sequence number is received.
        self.updates = []

        # The sequence number of the most recent full group of updates.
        self.current_seq_no = -1

        # The last time an update was received from each Rx, useful for
        # determining the cause of a timeout.
        self.last_update_times = [time.time()] * NUM_RXS

    def store(self, update):
        """ Store a new RxUpdate. Returns True if a new full group of readings
        is ready after storing this update, False otherwise.
        """
        # Increase the size of the updates list if needed.
        while update.seq_no >= len(self.updates):
            self.updates.append([None] * NUM_RXS)

        self.updates[update.seq_no][update.rx_id - 1] = update
        self.last_update_times[update.rx_id - 1] = update.timestamp

        # Check if we have a new full group of updates.
        if all([update is not None for update in self.updates[update.seq_no]]):
            assert (update.seq_no > self.current_seq_no)
            self.current_seq_no = update.seq_no
            self.check_timestamps()
            return True
        else:
            return False

    def current_group(self):
        """ Return the list corresponding to the most recent full group of updates.
        """
        return self.updates[self.current_seq_no]

    def check_timestamps(self):
        """ Check that all the readings in the current group of updates were
        taken within a time interval less than SYNC_ACCURACY_S.
        """
        times = [update.timestamp for update in self.current_group()]
        time_range = max(times) - min(times)
        if time_range >= SYNC_ACCURACY_S:
            raise TimingException(
                "ERROR: timestamps of readings in group #{} differed by {:.4f} s."
                .format(self.current_seq_no, time_range))

    def get_rx_positions(self):
        """ Return a list of the current positions of each Rx, ordered by Rx ID.
        The positions are taken from the most recent full group of Rx updates.
        """
        return [update.rx_coords for update in self.current_group()]

    def get_ranges(self):
        """ Return a list of the most recent range readings, ordered by Rx ID.
        The ranges are taken from the most recent full group of Rx updates.
        """
        return [update.range for update in self.current_group()]

    def get_actual_target_coords(self):
        """ Return the actual target coordinates corresponding to the most
        recent group of updates (sent by the Rxs for use in plotting).
        """
        # Assume that all updates in the group have the same actual target
        # position, so just return the first one.
        return self.current_group()[0].target_coords

    def get_last_update_times(self):
        return self.last_update_times


class TransmitterUAV:
    def __init__(self, context, should_plot):
        # PULL socket for receiving updates from the Rxs.
        self.receiver = context.socket(zmq.PULL)
        self.receiver.bind("tcp://*:{}".format(TX_RECEIVE_PORT))

        # PUB socket for sending target position estimates to the Rxs.
        self.sender = context.socket(zmq.PUB)
        self.sender.bind("tcp://*:{}".format(TX_SEND_PORT))

        # Current position of the Tx, initialised to its hard-coded start position,
        # then updated based on the desired location output by the swaming logic.
        # TODO: Eventually this will be the real position read from a GPS module.
        self.tx_coords = TX_START_COORDS

        # Store all the updates received from the Rxs.
        self.updates = UpdateStore()

        # Store all the estimated target positions.
        # TODO: only store positions temporarily then write them to a log file?
        self.target_positions = []

        # Poller required to set a timeout on receiving from the receiver socket.
        self.poller = zmq.Poller()
        self.poller.register(self.receiver, zmq.POLLIN)

        # Create a graph to plot the drone and target positions, if necessary.
        self.should_plot = should_plot
        if self.should_plot:
            plt.axis([MIN_LONG, MAX_LONG, MIN_LAT, MAX_LAT])

    def receive_updates(self, timeout_time):
        """ Repeatedly receive and store updates from the Rxs, returning once
        a new full group of readings is ready. Raises a TimeoutException if
        this doesn't happen before the timeout_time
        """
        while True:
            # Time interval until timeout_time in ms.
            timeout_interval = max(0, 1000 * (timeout_time - time.time()))
            sockets = dict(self.poller.poll(timeout=timeout_interval))
            if self.receiver in sockets:
                message = self.receiver.recv(flags=zmq.NOBLOCK)
                update = RxUpdate.from_bytes(message)
                print("Received update: {}".format(update))
                if self.updates.store(update):
                    return
            else:
                # Print error message including the the time since an update
                # was received from each Rx, to help diagnose the timeout.
                message = "ERROR: Timeout occurred. Times since last update:\n"
                times_since_update = [
                    time.time() - last_time
                    for last_time in self.updates.get_last_update_times()
                ]
                for rx_id in range(1, NUM_RXS + 1):
                    message += "Rx {}: {:.3f} s\n".format(
                        rx_id, times_since_update[rx_id - 1])
                raise TimeoutException(message)

    def perform_multilateration(self):
        """ Returns the target position estimated by the multilateration module.

        TODO: For now, only use readings from the first 3 Rxs for multilateration.
        Remove this once multilateration works with 4 Rxs.
        """
        num_rxs = 3
        rx_coords = self.updates.get_rx_positions()[:num_rxs]
        ranges = self.updates.get_ranges()[:num_rxs]

        return multilateration.estimate_target_position(
            self.tx_coords, *rx_coords, *ranges)
        
    def swarming_checks(self):
        """ Returns the desired centre position of the formation. 
        If formation is fine, output the target position, 
        otherwise outputs the averaged centre of the formation. """
        drone_positions = [self.tx_coords] + self.updates.get_rx_positions()
        target_coords = self.target_positions[-1]
        previous_target_coords = self.target_positions[-2]
        
        # Estimate (mean) the centre of the formation   
        centres = swarming_logic.centres_from_drones(drone_positions)
        est_centre, error = swarming_logic.mean_centre(centres)
        
        # Check the target position is valid 
        if not(swarming_logic.check_gps(target_coords, previous_target_coords)):
            # Replace target with previous_target if target coord is bad
            target_coords = previous_target_coords
            print("ERROR: BAD TARGET GPS COORD")
            self.target_positions[-1] = previous_target_coords # This is ugly
            # TODO: for consecutinve bad readings, stop the drones / move back home
        
        # Check the drone formation
        if not(swarming_logic.critical_formation(drone_positions)):
            # If formation is critical stop the drones
            #TODO: Stop the drones moving if critical
            output_dest = None
            print("ERROR: CRITICAL - STOP THE DRONES")
        elif not(swarming_logic.check_formation(drone_positions, est_centre, error)):
            # Output the average centre of the drones as the destination to reset the formation        
            output_dest = est_centre
            print("RESET FORMATION")
        else:
            # Output target position as the destination
            print("UPDATE TARGET")
            output_dest = target_coords 
        
        return output_dest  

    def plot_positions(self):
        """ Plot the current positions of the Tx and the Rxs, and the actual
        target position. """
        colors = ['k', 'b', 'g', 'r', 'm']
        positions = [self.tx_coords] + self.updates.get_rx_positions()
        for i in range(len(positions)):
            plt.plot(positions[i].long, positions[i].lat, 'x' + colors[i])

        # Get the actual target coords (sent from the Rxs for plotting).
        actual_target_coords = self.updates.get_actual_target_coords()
        plt.plot(actual_target_coords.long, actual_target_coords.lat, 'oc')

        # Call pause to render the changes.
        plt.pause(0.0000001)

    def run(self):
        """ Tx main loop.
        Receives updates from the Rxs until a new group of readings is ready
        (or until timeout occurs).
        Then performs multilateration and swarming checks to determine the
        desired target location, and sends this to each Rx.
        """
        # Wait until at least one update is received from each Rx.
        self.receive_updates(time.time() + TIMEOUT_S)
        last_updates_received_time = time.time()

        # Perform an initial multilateration, so that the swarming checks have a
        # previous target position to compare against.
        self.target_positions.append(self.perform_multilateration())

        while True:
            loop_start_time = time.time()

            self.receive_updates(last_updates_received_time + TIMEOUT_S)
            last_updates_received_time = time.time()

            target_coords = self.perform_multilateration()
            self.target_positions.append(target_coords)

            desired_centre_position = self.swarming_checks()

            print("Estimated target position:", target_coords)
            print("Desired formation centre:", desired_centre_position)

            # Update the Tx's own position.
            self.tx_coords = swarming_logic.update_loc(desired_centre_position,
                                                       TX_ID)

            # Plot the current Tx, Rx and actual target positions if needed.
            if self.should_plot:
                self.plot_positions()

            # Send the desired centre position and the Tx position to the Rxs.
            update = TxUpdate(desired_centre_position, self.tx_coords)
            print("Sending update: {}".format(update))
            self.sender.send(update.to_bytes())

            print()


def wait_for_rxs(context):
    """ Wait for a ready message to be received from each Rx, then send a
    reply once all Rxs are ready.
    """
    startup = context.socket(zmq.ROUTER)
    startup.bind("tcp://*:{}".format(TX_STARTUP_PORT))

    # Keep track of the Rx IDs which are ready.
    # Each ID is mapped to its address, so that the Tx can send a response to
    # the same addresses once all Rxs are ready.
    ready_ids = {}

    print("Waiting for ready messages from Rxs...")
    while len(ready_ids) < NUM_RXS:
        address, empty, message = startup.recv_multipart()
        # The ready message is a single byte containing the Rx ID.
        rx_id = message[0]
        ready_ids[rx_id - 1] = address
        print("Rx {} ready.".format(rx_id))

    print("All Rxs ready.")

    # Let the Rxs know the Tx is ready (with an empty message).
    for address in ready_ids.values():
        startup.send_multipart([address, b'', b''])

    startup.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-p',
        '--plot',
        action='store_true',
        help='plots the drone and target positions on a graph during execution'
    )
    args = parser.parse_args()

    context = zmq.Context()

    # Wait until all Rxs have sent a ready message.
    wait_for_rxs(context)

    tx = TransmitterUAV(context, args.plot)
    tx.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted. Exiting...")
        sys.exit(0)
    except Exception as e:
        print(e)
        sys.exit(0)
