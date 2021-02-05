
import threading
import socket
import numpy as np
from cv2 import cv2
import time

class VideoCamera(object):
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('0.0.0.0', 5555))
        self.s = [b'\xff' * 46080 for x in range(20)]
        # self.get_socket()
        threading.Thread(target=self.update, args=()).start()

    def __del__(self):
        self.sock.close()

    def get_socket(self):
        picture = b''
        data, addr = self.sock.recvfrom(57601)
        self.s[data[0]] = data[1:57601]
        if data[0] == 7:
            for i in range(8):
                picture += self.s[i]
            self.frame = np.fromstring(picture, dtype=np.uint8)
            self.frame = self.frame.reshape(240, 640, 3)
            self.grabbed = True

    def get_frame(self):
        image = self.frame
        ret, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()		

    def update(self):
        while True:
            self.get_socket()
            # time.sleep(0.1)

    # # frame (480, 640, 3)
    # # 480*640*3=921600
    # # ((480*640*3)/20=46080) < 65535
    # def get_socket(self):
    #     picture = b''
    #     data, addr = self.sock.recvfrom(46081)
    #     self.s[data[0]] = data[1:46081]
    #     if data[0] == 19:
    #         for i in range(20):
    #             picture += self.s[i]
    #         self.frame = np.fromstring(picture, dtype=np.uint8)
    #         self.frame = self.frame.reshape(480, 640, 3)
    #         self.grabbed = True

    # frame (240, 640, 3)
    # 240*640*3=460800
    # ((480*640*3)/8=57600) < 65535
