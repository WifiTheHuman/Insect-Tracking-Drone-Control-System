#!/usr/bin/env python2
#***************************************************************************
#
#   Copyright (c) 2015 PX4 Development Team. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 3. Neither the name PX4 nor the names of its contributors may be
#    used to endorse or promote products derived from this software
#    without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
# OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
# AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
#***************************************************************************/

#
# @author Andreas Antener <andreas@uaventure.com>
#
# The shebang of this file is currently Python2 because some
# dependencies such as pymavlink don't play well with Python3 yet.
from __future__ import division

import rospy
import math
from geographic_msgs.msg import GeoPoseStamped
from geometry_msgs.msg import Quaternion
from mavros_common import MavrosTestCommon
from pymavlink import mavutil
from std_msgs.msg import Header
from threading import Thread
# from tf.transformations import quaternion_from_euler


DEFAULT_ALTITUDE = 20


class MavrosOffboardPosctl(MavrosTestCommon):
    """ Controls a drone in Gazebo by sending position setpoints via MAVROS. """
    def __init__(self):
        rospy.init_node('test_node', anonymous=True)

    def setUp(self):
        super(MavrosOffboardPosctl, self).setUp()

        self.pos = GeoPoseStamped()
        self.pos_setpoint_pub = rospy.Publisher(
            'mavros/setpoint_position/global', GeoPoseStamped, queue_size=1)

        # send setpoints in seperate thread to better prevent failsafe
        self.pos_thread = Thread(target=self.send_pos, args=())
        self.pos_thread.daemon = True
        self.pos_thread.start()

        self.wait_for_topics(60)
        self.wait_for_landed_state(mavutil.mavlink.MAV_LANDED_STATE_ON_GROUND, 10, -1)
        self.set_mode("OFFBOARD", 5)
        self.set_arm(True, 5)
        rospy.loginfo("setup complete")

    def tearDown(self):
        """ Teardown, including landing and disarming the drone. """
        self.set_mode("AUTO.LAND", 5)
        self.wait_for_landed_state(mavutil.mavlink.MAV_LANDED_STATE_ON_GROUND, 45, 0)
        self.set_arm(False, 5)

        super(MavrosOffboardPosctl, self).tearDown()

    def send_pos(self):
        """ Runs in a separate thread, publishing current position at a rate of 10 Hz. """
        rate = rospy.Rate(10)  # Hz
        self.pos.header = Header()
        self.pos.header.frame_id = "base_footprint"

        while not rospy.is_shutdown():
            self.pos.header.stamp = rospy.Time.now()
            self.pos_setpoint_pub.publish(self.pos)
            try:  # prevent garbage in console output when thread is killed
                rate.sleep()
            except rospy.ROSInterruptException:
                pass

    def reach_position(self, x, y, z=DEFAULT_ALTITUDE):
        """ Set the position setpoint to the given values. """
        self.pos.pose.position.latitude = x
        self.pos.pose.position.longitude = y
        self.pos.pose.position.altitude = z
        rospy.loginfo(
            "attempting to reach position x: {0}, y: {1}, z: {2} | current position x: {3:.2f}, y: {4:.2f}, z: {5:.2f}".
            format(x, y, z, self.global_position.latitude,
                   self.global_position.longitude,
                   self.global_position.altitude))

        # Remove tf dependency for now to allow running with Python3
        # (this is equivalent to the below)
        self.pos.pose.orientation = Quaternion(0, 0, 0, 1)

        # For demo purposes we will lock yaw/heading to north.
        # yaw_degrees = 0  # North
        # yaw = math.radians(yaw_degrees)
        # quaternion = quaternion_from_euler(0, 0, yaw)
        # self.pos.pose.orientation = Quaternion(*quaternion)



if __name__ == '__main__':
    # Simple test to setup, fly in a line for 10 s, then land.
    # Similar to the way tx.py uses this class.

    controller = MavrosOffboardPosctl()
    controller.setUp()

    rate = rospy.Rate(1)
    for i in range(10):
        controller.reach_position(-43.52062 + i * 0.00001, 172.58325 + i * 0.00001)
        rate.sleep()

    controller.tearDown()
