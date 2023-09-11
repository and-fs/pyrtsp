# python3
# -*- coding:utf-8 -*-
"""
"""
# ------------------------------------------------------------------------------------------------------------------------------------------
import logging
import cv2
from cv2.typing import MatLike
from typing import TYPE_CHECKING, Any, Union
from config import Config
# ------------------------------------------------------------------------------------------------------------------------------------------
logger:logging.Logger = logging.getLogger("motion")
# ------------------------------------------------------------------------------------------------------------------------------------------
class MotionDetector:
    def __init__(self, cfg:Config):
        self.mog = cv2.createBackgroundSubtractorMOG2()
        self.threshold = cfg.motion_detection.get('threshold', 1000)
        self.mask_img:Union[None,MatLike] = None
        self.mask_width:int = cfg.motion_detection.get('width', 0)
        self.mask_height:int = cfg.motion_detection.get('height', 0)
        mask_img_name = cfg.motion_detection.get('mask', None)
        if mask_img_name:
            self.mask_img = cv2.imread(mask_img_name)
            self.mask_width = self.mask_img.shape[1]
            self.mask_height = self.mask_img.shape[0]
            logger.info("masking with image '%s' with size %s x %s", mask_img_name, self.mask_width, self.mask_height)

    def on_first_frame(self, frame:MatLike):
        width = frame.shape[1]
        height = frame.shape[0]
        if self.mask_width == 0:
            if width > 640:
                self.mask_width = 576
                self.mask_height = self.mask_width * (width / height)
            else:
                self.mask_width = width
                self.mask_height = height
        logger.info('detection frame size %s x %s', self.mask_width, self.mask_height)

    def __call__(self, frame:MatLike)->bool:
        frame = cv2.resize(frame, dsize=(self.mask_width, self.mask_height), interpolation=cv2.INTER_LINEAR)
        if self.mask_img is not None:
            frame = cv2.bitwise_and(frame, self.mask_img, mask=None)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        fgmask = self.mog.apply(gray)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        fgmask = cv2.erode(fgmask, kernel, iterations=1)
        fgmask = cv2.dilate(fgmask, kernel, iterations=1)
        
        contours, _unused = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            # Ignore small contours
            if cv2.contourArea(contour) < self.threshold:
                continue
            return True
        return False        
    
    def cleanup(self):
        logger.info('starting cleanup')
        logger.debug('finished cleanup')
