Env Vars:
mig_name - Name of the managed instance group (mig)
mig_region - Region of the mig
upper_session_count - max num of sessions per node
lower_session_count - lower num of sessions before marking for removal
new_session_lock_timeout - used to reserve a session on server per /new_session call (prevents one server getting over loaded)

checks:
/ - returns list of all servers and session counts
/new_session - returns json list of servers ranked in order of optimal usage
/test - Force addition or removal of nodes (add={int}, or sub={int} e.g /test?add=2) 
/check - Call to check a specific server and 


Permissions:
- 
- compute.instances.setLabels
