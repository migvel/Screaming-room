(beginning of start.txt)
G21 (Ultimaker profile - UM_JM - 0.4 s45 e80 alterations/start.gcode)
G90 (Absolute Positioning)
M92 E28
G1 X-240.0 F8000
G1 Y-240.0 F8000
M109 S234 (Extruder Temperature M109 is met wachten)
G1 Z-240.0 F700
G28 (home all axes to min endstops)
G92 X-105 Y-105 Z0.0 E0 (reset position to where the head is now)
G1 F7000 E760
G92 E0 (zero the extruded length)
G1 X-80.0 Y-105.0 F2000 E50
G1 X-50.0 Y-50.0 F8000 E50
;G92 X0 Y0 Z0 (set origin to current position)
G92 E0 (zero the extruded length)
M220 S190
M106 S200
(end of start.txt)