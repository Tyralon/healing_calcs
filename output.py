import numpy as np

def improvement_calc(arr, steps):
	return (arr[1,0] - arr[0,0]) / steps / arr[0,0] * 100

def improvement_calc_arr(data, result, steps):
	arrayLength = data.shape[0]
	for i in range(arrayLength):
		result[i] = improvement_calc(data[i], steps)

def analysis(tto, hld, hps, result_tto, result_hld, result_hps, steps):
	improvement_calc_arr(tto, result_tto, steps)
	improvement_calc_arr(hld, result_hld, steps)
	improvement_calc_arr(hps, result_hps, steps)

def analysis_libram(tto, hld, hps, result_tto, result_hld, result_hps):
	analysis(tto, hld, hps, result_tto, result_hld, result_hps, 1)
	
def eq_point_helper(hld, hps, step):
	return (hld + hps) / step

def eq_point_calc(hld, hps, sp_step, mp5_step, crit_step, int_step, haste_step, referenceValue, normalizingFactor):

	sp_eqpts = eq_point_helper(hld[0], hps[0], sp_step) / referenceValue * normalizingFactor
	mp5_eqpts = eq_point_helper(hld[1], hps[1], mp5_step) / referenceValue * normalizingFactor
	crit_eqpts = eq_point_helper(hld[2], hps[2], crit_step) / referenceValue * normalizingFactor
	int_eqpts = eq_point_helper(hld[3], hps[3], int_step) / referenceValue * normalizingFactor
	haste_eqpts = eq_point_helper(hld[4], hps[4], haste_step) / referenceValue * normalizingFactor

	return (sp_eqpts, mp5_eqpts, crit_eqpts, int_eqpts, haste_eqpts)

def roundStrN(var, n):
	return str(round(var, n))

def roundStr(var):
	return str(round(var))

def pretty_printing(helper_function, tto, hld, hps, result_tto, result_hld, result_hps, steps, headline):
	print("\n------------------------------------------------------ TTO ----------------------------------------------------\n")
	print(headline)
	helper_function(tto, result_tto, steps)
	print("\n------------------------------------------------------ HLD ----------------------------------------------------\n")
	print(headline)
	helper_function(hld, result_hld, steps)
	print("\n------------------------------------------------------ HPS ----------------------------------------------------\n")
	print(headline)
	helper_function(hps, result_hps, steps)

def pretty_printing_regular(tto, hld, hps, result_tto, result_hld, result_hps, steps):
	headline = "increased spell power\tincreased mp5\t\tincreased crit\t\tincreased int\t\tincreased haste"
	pretty_printing(pretty_printing_helper, tto, hld, hps, result_tto, result_hld, result_hps, steps, headline)
	print("\n*************************************************** EQ POINTS *************************************************")
	pretty_printing_eqpts(result_hld, result_hps, 19, 8, 16, 16, 16, eq_point_helper(result_hld[0], result_hps[0], 19), 10)

def pretty_printing_eqpts(hld, hps, sp_step, mp5_step, crit_step, int_step, haste_step, referenceValue, normalizingFactor):
	eq_points_stats = eq_point_calc(hld, hps, sp_step, mp5_step, crit_step, int_step, haste_step, referenceValue, normalizingFactor)
	for i in eq_points_stats:
		if i >= 100:
			print(roundStr(i) + "\t\t\t", end='')
		else:
			print(roundStrN(i, 1) + "\t\t\t", end='')
	print()

def pretty_printing_libram(tto, hld, hps, result_tto, result_hld, result_hps, extra_hld, extra_hps, steps, normalizingFactor):
	referenceValue = eq_point_helper(extra_hld[0], extra_hps[0], 19)

	headline = "Seal of Wisdom\t\tSeal of Light\t\t2-piece Tier 7\t\t4-piece Tier 7\t\tLibram of Renewal"
	pretty_printing(pretty_printing_helper_libram, tto, hld, hps, result_tto, result_hld, result_hps, steps, headline)
	print("\n*************************************************** EQ POINTS *************************************************")
	pretty_printing_eqpts(result_hld[:5], result_hps[:5], 1, 1, 1, 1, 1, referenceValue, normalizingFactor)
	
	headline = "2-piece Tier 6\t\t4-piece Tier 6\t\tLibram of Absolute...\tLibram of Mending\tLibram of Tolerance\t"
	pretty_printing(pretty_printing_helper_libram, tto[5:10], hld[5:10], hps[5:10], result_tto[5:10], result_hld[5:10], result_hps[5:10], steps, headline)
	print("\n*************************************************** EQ POINTS *************************************************")
	pretty_printing_eqpts(result_hld[5:10], result_hps[5:10], 1, 1, 1, 1, 1, referenceValue, normalizingFactor)

	headline = "Libram of Souls Red...\tLibram of the Lightbringer"
	pretty_printing(pretty_printing_helper_libram, tto[10:15], hld[10:15], hps[10:15], result_tto[10:15], result_hld[10:15], result_hps[10:15], steps, headline)
	print("\n*************************************************** EQ POINTS *************************************************")
	pretty_printing_eqpts(result_hld[10:15], result_hps[10:15], 1, 1, 1, 1, 1, referenceValue, normalizingFactor)

