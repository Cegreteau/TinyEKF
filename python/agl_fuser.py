#!/usr/bin/env python3
'''
agl_fuser.py - Sonar / Barometer fusion example using TinyEKF.  

Also requires RealtimePlotter: https://github.com/simondlevy/RealtimePlotter

Copyright (C) 2016 Simon D. Levy

This code is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.
This code is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with this code. If not, see <http://www.gnu.org/licenses/>.
'''

GROUNDTRUTH = 1000000

SONARMIN = 900000 # Centimeters
SONARMAX = 1100000 
BAROMIN  = 26000   # Pascals
BAROMAX  = 27000
 
import numpy as np
from tinyekf import EKF
from realtime_plot import RealtimePlotter
from time import sleep
import threading

# ground-truth AGL to sonar measurement, empirically determined:
# see http://diydrones.com/profiles/blogs/altitude-hold-with-mb1242-sonar
def sonar(groundtruth):

    return 0.933 * groundtruth - 2.894

# cm to Pascals: see http://www.engineeringtoolbox.com/air-altitude-pressure-d_462.html
def baro(groundtruth):

    return 101325 * pow((1 - 2.25577e-7 * groundtruth), 5.25588)

class AGL_EKF(EKF):

    def __init__(self):

        EKF.__init__(self, 1, 2)

    def f(self, x):

        # State-transition function is identity
        return np.copy(x)

    def getF(self, x):

        # So state-transition Jacobian is identity matrix
        return np.eye(1)

    def h(self, x):

        return np.array([baro(x[0]), sonar(x[0])])

    def getH(self, x):

        # Used http://www.wolframalpha.com
        dpdx = -0.120131 * pow((1 - 2.2577e-7 * x[0]), 4.25588)

        dsdx = 0.933

        return np.array([[dpdx], [dsdx]])


class AGLPlotter(RealtimePlotter):

    def __init__(self):

        sonarmin = int(0.9 * GROUNDTRUTH)
        sonarmax = int(1.1 * GROUNDTRUTH)

        RealtimePlotter.__init__(self, [(sonarmin,sonarmax), (BAROMIN,BAROMAX)], 
                window_name='Altitude Sensor Fusion',
                yticks = [range(sonarmin,sonarmax,int((sonarmax-sonarmin)/10.)), range(BAROMIN,BAROMAX,100)],
                styles = [('r','b'), 'g'], 
                legends = [('Sonar', 'Fused'), None],
                ylabels=['AGL (cm)', 'Baro (mb)'])

        self.xcurr = 0
        self.fused = 0
        self.baro  = baro(GROUNDTRUTH)  
        self.sonar = sonar(GROUNDTRUTH)
 
        self.ekf = AGL_EKF()

    def update(self):

        while True:

            self.fused = self.ekf.step((self.baro, self.sonar))[0]
            plotter.xcurr += 1
            sleep(.001)

    def getValues(self):

        return self.sonar, self.fused, self.baro

if __name__ == '__main__':

    plotter = AGLPlotter()

    thread = threading.Thread(target=plotter.update)
    thread.daemon = True

    thread.start()
    plotter.start()
