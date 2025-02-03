"""
Raspberry Pi Sensor Dashboard V1.5
Run if V2 is broken!!!
This script negates the data storage in write to .csv functionality which can cause issues in V2

Author: Loui Byrne
Date: 24 August 2022
Owner: PlasmaBound Ltd.

This GUI has been developed to display the CO2 and Ozone concentrations in the lab and
inside the robotic chamber. Misuse and mishandling of the hardware may result in failure.
The sensor unit, touchscreen and cables are very delicate and must be handled with care.

If you are running the script on a new raspberry Pi, or have recently flashed the OS,
You must copy and paste the following lines of code into the terminal and press Enter:

sudo apt-get update
sudo apt-get install libatlas3-base libffi-dev at-spi2-core python3-gi-cairo
pip install cairocffi
pip install matplotlib
"""
###############################################################################
# Setup

import datetime as dt
import tkinter as tk
import tkinter.font as tkFont
import os
import csv
from datetime import datetime

from PIL import Image, ImageTk
import matplotlib.figure as figure
import matplotlib.animation as animation
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

#Initialise C02 Sensor
from smbus import SMBus
import time
EE895ADDRESS = 0x5E
I2CREGISTER = 0x00

#Initialise Gas Sensor
from mics6814 import MICS6814
import logging
gas = MICS6814()
logging.basicConfig(
    format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

#Initialise Ozone Sensor
import sys
sys.path.append("../")
from DFRobot_Ozone import *
COLLECT_NUMBER   = 20              # collect number, the collection range is 1-100
IIC_MODE         = 0x01            # default use IIC1
ozone = DFRobot_Ozone_IIC(IIC_MODE ,OZONE_ADDRESS_3)
ozone.set_mode(MEASURE_MODE_AUTOMATIC)

###############################################################################
# Parameters and global variables

# Parameters
update_interval = 3000 # Time (ms) between polling/animation updates
max_elements = 10000 # Maximum number of elements to store in plot lists

# Declare global variables
root = None
dfont = None
frame = None
canvas = None
ax1 = None
ax2 = None
ax3 = None
ax4 = None
global num
num = 1

# Global variable to remember various states
fullscreen = False
co2_plot_visible = True
temp_plot_visible = False
pressure_plot_visible = False
ozone_plot_visible = True
danger_notif_visible = True
danger_button_colour = 'green'
notif_colour = 'white'

###############################################################################
# Functions

# Toggle fullscreen
def toggle_fullscreen(event=None):

    global root
    global fullscreen

    # Toggle between fullscreen and windowed modes
    fullscreen = not fullscreen
    root.attributes('-fullscreen', fullscreen)
    resize(None)   

# Return to windowed mode
def end_fullscreen(event=None):

    global root
    global fullscreen

    # Turn off fullscreen mode
    fullscreen = False
    root.attributes('-fullscreen', False)
    resize(None)

# Automatically resize font size based on window size
def resize(event=None):

    global dfont
    global frame

    # Resize font based on frame height (minimum size of 12)
    # Use negative number for "pixels" instead of "points"
    new_size = -max(12, int((frame.winfo_height() / 20)))
    dfont.configure(size=new_size)

# Toggle the C02 plot
def toggle_co2():

    global canvas
    global ax1
    global co2_plot_visible

    # Toggle plot and axis ticks/label
    co2_plot_visible = not co2_plot_visible
    ax1.get_lines()[0].set_visible(co2_plot_visible)
    ax1.get_yaxis().set_visible(co2_plot_visible)
    canvas.draw()

# Toggle the temp plot
def toggle_temp():

    global canvas
    global ax2
    global temp_plot_visible

    # Toggle plot and axis ticks/label
    temp_plot_visible = not temp_plot_visible
    ax2.get_lines()[0].set_visible(temp_plot_visible)
    ax2.get_yaxis().set_visible(temp_plot_visible)
    canvas.draw()
    
# Toggle the pressure plot
def toggle_pressure():

    global canvas
    global ax3
    global pressure_plot_visible

    # Toggle plot and axis ticks/label
    pressure_plot_visible = not pressure_plot_visible
    ax3.get_lines()[0].set_visible(pressure_plot_visible)
    ax3.get_yaxis().set_visible(pressure_plot_visible)
    canvas.draw()
    
# Toggle the Ozone plot
def toggle_ozone():

    global canvas
    global ax4
    global ozone_plot_visible

    # Toggle plot and axis ticks/label
    ozone_plot_visible = not ozone_plot_visible
    ax4.get_lines()[0].set_visible(ozone_plot_visible)
    ax4.get_yaxis().set_visible(ozone_plot_visible)
    canvas.draw()

# Toggle the Danger Notification
def toggle_danger_notif():

    global danger_notif_visible
    global danger_button_colour
    danger_notif_visible = not danger_notif_visible
    if (danger_notif_visible == True):
        danger_button_colour = 'green'
    else:
        danger_button_colour = 'red'
        danger_notif('white')
    button_danger_notif = tk.Button(frame, text="Notif", font=dfont, command=toggle_danger_notif, bg=danger_button_colour,fg='white')
    button_danger_notif.grid(row=5,column=6,columnspan=1)

# Define Function to set background colour to danger notification
def danger_notif(notif_colour):
    frame.configure(bg=notif_colour)
    fig.patch.set_facecolor(notif_colour)
    label_co2.config(bg=notif_colour)
    label_co2value.config(bg=notif_colour)
    label_co2unit.config(bg=notif_colour)
    label_temp.config(bg=notif_colour)
    label_tempvalue.config(bg=notif_colour)
    label_tempunit.config(bg=notif_colour)
    label_pressure.config(bg=notif_colour)
    label_pressurevalue.config(bg=notif_colour)
    label_pressureunit.config(bg=notif_colour)
    label_ozone.config(bg=notif_colour)
    label_ozonevalue.config(bg=notif_colour)
    label_ozoneunit.config(bg=notif_colour)
    
# This function is called periodically from FuncAnimation
def animate(i, ax1, ax2, ax3, ax4, xaxisarray, co2array, temparray, pressurearray, ozonearray, co2value, tempvalue, pressurevalue, ozonevalue):

    # Update data to display C02, temp, pressure and Ozone values
    try:
        i2cbus = SMBus(1)

        # C02 Data
        read_data = i2cbus.read_i2c_block_data(EE895ADDRESS, I2CREGISTER, 8)
        new_co2 = int.from_bytes(read_data[0].to_bytes(1, 'big') + read_data[1].to_bytes(1, 'big'), "big")
        new_temp = round(int.from_bytes(read_data[2].to_bytes(1, 'big') + read_data[3].to_bytes(1, 'big'), "big")/100,1)
        new_pressure = round(int.from_bytes(read_data[6].to_bytes(1, 'big') + read_data[7].to_bytes(1, 'big'), "big")/10)

        # Ozone Data
        new_ozone_long = (ozone.get_ozone_data(COLLECT_NUMBER))/1000
        new_ozone = round(new_ozone_long, 3)

    except:
        pass

    # Update our labels
    co2value.set(new_co2)
    tempvalue.set(new_temp)
    pressurevalue.set(new_pressure)
    ozonevalue.set(new_ozone)

    # Append timestamp to x-axis list
    timestamp = mdates.date2num(dt.datetime.now())
    xaxisarray.append(timestamp)

    # Append sensor data to lists for plotting
    co2array.append(new_co2)
    temparray.append(new_temp)
    pressurearray.append(new_pressure)
    ozonearray.append(new_ozone)

    # Limit lists to a set number of elements
    xaxisarray = xaxisarray[-max_elements:]
    co2array = co2array[-max_elements:]
    temparray = temparray[-max_elements:]
    pressurearray = pressurearray[-max_elements:]
    ozonearray = ozonearray[-max_elements:]

    # Clear, format, and plot C02 values first (behind)
    color = 'black'
    ax1.clear()
    ax1.set_ylabel('C02 (ppm)', color=color)
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.plot(xaxisarray, co2array, linewidth=2, color=color)

    # Clear, format, and plot temp values (in front)
    color = 'tab:green'
    ax2.clear()
    ax2.set_ylabel('Temperature (°C)', color=color)
    ax2.tick_params(axis='y', labelcolor=color)
    ax2.plot(xaxisarray, temparray, linewidth=2, color=color)
    
    # Clear, format, and plot pressure values (in front)
    color = 'tab:orange'
    ax3.clear()
    ax3.set_ylabel('Pressure (mbar)', color=color)
    ax3.tick_params(axis='y', labelcolor=color)
    ax3.plot(xaxisarray, pressurearray, linewidth=2, color=color)
    
    # Clear, format, and plot Ozone values (in front)
    color = 'tab:blue'
    ax4.clear()
    ax4.set_ylabel('Ozone (ppm)', color=color)
    ax4.tick_params(axis='y', labelcolor=color)
    ax4.plot(xaxisarray, ozonearray, linewidth=2, color=color)

    # Format timestamps to be more readable
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    fig.autofmt_xdate()

    # Make sure plots stay visible or invisible as desired
    ax1.get_lines()[0].set_visible(co2_plot_visible)
    ax1.get_yaxis().set_visible(co2_plot_visible)
    ax2.get_lines()[0].set_visible(temp_plot_visible)
    ax2.get_yaxis().set_visible(temp_plot_visible)
    ax3.get_lines()[0].set_visible(pressure_plot_visible)
    ax3.get_yaxis().set_visible(pressure_plot_visible)
    ax4.get_lines()[0].set_visible(ozone_plot_visible)
    ax4.get_yaxis().set_visible(ozone_plot_visible)

    # Write data to .csv file
#     file = open("data_log.csv", "a")
#     file.write(str(new_co2)+","+str(new_temp)+","+str(new_pressure)+","+str(new_ozone)+","+datetime.today().strftime('%Y-%m-%d'+","+'%H:%M:%S')+"\n")
#     
#     with open("data_log.csv", "r") as file:
#         with open("final_log.csv", "w") as output:
#             reader = csv.reader(file)
#             output.write("Log ID"+","+"C02 (ppm)"+","+"Temp (C)"+","+"Pressure (mbar)"+","+"Ozone (ppm)"+","+"Date"+","+"Time"+"\n")
#             writer = csv.writer(output,lineterminator='\n')
#             for row in reader:
#                 global num
#                 writer.writerow([num]+row)
#                 num = num + 1
#     file.close()
#     output.close()
    
    #Change background colour if co2 or ozone is too high
    global notif_colour
    if (new_co2 < 1000) and (new_ozone_long < 0.1):
        notif_colour = 'white'
    elif (new_co2 < 5000) and (new_ozone_long < 0.15):
        
        notif_colour = 'yellow'
    else:
        notif_colour = 'red'
    
    #Set Frame Background colour
    if (danger_notif_visible == True):
        danger_notif(notif_colour)
    
# Destroy function to kill script
def _destroy(event):
    raise SystemExit
    pass

###############################################################################
# Main script

# Create the main window
root = tk.Tk()
root.title("Sensor Dashboard V2")

# Create the main container
frame = tk.Frame(root)
frame.configure(bg=notif_colour)

# Lay out the main container (expand to fit window)
frame.pack(fill=tk.BOTH, expand=1)

# Create figure for plotting
fig = figure.Figure(figsize=(2, 2))
fig.subplots_adjust(left=0.175, right=0.8)
ax1 = fig.add_subplot(1, 1, 1)

# Instantiate a new set of axes that shares the same x-axis
ax2 = ax1.twinx()
ax3 = ax1.twinx()
ax4 = ax1.twinx()

# Empty x and y lists for storing data to plot later
xaxisarray = []
co2array = []
temparray = []
pressurearray = []
ozonearray = []

# Variables for holding C02, temp, pressure, and Ozone data
co2value = tk.DoubleVar()
tempvalue = tk.DoubleVar()
pressurevalue = tk.DoubleVar()
ozonevalue = tk.DoubleVar()

# Create dynamic font for text
dfont = tkFont.Font(size=-12)

# Create a Tk Canvas widget out of our figure
canvas = FigureCanvasTkAgg(fig, master=frame)
canvas_plot = canvas.get_tk_widget()

# Create other supporting widgets
label_co2 = tk.Label(frame, text='C02:', font=dfont, bg='white', fg='black')
label_co2value = tk.Label(frame, textvariable=co2value, font=dfont, bg='white',fg='black')
label_co2unit = tk.Label(frame, text="ppm", font=dfont, bg='white', fg='black')

label_temp = tk.Label(frame, text='Temp:', font=dfont, bg='white', fg='#2ca02c')
label_tempvalue = tk.Label(frame, textvariable=tempvalue, font=dfont, bg='white', fg='#2ca02c')
label_tempunit = tk.Label(frame, text="°C", font=dfont, bg='white', fg='#2ca02c')

label_pressure = tk.Label(frame, text='Pressure:', font=dfont, bg='white', fg='#ff7f0e')
label_pressurevalue = tk.Label(frame, textvariable=pressurevalue, font=dfont, bg='white', fg='#ff7f0e')
label_pressureunit = tk.Label(frame, text="mbar", font=dfont, bg='white', fg='#ff7f0e')

label_ozone = tk.Label(frame, text="Ozone:", font=dfont, bg='white', fg='#1f77b4')
label_ozonevalue = tk.Label(frame, textvariable=ozonevalue, font=dfont, bg='white', fg='#1f77b4')
label_ozoneunit = tk.Label(frame, text="ppm", font=dfont, bg='white', fg='#1f77b4')

button_co2 = tk.Button(frame, text="C02", font=dfont, command=toggle_co2, bg='#d62728',fg='white')
button_temp = tk.Button(frame, text="Temp", font=dfont, command=toggle_temp, bg='#2ca02c',fg='white')
button_pressure = tk.Button(frame, text="Pressure", font=dfont, command=toggle_pressure, bg='#ff7f0e',fg='white')
button_ozone = tk.Button(frame, text="Ozone", font=dfont, command=toggle_ozone, bg='#1f77b4',fg='white')
button_danger_notif = tk.Button(frame, text="Notif", font=dfont, command=toggle_danger_notif, bg=danger_button_colour,fg='white')
button_quit = tk.Button(frame, text="Quit", font=dfont, command=root.destroy)

# Lay out widgets in a grid in the frame
canvas_plot.grid(row=0, column=0, rowspan=5, columnspan=4, sticky=tk.W+tk.E+tk.N+tk.S)

label_co2.grid(row=0, column=4, columnspan=1, sticky=tk.W)
label_co2value.grid(row=0, column=6, columnspan=2, sticky=tk.W)
label_co2unit.grid(row=0, column=8, sticky=tk.W)

label_temp.grid(row=1, column=4, columnspan=1, sticky=tk.W)
label_tempvalue.grid(row=1, column=6, columnspan=2, sticky=tk.W)
label_tempunit.grid(row=1, column=8, sticky=tk.W)

label_pressure.grid(row=2, column=4, columnspan=1, sticky=tk.W)
label_pressurevalue.grid(row=2, column=6, columnspan=2, sticky=tk.W)
label_pressureunit.grid(row=2, column=8, sticky=tk.W)

label_ozone.grid(row=3, column=4, columnspan=1, sticky=tk.W)
label_ozonevalue.grid(row=3, column=6, columnspan=2, sticky=tk.W)
label_ozoneunit.grid(row=3, column=8, sticky=tk.W)

button_co2.grid(row=5, column=0, columnspan=1)
button_temp.grid(row=5, column=1, columnspan=1)
button_pressure.grid(row=5, column=2, columnspan=1)
button_ozone.grid(row=5, column=3, columnspan=1)
button_danger_notif.grid(row=5,column=6,columnspan=1)
button_quit.grid(row=5, column=8, columnspan=1)


# Add a standard 10 pixel padding to all widgets
for w in frame.winfo_children():
    w.grid(padx=5, pady=5)

# Make it so that the grid cells expand out to fill window
for i in range(0, 5):
    frame.rowconfigure(i, weight=1)
for i in range(0, 8):
    frame.columnconfigure(i, weight=1)

# Bind F11 to toggle fullscreen and ESC to end fullscreen
root.bind('<F11>', toggle_fullscreen)
root.bind('<Escape>', end_fullscreen)

# Have the resize() function be called every time the window is resized
root.bind('<Configure>', resize)

# Call empty _destroy function on exit to prevent segmentation fault
root.bind("<Destroy>", _destroy)

# Call animate() function periodically
fargs = (ax1, ax2, ax3, ax4, xaxisarray, co2array, temparray, pressurearray, ozonearray, co2value, tempvalue, pressurevalue, ozonevalue)
ani = animation.FuncAnimation(fig, animate, fargs=fargs, interval=update_interval)               

# Start in fullscreen mode and run
toggle_fullscreen()
root.mainloop()


