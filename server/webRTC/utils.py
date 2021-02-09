import threading
import socket
import numpy as np
import time
import cv2
import sys
import jetson.inference
import jetson.utils
from jetbot import Robot

class VideoCamera(object):
    def __init__(self):
        # jetbot setting
        self.robot = Robot()
        self.avoidance_status = False
        self.cruise_status = False
        self.move_arrow = 'stop'
        self.n = 0.0
        self.direction = ""
        self.pw = 1
        self.pw_c = 1.5
        self.left_power = (0.15)
        self.right_power = (0.145)
        # deep learning model setting
        self.set_detect_model()
        self.set_seg_model()
        self.roi = [(0, 120),(80, 60),(160, 120),]
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

    def set_seg_model(self):
        self.segNet = jetson.inference.segNet("fcn-resnet18-sun")
        self.segNet.SetOverlayAlpha(150)
        self.buffers = segmentationBuffers(self.segNet)

    def set_detect_model(self):
        self.detectNet = jetson.inference.detectNet("ssd-mobilenet-v2")

    def get_seg(self):
        img = jetson.utils.cudaFromNumpy(self.frame)
        self.buffers.Alloc(img.shape, img.format)
        self.segNet.Process(img, ignore_class="toilet")
        self.segNet.Overlay(self.buffers.overlay, filter_mode="linear") 
        self.segNet.Mask(self.buffers.mask, filter_mode="linear")

        self.img_rander = jetson.utils.cudaToNumpy(self.buffers.overlay)
        self.mask_rander = jetson.utils.cudaToNumpy(self.buffers.mask)

        self.floor_rander = self.mask_rander[:,:,1].copy()
        self.floor_rander[self.floor_rander[:,:]!=128] = 0
        self.floor_rander[self.floor_rander[:,:]==128] = 1
        self.floor_rander = self.floor_rander.reshape((120,320))

        self.floor_rander[:,:160] = mask_roi(self.floor_rander[:,:160], self.roi)
        self.floor_rander[:,160:] = mask_roi(self.floor_rander[:,160:], self.roi)
        self.get_score()

    def get_detect(self):
        img = jetson.utils.cudaFromNumpy(self.frame)
        detections = self.detectNet.Detect(img, overlay="box,labels,conf")
        self.img_detect_rander = jetson.utils.cudaToNumpy(img)

    def get_score(self):
        self.n = np.sum(self.floor_rander)
        self.n_left = np.sum(self.floor_rander[:,:80])
        self.n_right = np.sum(self.floor_rander[:,240:])

    def update_jetbot(self):
        if self.avoidance_status and self.cruise_status:
            if self.n > 6000:
                self.direction = "Straight"
                self.robot.set_motors(self.pw*self.left_power, self.pw*self.right_power)
            elif self.n < 2000:
                self.direction = "back"
                self.robot.set_motors(-self.pw*self.left_power, -self.pw*self.right_power)
            elif self.n_right >= self.n_left + 100:
                self.direction = "right"
                self.robot.set_motors(0.75*self.left_power, -0.75*self.right_power)
            elif self.n_left > self.n_right + 100:
                self.direction = "left"
                self.robot.set_motors(-0.75*self.left_power, 0.75*self.right_power)
            else:
                self.direction = "Unknown"
                self.robot.set_motors(0.75*self.left_power, -0.75*self.right_power)
        elif self.cruise_status:
            if self.move_arrow == "stop":
                self.direction = "stop"
                self.robot.stop()
            elif self.move_arrow == "up":
                self.direction = "Straight"
                self.robot.set_motors(self.pw_c*self.left_power, self.pw_c*self.right_power)
            elif self.move_arrow == "down":
                self.direction = "back"
                self.robot.set_motors(-self.pw*self.left_power, -self.pw*self.right_power)
            elif self.move_arrow == "left":
                self.direction = "left"
                self.robot.set_motors(-0.75*self.left_power, 0.75*self.right_power)
            elif self.move_arrow == "right":
                self.direction = "right"
                self.robot.set_motors(0.75*self.left_power, -0.75*self.right_power)
            else:
                self.direction = "Unknown"
                self.robot.stop()
        elif self.avoidance_status:
            if self.move_arrow == "stop":
                self.direction = "stop"
                self.robot.stop()
            elif self.move_arrow == "up":
                if self.n > 6000:
                    self.direction = "Straight"
                    self.robot.set_motors(self.pw_c*self.left_power, self.pw_c*self.right_power)
                else:
                    self.direction = "stop with avoidance"
                    self.robot.stop()
                    self.move_arrow = "stop"
            elif self.move_arrow == "down":
                self.direction = "back"
                self.robot.set_motors(-self.pw*self.left_power, -self.pw*self.right_power)
            elif self.move_arrow == "left":
                self.direction = "left"
                self.robot.set_motors(-0.75*self.left_power, 0.75*self.right_power)
            elif self.move_arrow == "right":
                self.direction = "right"
                self.robot.set_motors(0.75*self.left_power, -0.75*self.right_power)
            else:
                self.direction = "Unknown"
                self.robot.stop()
        else:
            if self.move_arrow == "stop":
                self.direction = "stop"
                self.robot.stop()
            elif self.move_arrow == "up":
                self.direction = "Straight"
                self.robot.set_motors(self.pw*self.left_power, self.pw*self.right_power)
            elif self.move_arrow == "down":
                self.direction = "back"
                self.robot.set_motors(-self.pw*self.left_power, -self.pw*self.right_power)
            elif self.move_arrow == "left":
                self.direction = "left"
                self.robot.set_motors(-0.75*self.left_power, 0.75*self.right_power)
            elif self.move_arrow == "right":
                self.direction = "right"
                self.robot.set_motors(0.75*self.left_power, -0.75*self.right_power)
            else:
                self.direction = "Unknown"
                self.robot.stop()
            self.move_arrow = "stop"

    def get_frame(self):
        image = self.img_rander
        detect_img = self.img_detect_rander
        text = f'floor: {self.n:0.2f}, left_n: {self.n_left}, right_n: {self.n_right}, direction: {self.direction}'
        image = cv2.putText(image, text, (5,15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA) 
        ret, jpeg = cv2.imencode('.jpg', image)
        # roi visualization
        tmp = cv2.resize(self.floor_rander, dsize=(0, 0), fx=2, fy=2, interpolation=cv2.INTER_LINEAR)
        tmp = np.stack((255*tmp,)*3,axis = 2)
        result = np.concatenate((detect_img, image, tmp, ),axis=0)
        self.result = result
        ret, jpeg = cv2.imencode('.jpg', result)
        return jpeg.tobytes()

    def update(self):
        while True:
            start = time.time()
            (self.grabbed, self.frame) = self.cap.read()
            # segmentation
            self.get_seg()
            # detection
            self.get_detect()
            # update jetbot
            self.update_jetbot()
            end = time.time() - start
            if end < 0.1:
                time.sleep(0.1-end)
            print("time :", end, ",\ttotal: ", time.time() - start)  # check time 
            
class segmentationBuffers:
    def __init__(self, net):
        self.net = net
        self.mask = None
        self.overlay = None
        self.mask_downsample = 2
            
    def Alloc(self, shape, format):
        self.overlay = jetson.utils.cudaAllocMapped(width=shape[1], height=shape[0], format=format)
        self.mask = jetson.utils.cudaAllocMapped(width=shape[1]/self.mask_downsample, height=shape[0]/self.mask_downsample, format=format) 

def mask_roi(img_th, roi):
    mask = np.zeros_like(img_th)
    cv2.fillPoly(mask, np.array([roi], np.int32), 255)
    masked_image = cv2.bitwise_and(img_th, mask)
    return masked_image