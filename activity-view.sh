function activity-view
{
    old="$PYTHONPATH"
    oldlib="$LD_LIBRARY_PATH"
    export PYTHONPATH=
    export LD_LIBRARY_PATH=
    python3 ./activityview.py
    export PYTHONPATH="$old"
    export LD_LIBRARY_PATH="$oldlib"
}
