import random
import statistics
import numpy as np

def ana_helper(arr, steps):
	x = np.arange(0, steps)
	y = np.zeros(steps)
	for i in range(steps - 1):
		y[i] = (arr[i+1, 0] - arr[i, 0]) / arr[i, 0]
	for i in range(steps):
		if i == 0:
			print(str(round(arr[i, 0], 2)) + "\t\t" + str(round(arr[i, 1] * 100)) + "% ")
		else:
			print(str(round(arr[i, 0], 2)) + "\t" + str(round(y[i-1] * 100, 3)) + "%\t" + str(round(arr[i, 1] * 100)) + "% ")

	z = np.polyfit(x, arr[:,0], 1)
	print("OLS: " + str(round(z[0], 2)))
	print("Average increase: " + str(round(np.mean(y) * 100, 3)) + "%")


def analysis(arr, steps):
	print("\nincreased healing")
	ana_helper(arr[0], steps)
	print("\nincreased mp5")
	ana_helper(arr[1], steps)
	print("\nincreased crit")
	ana_helper(arr[2], steps)
	print("\nincreased int")
	ana_helper(arr[3], steps)
	print("\nincreased haste")
	ana_helper(arr[4], steps)



l_tto = np.load("tto_15_steps_10000_iter.npy")
l_hps = np.load("hps_15_steps_10000_iter.npy")
l_hld = np.load("hld_15_steps_10000_iter.npy")
print("\nTTO")
analysis(l_tto, 15)
print("\nhealed")
analysis(l_hld, 15)
print("\nHPS")
analysis(l_hps, 15)
