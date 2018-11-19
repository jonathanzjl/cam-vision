#! /usr/bin/env python3
# Copyright (C) 2018  Zhijin Li

# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:

#     * Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above
# copyright notice, this list of conditions and the following disclaimer
# in the documentation and/or other materials provided with the
# distribution.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

## ---------------------------------------------------------------------------
##
## File: capture_cam.py<utils> for Cam-Vision
##
## Created by Zhijin Li
## E-mail:   <jonathan.zj.lee@gmail.com>
##
## Started on  Sat Oct 13 00:05:50 2018 Zhijin Li
## Last update Mon Oct 29 22:34:54 2018 Zhijin Li
## ---------------------------------------------------------------------------


import cv2
import time
import numpy as np
import threading as thr


class FastVideoStream():

  def __init__(self, video_src):
    """

    Constructor. Create FastVideoStream instance.

    Parameters
    ----------
    video_src: int or str
    Video input source. Can be an integer indicating
    the number tag of camera. Can be a string
    indicating path to a video file.

    Returns
    ----------
    FastVideoStream instance.

    """
    self.video_stream = cv2.VideoCapture(video_src)
    # self.video_stream.set(cv2.CAP_PROP_FPS, 5)
    self.success, self.frame = self.video_stream.read()
    self.finished = False

  def read_frames(self):
    """

    Read frames from input source.

    This launches a seperate thread to continuously
    update current frame.

    Returns
    ----------
    FastVideoStream instance.

    """
    thr.Thread(
      target=self.update_frame,
      daemon=True,
      args=(),).start()
    return self


  def update_frame(self):
    """

    Continuously update current frame.

    """
    while True:
      if self.finished:
        print('video stream stopped.')
        self.video_stream.release()
        return
      self.success, self.frame = self.video_stream.read()
      if not self.success:
        raise Exception('error reading frames.')


  def get_frame(self):
    """

    Get current in-coming frame.

    Returns
    ----------
    np.array
    Current frame.

    """
    return self.frame

  def stop(self):
    """

    Stop frame frame reading.

    """
    self.finished = True


def trim_frame_square(frame, resize_ratio, trim_factor):
  """

  Resize a frame according to specified ratio while
  keeping original the original aspect ratio, then trim
  the longer side of the frame according to specified
  factor.

  Parameters
  ----------
  frame: np.array
  The input frame

  resize_ratio: float
  Resize factor.

  trim_factor: float
  Trim factor for the longer side of the frame. Must
  be btw 0 and 1.

  Returns
  ----------
  np.array
  Resized and trimmed frame.

  """
  frame = cv2.resize(
    frame, dsize=(0,0), fx=resize_ratio, fy=resize_ratio)
  __hor_longer, __l = (
    True, frame.shape[1] if frame.shape[1] > frame.shape[0]
    else (False, frame.shape[0]))
  __t = int(__l * trim_factor)
  __i = int((max(__l-__t, 0))/2)
  if __hor_longer:
    frame = frame[:,__i:__i+__t,:]
  else:
    frame = frame[__i:__i+__t,:,:]
  return frame


def print_fps(frame, fps):
  """

  Print FPS in top left corner of the frame
  image.

  Parameters
  ----------
  frame: np.array
  Current frame image.

  fps: float
  Current FPS.

  """
  cv2.putText(
    frame, 'FPS {:.1f}'.format(fps), (10,20),
    cv2.FONT_HERSHEY_COMPLEX_SMALL, .6, (54,241,255),
    lineType=cv2.LINE_AA)


def print_pred(frame, labels, scores):
  """

  Print prediction labels and scores to frame.

  Parameters
  ----------
  label: list
  List of predicted labels.

  scores: list
  List of corresponding prediction scores.

  """
  __s = frame.shape[0]/400.0*0.6
  __w = 20
  cv2.putText(
    frame, 'top {} predictions:'.format(len(labels)),
    (10,100), cv2.FONT_HERSHEY_COMPLEX_SMALL, __s, (125,0,0),
    lineType=cv2.LINE_AA)
  for indx, (lab, scr) in enumerate(zip(labels, scores)):
    cv2.putText(
      frame, '{:25s}: {:.3f}'.format(lab, scr),
      (10,100+__w*(indx+1)), cv2.FONT_HERSHEY_COMPLEX_SMALL,
      __s, (0,255,0), lineType=cv2.LINE_AA)


def make_pred_frame(frame, labels, scores):
  """

  Print prediction labels and scores to frame.

  Parameters
  ----------
  label: list
  List of predicted labels.

  scores: list
  List of corresponding prediction scores.

  """
  __s, __n, __e = frame.shape[0]/400.0*0.6, 5, 6
  __w = int(frame.shape[0]/__n/(len(labels)+1))
  __pframe = 255*np.ones(
    (int(frame.shape[0]/__n)+__e,*frame.shape[1:]),
    dtype=np.uint8)

  cv2.putText(
    __pframe, 'top {} predictions:'.format(len(labels)),
    (5,int(__w/2)+__e), cv2.FONT_HERSHEY_COMPLEX_SMALL,
    __s, (204,0,102), lineType=cv2.LINE_AA)

  for indx, (lab, scr) in enumerate(zip(labels, scores)):
    cv2.putText(
      __pframe, '{:25s}: {:.3f}'.format(
        lab[:min(len(lab),20)],scr),
      (10,int(__w/2)+__e+__w*(indx+1)),
      cv2.FONT_HERSHEY_COMPLEX_SMALL,
      __s, (0,0,0), lineType=cv2.LINE_AA)
  return np.concatenate((frame, __pframe), axis=0)


if __name__ == '__main__':

  stream = FastVideoStream(0).read_frames()
  print('frame rate: {}'.format(cv2.CAP_PROP_FPS))

  fps = 0
  while True:
    __start = time.time()

    frame = stream.get_frame()
    frame = trim_frame_square(frame, .3, 0.5625)

    print_fps(frame, fps)
    cv2.imshow('Video Cam', frame)

    if cv2.waitKey(1) == ord('q'):
      stream.stop()
      break

    fps = 1.0/(time.time()-__start)

  cv2.destroyAllWindows()