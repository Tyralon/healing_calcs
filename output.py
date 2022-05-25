import numpy as np

def ana_helper(arr, steps):
	baseline = arr[0, 0]
	topline = arr[1, 0]
	improvement = (topline - baseline) / steps / baseline * 100
	baseline_ot = arr[0, 1] * 100
	topline_ot = arr[1, 1] * 100
	
	base_str = str(round(baseline)) + "\t\t" + str(round(baseline_ot)) + "%"
	top_str = str(round(topline)) + "\t" + str(round(improvement, 3)) + "%\t"  + str(round(topline_ot)) + "%"

	return (base_str, top_str)

def analysis(arr, steps):
	print("\nincreased healing\tincreased mp5\t\tincreased crit\t\tincreased int\t\tincreased haste")
	heal = ana_helper(arr[0], steps)
	mp5 = ana_helper(arr[1], steps)
	crit = ana_helper(arr[2], steps)
	intellect = ana_helper(arr[3], steps)
	haste = ana_helper(arr[4], steps)

	print(heal[0] + "\t" + mp5[0] + "\t" + crit[0] + "\t" + intellect[0] + "\t" + haste[0])

	print(heal[1] + "\t" + mp5[1] + "\t" + crit[1] + "\t" + intellect[1] + "\t" + haste[1])

	

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
