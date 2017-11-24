from tkinter import Tk
import matplotlib.pyplot as plt
import random
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D
import sys
import os
import matplotlib
from numpy import arange, sin, pi
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.widgets import Button

is_scanning = True
delay = 100
nb_points = 500

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

def refresh():
    global is_scanning

    if (not plt.fignum_exists(fig.number)):
        root.destroy()
        return

    if is_scanning:
        ax.cla()

        sequence_containing_x_vals = list(range(0, nb_points))
        sequence_containing_y_vals = list(range(0, nb_points))
        sequence_containing_z_vals = list(range(0, nb_points))

        random.shuffle(sequence_containing_x_vals)
        random.shuffle(sequence_containing_y_vals)
        random.shuffle(sequence_containing_z_vals)

        ax.scatter(sequence_containing_x_vals, sequence_containing_y_vals, sequence_containing_z_vals, marker='o')
        plt.draw()

    root.after(delay, refresh)

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

root.after(delay, refresh)
root.mainloop()
