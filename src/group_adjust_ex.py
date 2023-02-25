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
	cal_mode = 'world' # 'first'
	use_pts = 'after_cal' # 'raw_pts'
	prev_3dpts = None
	flip = False
	dump = False
	scale = 1.0
	poly_mode = 'vertices' #polygon
	output_path = None

	def set_world(self, world, flip, scale, output_path) :
		self.p = np.float32(np.array([[world[0], world[1]], [world[2], world[3]], [world[4], world[5]], [world[6], world[7]]]))
		self.p[:, 0] = self.p[:, 0] + self.x_pad
		self.p[:, 1] = self.p[:, 1] + self.y_pad		
		self.flip = flip
		self.dump = True
		self.scale = scale
		self.output_path = output_path

	def calculate_back_projection(self, cameras, polygon) :
		first = True

		for camera in cameras : 
			print(" ------ ", camera.name)
			file_name = os.path.join(self.output_path, camera.name + '_bp.jpg')			
			if self.dump == True :
				if self.use_pts == 'raw_pts' :
					in_img = camera.image
				elif self.use_pts == 'after_cal' :
					in_img = camera.adj_image					
			if self.flip == True and self.use_pts == 'raw_pts':
				in_img = cv2.flip(in_img, -1)

			if self.use_pts == 'raw_pts' :
				pts_3d = camera.pts_3d / self.scale
			elif self.use_pts == 'after_cal' :
				pts_3d = camera.adj_pts3d 				

			mv_poly = None

			if self.cal_mode == 'world' :
				H, _ = cv2.findHomography(self.p, pts_3d, 1)
				mv_poly = cv2.perspectiveTransform(polygon, H)
				# mv_poly = cv2.transform(polygon, H[:2, :3])				
				camera.adj_polygon = mv_poly
			
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

	def calculate_common_area_3D(self, cameras, margin_pt) :
		print("---- calculate projection \n ")
		canvas  = np.zeros((10000, 10000, 3), dtype="uint8")		
		vertices = None

		first = True
		index = 0
		for camera in cameras : 
			vertices = self.calculate_projection_corners_3D(camera, margin_pt, canvas, vertices, first)
			first = False
			index += 1

		print("---- intersect point --- ")
		prev = None
		for i, pt in enumerate(vertices) :
			print(pt)
			cv2.circle(canvas, (int(pt[0][0]), int(pt[0][1])), 20, (0, 0, 255), -1)

		if self.poly_mode == 'polygon' :
			poly = cv2.approxPolyDP(vertices, cv2.arcLength(vertices, True) * 0.03, True); #0.03 - octagon
		elif self.poly_mode == 'vertices' :
			poly = vertices

		print("---- approx polygon --- ")
		prev = None
		for i, pt in enumerate(poly):
			print(pt)
			cv2.circle(canvas, (int(pt[0][0]), int(pt[0][1])), 20, (255, 0, 0), -1)
			if i > 0 :
				cv2.line(canvas, (int(pt[0][0]), int(pt[0][1])), (int(prev[0][0]), int(prev[0][1])), (255, 255, 0), 5)
			prev = pt

		cv2.line(canvas, (int(poly[0][0][0]), int(poly[0][0][1])), (int(prev[0][0]), int(prev[0][1])), (255, 255, 0), 5)				

		file_name = os.path.join(self.output_path, 'canvas2.jpg')
		cv2.imwrite(file_name, canvas)			

		return poly

	def calculate_projection_corners_3D(self, camera, margin_pt, canvas, vertices, first) :

		ground = '/Users/4dreplay/work/sfm_python/simulation/Cal3D_085658/Basketball_Half.png'		
		# gr_img = cv2.imread(ground)			

		file_name = os.path.join(self.output_path, camera.name + '_wp.jpg')
		file_name2 = os.path.join(self.output_path, camera.name + '_wp2.jpg')		

		if self.dump == True:
			bl_img = np.zeros((10000, 10000, 3), dtype="uint8")			

			if self.flip == True :
				in_img = cv2.flip(camera.image, -1)			
			else :
				in_img = camera.image


		print(" ------ ", camera.name)
		if self.use_pts == 'raw_pts' :
			pts_3d = camera.pts_3d / self.scale # by origin point from pts
		elif self.use_pts == 'after_cal' :
			pts_3d = camera.adj_pts3d # by adjust point from calibrated image


		# crns = np.float32(np.array([[[0, 0], [camera.image_width, 0], [camera.image_width, camera.image_height], [0, camera.image_height]]])) # all size image used.
		crns = np.float32(margin_pt) # use margin rectagle

		mv_crns = None
		mv_img = None
		intst_pt = None

		if self.cal_mode == 'world' :
			H, ret = cv2.findHomography(pts_3d, self.p, cv2.RANSAC)
			# print("homogray return .. ")
			# print(H)
			std_rect = np.float32(np.array([[[200, 200], [9800, 200], [9800, 9800], [200, 9800]]]))

			if self.dump == True:
				mv_img = cv2.warpPerspective(in_img, H, (10000, 10000))		

			mv_crns = cv2.perspectiveTransform(crns, H)
			# mv_crns = cv2.transform(crns, H[:2, :3])			

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


		vertices = intst_pt

	
		'''
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
		'''
		return vertices


	def get_reverse_affine_matrix(self, cam, margin, scale = 1.0) :
		print("get_reverse_affine_matrix margin_proc : ", scale, cam.view.image_width, cam.view.image_height)

		mat1 = get_rotation_matrix_with_center(-cam.radian, cam.rotate_x/scale, cam.rotate_y/scale)
		# print("rot : ", cam.radian, mat1)
		mat2 = get_scale_matrix_center(1/cam.scale, 1/cam.scale, cam.rotate_x/scale, cam.rotate_y/scale)
		# print("scale : ", cam.scale, mat2)
		mat3 = get_translation_matrix(-cam.adjust_x/scale, -cam.adjust_y/scale)
		# print("mtran : ", mat3)

		mat4 = get_reverse_margin_matrix(cam.view.image_width, cam.view.image_height, margin[0]/scale, margin[1]/scale, margin[2]/scale, margin[3]/scale)

		out = np.linalg.multi_dot([mat3, mat1, mat2, mat4])

		return out

	def calculate_polygon_to_raw(self, cameras, margin, margin_pt):
		print("-------- calculate_polygon_to_raw.. ")	

		for camera in cameras : 
			file_name = os.path.join(self.output_path, camera.name + '_rev.jpg')
			if self.dump == True :
				in_img = camera.image
	
			if self.flip == True :
				in_img = cv2.flip(in_img, -1)

			mat = self.get_reverse_affine_matrix(camera, margin, self.scale)
			mv_poly = cv2.perspectiveTransform(camera.adj_polygon, mat)
			# mv_poly = cv2.transform(camera.adj_polygon, mat[:2, :3])
			camera.adj_polygon_toraw = mv_poly

			if self.dump == True :
				prev = None
				for i, pt in enumerate(mv_poly) :
					print(pt)
					cv2.circle(in_img, (int(pt[0][0]), int(pt[0][1])), 7, (255, 0, 255), -1)
					if i > 0 :
						cv2.line(in_img, (int(pt[0][0]), int(pt[0][1])), (int(prev[0][0]), int(prev[0][1])), (255, 255, 0), 5)
					prev = pt
		
				cv2.line(in_img, (int(mv_poly[0][0][0]), int(mv_poly[0][0][1])), (int(prev[0][0]), int(prev[0][1])), (0, 255, 255), 5)
				'''
				print("margin_pt drawing ... ")
				print(margin_pt)
				for i, pt in enumerate(margin_pt) :
					print(pt)
					cv2.circle(in_img, (pt[0], pt[1]), 5, (0, 255, 0), -1)

					if i > 0 :
						cv2.line(in_img, (pt[0], pt[1]), (prev[0], prev[1]), (255, 255, 0), 3)
					prev = pt
				cv2.line(in_img, (int(margin_pt[0][0]), int(margin_pt[0][1])), (int(prev[0]), int(prev[1])), (0, 255, 255), 5)
				'''
				cv2.imwrite(file_name, in_img)


	def calculate_swipe_position(self, base, camera, x, y, zoom, first):
		print("-------- calculate_swipe_position. ")	

		in_img = camera.adj_image.copy()

		if first == False : 
			H, ret = cv2.findHomography(base, camera.adj_pts3d, cv2.RANSAC)
			mv_pt = cv2.perspectiveTransform(np.float32(np.array([[[int(x), int(y)]]])), H)
			print(mv_pt)
		else :
			mv_pt = base

		print(mv_pt)
		cv2.circle(in_img, (int(mv_pt[0][0][0]), int(mv_pt[0][0][1])), 7, (255, 0, 255), -1)

		return in_img		
	

	
	def calculate_livepd_crop(self, base, camera, center, width, height, first):
		print("-------- calculate_livepd_crop ")	

		in_img = camera.adj_image.copy()
		# pd_pts = np.float32(np.array([[[points[0], points[1]], [points[2], points[3]], [center[0], center[1]]]]))
		adj_pd_pts = np.float32(np.array([[[center[0], center[1]]]]))		
		print("adj center : ", adj_pd_pts)

		if first == False : 
			H, ret = cv2.findHomography(base, camera.adj_pts3d, cv2.RANSAC)
			mv_pt = cv2.perspectiveTransform(adj_pd_pts, H)
			# mv_pt = cv2.transform(adj_pd_pts, H[:2, :3])			
		else :
			mv_pt = adj_pd_pts

		for i, pt in enumerate(mv_pt[0]) :
			if i == 2 :
				print("moved : " , pt)

			cv2.circle(in_img, (int(pt[0]), int(pt[1])), 7, (125, 125, 255), -1)

		left_x = int(mv_pt[0][0][0] - width / 2)
		left_y = int(mv_pt[0][0][1] - height /2)
		bottom_x = int(mv_pt[0][0][0] + width / 2)
		bottom_y = int(mv_pt[0][0][1] + height /2)

		print(left_x, left_y, bottom_x, bottom_y)
		crop = np.zeros((height, width, 3), dtype = "uint8")		

		if left_x < 0 or left_y < 0 or bottom_x > 3840 or bottom_y > 2160 :
			print("================ WARN ===================== ")
		else : 
			cv2.rectangle(in_img, (left_x, left_y), (bottom_x, bottom_y), (255, 0, 0), 3)
			crop = in_img[left_y: bottom_y, left_x: bottom_x]

		# crop = cv2.resize(crop, dsize=(960, 540), interpolation=cv2.INTER_CUBIC)

		return in_img, crop		