
import threading
import socket
import numpy as np
import cv2
import time
import jetson.inference
import jetson.utils

class VideoCamera(object):
    def __init__(self):
        self.set_model()
        self.video = cv2.VideoCapture(1)
        (self.grabbed, self.frame) = self.video.read()
        threading.Thread(target=self.update, args=()).start()

    def __del__(self):
        self.video.release()

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
        if self.buffers.overlay:
            self.net.Overlay(self.buffers.overlay, filter_mode=self.filter_mode) 
        if self.buffers.mask:
            self.net.Mask(self.buffers.mask, filter_mode=self.filter_mode)
        if self.buffers.composite:
            jetson.utils.cudaOverlay(self.buffers.overlay, self.buffers.composite, 0, 0)
            jetson.utils.cudaOverlay(self.buffers.mask, self.buffers.composite, self.buffers.overlay.width, 0)
        self.img_rander = jetson.utils.cudaToNumpy(self.buffers.output)
        self.mask_rander = jetson.utils.cudaToNumpy(self.buffers.mask)
        self.mask_rander = cv2.resize(self.mask_rander, dsize=(0, 0), fx=2, fy=2, interpolation=cv2.INTER_AREA)
        self.result = np.concatenate((self.frame, self.img_rander[:,:640,:], self.mask_rander), axis=0)
        self.floor_rander = self.mask_rander.copy()
        self.floor_rander[self.mask_rander[:,:,1]!=128] = 0
        self.floor_rander[self.mask_rander[:,:,0]!=0] = 0
        self.floor_rander[self.mask_rander[:,:,2]!=0] = 0
        self.floor_mask = self.floor_rander.reshape((240,640,3))
        self.get_score()
        self.do_jetbot()

    def get_score(self):
        self.height, self.width, self.channel = self.floor_mask.shape
        roi = [(0, self.height),(100, self.height/2), (self.width-100, self.height/2),(self.width, self.height),]
        self.floor_mask_roi = mask_roi(self.floor_mask[:,:,1], roi)
        self.n = np.sum(self.floor_rander)/(128*4)
        self.n_roi = np.sum(self.floor_mask_roi.reshape((self.height*self.width)))/(128*4)

    def get_frame(self):
        # image = self.frame
        image = self.result
        text = f'floor: {self.n:0.2f}, floor_roi: {self.n_roi:0.2f}, nstop: {self.n_roi<=2300}, direction: {self.direction}'
        image = cv2.putText(image, text, (5,15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA) 
        ret, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()

    def do_jetbot(self):
        self.left_power = (0.15)
        self.right_power = (0.145)
        self.floor_mask_roi_left = self.floor_mask_roi[:,:int(0.5*self.width)].reshape((int(self.height*self.width/2)))
        self.n_roi_l = np.sum(self.floor_mask_roi_left)/128
        if self.n_roi>2200:
            self.pw = 1.0
            self.direction = "Straight"
            # robot.set_motors(pw*left_power, pw*right_power)
        elif self.n_roi < 500:
            self.direction = "stop"
            # robot.stop()
        elif self.n_roi_l>self.n_roi-self.n_roi_l:
            self.pw = 0.75
            self.direction = "left"
            # robot.set_motors(-pw*left_power, pw*right_power)
        else:
            self.pw = 0.75
            self.direction = "right"
            # robot.set_motors(pw*left_power, -pw*right_power)

    def update(self):
        while True:
            (self.grabbed, self.frame) = self.video.read()
            self.get_seg()


class segmentationBuffers:
    def __init__(self, net):
        self.net = net
        self.mask = None
        self.overlay = None
        self.composite = None
        self.class_mask = None
        
        self.use_stats = True
        self.use_mask = True
        self.use_overlay = True
        self.use_composite = self.use_mask and self.use_overlay
        
        if not self.use_overlay and not self.use_mask:
            raise Exception("invalid visualize flags - valid values are 'overlay' 'mask' 'overlay,mask'")
             
        self.grid_width, self.grid_height = net.GetGridSize()	
        self.num_classes = net.GetNumClasses()

    @property
    def output(self):
        if self.use_overlay and self.use_mask:
            return self.composite
        elif self.use_overlay:
            return self.overlay
        elif self.use_mask:
            return self.mask
            
    def Alloc(self, shape, format):
        if self.overlay is not None and self.overlay.height == shape[0] and self.overlay.width == shape[1]:
            return

        if self.use_overlay:
            self.overlay = jetson.utils.cudaAllocMapped(width=shape[1], height=shape[0], format=format)

        if self.use_mask:
            mask_downsample = 2 if self.use_overlay else 1
            self.mask = jetson.utils.cudaAllocMapped(width=shape[1]/mask_downsample, height=shape[0]/mask_downsample, format=format) 

        if self.use_composite:
            self.composite = jetson.utils.cudaAllocMapped(width=self.overlay.width+self.mask.width, height=self.overlay.height, format=format) 

        if self.use_stats:
            self.class_mask = jetson.utils.cudaAllocMapped(width=self.grid_width, height=self.grid_height, format="gray8")
            self.class_mask_np = jetson.utils.cudaToNumpy(self.class_mask)
            
    def ComputeStats(self):
        if not self.use_stats:
            return
            
        # get the class mask (each pixel contains the classID for that grid cell)
        self.net.Mask(self.class_mask, self.grid_width, self.grid_height)

        # compute the number of times each class occurs in the mask
        class_histogram, _ = np.histogram(self.class_mask_np, self.num_classes)

        print('grid size:   {:d}x{:d}'.format(self.grid_width, self.grid_height))
        print('num classes: {:d}'.format(self.num_classes))

        print('-----------------------------------------')
        print(' ID  class name        count     %')
        print('-----------------------------------------')

        for n in range(self.num_classes):
            percentage = float(class_histogram[n]) / float(self.grid_width * self.grid_height)
            print(' {:>2d}  {:<18s} {:>3d}   {:f}'.format(n, self.net.GetClassDesc(n), class_histogram[n], percentage)) 
            
def mask_roi(img_th, roi):
    mask = np.zeros_like(img_th)
    cv2.fillPoly(mask, np.array([roi], np.int32), 255)
    masked_image = cv2.bitwise_and(img_th, mask)
    return masked_image