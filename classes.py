import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import datetime
import cv2
import easyocr
import itertools
import statistics

class SearchColor:
    def __init__(self, img = None, color = (0, 0, 0), base_pty=0, base_valy=0.0, dy=0.0, xlim=[]):
        self.img = img             # 検索する画像
        self.color = color         # 検索する色(RGB)
        self.base_pty = base_pty   # 基準となるyの位置
        self.base_valy = base_valy # 基準となるyの値
        self.dy = dy               # 1pxあたりのyの値
        self.xlim = xlim           # xの範囲
    
    def _set_yrange_along_xaxis(self):
        # カラーが一致するピクセルを取得
        self.__pt_color = np.argwhere(np.all(self.img == self.color, axis=-1))[:,:2]
        
        # 色の存在するx位置を取得する
        self.__ptx = np.unique(self.__pt_color[:,1])
        self.__ptx = self.__ptx[np.where(np.diff(self.__ptx)==1)]
        
        # 各x座標ごとに棒グラフの端の座標を取得する
        self.__pty = np.array([[np.min(self.__pt_color[self.__pt_color[:,1] == x][:,0]), np.max(self.__pt_color[self.__pt_color[:,1] == x][:,0])] for x in self.__ptx])
        
    def trans_px2val(self):
        # 棒グラフの上下端の座標をセット
        self._set_yrange_along_xaxis()
        
        # yをピクセルから値に変換し、絶対値の大きなものを取得
        ys = [self.base_valy + (self.base_pty-y) * self.dy for y in self.__pty]
        self.__y_absmax = np.array([y[np.argmax(np.abs(y))] for y in ys])       
        
        # xをピクセルから値に線形変換する
        a = (self.xlim[1]-self.xlim[0]) / (self.img.shape[1] - 4) # 画像の枠線4px分を除いたxの範囲をxlimに対応させる
        b = self.xlim[0] - a * np.min(self.__ptx)
        self.__x = a * self.__ptx + b
        
        # x=0~99の範囲で間隔が1でまびく
        ind_thinout = [np.argmin(np.abs(self.__x - _x)) for _x in np.arange(100)]
        x = self.__x[ind_thinout]
        y = self.__y_absmax[ind_thinout]
        
        return x, y 
    
    def set_img(self, img):
        self.img = img
    
    def set_color(self, color):
        self.color = color
    
    def set_base_pty(self, base_pty):
        self.base_pty = base_pty
        
    def set_base_val(self, base_valy):
        self.base_valy = base_valy
    
    def set_dy(self, dy):
        self.dy = dy
        
    def set_xlim(self, xlim):
        self.xlim = xlim
    
    