import random
import statistics
import numpy as np

def ana_helper(arr, steps):
	x = np.arange(0, steps)
	for i in range(steps):
		print(str(round(arr[i, 0], 2)) + ", " + str(round(arr[i, 1] * 100)) + "% ")
	z = np.polyfit(x, arr[:,0], 1)
	print("OLS: " + str(round(z[0], 2)))


def analysis(arr, steps):
	print("\nincreased healing")
	ana_helper(arr[0], steps)
	x = np.arange(0, steps)
	print("\nincreased mp5")
	ana_helper(arr[1], steps)
	print("\nincreased crit")
	ana_helper(arr[2], steps)



l_tto = np.load("tto_15_steps_10000_iter.npy")
l_hps = np.load("hps_15_steps_10000_iter.npy")
l_hld = np.load("hld_15_steps_10000_iter.npy")
print("\nTTO")
analysis(l_tto, 15)
print("\nhealed")
analysis(l_hld, 15)
print("\nHPS")
analysis(l_hps, 15)
