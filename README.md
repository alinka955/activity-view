# activity-view
This project displays the use of cores and memory of the nodes in the cluster of computers.

Initially, this program was created to help students and faculty at the University of Richmond to see availability of the university cluster, called Spydur. 

![Screenshot 2023-09-03 at 14 15 26](https://github.com/alinka955/activity-view/assets/78833495/ac054306-85c7-4c87-a343-21fa169cf1eb)

## What is this for?
At the University of Richmond (UR), students and faculty conduct comprehensive research that requires heavy calculations. Since regular PCs have limited resources, users take advantage of the UR cluster and have their calculations done in seconds, rather than hours or days. Once a user submits their job, SLURM [^footnote] takes care of its allocation and execution. While there is an opportunity to rely on SLURM's scheduling, users prefer to choose the nodes they want to run a job on independently. The map clearly displays the nodes with the most available resources. 

## What does this map mean?
University of Richmond cluster has 30 nodes, called 'spdr..'. Each node has 52 cores and some memory capacity, ranging from 384 to 1536 GB. 

Next to the name of the node, you can see the map. It tells you how many cores (CPUs), out of 52, SLURM has allocated, based on the requests from users. Columns 'Allocated' reflect the amount of cores and memory requested by the usrs.
It happens that users either underestimate or overestimate the cores or memory than their program actually needs to execute. The amount of resources requested by users is reflected in the columns 'Used'. 

## What do color mean?
If the node is colored in green, that means that its load is less than 75% in terms of both memory and CPU usage. 

If the node is colored in yellow, that means that either node's memory or CPUs are more than 75% occupied.

The red color signifies anomaly - either the node is down or the number of cores used is more than 52. In the snapshot of the map above, nodes 'spdr16' and 'spdr51' are highlighted in red and respectively display 88 and 92 cores as used. This happened because users underestimated the resources that their job needed. That is why, although the numbers in columns 'Allocated' are within appripriate limits, the numbers in columns 'Used' overflow. 
 



[^footnote]: systen that manages and schedules the jobs on the cluster.
