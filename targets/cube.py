import cv2
import numpy as np

import utils
from targets.target_base import TargetBase


class Target(TargetBase):
    def __init__(self):
        self.kernel_s = np.array([1], dtype=np.uint8)
        self.kernel_m = np.array([[1, 1],
                                  [1, 1]], dtype=np.uint8)
        self.kernel_b = np.array([[0, 1, 0],
                                  [1, 1, 1],
                                  [0, 1, 0]], dtype=np.uint8)

    def create_mask(self, frame, hsv):
        mask = utils.hsv_mask(frame, hsv)
        mask = utils.morphology(mask, self.kernel_b)
        mask = utils.binary_thresh(mask, 127)
        mask = self.edge_detection(frame, mask)
        return mask

    def edge_detection(self, frame, mask):
        edge = utils.bitwise_and(frame, mask)
        edge = utils.canny_edge_detection(edge)
        edge = utils.binary_thresh(edge, 20)
        edge = utils.array8(edge)
        edge = utils.opening_morphology(edge, kernel_e=self.kernel_s, kernel_d=self.kernel_s)
        mask = utils.bitwise_not(mask, edge)
        mask = utils.closing_morphology(mask, kernel_d=self.kernel_m, kernel_e=self.kernel_m)
        return mask

    def find_contours(self, mask):
        img, contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        return contours, hierarchy

    @staticmethod
    def filter_contours(contours, hierarchy):
        if contours is None:
            return []
        return [cnt for cnt in contours if
                len(cnt) > 2 and cv2.contourArea(cnt) > 150 and 0.5 < utils.aspect_ratio(cnt) < 1.25 and 4 < len(utils.points(cnt)) < 6]

    @staticmethod
    def draw_contours(filtered_contours, original):
        for cnt in filtered_contours:
            rect = cv2.minAreaRect(cnt)
            box = cv2.boxPoints(rect)
            box = np.int0(box)

            approx = utils.approx(cnt)
            cv2.drawContours(original, [approx], 0, (255, 0, 0), 2)

            cv2.drawContours(original, [box], 0, (0, 0, 255), 2)

            points = utils.points(cnt)
            for p in points:
                cv2.circle(original, p, 5, (0, 255, 0), -1)
                cv2.putText(original, str(points.index(p)), (p[0] + 5, p[1]), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0))