def pretty_printing_helper_libram(arr, result, steps):
	heal = (arr[0,0,0], arr[0,1,0])
	mp5 = (arr[1,0,0], arr[1,1,0])
	crit = (arr[2,0,0], arr[2,1,0])
	intellect = (arr[3,0,0], arr[3,1,0])
	haste = (arr[4,0,0], arr[4,1,0])

	print(roundStr(heal[0]) + "\t\t\t" + roundStr(mp5[0]) + "\t\t\t" + roundStr(crit[0]) + "\t\t\t" + roundStr(intellect[0]) + "\t\t\t" + roundStr(haste[0]))

	print(roundStr(heal[1]) + "\t" + roundStrN(result[0], 3) + "%\t\t" + \
			 roundStr(mp5[1]) + "\t" + roundStrN(result[1], 3) + "%\t\t" + \
			 roundStr(crit[1]) + "\t" + roundStrN(result[2], 3) + "%\t\t" + \
			 roundStr(intellect[1]) + "\t" + roundStrN(result[3], 3) + "%\t\t" + \
			 roundStr(haste[1]) + "\t" + roundStrN(result[4], 3) + "%")
	
"""
def pretty_printing_helper_libram(arr, result, steps):
	print("wisdom\t\t\tlight\t\t\t4p T7\t\t\trenewal\t\t\tabsolute truth\t\tmending\t\t\ttolerance\t\tsouls redeemed\t\tlightbringer")
	wisdom = (arr[0,0,0], arr[0,1,0])
	light = (arr[1,0,0], arr[1,1,0])
	fourT7 = (arr[2,0,0], arr[2,1,0])
	renewal = (arr[3,0,0], arr[3,1,0])
	loat = (arr[4,0,0], arr[4,1,0])
	mending = (arr[5,0,0], arr[5,1,0])
	tolerance = (arr[6,0,0], arr[6,1,0])
	souls = (arr[7,0,0], arr[7,1,0])
	lightbringer = (arr[8,0,0], arr[8,1,0])

	print(roundStr(wisdom[0]) + "\t\t\t" + roundStr(light[0]) + "\t\t\t" + roundStr(fourT7[0]) + "\t\t\t" + \
			 roundStr(renewal[0]) + "\t\t\t" + roundStr(loat[0]) + "\t\t\t" + roundStr(mending[0]) + "\t\t\t" + \
			 roundStr(tolerance[0]) + "\t\t\t" + roundStr(souls[0]) + "\t\t\t" + roundStr(lightbringer[0]))
	print(roundStr(wisdom[1]) + "\t" + roundStrN(result[0], 3) + "%\t\t" + \
			 roundStr(light[1]) + "\t" + roundStrN(result[1], 3) + "%\t\t" + \
			 roundStr(fourT7[1]) + "\t" + roundStrN(result[2], 3) + "%\t\t" + \
			 roundStr(renewal[1]) + "\t" + roundStrN(result[3], 3) + "%\t\t" + \
			 roundStr(loat[1]) + "\t" + roundStrN(result[4], 3) + "%\t\t" + \
			 roundStr(mending[1]) + "\t" + roundStrN(result[5], 3) + "%\t\t" + \
			 roundStr(tolerance[1]) + "\t" + roundStrN(result[6], 3) + "%\t\t" + \
			 roundStr(souls[1]) + "\t" + roundStrN(result[7], 3) + "%\t\t" + \
			 roundStr(lightbringer[1]) + "\t" + roundStrN(result[8], 3) + "%")
"""

def pretty_printing_helper(arr, result, steps):
	heal = (arr[0,0,0], arr[0,1,0])
	mp5 = (arr[1,0,0], arr[1,1,0])
	crit = (arr[2,0,0], arr[2,1,0])
	intellect = (arr[3,0,0], arr[3,1,0])
	haste = (arr[4,0,0], arr[4,1,0])

	print(roundStr(heal[0]) + "\t\t\t" + roundStr(mp5[0]) + "\t\t\t" + roundStr(crit[0]) + "\t\t\t" + roundStr(intellect[0]) + "\t\t\t" + roundStr(haste[0]))

	print(roundStr(heal[1]) + "\t" + roundStrN(result[0], 3) + "%\t\t" + \
			 roundStr(mp5[1]) + "\t" + roundStrN(result[1], 3) + "%\t\t" + \
			 roundStr(crit[1]) + "\t" + roundStrN(result[2], 3) + "%\t\t" + \
			 roundStr(intellect[1]) + "\t" + roundStrN(result[3], 3) + "%\t\t" + \
			 roundStr(haste[1]) + "\t" + roundStrN(result[4], 3) + "%")

steps = 12
l_tto = np.load("tto_12_gems.npy")
l_hps = np.load("hps_12_gems.npy")
l_hld = np.load("hld_12_gems.npy")
result_tto = np.zeros([5], float)
result_hld = np.zeros([5], float)
result_hps = np.zeros([5], float)

analysis(l_tto, l_hld, l_hps, result_tto, result_hld, result_hps, steps)

pretty_printing_regular(l_tto, l_hld, l_hps, result_tto, result_hld, result_hps, steps)

steps = 1
libram_tto = np.load("tto_libram.npy")
libram_hps = np.load("hps_libram.npy")
libram_hld = np.load("hld_libram.npy")
result_libram_tto = np.ones([15], float)
result_libram_hld = np.ones([15], float)
result_libram_hps = np.ones([15], float)

analysis_libram(libram_tto, libram_hld, libram_hps, result_libram_tto, result_libram_hld, result_libram_hps)

pretty_printing_libram(libram_tto, libram_hld, libram_hps, result_libram_tto, result_libram_hld, result_libram_hps, result_hld, result_hps, steps, 10)
