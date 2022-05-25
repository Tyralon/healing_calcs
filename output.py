import numpy as np

def ana_helper(arr, steps):
	baseline = arr[0, 0]
	topline = arr[1, 0]
	improvement = (topline - baseline) / steps / baseline * 100
	baseline_ot = arr[0, 1]
	topline_ot = arr[1, 1]
	
	print(str(round(baseline, 2)) + "\t\t" + str(round(baseline_ot)) + "%")
	print(str(round(topline, 2)) + "\t" + str(round(improvement, 3)) + "%\t"  + str(round(topline_ot)) + "%")

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


steps = 12
l_tto = np.load("tto_15_steps_10000_iter.npy")
l_hps = np.load("hps_15_steps_10000_iter.npy")
l_hld = np.load("hld_15_steps_10000_iter.npy")
print("\nTTO")
analysis(l_tto, steps)
print("\nhealed")
analysis(l_hld, steps)
print("\nHPS")
analysis(l_hps, steps)
