import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from ttkwidgets import CheckboxTreeview
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import japanize_matplotlib
import os
from PIL import Image, ImageTk
import queue
import threading
import numpy as np
import seaborn as sns
import pandas as pd
import extract

# Params set by setting TAB
dir_out = 'results'
fname_out = 'data'
red_line_value = 1.0
xlim = [0, 100]
save_image_frag = True
dx_ticks = 5
dy_ticks = 0.1

class Application(ttk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.pack(fill=tk.BOTH, expand=True)
        
        self.queue = queue.Queue()
        self.csv_out = []
        self.tasks_num = 0
        self.progress = 0.0
        self.stop_thread = False
        self.check_queue_flag = True
        self.fig_g, self.ax_g = plt.subplots()
        self.thread = None
        self.dashboard_csv_data = pd.DataFrame()
        self.cmap = matplotlib.colors.LinearSegmentedColormap.from_list('', ['#1E00B3', '#D4CDFF', 'white', '#FCCCE4', '#CC1470'])
        
        self.notebook = ttk.Notebook(self)
        self.main_frame = ttk.PanedWindow(self.notebook, orient='horizontal')
        self.dashboard_frame = ttk.Frame(self.notebook)
        self.setting_frame = ttk.Frame(self.notebook)
        
        self.notebook.add(self.main_frame, text='Main')
        self.notebook.add(self.dashboard_frame, text='Dashboard')
        self.notebook.add(self.setting_frame, text='Settings')
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.create_main_frame()
        self.create_dashboard_frame()
        self.master.after(300, lambda: self.main_frame.sashpos(0, 200))
        self.master.protocol('WM_DELETE_WINDOW', self.on_window_close)
        
    def create_main_frame(self):
        # mainframe
        left_frame = ttk.Frame(self.main_frame)
        right_frame = ttk.Frame(self.main_frame)
        self.main_frame.add(left_frame)
        self.main_frame.add(right_frame)
        
        # treeframe
        tree_frame = ttk.Frame(left_frame)
        tree_frame.pack(side='top', fill='both', expand=True)
        self.folder_tree = CheckboxTreeview(tree_frame)
        self.folder_tree.grid(row=0, column=0, sticky='nsew', padx=0, pady=0)
        
        # scrollbar
        self.scrollbar_y = ttk.Scrollbar(tree_frame, orient='vertical', command=self.folder_tree.yview)
        self.scrollbar_y.grid(row=0, column=1, sticky='ns')
        self.folder_tree.configure(yscrollcommand=self.scrollbar_y.set)
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        self.populate_tree(os.getcwd())
        
        # style of separators
        sep_style = ttk.Style()
        sep_style.configure('TSeparator', background='blue')
        
        # buttons
        self.button_frame = ttk.Frame(right_frame)
        self.button_frame.pack(side='top', fill='x')
        self.radio_bar = tk.BooleanVar()
        self.radio_bar.set(False)
        self.radio_button1 = ttk.Radiobutton(self.button_frame, text='Save Images', variable=self.radio_bar, value=True)
        self.radio_button1.pack(side='left', padx=(10,0), pady=(10,10))
        self.radio_button2 = ttk.Radiobutton(self.button_frame, text='Do not save Images', variable=self.radio_bar, value=False)
        self.radio_button2.pack(side='left', padx=(10,0), pady=(10,10))
        self.execute_button = ttk.Button(self.button_frame, text='Execute', command=self.on_execute_button_clicked, style='Accent.TButton', width=8)
        self.execute_button.pack(side='right', padx=20, pady=(10,10))
        
        # dashboard (in mainframe)
        self.main_dashboard_frame = ttk.Frame(right_frame)
        self.main_dashboard_frame.pack(side='top', fill='both', expand=True)
        sep1 = ttk.Separator(self.main_dashboard_frame, orient='horizontal', style='TSeparator')
        sep1.pack(side='top', fill='both', pady=(5,0))
        self.main_dashboard_right_frame = ttk.Frame(self.main_dashboard_frame)
        self.main_dashboard_right_frame.pack(side='right', fill='both', expand=True, padx=10)
        
        # graph settings
        self.dpi = 100.0
        self.width_in_pixels = 420
        self.height_in_pixels = 245
        self.figsize = (self.width_in_pixels/self.dpi, self.height_in_pixels/self.dpi)
        self.fig = plt.figure(figsize=self.figsize, dpi=self.dpi)
        self.fig.subplots_adjust(left=0.13, right=0.955)
        self.ax = self.fig.add_subplot(1,1,1)
        
        # initial graph
        self.ax.set_xlim(xlim)
        self.ax.set_ylim([red_line_value*(-1.2), red_line_value*1.2])
        for spine in self.ax.spines.values():
            spine.set_visible(False)
        self.ax.grid(alpha=0.3)
        self.ax.tick_params(labelsize=8)
        self.image_frame = ttk.Frame(self.main_dashboard_right_frame)
        self.image_frame.pack(side='top', fill='both', padx=10)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.image_frame)
        self.canvas.get_tk_widget().pack(side='top', fill='both', expand=1)
        
        # the numbers of executed images
        self.main_fileinfo_frame = ttk.Frame(self.main_dashboard_right_frame)
        self.main_fileinfo_frame.pack(side='top', fill='both', pady=(20,0), expand=True)
        self.main_fileinfo_frame.grid_columnconfigure(1, weight=1)
        
        self.main_dashboard_frame_bar_tot_label1 = ttk.Label(self.main_fileinfo_frame, text='', width=5, font=('Arial', 8), anchor='e')
        self.main_dashboard_frame_bar_tot_label1.grid(row=0, column=0, padx=(10, 10), pady=(10, 0))
        self.main_dashboard_frame_bar_tot = ttk.Progressbar(self.main_fileinfo_frame)
        self.main_dashboard_frame_bar_tot.grid(row=0, column=1, sticky='nsew', padx=(10, 28), pady=(10, 0))
        self.main_dashboard_frame_bar_tot_label2 = ttk.Label(self.main_fileinfo_frame, text='Total', font=('Arial', 8), anchor='e')
        self.main_dashboard_frame_bar_tot_label2.grid(row=1, column=1, padx=(10, 10), pady=(0, 10), sticky='w')
        
        self.main_dashboard_frame_bar_good_label1 = ttk.Label(self.main_fileinfo_frame, text='', width=5, font=('Arial', 8), anchor='e')
        self.main_dashboard_frame_bar_good_label1.grid(row=2, column=0, padx=(10, 10), pady=(10, 0))
        self.main_dashboard_frame_bar_good = ttk.Progressbar(self.main_fileinfo_frame)
        self.main_dashboard_frame_bar_good.grid(row=2, column=1, sticky='nsew', padx=(10, 28), pady=(10, 0))
        self.main_dashboard_frame_bar_good_label2 = ttk.Label(self.main_fileinfo_frame, text='Available', font=('Arial', 8), anchor='e')
        self.main_dashboard_frame_bar_good_label2.grid(row=3, column=1, padx=(10, 10), pady=(0, 10), sticky='w')
        
        self.main_dashboard_frame_bar_bad_label1 = ttk.Label(self.main_fileinfo_frame, text='', width=5, font=('Arial', 8), anchor='e')
        self.main_dashboard_frame_bar_bad_label1.grid(row=4, column=0, padx=(10, 10), pady=(10, 0))
        self.main_dashboard_frame_bar_bad = ttk.Progressbar(self.main_fileinfo_frame)
        self.main_dashboard_frame_bar_bad.grid(row=4, column=1, sticky='nsew', padx=(10, 28), pady=(10, 0))
        self.main_dashboard_frame_bar_bad_label2 = ttk.Label(self.main_fileinfo_frame, text='Unavailable', font=('Arial', 8), anchor='e')
        self.main_dashboard_frame_bar_bad_label2.grid(row=5, column=1, padx=(10, 10), pady=(0, 0), sticky='w')
        
        # information of files
        self.main_dashboard_left_frame = ttk.Frame(self.main_dashboard_frame)
        self.main_dashboard_left_frame.pack(side='left', fill='both')
        self.main_dashboard_left_frame_scrollbar = ttk.Scrollbar(self.main_dashboard_left_frame)
        self.main_dashboard_left_frame_scrollbar.pack(side='right', fill='y', pady=10)
        tv_custom_style = ttk.Style()
        tv_custom_style.configure('Custom.Treeview', font=('Arial', 8))
        self.main_dashboard_left_frame_treeview = ttk.Treeview(
            self.main_dashboard_left_frame,
            style='Custom.Treeview',
            selectmode='browse',
            yscrollcommand=self.main_dashboard_left_frame_scrollbar.set,
            columns=(1, 2),
            height=9,
            show='headings' # hide row at #0 
        )
        self.main_dashboard_left_frame_treeview.pack(side='left', fill='both', padx=(12,0), pady=10)
        self.main_dashboard_left_frame_scrollbar.config(command=self.main_dashboard_left_frame_treeview.yview)
        self.main_dashboard_left_frame_treeview.column(1, anchor='w', width=150, stretch=False)
        self.main_dashboard_left_frame_treeview.column(2, anchor='w', width=172, stretch=False)
        self.main_dashboard_left_frame_treeview.heading(1, anchor='w', text='Image')
        self.main_dashboard_left_frame_treeview.heading(2, anchor='w', text='Error')
        
        # progressbar
        self.progress_frame = ttk.Frame(right_frame)
        self.progress_frame.pack(side='top', fill='x', padx=(3,17), pady=(8,10))
        self.console_output1 = ttk.Label(self.progress_frame, text='Processing :', foreground='#66B3FF', font=('Arial', 8))
        self.console_output1.grid(row=0, column=0, sticky='w', padx=(10,10))
        self.console_output2 = ttk.Label(self.progress_frame, text=f'{self.progress:.0f}%', foreground='#0080FF', font=('Arial', 12, 'bold'))
        self.console_output2.grid(row=0, column=1, sticky='w', padx=(10,10))
        self.progress_bar = ttk.Progressbar(self.progress_frame)
        self.progress_bar.grid(row=1, column=0, columnspan=2, sticky='ew', padx=(10,10), pady=(5,15))
        self.progress_frame.columnconfigure(0, weight=1)
        
        self.master.after(100, self.adjust_tree_width)
        
    def populate_tree(self, path, parent_node=''):
        for p in sorted(os.listdir(path)):
            abspath = os.path.join(path, p)
            oid = self.folder_tree.insert(parent_node, 'end', text=p, iid=abspath, open=False)
            
            if os.path.isdir(abspath):
                self.populate_tree(abspath, oid)
                self.folder_tree.column('#0', stretch=True)
    
    def adjust_tree_width(self):
        self.folder_tree.column('#0', width=self.scrollbar_y.winfo_x())
    
    def on_execute_button_clicked(self):
        style = ttk.Style()
        style.configure('Toggle.TButton', font=('Arial', 8))
        self.execute_button.config(text='Cancel', command=self.on_cancel_button_clicked, style='Toggle.TButton', width=8)
        checked_paths = self.get_checked_paths()
        self.thread = threading.Thread(target=self.run_main, args=(checked_paths, dir_out, red_line_value, xlim, fname_out))
        self.thread.start()
        self.check_queue_flag = True
        self.after(100, self.check_queue)
        
    def on_cancel_button_clicked(self):
        self.execute_button.config(text='Execute', command=self.on_execute_button_clicked, style='Accent.TButton')
        self.stop_thread = True
        self.check_queue_flag = False
        self.tasks_num = 0
        self.progress = 0.0
        self.console_output1['text'] = 'Processing : '
        self.console_output2['text'] = f'{self.progress:.0f}%'
        self.progress_bar['value'] = self.progress
        
        self.ax.clear()
        self.ax.set_xlim(xlim)
        self.ax.set_ylim([red_line_value*(-1.2), red_line_value*1.2])
        self.ax.grid(alpha=0.3)
        self.canvas.draw()
        self.reset_main_dashboard_frame_bar()
        self.reset_main_treeview_columns()
        
    def stop_requested(self):
        return self.stop_thread
        
    def get_checked_paths(self):
        return self.folder_tree.get_checked()
    
    def run_main(self, checked_paths, dir_out, red_line_value, xlim, fname_out):
        self.stop_thread = False
        self.tasks_num = 0
        self.progress = 0.0
        self.csv_out = extract.main(self.queue, checked_paths, dir_out, red_line_value, xlim, fname_out, self.radio_bar.get(), self)
        
        # make graphs from csv data
        if self.radio_bar.get():
            self.save_images()
        
        # adjust progress bars 
        self.progress = 100.0
        self.console_output2['text'] = f'{self.progress:.0f} %'
        self.progress_bar['value'] = self.progress

        # reset execute button
        self.execute_button.config(text='Execute', command=self.on_execute_button_clicked, style='Accent.TButton')
        
        # reset dashborad in mainframe
        self.reset_main_treeview_columns()
        self.reset_main_dashboard_frame_bar()
    
    def reset_main_treeview_columns(self):
        for i in self.main_dashboard_left_frame_treeview.get_children():
            self.main_dashboard_left_frame_treeview.delete(i)
    
    def reset_main_dashboard_frame_bar(self):
        self.main_current_filenum = 0
        self.main_dashboard_frame_bar_tot_label1['text'] = ''
        self.main_dashboard_frame_bar_good_label1['text'] = ''
        self.main_dashboard_frame_bar_bad_label1['text'] = ''
        self.main_dashboard_frame_bar_tot['value'] = 0
        self.main_dashboard_frame_bar_good['value'] = 0
        self.main_dashboard_frame_bar_bad['value'] = 0
        
    def save_images(self):
        for path_csv in self.csv_out:
            if os.path.exists(path_csv):
                dir_name, file_name = os.path.split(path_csv)
                dfx = pd.read_csv(path_csv, usecols=['角度'], dtype=float)
                df_columns = pd.read_csv(path_csv, nrows=1, encoding='utf_8_sig').columns.tolist().remove('角度') # y columns
                
                for col in df_columns:
                    self.console_output1['text'] = f'Saving : {dir_name}\{col}_result.png'
                    dfy = pd.read_csv(path_csv, usecols=[col], dtype=float)
                    dxs = np.insert(np.diff(dfx.values.reshape(-1,).tolist()), -1, 100.0-dfx.values.reshape(-1,).tolist()[-1]) # width for barplot 
                    
                    self.ax_g.clear()
                    self.ax_g.bar(dfx.values.reshape(-1,), dfy.values.reshape(-1,), align='edge', width=dxs)
                    self.ax_g.set_xlim(xlim)
                    self.ax_g.set_ylim([red_line_value*(-1.2), red_line_value*1.2])
                    self.ax_g.set_xticks(np.arange(xlim[0], xlim[1]+dx_ticks*0.1, dx_ticks))
                    self.ax_g.set_yticks(np.arange(red_line_value*(-1.2), red_line_value*1.2+dy_ticks))
                    self.ax_g.hlines(red_line_value, color='red', xmin=xlim[0], xmax=xlim[1])
                    self.ax_g.hlines(red_line_value*(-1.0), color='red', xmin=xlim[0], xmax=xlim[1])
                    self.ax_g.grid(alpha=0.3)
                    self.fig_g.savefig(os.path.join(dir_name, col+'_result.png'))
                    
                    # update the progress bar
                    self.progress += 100/self.tasks_num
                    self.console_output2['text'] = f'{self.progress:.0f}%'
                    self.progress_bar['value'] = self.progress
                    
    def check_queue(self):
        if self.check_queue_flag and self.winfo_exists():
            try:
                item = self.queue.get(0)
                if item[0] == 'fname':
                    self.console_output1['text'] = 'Processing : {} >> {}'.format(item[2], item[1])
                    self.main_current_filenum = int(item[3])
                    self.main_dashboard_frame_bar_tot_label1['text'] = f'{self.main_current_filenum}/{self.main_current_filenum}'
                    self.main_dashboard_frame_bar_tot['value'] = 100
                
                elif item[0] == 'graph':
                    dfs = item[1]
                    
                    # list of y columns
                    cols = dfs.columns.tolist()
                    cols.remove('角度')
                    
                    # replots   
                    self.ax.clear()
                    for i, col in enumerate(cols):
                        self.ax.plot(dfs['角度'].values, dfs[col].values, c='#007FFF', alpha=0.05)
                    self.ax.plot(dfs['角度'].values, dfs.iloc[:,-1], c='#007FFF', lw=1)
                    
                    # update the graph after setting graph layouts
                    self.ax.set_xlim(xlim)
                    self.ax.set_ylim([red_line_value*(-1.2), red_line_value*1.2])
                    for spine in self.ax.spines.values():
                        spine.set_visible(False)
                    self.ax.grid(alpha=0.3)
                    self.canvas.draw()

                elif item[0] == 'progress':
                    self.progress = float(item[1])
                    self.console_output2['text'] = f'{self.progress:.0f}%'
                    self.progress_bar['value'] = self.progress
                    self.main_dashboard_left_frame_treeview.insert('', 'end', values=(item[2], item[3]))
                    fnum_available = int(item[4])
                    fnum_unavailable = int(item[5])
                    self.main_dashboard_frame_bar_good_label1['text'] = f'{fnum_available}/{self.main_current_filenum}'
                    self.main_dashboard_frame_bar_bad_label1['text'] = f'{fnum_unavailable}/{self.main_current_filenum}'
                    if self.main_current_filenum != 0:
                        self.main_dashboard_frame_bar_good['value'] = fnum_available / self.main_current_filenum * 100
                        self.main_dashboard_frame_bar_bad['value'] = fnum_unavailable / self.main_current_filenum * 100
                
                elif item[0] == 'tasks_num':
                    self.tasks_num = int(item[1])
            except queue.Empty:
                pass
            finally:
                self.after(100, self.check_queue)
    
    def create_dashboard_frame(self):
        # mainframe
        left_frame2 = ttk.Frame(self.dashboard_frame, width=410)
        left_frame2.pack(side='left', fill='both')
        right_frame2 = ttk.Frame(self.dashboard_frame)
        right_frame2.pack(side='right', fill='both', expand=True, padx=(30,0))
        
        # select folder frame
        self.folder_frame = ttk.Frame(left_frame2)
        self.folder_frame.pack(fill='x', padx=5, pady=5)
        sep_dashbord1 = ttk.Separator(self.folder_frame, orient='horizontal')
        sep_dashbord1.pack(side='bottom', fill='both', pady=(5,5))
        self.browse_button = ttk.Button(self.folder_frame, text='Browse', command=self.select_csv, width=6)
        self.browse_button.pack(side='right', padx=5, pady=5)
        self.dashboard_frame = ttk.Label(self.folder_frame, text='Select a csv data', width=20, font=('Arial', 10), anchor='w')
        self.dashboard_frame.pack(side='bottom', fill='both', pady=(5,5))
        
        # the numbers of ok/poor datas
        self.datainfo_frame = ttk.Frame(left_frame2)
        self.datainfo_frame.pack(fill='x', padx=5, pady=5)
        self.datainfo_frame.grid_columnconfigure(1, weight=1)
        
        self.total_data_label = ttk.Label(self.datainfo_frame, text='', width=5, font=('Arial', 10), anchor='e')
        self.total_data_label.grid(row=1, column=0, padx=(10,10), pady=(10,0))
        self.total_data_num_bar = ttk.Progressbar(self.datainfo_frame)
        self.total_data_num_bar.grid(row=1, column=1, sticky='nsew', padx=(10,20), pady=(10,0))
        self.total_data_label2 = ttk.Label(self.datainfo_frame, text='Total Data', font=('Arial', 8))
        self.total_data_label2.grid(row=2, column=1, padx=(10,10), sticky='w')
        
        self.good_data_label = ttk.Label(self.datainfo_frame, text='', width=5, font=('Arial', 10), anchor='e')
        self.good_data_label.grid(row=3, column=0, padx=(10,10), pady=(10,0))
        self.good_data_num_bar = ttk.Progressbar(self.datainfo_frame)
        self.good_data_num_bar.grid(row=3, column=1, sticky='nsew', padx=(10,20), pady=(20,0))
        self.good_data_label2 = ttk.Label(self.datainfo_frame, text='Good', font=('Arial', 8))
        self.good_data_label2.grid(row=4, column=1, padx=(10,10), sticky='w')
        
        self.poor_data_label = ttk.Label(self.datainfo_frame, text='', width=5, font=('Arial', 10), anchor='e')
        self.poor_data_label.grid(row=5, column=0, padx=(10,10), pady=(10,0))
        self.poor_data_num_bar = ttk.Progressbar(self.datainfo_frame)
        self.poor_data_num_bar.grid(row=5, column=1, sticky='nsew', padx=(10,20), pady=(20,0))
        self.poor_data_label2 = ttk.Label(self.datainfo_frame, text='Poor', font=('Arial', 8))
        self.poor_data_label2.grid(row=6, column=1, padx=(10,10), sticky='w')
        
        # treeview
        self.treeview_frame = ttk.Frame(left_frame2, width=410)
        self.treeview_frame.pack(side='left', fill='both', padx=(10,10), pady=(10,10))
        self.treeview_frame.pack_propagate(False) # fix the frame size
        self.treeview_scrollbar = ttk.Scrollbar(self.treeview_frame)
        self.treeview_scrollbar.pack(side='right', fill='y')
        self.dashboard_treeview = ttk.Treeview(
            self.treeview_frame,
            selectmode='browse',
            yscrollcommand=self.treeview_scrollbar.set,
            columns=(1,2,3,4,5,6),
            height=10,
            show='headings' # hide row at #0 
        )
        self.dashboard_treeview.pack(side='left', fill='both', expand=True, padx=0, pady=10)
        self.treeview_frame.pack_propagate(False) # fix the frame size
        self.treeview_scrollbar.config(command=self.dashboard_treeview.yview)
        
        self.dashboard_treeview.column(1, anchor='w', width=35, stretch=False)
        self.dashboard_treeview.column(2, anchor='w', width=135, stretch=False)
        self.dashboard_treeview.column(3, anchor='w', width=55, stretch=False)
        self.dashboard_treeview.column(4, anchor='w', width=55, stretch=False)
        self.dashboard_treeview.column(5, anchor='w', width=55, stretch=False)
        self.dashboard_treeview.column(6, anchor='w', width=55, stretch=False)        
        self.dashboard_treeview.heading(1, text='Id', anchor='w')
        self.dashboard_treeview.heading(2, text='File name', anchor='w')
        self.dashboard_treeview.heading(3, text='Mean', anchor='w')
        self.dashboard_treeview.heading(4, text='Std', anchor='w')
        self.dashboard_treeview.heading(5, text='Max', anchor='w')
        self.dashboard_treeview.heading(6, text='Min', anchor='w')
        
        # lineplot
        self.lineplot_frame = ttk.Frame(right_frame2, height=250, width=550)
        self.lineplot_frame.pack(side='top', fill='both', expand=True, padx=5, pady=5)
        self.dpi_lineplot = 100
        self.lineplot_width_in_pixels = 500
        self.lineplot_height_in_pixels = 250
        self.figsize_lineplot = (self.lineplot_width_in_pixels/self.dpi_lineplot, self.lineplot_height_in_pixels/self.dpi_lineplot)
        self.fig_lineplot = plt.figure(figsize=self.figsize_lineplot, dpi=self.dpi_lineplot)
        self.ax_lineplot = self.fig_lineplot.add_subplot(1,1,1)
        self.ax_lineplot.set_xticks([])
        self.ax_lineplot.set_xlabel('Id')
        self.ax_lineplot.set_ylim([red_line_value*(-1.2), red_line_value*1.2])
        self.ax_lineplot.tick_params(labelsize=8)
        for spine in self.ax_lineplot.spines.values():
            spine.set_visible(False)
        self.fig_lineplot.subplots_adjust(left=0.1, right=0.93, bottom=0.15, top=0.95)
        self.canvas_lineplot = FigureCanvasTkAgg(self.fig_lineplot, master=self.lineplot_frame)
        self.canvas_lineplot.get_tk_widget().pack(side='top', fill='both', expand=1)
        
        # heatmap
        self.heatmap_frame = ttk.Frame(right_frame2, width=550)
        self.heatmap_frame.pack(side='right', fill='both', expand=True, padx=0, pady=5)
        self.dpi_heatmap = 100
        self.heatmap_width_in_pixels = 500
        self.heatmap_height_in_pixels = 300
        self.figsize_heatmap = (self.heatmap_width_in_pixels/self.dpi_heatmap, self.heatmap_height_in_pixels/self.dpi_heatmap)
        self.fig_heatmap = plt.figure(figsize=self.figsize_heatmap, dpi=self.dpi_heatmap)
        self.fig_heatmap.subplots_adjust(left=0.105, right=0.995, bottom=0.13, top=0.95)
        self.ax_heatmap = self.fig_heatmap.add_subplot(1,1,1)
        heatmap_ = pd.DataFrame(0, index=np.arange(1), columns=np.arange(1))
        self.ax_heatmap = sns.heatmap(heatmap_, ax=self.ax_heatmap, cmap=self.cmap, vmax=red_line_value, vmin=red_line_value*(-1.0))
        self.cbar = self.ax_heatmap.collections[0].colorbar
        self.cbar.ax.tick_params(labelsize=8)
        self.cbar.set_ticks([red_line_value*(-1.0), 0, red_line_value])
        self.ax_heatmap.set_xticks([0, 50, 100])
        self.ax_heatmap.set_xticklabels(['0', '50', '100'], rotation=0)
        self.ax_heatmap.set_xlabel('')
        self.ax_heatmap.set_yticks([])
        self.ax_heatmap.set_ylabel('Id')
        self.ax_heatmap.tick_params(labelsize=8)
        self.canvas_heatmap = FigureCanvasTkAgg(self.fig_heatmap, master=self.heatmap_frame)
        self.canvas_heatmap.get_tk_widget().pack(side='top', fill='both', expand=True)
        
    def select_csv(self):
        filename = filedialog.askopenfilename(initialdir=dir_out, filetypes=[('CSV Files', '*.csv')])
        if filename:
            self.dashboard_csv_data = pd.read_csv(filename, index_col='角度')
            described_data = self.dashboard_csv_data.describe().loc[['mean', 'std', 'max', 'min'], :]
            self.dashboard_frame['text'] = os.path.relpath(filename)
            
            # reset the treeview
            for i in self.dashboard_treeview.get_children():
                self.dashboard_treeview.delete(i)   
            
            # insert described data into the treeview
            for i, (fname, col) in enumerate(described_data.items()):
                stats_vals = ['{:.3f}'.format(val) for val in col.values.tolist()]
                self.dashboard_treeview.insert('', 'end', values=[str(i), fname] + stats_vals, iid=None)
            
            # progress bar
            total_datas_num = len(described_data.columns.tolist())
            poor_data_num = (described_data.apply(lambda x: x['max'] >= red_line_value or x['min'] <= red_line_value*(-1.0), axis=0)).sum()
            self.total_data_label['text'] = f'{total_datas_num}/{total_datas_num}'
            self.total_data_num_bar['value'] = 100
            self.good_data_label['text'] = f'{total_datas_num-poor_data_num}/{total_datas_num}'
            self.good_data_num_bar['value'] = (total_datas_num-poor_data_num) / total_datas_num * 100
            self.poor_data_label['text'] = f'{poor_data_num}/{total_datas_num}'
            self.poor_data_num_bar['value'] = poor_data_num / total_datas_num * 100

            # lineplot
            self.ax_lineplot.clear()
            lpx_ = np.arange(len(described_data.columns.tolist()))
            self.ax_lineplot.errorbar(lpx_, described_data.loc['mean', :], yerr=described_data.loc['std', :], fmt='o-', markersize=3, elinewidth=1, c='#0036D9', ecolor='#6D88D9')
            self.ax_lineplot.set_xticks(lpx_[::5])
            self.ax_lineplot.set_xlabel('Id')
            self.ax_lineplot.set_ylim([red_line_value*(-1.2), red_line_value*1.2])
            self.ax_lineplot.grid(alpha=0.3)
            self.ax_lineplot.tick_params(labelsize=8)
            for spine in self.ax_lineplot.spines.values():
                spine.set_visible(False)
            self.canvas_lineplot.draw()
            
            # heatmap
            self.dashboard_csv_data = self.dashboard_csv_data.T
            self.cbar.remove()
            self.ax_heatmap.clear()
            self.ax_heatmap = sns.heatmap(self.dashboard_csv_data, cmap=self.cmap, vmax=red_line_value, vmin=red_line_value*(-1.0))
            self.cbar = self.ax_heatmap.collections[0].colorbar
            self.cbar.ax.tick_params(labelsize=8)
            self.ax_heatmap.set_xticks([0, 50, 100])
            self.ax_heatmap.set_xticklabels(['0', '50', '100'], rotation=0)
            self.ax_heatmap.set_yticks([i for i in np.arange(0, len(self.dashboard_csv_data.index.tolist()), 5)])
            self.ax_heatmap.set_yticklabels([str(i) for i in np.arange(0, len(self.dashboard_csv_data.index.tolist()), 5)])
            self.ax_heatmap.set_xlabel('')
            self.ax_heatmap.set_ylabel('Id')
            self.ax_heatmap.tick_params(labelsize=8)
            self.cbar.set_ticks([red_line_value*(-1.0), 0, red_line_value])
            self.canvas_heatmap.draw()
            
    def on_window_close(self):
        self.stop_thread = True
        self.check_queue_flag = False
        plt.close('all')
        self.master.destroy()

root = tk.Tk()
root.geometry('1050x600')
root.tk.call('source', './Azure-ttk-theme-main/azure.tcl')
root.tk.call('set_theme', 'light')

app = Application(master=root)
app.mainloop()