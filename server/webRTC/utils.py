import threading
import socket
import numpy as np
import time
import cv2
import jetson.inference
import jetson.utils
from jetbot import Robot

class VideoCamera(object):
    def __init__(self):
        # jetbot setting
        self.robot = Robot()
        self.move = False
        self.n = 0.0
        self.direction = ""
        self.pw = 0.8
        self.left_power = (0.15)
        self.right_power = (0.145)
        # deep learning model setting
        self.set_model()
        # camera setting
        self.cap = cv2.VideoCapture(1)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # width
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240) # height
        self.cap.set(cv2.CAP_PROP_FPS, 10)
        (self.grabbed, self.frame) = self.cap.read()
        # thread
        threading.Thread(target=self.update, args=()).start()

    def __del__(self):
        self.cap.release()
        self.robot.stop()

    def set_model(self):
        self.model = "fcn-resnet18-sun"
        self.overlay_Alpha = 150
        self.filter_mode = "linear" # choices=["point", "linear"]
        self.ignore_class = "toilet"
        self.net = jetson.inference.segNet(self.model)
        self.net.SetOverlayAlpha(self.overlay_Alpha)
        self.buffers = segmentationBuffers(self.net)

    def get_seg(self):
        img = jetson.utils.cudaFromNumpy(self.frame)
        self.buffers.Alloc(img.shape, img.format)
        self.net.Process(img, ignore_class=self.ignore_class)
        self.net.Overlay(self.buffers.overlay, filter_mode=self.filter_mode) 
        self.net.Mask(self.buffers.mask, filter_mode=self.filter_mode)

        self.img_rander = jetson.utils.cudaToNumpy(self.buffers.overlay)
        self.mask_rander = jetson.utils.cudaToNumpy(self.buffers.mask)

        self.floor_rander = self.mask_rander[:,:,1].copy()
        self.floor_rander[self.floor_rander[:,:]!=128] = 0
        self.floor_rander[self.floor_rander[:,:]==128] = 1
        self.floor_rander = self.floor_rander.reshape((120,320))
        self.floor_mask = np.concatenate((self.floor_rander[:,:160], self.floor_rander[:,160:]), axis=0)

    def get_score(self):
        self.n = np.sum(self.floor_mask)
        self.n_left = np.sum(self.floor_mask[:,:80])
        self.n_right = self.n - self.n_left

    def update_jetbot(self):
        if self.move:
            if self.n > 2200:
                self.direction = "Straight"
                self.robot.set_motors(self.pw*self.left_power, self.pw*self.right_power)
            elif self.n < 500:
                self.direction = "stop"
                self.robot.stop()
            elif self.n_left > self.n_right:
                self.direction = "left"
                self.robot.set_motors(-0.75*self.left_power, 0.75*self.right_power)
            elif self.n_left < self.n_right:
                self.direction = "right"
                self.robot.set_motors(0.75*self.left_power, -0.75*self.right_power)
            else:
                self.direction = "stop"
                self.robot.stop()
        else:
            self.robot.stop()

    def get_frame(self):
        image = self.img_rander
        text = f'floor: {self.n:0.2f}, direction: {self.direction}'
        image = cv2.putText(image, text, (5,15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA) 
        ret, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()

    def update(self):
        while True:
            start = time.time()
            (self.grabbed, self.frame) = self.cap.read()
            self.get_seg()
            self.get_score()
            self.update_jetbot()
            end = time.time() - start
            if end < 0.1:
                time.sleep(0.1-end)
            print("time :", end, ", total: ", time.time() - start)  # check time 
            
class segmentationBuffers:
    def __init__(self, net):
        self.net = net
        self.mask = None
        self.overlay = None
        self.mask_downsample = 2
            
    def Alloc(self, shape, format):
        self.overlay = jetson.utils.cudaAllocMapped(width=shape[1], height=shape[0], format=format)
        self.mask = jetson.utils.cudaAllocMapped(width=shape[1]/self.mask_downsample, height=shape[0]/self.mask_downsample, format=format) 