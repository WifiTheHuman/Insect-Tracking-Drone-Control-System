# Insect Tracking Drone Control System
Scion Research has sponsored research and development of a system capable of tracking insects using radio-frequency harmonic radars mounted on drones paired with a tiny reflector strip on the insect (a GPS module is too large for an insect to carry).
  
The research team consists of Yifei Ma, Reka Norman, Zeb Barry and Callum Fraser.  
  
The system consists of a transmitter drone and several receiver drones. The Tx drone emits the radar, which reflects off the insect and is read by the Rx drones, which can then calculate the distance travelled by the radio waves.  
  
To find the actual location of the target, the drones must communicate with each other and perform triangulation/multilateration. This is the part that Yifei Ma was responsible for.

Once the target location is found, the drones must maintain formation and follow the target.
