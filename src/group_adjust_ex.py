import os
import subprocess
import numpy as np
import math
import cv2
from logger import Logger as l
from mathutil import *
from intrn_util import *
from extn_util import *
from definition import DEFINITION as df
from group_adjust import GroupAdjust


class GroupAdjustEx(object):

	def calculate_projection(self, output_path, cameras, world) :
		print("---- calculate projection \n ", world)

		ax_min = 100000
		ax_max = -100000
		ay_min = 100000 
		ay_max = -100000
		xmin = 0
		xmax = 0 
		ymin = 0 
		ymax = 0

		for camera in cameras : 
			xmin, xmax, ymin, ymax = self.calculate_projection_corners(output_path, camera, world)
			if xmin < ax_min : 
				ax_min = xmin
			if xmax > ax_max :
				ax_max = xmax

			if ymin < ay_min : 
				ay_min = ymin
			if ymax > ay_max :
				ay_max = ymax
		
		print(ax_min, ax_max, ay_min, ay_max)

	def calculate_projection_corners(self, output_path, camera, world) :
		ground = '/Users/4dreplay/work/sfm_python/simulation/Cal3D_085658/Basketball_Half.png'		
		# gr_img = cv2.imread(ground)			

		file_name = os.path.join(output_path, camera.name + '_wp.jpg')
		file_name2 = os.path.join(output_path, camera.name + '_wp2.jpg')		
		in_img = cv2.flip(camera.image, -1)

		print(" ------ corner projection ", camera.name)
		p = np.array([[world[0], world[1]], [world[2], world[3]], [world[4], world[5]], [world[6], world[7]]])
		p = p + 1100
		pts_3d = camera.pts_3d / 2
		print(p, pts_3d)

		H, _ = cv2.findHomography(pts_3d, p, 1)
		#H = cv2.getPerspectiveTransform(pts_3d, p)
		crns = np.float32(np.array([[[0, 0], [camera.image_width, 0], [camera.image_width, camera.image_height], [0, camera.image_height]]]))
		# mv_img = cv2.warpAffine(camera.image, H[:2, :3], (1920, 1080))
		mv_img = cv2.warpPerspective(in_img, H, (3000, 3000))		
		mv_crns = cv2.perspectiveTransform(crns, H)
		cv2.imwrite(file_name, mv_img)

		camera.prj_crns = mv_crns

		xmin = 3840
		xmax = 0
		ymin = 2160
		ymax = 0 

		for i, mv_pt in enumerate(mv_crns[0]) :
			print(mv_pt) 
			if mv_pt[0] < xmin :
				xmin = int(mv_pt[0])
			elif mv_pt[0] > xmax : 
				xmax = int(mv_pt[0])

			if mv_pt[1] < ymin :
				ymin = int(mv_pt[1])
			elif mv_pt[1] > ymax :
				ymax = int(mv_pt[1])


		return xmin, xmax, ymin, ymax