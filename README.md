# activity-view
This project displays the use of cores and memory of the nodes in the cluster of computers

Initially, this program was created to help students and faculty at the University of Richmond to see availability of the university cluster, called Spydur. 

![Screenshot 2023-09-03 at 14 15 26](https://github.com/alinka955/activity-view/assets/78833495/ac054306-85c7-4c87-a343-21fa169cf1eb)


Next to the name of the node, you can see the map.
 It tells you how many cores (CPUs), out of 52, SLURM has allocated,
 based on the requests from users.
It happens that users request more cores than their program actually needs.
 The number that follows the map, indicates how many
 cores the node actually uses.
Notice the 3 numbers that follow. Just like cores, these
 numbers indicate SLURM-allocated, actually-used and total
 memory in GB.
If the node is colored in green, that means that its load
 is less than 75% in terms of both memory and CPU usage.
If the node is colored in yellow, that means that either node's
 memory or CPUs are more than 75% occupied.
The red color signifies anomaly - either the node is down or
 the number of cores used is more than 52.
