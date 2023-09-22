function activity-view
{
    old="$PYTHONPATH"
    oldlib="$LD_LIBRARY_PATH"
    export PYTHONPATH=
    export LD_LIBRARY_PATH=
    python /home/ae9qg/activity-view/activityview.py
    export PYTHONPATH="$old"
    export LD_LIBRARY_PATH="$oldlib"
}
