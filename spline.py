from scipy import interpolate
import matplotlib.pyplot as plt
import numpy as np

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
