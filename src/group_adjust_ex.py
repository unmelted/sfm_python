import os
import sys
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
	x_pad = 5000
	y_pad = 5000
	p = None
	cal_mode = 'first_ch' #'world'
	prev_3dpts = None

	def set_world(self, world, flip) :
		self.p = np.float32(np.array([[world[0], world[1]], [world[2], world[3]], [world[4], world[5]], [world[6], world[7]]]))
		self.p[:, 0] = self.p[:, 0] + self.x_pad
		self.p[:, 1] = self.p[:, 1] + self.y_pad		
		self.flip = flip
		self.dump = True
	
	def calculate_back_projection(self, output_path, cameras, polygon) :
		first = True

		for camera in cameras : 
			print(" ------ ", camera.name)
			file_name = os.path.join(output_path, camera.name + '_bp.jpg')			
			if self.dump == True :
				in_img = camera.image
			if self.flip == True :
				in_img = cv2.flip(in_img, -1)

			pts_3d = camera.pts_3d / 2
			mv_poly = None

			if self.cal_mode == 'world' :
				H, _ = cv2.findHomography(self.p, pts_3d, 1)
				mv_poly = cv2.perspectiveTransform(polygon, H)

			elif self.cal_mode == 'first_cn':
				if first == True :
					mv_poly = polygon
					self.prev_3dpts = pts_3d					
				else : 
					H, _ = cv2.findHomography(pts_3d, self.prev_3dpts, 1)
					mv_poly = cv2.perspectiveTransform(polygon, H)

			
			if self.dump == True :
				prev = None
				for i, pt in enumerate(mv_poly) :
					print(pt)
					cv2.circle(in_img, (int(pt[0][0]), int(pt[0][1])), 7, (255, 0, 255), -1)
					if i > 0 :
						cv2.line(in_img, (int(pt[0][0]), int(pt[0][1])), (int(prev[0][0]), int(prev[0][1])), (255, 255, 0), 5)
					prev = pt
		
				cv2.line(in_img, (int(mv_poly[0][0][0]), int(mv_poly[0][0][1])), (int(prev[0][0]), int(prev[0][1])), (0, 255, 255), 5)
				cv2.imwrite(file_name, in_img)

	def calculate_projection(self, output_path, cameras) :
		print("---- calculate projection \n ")
		canvas  = np.zeros((10000, 10000, 3), dtype="uint8")		
		vertices = None
		ax_min = 100000
		ax_max = -100000
		ay_min = 100000 
		ay_max = -100000
		xmin = 0
		xmax = 0 
		ymin = 0 
		ymax = 0
		first = True
		index = 0
		for camera in cameras : 
			vertices, xmin, xmax, ymin, ymax = self.calculate_projection_corners(output_path, camera, canvas, vertices, first)
			first = False
			index += 1
			if xmin < ax_min : 
				ax_min = xmin
			if xmax > ax_max :
				ax_max = xmax

			if ymin < ay_min : 
				ay_min = ymin
			if ymax > ay_max :
				ay_max = ymax

			# if index == 3 :
			# 	break		
		print(ax_min, ax_max, ay_min, ay_max)


		print("---- intersect point --- ")
		prev = None
		for i, pt in enumerate(vertices) :
			print(pt)
			cv2.circle(canvas, (int(pt[0][0]), int(pt[0][1])), 20, (0, 0, 255), -1)

		poly = cv2.approxPolyDP(vertices, cv2.arcLength(vertices, True) * 0.01, True);

		print("---- approx polygon --- ")
		prev = None
		for i, pt in enumerate(poly):
			print(pt)
			cv2.circle(canvas, (int(pt[0][0]), int(pt[0][1])), 20, (255, 0, 0), -1)
			if i > 0 :
				cv2.line(canvas, (int(pt[0][0]), int(pt[0][1])), (int(prev[0][0]), int(prev[0][1])), (255, 255, 0), 5)
			prev = pt

		cv2.line(canvas, (int(poly[0][0][0]), int(poly[0][0][1])), (int(prev[0][0]), int(prev[0][1])), (255, 255, 0), 5)				

		file_name = os.path.join(output_path, 'canvas2.jpg')
		cv2.imwrite(file_name, canvas)			

		return vertices

	def calculate_projection_corners(self, output_path, camera, canvas, vertices, first) :

		ground = '/Users/4dreplay/work/sfm_python/simulation/Cal3D_085658/Basketball_Half.png'		
		# gr_img = cv2.imread(ground)			

		file_name = os.path.join(output_path, camera.name + '_wp.jpg')
		file_name2 = os.path.join(output_path, camera.name + '_wp2.jpg')		

		if self.dump == True:
			bl_img = np.zeros((10000, 10000, 3), dtype="uint8")			

			if self.flip == True :
				in_img = cv2.flip(camera.image, -1)			
			else :
				in_img = camera.image


		print(" ------ ", camera.name)
		pts_3d = camera.pts_3d / 2 + self.x_pad
		# print(p, pts_3d)
		crns = np.float32(np.array([[[0, 0], [camera.image_width, 0], [camera.image_width, camera.image_height], [0, camera.image_height]]])) + self.x_pad
		mv_crns = None
		mv_img = None
		intst_pt = None

		if self.cal_mode == 'world' :
			H, ret = cv2.findHomography(pts_3d, self.p, cv2.RANSAC)
			print("homogray return .. : ", ret)
			print("h .", H)
			std_rect = np.float32(np.array([[[200, 200], [9800, 200], [9800, 9800], [200, 9800]]]))

			if self.dump == True:
				mv_img = cv2.warpPerspective(in_img, H, (10000, 10000))		

			mv_crns = cv2.perspectiveTransform(crns, H)
			camera.prj_crns = mv_crns
			print("-- mv corner")
			print(mv_crns)

			if first == True:
				print(std_rect)
				nested, intst_pt = cv2.intersectConvexConvex(std_rect, mv_crns, True)			
				print("--- after convex1")
				print(intst_pt)
			else :
				print(vertices)
				nested, intst_pt = cv2.intersectConvexConvex(vertices, mv_crns, True)		
				print("--- after convex2")
				print(intst_pt)

		elif self.cal_mode == 'first_ch':
			if first == True :
				self.prev_3dpts = pts_3d
				mv_crns = crns
				intst_pt = crns
				mv_img = in_img
				print("first ch..--- ")
				print(self.prev_3dpts)
				print(mv_crns)

			else : 
				H, ret = cv2.findHomography(pts_3d, self.prev_3dpts, cv2.RANSAC)			
				print("homogray return .. : ", ret)
				print("h .", H)

				if self.dump == True:
					mv_img = cv2.warpPerspective(in_img, H, (10000, 10000))		

				mv_crns = cv2.perspectiveTransform(crns, H)
				camera.prj_crns = mv_crns
				print("-- mv corner")
				print(mv_crns)
				print("-- input vertices")
				print(vertices)
				nested, intst_pt = cv2.intersectConvexConvex(vertices, mv_crns, True)		
				print("--- after convex2")
				print(intst_pt)

		vertices = intst_pt

		xmin = sys.maxsize
		xmax = -sys.maxsize -1
		ymin = sys.maxsize
		ymax = -sys.maxsize -1

		prev = None
		for i, mv_pt in enumerate(mv_crns[0]) :
			# print(mv_pt) 
			if mv_pt[0] < xmin :
				xmin = int(mv_pt[0])
			elif mv_pt[0] > xmax : 
				xmax = int(mv_pt[0])

			if mv_pt[1] < ymin :
				ymin = int(mv_pt[1])
			elif mv_pt[1] > ymax :
				ymax = int(mv_pt[1])
			
			cv2.circle(bl_img, (int(mv_pt[0]), 	int(mv_pt[1])), 20, (0, 0, 255), -1)

			if self.dump == True:			
				if i > 0 :
					cv2.line(bl_img, (int(mv_pt[0]), int(mv_pt[1])), (int(prev[0]), int(prev[1])), (255, 0, 0), 5)
			prev = mv_pt

		# cv2.line(bl_img, (int(mv_crns[0][0]), int(mv_crns[0][1])), (int(prev[0]), int(mv_pt[1])), (255, 0, 0), 5)

		if self.dump == True:
			print("---- intersect point --- ")
			prev = None
			for i, pt in enumerate(intst_pt) :
				print(pt)
				cv2.circle(canvas, (int(pt[0][0]), int(pt[0][1])), 20, (0, 255, 255), -1)
				if i > 0 : 
					cv2.line(canvas, (int(pt[0][0]), int(pt[0][1])), (int(prev[0][0]), int(prev[0][1])), (255, 255, 0), 5)
				prev = pt

			cv2.line(canvas, (int(intst_pt[0][0][0]), int(intst_pt[0][0][1])), (int(prev[0][0]), int(prev[0][1])), (255, 255, 0), 5)
			cv2.imwrite(file_name, mv_img)
			cv2.imwrite(file_name2, bl_img)

		return vertices, xmin, xmax, ymin, ymax