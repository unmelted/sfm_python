from scipy import interpolate
import matplotlib.pyplot as plt
import numpy as np
import cv2

class Interpolate(object):
	
	def store_posisition(self, wcenter):
		self.yy = []
		self.xx = []
		self.x = []
		self.n = 0
		self.x_fit = []
		self.y_fit = []

		for i in range(len(wcenter)) :
			self.xx.append(wcenter[i][0])
			self.yy.append(wcenter[i][1])

		self.n = len(self.xx)
		self.x = range(0, self.n)
		print("Interpoateion n", self.n)

	def make_trajectory(self) :
		tckx = interpolate.splrep(self.x ,self.xx, s=2400, k=2)
		tcky = interpolate.splrep(self.x ,self.yy, s=2400, k=2)

		x_new = np.linspace(min(self.x), max(self.x), self.n)
		self.x_fit = interpolate.BSpline(*tckx)(x_new)
		self.y_fit = interpolate.BSpline(*tcky)(x_new)

		##display


	def show_trajectory(self, stadium, root_path) :
		# plt.title("BSpline curve fitting")
		# plt.plot(self.x, self.xx, 'ro', label="original")
		# plt.plot(self.x, self.x_fit, '-c', label="B-spline")
		# plt.legend(loc='best', fancybox=True, shadow=True)
		# plt.grid()
		# plt.show()

		# plt.title("BSpline curve fitting2")
		# plt.plot(self.x, self.yy, 'ro', label="original")
		# plt.plot(self.x, self.y_fit, '-c', label="B-spline")
		# plt.legend(loc='best', fancybox=True, shadow=True)
		# plt.grid()
		# plt.show()

		ground = cv2.imread(stadium)

		for i in range(len(self.x)):
			w_cenx = self.x_fit[i]
			w_ceny = self.y_fit[i]
			print(i, w_cenx, w_ceny)         
			cv2.circle(ground, (int(w_cenx), int(w_ceny)), 2, (255, 255, 0), -1)

		filename = root_path + '/dbg_ground_o.png'
		cv2.imwrite(filename, ground)


'''
y = [0, 1, 3, 4, 3, 5, 7, 5, 2, 3, 4, 8, 9, 8, 7]
n = len(y)
x = range(0, n)

# plt.plot(x, y, 'ro', label="original")
# plt.plot(x, y, 'b', label="linear interpolation")
# plt.title("Target data")
# plt.legend(loc='best', fancybox=True, shadow=True)
# plt.grid()
# plt.show()

tck = interpolate.splrep(x, y, s=20, k=3)
x_new = np.linspace(min(x), max(x), 100)
y_fit = interpolate.BSpline(*tck)(x_new)

plt.title("BSpline curve fitting")
plt.plot(x, y, 'ro', label="original")
plt.plot(x_new, y_fit, '-c', label="B-spline")
plt.legend(loc='best', fancybox=True, shadow=True)
plt.grid()
plt.show()
'''