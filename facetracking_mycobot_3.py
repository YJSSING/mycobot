# 이동 평균 필터 추가

import cv2
from cvzone.FaceDetectionModule import FaceDetector
from pymycobot.mycobot import MyCobot
import numpy as np

# 이동 평균 필터 클래스 정의
class MovingAverageFilter:
    def __init__(self, window_size):
        self.window_size = window_size
        self.data = []

    def add_data(self, value):
        self.data.append(value)
        if len(self.data) > self.window_size:
            del self.data[0]

    def get_average(self):
        if len(self.data) == 0:
            return 0
        return sum(self.data) / len(self.data)

cap = cv2.VideoCapture(1)
ws, hs = 1280, 720
cap.set(3, ws)
cap.set(4, hs)

if not cap.isOpened():
    print("Camera couldn't Access!!!")
    exit()

# myCobot 설정
mc = MyCobot('COM4')

detector = FaceDetector()
servoPos = [-90, 0]  # 초기 서보 위치

# 이동 평균 필터 초기화
filter_size = 5  # 필터 크기 설정
x_filter = MovingAverageFilter(filter_size)
y_filter = MovingAverageFilter(filter_size)

while True:
    success, img = cap.read()
    img, bboxs = detector.findFaces(img, draw=False)

    if bboxs:
        # 좌표 가져오기
        fx, fy = bboxs[0]["center"][0], bboxs[0]["center"][1]
        pos = [fx, fy]

        # 이동 평균 필터에 좌표값 추가
        x_filter.add_data(fx)
        y_filter.add_data(fy)

        # 이동 평균 필터에서 평균값 가져오기
        fx_avg = int(x_filter.get_average())
        fy_avg = int(y_filter.get_average())

        # 좌표를 서보 각도로 변환
        servoX = np.interp(fx_avg, [0, ws], [-90, 90])
        servoY = np.interp(fy_avg, [0, hs], [-90, 90])

        if servoX < -90:
            servoX = -90
        elif servoX > 90:
            servoX = 90
        if servoY < -90:
            servoY = -90
        elif servoY > 90:
            servoY = 90

        servoPos[0] = -(servoX)   # 1번 joint
        servoPos[1] = servoY

        # servoPos[0] = -(servoX+180)  # 5번 joint

        cv2.circle(img, (fx_avg, fy_avg), 80, (0, 0, 255), 2)
        cv2.putText(img, str(pos), (fx_avg + 15, fy_avg - 15), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)
        cv2.line(img, (0, fy_avg), (ws, fy_avg), (0, 0, 0), 2)  # x line
        cv2.line(img, (fx_avg, hs), (fx_avg, 0), (0, 0, 0), 2)  # y line
        cv2.circle(img, (fx_avg, fy_avg), 15, (0, 0, 255), cv2.FILLED)
        cv2.putText(img, "TARGET LOCKED", (850, 50), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 255), 3)

        # myCobot으로 서보 제어
        mc.send_angles([servoPos[0], 0, -servoPos[1], servoPos[1], 0, 0], 100)
        # mc.send_angles([0, 0, 0, 0, servoPos[0], 0], 40)
        # mc.send_angles([0, 0, 0, servoPos[1], 0, 0], 100)
        # mc.send_angles([0, 0, -servoPos[1], servoPos[1], 0, 0], 100)
        # mc.send_angles([0, 0, 0, 0, -90, 0], 100)

    else:
        cv2.putText(img, "NO TARGET", (880, 50), cv2.FONT_HERSHEY_PLAIN, 3, (0, 0, 255), 3)
        cv2.circle(img, (640, 360), 80, (0, 0, 255), 2)
        cv2.circle(img, (640, 360), 15, (0, 0, 255), cv2.FILLED)
        cv2.line(img, (0, 360), (ws, 360), (0, 0, 0), 2)  # x line
        cv2.line(img, (640, hs), (640, 0), (0, 0, 0), 2)  # y line

    cv2.putText(img, f'Servo X: {int(servoPos[0])} deg', (50, 50), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)
    cv2.putText(img, f'Servo Y: {int(servoPos[1])} deg', (50, 100), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)

    cv2.imshow("Image", img)
    cv2.waitKey(1)
