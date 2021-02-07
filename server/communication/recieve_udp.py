import socket
import numpy
from cv2 import cv2

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('0.0.0.0', 5555))

str = [b'\xff' * 46080 for x in range(20)]

while True:
    picture = b''
    data, addr = sock.recvfrom(46081)
    str[data[0]] = data[1:46081]
    if data[0] == 19:
        for i in range(20):
            picture += str[i]
        frame = numpy.fromstring(picture, dtype=numpy.uint8)
        frame = frame.reshape(480, 640, 3)
        cv2.imwrite("media/frame.jpg", frame)
        if cv2.waitKey(1) == ord('q'):
            break
cv2.destroyAllWindows()
sock.close()