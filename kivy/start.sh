#! /bin/bash

# echo "Flipping touch screen"
# xinput --set-prop 'FT5406 memory based driver' 'Coordinate Transformation Matrix' 0 1 0 -1 0 1 0 0 1

echo "Starting Kivy Photo Application"
python3 CarouselApp.py