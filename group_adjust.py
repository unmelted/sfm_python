import numpy as np
import math
import cv2
from logger import Logger as l
from mathutil import get_rotate_point

class GroupAdjust(object) :

    def __init__(self) :
        pass

    def calculate_radian(self, cameras) :
        for i in range(len(cameras)):
            dist = 0
            diffx = cameras[i].pts_extra[0][0] - cameras[i].ptx_extra[2][0]
            diffy = cameras[i].pts_extra[0][1] - cameras[i].ptx_extra[2][1]
            if diffx == 0:
                dist = diffy
            else : 
                dist = math.sqrt(diffx* diffx + diffy * diffy)

            cameras[i].rod_length = dist
            degree = cv2.fastAtan2(diffy, diffx)
            cameras[i].radian = degree * math.pi / 180
            l.get().w.debug("camera {} diffx {} diffy {} degree {} radian {} ".format(i, diffx, diffy, degree, cameras[i].radian))


    def calculate_scaleshift(self, cameras) :
        sumx = 0
        sumy = 0
        avex = 0    
        avey = 0
        dsccnt = 0
        targx = 0
        targy = 0

        startx = cameras[0].ptx_extra[1][0]
        startx = cameras[0].ptx_extra[1][1]        
        start_len = cameras[0].rod_length
        target_len = cameras[len(cameras) -1].rod_length

        for i in range(len(cameras)):
            sumx += cameras[i].pts_extra[1][0]
            sumy += cameras[i].pts_extra[1][1]
            dsccnt += 1

        avex = sumx / dsccnt
        avey = sumy / dsccnt
        targx = avex 
        targy = avey
        interval = (target_len - start_len) / (dsccnt - 1)

        for i in range(len(cameras)):
            dist_len = start_len + (interval * i)
            cameras[i].scale = dist_len / cameras[i].rod_length
            cameras[i].adjust_x = targx - cameras[i].ptx_extra[1][0]
            cameras[i].adjust_y = targy - cameras[i].ptx_extra[1][1]
            cameras[i].rotate_x = cameras[i].ptx_extra[1][0]
            cameras[i].rotate_y = cameras[i].ptx_extra[1][1]
            l.get().w.debug("camera {} scale {} adjustx {} ajdusty {} ".format(i, cameras[i].scale, cameras[i].ajdust_x, cameras[i].adjust_y))


    def calculate_margin(self, cameras) :
        left = []
        right = []
        top = []
        bottom = []

        for i in range(len(cameras)):
            scale = cameras[i].scale
            center_x = cameras[i].rotate_x
            center_y = cameras[i].rotate_y
            w = cameras[i].view.image_width
            h = cameras[i].view.image_height

            e1_x = center_x * ( 1 - scale)
            e1_y = center_y * ( 1 - scale)
            e2_x = e1_x + (scale * w)
            e2_y = e1_y
            e3_x = e2_x
            e3_y = e1_y + (scale * h)
            e4_x = e1_x
            e4_y = e3_y

            e1r_x, e1r_y = get_rotate_point(center_x, center_y, e1_x, e1_y, cameras[i].radian)
            e2r_x, e2r_y = get_rotate_point(center_x, center_y, e2_x, e2_y, cameras[i].radian)
            e3r_x, e3r_y = get_rotate_point(center_x, center_y, e3_x, e3_y, cameras[i].radian)
            e4r_x, e4r_y = get_rotate_point(center_x, center_y, e4_x, e4_y, cameras[i].radian)                                    

            margin_left = max((e1r_x + cameras[i].adjust_x), 0)
            margin_top  = max((e1r_y + cameras[i].adjust_y), 0)

            margin_right = min((e2r_x + cameras[i].adjust_x), w)
            margin_top = max((e2r_y + cameras[i].adjust_y), 0)

            margin_right = min((e3r_x + cameras[i].adjust_x), margin_right)
            margin_bottom = min((e3r_y + cameras[i].adjust_y), h)

            margin_left = max((e4r_x + cameras[i].adjust_x), margin_left)
            margin_bottom = min((e4r_y + cameras[i].adjust_y), margin_bottom)

            if margin_left > margin_top * w / h :
                margin_top = margin_left * h / w
            else : 
                margin_left = margin_top * w / h
            
            if margin_right < margin_bottom * w / h :
                margin_bottom = margin_right * h / w
            else :
                margin_right = margin_bottom * w / h

            if margin_left > margin_right :
                t = margin_left
                margin_left = margin_right
                margin_right = t

            if margin_top > margin_bottom : 
                t = margin_top
                margin_top = margin_bottom
                margin_bottom = t

            left.append(margin_left)
            right.append(margin_right)
            top.apeend(margin_top)
            bottom.append(margin_bottom)

        left.sort(reverse=True)
        right.sort()
        top.sort(reverse=True)
        bottom.sort()
        margin_width = right[0] - left[0]
        margin_height = bottom[0] - top[0]
        l.get().w.debug('calculated margin l {} r {} t {} b {} width {} height {}'.format(left[0], right[0],top[[0], bottom[0]], margin_width, margin_height))

        return left[0], right[0],top[[0], bottom[0]], margin_width, margin_height