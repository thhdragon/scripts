#!/usr/bin/env python3
import os
from math import pi, sqrt

# === USER VARIABLES (edit these as needed) ===
hotend_temp = 240   # Hotend (extruder) temperature in °C
bed_temp = 80       # Bed temperature in °C

# Bed center and size configuration
bed_center_is_zero = 0  # Set to 1 if your printer's bed center is (0,0), or 0 to use bed size and center the print
bed_size_x = 175        # Only used if bed_center_is_zero != 0 (enter your bed size in mm)
bed_size_y = 175        # Only used if bed_center_is_zero != 0 (enter your bed size in mm)

# Extrusion parameters (mm)
extrusion_width   = 0.6
layer_height      = 0.2
filament_diameter = 1.75

# Print speeds (mm/s)
travel_speed      = 500
first_layer_speed =  50
slow_speed        =   20
fast_speed        =  120

# Calibration object dimensions (mm)
layers        = 100
object_width  = 90
num_patterns  =  4
pattern_width =  5

# Pressure advance gradient (s)
pressure_advance_min = 0.03
pressure_advance_max = 0.05

layer0_z = layer_height

# Retraction settings
retract_length = 0.5   # mm
retract_speed = 30     # mm/s

def extrusion_for_length(length):
    """Calculate extruded length for a given move (relative mode)"""
    area = extrusion_width * layer_height
    filament_area = pi * (filament_diameter / 2) ** 2
    return area * length / filament_area

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    gcode_path = os.path.join(script_dir, "pa-test.gcode")

    # Offset calculation
    if bed_center_is_zero:
        offset_x = 0
        offset_y = 0
    else:
        offset_x = bed_size_x / 2
        offset_y = bed_size_y / 2

    with open(gcode_path, "w") as f:
        def emit(line):
            f.write(line + "\n")

        emit(f"START_PRINT BED_TEMP={bed_temp} EXTRUDER_TEMP={hotend_temp}")
        emit("M83 ; extruder relative mode")

        curr_x = offset_x
        curr_y = offset_y
        curr_z = layer0_z

        emit(f"G1 X{curr_x:.3f} Y{curr_y:.3f} Z{curr_z:.3f} F{travel_speed*60:.0f}")
        emit("G92 E0 ; reset extrusion distance")

        def up():
            nonlocal curr_z
            curr_z += layer_height
            emit(f"G1 Z{curr_z:.3f}")
            emit(f"G1 E{retract_length:.3f} F{retract_speed*60:.0f} ; detract")

        def line(x, y, speed):
            nonlocal curr_x, curr_y
            length = sqrt(x**2 + y**2)
            curr_x += x
            curr_y += y
            if speed > 0:
                extrude = extrusion_for_length(length)
                emit(f"G1 X{curr_x:.3f} Y{curr_y:.3f} E{extrude:.4f} F{speed*60:.0f}")
            else:
                emit(f"G1 X{curr_x:.3f} Y{curr_y:.3f} F{travel_speed*60:.0f}")

        def goto(x, y):
            nonlocal curr_x, curr_y
            curr_x = x + offset_x
            curr_y = y + offset_y
            emit(f"G1 X{curr_x:.3f} Y{curr_y:.3f}")

        # Prime lines (first 2 layers)
        line(-object_width/2, 0, 0)
        for l in range(2):
            for offset_i in range(5):
                offset = offset_i * extrusion_width
                line(object_width+offset,0,first_layer_speed)
                line(0,extrusion_width+offset*2,first_layer_speed)
                line(-object_width-offset*2,0,first_layer_speed)
                line(0,-extrusion_width-offset*2,first_layer_speed)
                line(offset,0,first_layer_speed)
                line(0,-extrusion_width,0)
            # End of this layer: retract and reset E
            emit(f"G1 E-{retract_length:.3f} F{retract_speed*60:.0f} ; retract")
            emit("G92 E0 ; reset extrusion distance")
            up()
            goto(-object_width/2,0)
            emit("G92 E0 ; reset extrusion distance after move")

        segment = object_width / num_patterns
        space = segment - pattern_width

        for l in range(layers):
            pa = pressure_advance_min + (l / layers) * (pressure_advance_max - pressure_advance_min)
            emit(f"; layer {l}, pressure advance: {pa:.3f}")
            emit(f"SET_PRESSURE_ADVANCE ADVANCE={pa:.3f}")

            for i in range(num_patterns):
                line(space/2, 0, fast_speed)
                line(pattern_width, 0, slow_speed)
                line(space/2, 0, fast_speed)
            line(0, extrusion_width, fast_speed)

            for i in range(num_patterns):
                line(-space/2, 0, fast_speed)
                line(-pattern_width, 0, slow_speed)
                line(-space/2, 0, fast_speed)
            line(0, -extrusion_width, fast_speed)

            # End of this layer: retract and reset E
            emit(f"G1 E-{retract_length:.3f} F{retract_speed*60:.0f} ; retract")
            emit("G92 E0 ; reset extrusion distance")
            up()
            goto(-object_width/2,0)
            emit("G92 E0 ; reset extrusion distance after move")
            emit(f"G1 E{retract_length:.3f} F{retract_speed*60:.0f} ; detract")

        emit("END_PRINT")

if __name__ == "__main__":
    main()
