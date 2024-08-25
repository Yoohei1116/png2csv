import numpy as np
import matplotlib.pyplot as plt
import classes
import datetime
import cv2
import os
import pandas as pd
import time
from collections import defaultdict
from scipy.ndimage import convolve


def get_graph_corner_points(image, k1_3, k2_3, k3_2, k4_1):
    # count px of some colors around 3*3 px (self included)
    cnt_k1 = convolve(np.all(image == k1_3, axis=-1).astype(int), np.ones((3,3)))
    cnt_k2 = convolve(np.all(image == k2_3, axis=-1).astype(int), np.ones((3,3)))
    cnt_k3 = convolve(np.all(image == k3_2, axis=-1).astype(int), np.ones((3,3)))
    cnt_k4 = convolve(np.all(image == k4_1, axis=-1).astype(int), np.ones((3,3)))
    
    # get some points by cnt conditions 
    pts = np.where((cnt_k1 == 3) & (cnt_k2 == 3) & (cnt_k3 == 2) & (cnt_k4 == 1))
    return np.vstack(pts).T

def is_image_of_colors(image, colors_set):
    # reshape image to 2D array where each row is a pixel and columns are RGB values
    image_reshaped = image.reshape(-1, image.shape[-1])
    
    # get unique colors in the image
    unique_colors = set(tuple(color) for color in image_reshaped)
    
    # check if all unique colors in the image are in the set of allowed colors
    return unique_colors.issubset(colors_set)

def mkdir(dir_out):
    if not os.path.isdir(dir_out):
        os.makedirs(dir_out)

def main(queue, paths, dir_out, red_line_value, xlim, fname_out, save_image_frag, gui):
    
    # colors (BGR) used for detecting corner points  
    colors_corner = {
        'k1_3':(0, 0, 0),
        'k2_3':(227,227,227),
        'k3_2':(240,240,240),
        'k4_1':(253,253,253),
    }
    
    # colors (BGR) used for checking no non-graph objecects are in the inside of the graph 
    colors_inside = {(0, 0, 0), (255,255,255), (144, 95, 74), (227,227,227), (180, 119, 31), (0, 0, 255), (0, 0, 241), (205, 205, 255), (193, 193, 241), (170, 112, 29), (241, 241, 241)}

    # make a output folder
    mkdir(dir_out)
    
    # classify png image files according to folders
    tasks_num = 0
    selected_files = defaultdict(list)
    for file_path in paths:
        dir_name, file_name = os.path.split(file_path)
        if os.path.splitext(file_name)[1] == '.png':
            selected_files[dir_name].append(file_name)
            tasks_num += 1
            
    # double tasks num if saving images of csv data
    if save_image_frag:
        tasks_num = int(tasks_num * 2)
    
    queue.put(('tasks_num', tasks_num))
    
    # execute by folder names
    fout_list = []
    progress = 0.0
    for folder, files in selected_files.items():
    
        # make a output folder
        dir_image = folder
        dir_out_folder = os.path.join(dir_out, os.path.relpath(folder))
        mkdir(dir_out_folder)
        
        # main processing
        dfs = pd.DataFrame()
        file_num_available = 0
        file_num_unavailable = 0
        for iter, img_name in enumerate(sorted(files)):
            print(img_name)
            
            # check stop flag
            if gui.stop_requested():
                exit()
            
            queue.put(('fname', img_name, os.path.basename(os.path.normpath(folder)), len(files)))
            
            # load image 
            img = cv2.imdecode(np.fromfile(os.path.join(dir_image, img_name), np.uint8), cv2.IMREAD_COLOR)
            h, w, _ = img.shape
            
            # detect corner points
            points = get_graph_corner_points(img, k1_3=colors_corner['k1_3'], k2_3=colors_corner['k2_3'], k3_2=colors_corner['k3_2'], k4_1=colors_corner['k4_1'])
            
            # check if number of points is 4 (rectangle must have 4 corner points)
            err = ''
            if points.shape[0] == 4: 
                
                # trim off the outside of the edge lines
                img_graph = img[np.min(points[:,0]):np.max(points[:,0])+1, np.min(points[:,1]):np.max(points[:,1])+1] 
                
                # check if no non-graph objecects are in the inside of the graph
                if is_image_of_colors(img_graph, colors_inside):
                    
                    file_num_available += 1
                    
                    # search for y coordinates of redlines
                    pty_redline = set(np.argwhere(np.all(img_graph == (0, 0, 255), axis=-1))[:,0])
                    dy_per_px = 2 * red_line_value / (max(pty_redline) - min(pty_redline)) # value per 1px along y axis     
                    
                    # search for barplot
                    sc = classes.SearchColor(img=img_graph, color=(180, 119, 31), base_pty=min(pty_redline), base_valy=1.0, dy=dy_per_px, xlim=xlim)
                    x, y = sc.trans_px2val()
                    
                    # add results to pd
                    col_name = os.path.splitext(os.path.basename(img_name))[0]
                    if iter==0:
                        dfs = pd.DataFrame({'角度':np.arange(100), col_name:y})
                    else:
                        dfs = pd.concat([dfs, pd.DataFrame({col_name:y})], axis=1)
                        
                    queue.put(('graph', dfs, os.path.basename(os.path.normpath(folder))))
                    
                    """
                    # 値の精度を確認する
                    fig, ax = plt.subplots()
                    ax.plot(xcorrect, ycorrect, label='correct')
                    ax.plot(x, y, label='extracted2')
                    ax.legend()
                    plt.show()
                    """
                else:
                    err = 'Non-graph objects detected'
                    file_num_unavailable += 1
            else:
                err = 'Could not detect the corners'
                file_num_unavailable += 1
            
            # update progress bar
            progress += 100/tasks_num
            queue.put(('progress', progress, img_name, err, file_num_available, file_num_unavailable))
            
            # 1sec sleep after processing a last file
            if iter == len(files)-1:
                time.sleep(1)
            
        queue.put(('finished', ))
        
        # output df as a csv file
        fout = os.path.join(dir_out_folder, fname_out+'.csv')
        dfs.to_csv(fout, encoding='utf_8_sig', index=False)
        fout_list.append(fout)
        
    return fout_list
            
if __name__ == '__main__':
    pass
    