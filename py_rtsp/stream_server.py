# python3
# -*- coding:utf-8 -*-
"""
"""
# ------------------------------------------------------------------------------------------------------------------------------------------
import sys
import logging
import time
from typing import Union, List
import cv2
from cv2.typing import MatLike
from config import Config
from .motion_detection import MotionDetector
from .frame_publisher import FramePublisher
from .cli import cli
# ------------------------------------------------------------------------------------------------------------------------------------------
logger:logging.Logger = logging.getLogger("server")
# ------------------------------------------------------------------------------------------------------------------------------------------
FrameType = MatLike
DeviceType = cv2.VideoCapture
# ------------------------------------------------------------------------------------------------------------------------------------------
class StreamServer:
    def __init__(self, cfg:Config):
        #: Termination flag.
        #: :meth:`_serve` will stop as soon as this flag is set.
        self._run:bool = True
        self.config:Config = cfg
        self.device:Union[DeviceType,None]=None
        self.width:int = 0
        self.height:int = 0
        self.fps:int = 0
        self.out = None
        self.motion_detector = MotionDetector(cfg)
        self.frame_publisher = FramePublisher(cfg)
    
    def on_first_frame(self, frame):
        self.width = frame.shape[1]
        self.height = frame.shape[0]
        logger.info('Capturing with size %s x %s', self.width, self.height)
        self.motion_detector.on_first_frame(frame)
        self.out = cv2.VideoWriter("video.avi", cv2.VideoWriter_fourcc('F', 'M', 'P', '4'), 15, (self.width, self.height))

    def create_video_device(self)->cv2.VideoCapture:
        """
        """
        self.width = 0
        self.height = 0
        self.fps = 0
        logger.debug("Creating video device '%s'", self.config.device)
        return cv2.VideoCapture(self.config.device, cv2.CAP_FFMPEG)

    def next_frame(self)->Union[None,FrameType]:
        success, frame = self.device.read()
        if not success:
            logger.warning("Failed to read frame from '%s", self.device)
            return None
        if not self.width:
            self.on_first_frame(frame)
        return frame

    def publish_frame(self, frame:FrameType, frame_time:float, motion_detected:bool):
        cv2.imshow('Movement detector', frame)
        self.frame_publisher(frame, motion_detected, frame_time)

    def cleanup(self):
        logger.info("starting cleanup")
        self.motion_detector.cleanup()
        self.frame_publisher.cleanup()
        if self.device:
            self.device.release()
        if self.out:
            self.out.release()
        logger.debug("finished cleanup")

    def serve_forever(self):
        """
        """
        frames = 0
        started = time.time()
        self.device = self.create_video_device()
        while self._run:
            if (frame:=self.next_frame()) is None:
                continue
            frames += 1
            frame_time:float = time.time()
            motion:bool = self.motion_detector(frame)
            self.out.write(frame)
            cv2.waitKey()
            self.publish_frame(frame, motion, frame_time)

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, exc_tb):
        self.cleanup()
# ------------------------------------------------------------------------------------------------------------------------------------------
def main(argv:List[str])->int:
    result:int = 0

    cfg:Config = cli('server', argv)

    try:
        with StreamServer(cfg) as ss:
            ss.serve_forever()
    except (KeyboardInterrupt, SystemExit) as exc:
        logger.warning("stopping due to %s", exc)
    except Exception: # pylint:disable=broad-exception-caught
        logger.exception("caught unhandled exception")
        result = 1
    
    logger.info("stopped")

    return result
# ------------------------------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))        
