from tkinter import Tk
import matplotlib.pyplot as plt
import random
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D
import sys
import os
import matplotlib
from numpy import arange, sin, pi, matrix, array
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.widgets import Button
import cv2
import math

is_scanning = True

root = Tk()
root.withdraw()

def toggle_scan(object):
    global is_scanning
    is_scanning = not is_scanning
    if (is_scanning):
        toggle_scan_button.label.set_text("Stop")
    else:
        toggle_scan_button.label.set_text("Start")

def quit(object):
    plt.close('all')
    root.destroy()

def full_screen(object):
    mng = plt.get_current_fig_manager()
    mng.full_screen_toggle()

plt.rcParams['toolbar'] = 'None'
fig = plt.figure("3D Reconstruction")
ax = fig.add_subplot(111, projection='3d')
plt.ion()
plt.show()

toggle_scan_button = Button(plt.axes([0.04, 0.9, 0.1, 0.06]), 'Stop')
toggle_scan_button.on_clicked(toggle_scan)
full_screen_button = Button(plt.axes([0.75, 0.05, 0.1, 0.06]), 'Full')
full_screen_button.on_clicked(full_screen)
quit_button = Button(plt.axes([0.86, 0.05, 0.1, 0.06]), 'Quit')
quit_button.on_clicked(quit)

focal = 0.004
baseline = 0.1

# Change these matrixes with real camera calibration matrixes
projMatr1 = matrix([[1, 0, 0, 0],
                    [0, 1, 0, 0],
                    [0, 0, 1/focal, 0]])
projMatr2 = matrix([[1, 0, 0, baseline],
                    [0, 1, 0, 0],
                    [0, 0, 1/focal, 0]])

while True:
    root.update_idletasks()
    root.update()

    # Change these points with real image points
    projPoints1 = array([0 + random.uniform(0.005, 0.02), 0 - random.uniform(0.005, 0.02)])
    projPoints2 = array([0 - random.uniform(0.005, 0.02), 0 + random.uniform(0.005, 0.02)])

    worldPoint = cv2.triangulatePoints(projMatr1, projMatr2, projPoints1, projPoints2)

    ax.scatter(worldPoint[0], worldPoint[1], worldPoint[2], marker='o')
    plt.draw()