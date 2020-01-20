from numpy import cos, arccos, sin, arctan, tan, tanh, pi, sqrt; from numpy import array as ary; import numpy as np; tau = 2*pi
from particlerelax import Point, REF_STEP_SIZE, F_LIMIT
from SimpleMapping import circle_to_sextant, tessellate_circle_properly, rotate_list_of_points, quadrature
from scipy.stats import describe
import logging
logger = logging.getLogger(__name__) #created logger with NOSET level of logging, i.e. all messages are recorded.
logger.setLevel(logging.DEBUG)
logHandler = logging.FileHandler('attract_relaxed.log')
handler = logger.addHandler(logHandler)

REF_STEP_SIZE = 0.5
START_FROM_PRISTINE = False
RESOLUTION = 100

def str2array(l):
    p=0
    text = ['',]*l.count(']') 
    for i in l: 
        if i==']': 
            p += 1 
        elif i =='[': 
            pass 
        else: 
            text[p] += i 
    return ary([np.fromstring(entry.lstrip(', '), sep=',') for entry in text])

def attract_kernel(x):
    return -tanh(x*2/pi)

class Slice:
    def __init__(self, list_of_points, ak=attract_kernel):
        self.points = []
        self.ak_raw = ak
        self.weaken_factor = 0.4
        for p in list_of_points:
            #each one should be a Point object
            self.points.append(p)
        self.num_points = len(self.points)
    
    def attract_kernel(self, disp):
        return self.weaken_factor*self.ak_raw(disp) # no scaling needed
    
    def walk(self, final_force_array):
        for i in range(self.num_points):
            self.points[i].walk(final_force_array[i])

    def get_full_internal_forces(self):
        return [ p.get_force_raw(self.points) for p in self.points]

    def get_total_force_raw(self, slice_above, slice_below):
        force_list = self.get_full_internal_forces()
        for i in range(self.num_points):
            disp_above = slice_above.points[i].pos - self.points[i].pos
            disp_below = slice_below.points[i].pos - self.points[i].pos
            force_list[i] = np.append(force_list[i], [self.attract_kernel(disp_above), self.attract_kernel(disp_below)], axis=0)
        return force_list
    
    def get_total_force(self, slice_above, slice_below):
        force_list = self.get_total_force_raw(slice_above, slice_below)
        averaged_forces = []
        for i in range(self.num_points):
            force = force_list[i]
            averaged_forces.append( [sum(force[:,0])/len(force), sum(force[:,1])/len(force)] )
        return averaged_forces

if __name__=='__main__':
    if START_FROM_PRISTINE:
        circle = tessellate_circle_properly(417)
        data = []
        for theta in np.linspace(0, tau, RESOLUTION):
            rotated_circle = rotate_list_of_points(circle, theta)
            transformed_list = circle_to_sextant(rotated_circle)
            data.append(rotated_circle)
    else:
        with open('single_cable_data.txt', 'r') as f:
            data = ('').join(f.readlines()).replace('\n','').replace(']],',']]\n').split('\n')
            data = [i for i in data if len(i)>3] #at least 3 characters long string is needed
        step_size = len(data)//RESOLUTION
        data_trimmed = ary([ str2array(dat_line[1:-1]) for dat_line in data])[::step_size]

    #create a column containing {RESOLUTION} number of slices
    column = []
    for cross_section in data_trimmed:
        column.append( Slice([ Point(pos) for pos in cross_section ]))

    step = 0
    des = describe([1,1]) #create a dummy describe object to start the iteration off with.
    while des.minmax[1] > F_LIMIT and des.mean > F_LIMIT/2.5:
        column_force = []
        for i in range(len(column)):
            below = i-1
            above = (i+1)%len(column)
            column_force.append( column[i].get_total_force(column[below], column[above]) )
        des = describe( [quadrature(xy) for xy in np.concatenate(column_force)] )
        logger.debug("Step {0} has a mean force of {1} with bounds of {2} and skewness={3}.".format( step, des.mean, des.minmax, des.skewness) )

        for i in range(len(data_trimmed)):
            column[i].walk( ary(column_force)[i]*REF_STEP_SIZE )
        # logger.info("finished step "+str(step))
        np.save('attract_relaxed.npy', column)
        step += 1 