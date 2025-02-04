## IoT-Sensor-project
An IoT project measuring and tracking dangerous gasses in a lab environment to alert machine operators of danger.

### Required Equipment
- RaspberryPi
- RaspberryPi Touchscreen
- MICS6814 Gas Sensor
- DFRobot Ozone Sensor

### USAGE INSTRUCTIONS
Run the Sensor_Dashboard_V2_Deployed.py file to start the sensor dashboard.<br />
The CO2, Ozone, Temp, and Pressure buttons all toggle the respective graphs.
The Notif. button toggles the Danger Notification. 

The entire screen will change colour based on the following gas levels:

|Colour | CO2  | Ozone | Status |
| --- | --- | --- | --- |
| White | <1000 | <0.1 | Safe |
| $${\color{yellow}Yellow}$$  | 1000  | 0.1 | Above the 8-hour working limit |
| $${\color{red}Red}$$  | 5000  | 0.2  | Dangerous |

These have been deemed to be appropriate levels based on online sources.

When the mouse is moved away from the Notif button it will show its status.
- $${\color{green}\textbf{Green}}$$ = Active, showing danger notifications
- $${\color{red}\textbf{Red}}$$ = Not active, not showing danger notifications

The Quit button will exit the program.
