from numpy import cos, arccos, sin, arctan, tan, pi, sqrt; from numpy import array as ary; import numpy as np; tau = 2*pi
from matplotlib import pyplot as plt
from matplotlib import animation
import matplotlib.animation as manimation
from ConvrgenceVideo import get_outline
from create_spiral import get_closest_neighbour_distance
from scipy.stats import describe

VIDEO = False
READ_FROM_HUMAN_READABLE_FILE= False

target_r_min_to_r_max_ratio = 0.45/1.985 #both radii measurements were recorded in mm.
offset_constant_in_sqrt = 12 * (1 + target_r_min_to_r_max_ratio**2)/(1 - target_r_min_to_r_max_ratio**2)
radius_max = sqrt(offset_constant_in_sqrt+12)/sqrt(pi)
radius_min = sqrt(offset_constant_in_sqrt-12)/sqrt(pi)

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

def check_in_bound(p):
    dist_from_centre = quadrature(p)
    if abs(p[1]/p[0])>tan(pi/6):
        return True
    elif (dist_from_centre>radius_max) or (dist_from_centre<radius_min):
        return True
    else:
        return False

if __name__=='__main__':
    frame_data = []
    if READ_FROM_HUMAN_READABLE_FILE:
        with open('single_cable_data.txt', 'r') as f:
            data = ('').join(f.readlines()).replace('\n','').replace(']],',']]\n').split('\n')
        for i in range(len(data)):
            frame_data.append(str2array(data[i][1:-1]))
    else:
        from interframeattract import *
        column = np.load('repel_result.npy', allow_pickle=True)
        for i in range(len(column)):
            frame_data.append( [column[i].points[j].pos for j in range(column[i].num_points)] )

    FFMpegWriter = manimation.writers['ffmpeg']
    metadata = dict(title='short_repel', artist='Matplotlib', comment='100 frames, Triple repel')
    writer = FFMpegWriter(fps=15, metadata=metadata)
    fig, ax = plt.subplots()
    ax.set_aspect(1.0)
    ax.set_xlim((1-sqrt(3)/2)*radius_min, radius_max)
    ax.set_ylim(-1/2*radius_max, 1/2*radius_max)
    ax.set_xticks([])
    ax.set_yticks([])
    outline = ary(get_outline()).T
    ax.plot(outline[0], outline[1])
    xycoods = ax.scatter(np.ones(417), np.zeros(417))
               
    if VIDEO:
        with writer.saving(fig, "short_repel.mp4", 300):
            for i in range(len(frame_data)):
                xycoods.set_offsets( frame_data[i] )
                ax.set_title("Layer "+str(i))
                writer.grab_frame()
            fig.clf()
    else:
        plt.cla()
        for i in range(len(frame_data)):
            distances = get_closest_neighbour_distance(frame_data[i])
            des = describe(distances)
            print(des)
            if sum(n:=[ check_in_bound(p) for p in frame_data[i] ])>0:
                print("Out of bounds points = ")
                print(np.argwhere(n))
            # plt.hist(distances, bins=100)
            # plt.title("spacing for frame"+str(i))
            # plt.show()
            # print(f"for frame {i}, the minimum and maximum spacings are {min(distances)}, {max(distances)}")
