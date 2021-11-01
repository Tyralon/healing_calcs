import random
import statistics
import numpy as np

def ana_helper(arr):
#	x = np.arange(0, steps)
	y = np.zeros(2)
	y[1] = (arr[1, 0] - arr[0, 0]) / arr[0, 0]
	print(str(round(arr[0, 0], 2)) + "\t\t" + str(round(arr[0, 1] * 100)) + "% ")
	print(str(round(arr[1, 0], 2)) + "\t" + str(round(y[1] * 100, 3)) + "%\t" + str(round(arr[1, 1] * 100)) + "% ")

#	z = np.polyfit(x, arr[:,0], 1)
#	print("OLS: " + str(round(z[0], 2)))
#	print("Average increase: " + str(round(np.mean(y) * 100, 3)) + "%")


def analysis(tto, hld, hps, index):
	print("\nTTO")
	ana_helper(tto[index])
	print("\nHealed")
	ana_helper(hld[index])
	print("\nHPS")
	ana_helper(hps[index])


l_tto = np.load("tto_libram.npy")
l_hld = np.load("hld_libram.npy")
l_hps = np.load("hps_libram.npy")
print("\nLibram of Absolute Truth")
analysis(l_tto, l_hld, l_hps, 0)
print("\nLibram of Souls Redeemed")
analysis(l_tto, l_hld, l_hps, 1)
print("\nBlessed Book of Nagrand")
analysis(l_tto, l_hld, l_hps, 2)
print("\nLibram of the Lightbringer")
analysis(l_tto, l_hld, l_hps, 3)
print("\nLibram of Mending")
analysis(l_tto, l_hld, l_hps, 4)
