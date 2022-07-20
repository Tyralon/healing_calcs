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
	
def eq_point_calc_libram(hld, hps, referenceValue, normalizingFactor):
	arr = []
	for i in range(hld.shape[0]):
		arr.append(eq_point_calc2(hld[i], hps[i], referenceValue, normalizingFactor))

	return arr

def eq_point_calc2(hld, hps, referenceValue, normalizingFactor):
	return eq_point_helper(hld, hps, 1) / referenceValue * normalizingFactor

def roundStrN(var, n):
	return str(round(var, n))

def roundStr(var):
	return str(round(var))

def pretty_printing(helper_function, tto, hld, hps, result_tto, result_hld, result_hps, headline):
	print("\n------------------------------------------------------ TTO ----------------------------------------------------\n")
	print(headline)
	helper_function(tto, result_tto)
	print("\n------------------------------------------------------ HLD ----------------------------------------------------\n")
	print(headline)
	helper_function(hld, result_hld)
	print("\n------------------------------------------------------ HPS ----------------------------------------------------\n")
	print(headline)
	helper_function(hps, result_hps)

def pretty_printing_regular(tto, hld, hps, result_tto, result_hld, result_hps, normalizingFactor):
	headline = "increased spell power\tincreased mp5\t\tincreased crit\t\tincreased int\t\tincreased haste"
	pretty_printing(pretty_printing_helper, tto, hld, hps, result_tto, result_hld, result_hps, headline)
	print("\n*************************************************** EQ POINTS *************************************************")
	pretty_printing_eqpts(result_hld, result_hps, 19, 8, 16, 16, 16, eq_point_helper(result_hld[0], result_hps[0], 19), normalizingFactor)

def pretty_printing_eqpts(hld, hps, sp_step, mp5_step, crit_step, int_step, haste_step, referenceValue, normalizingFactor):
	eq_points_stats = eq_point_calc(hld, hps, sp_step, mp5_step, crit_step, int_step, haste_step, referenceValue, normalizingFactor)
	for i in eq_points_stats:
		if i >= 100:
			print(roundStr(i) + "\t\t\t", end='')
		else:
			print(roundStrN(i, 1) + "\t\t\t", end='')
	print()

def pretty_printing_eqpts_libram(hld, hps, referenceValue, normalizingFactor):
	eq_points_stats = eq_point_calc_libram(hld, hps, referenceValue, normalizingFactor)
	for i in eq_points_stats:
		if i >= 100:
			print(roundStr(i) + "\t\t\t", end='')
		else:
			print(roundStrN(i, 1) + "\t\t\t", end='')
	print()

def pretty_printing_libram(tto, hld, hps, result_tto, result_hld, result_hps, extra_hld, extra_hps, numberOfItems, normalizingFactor):
	referenceValue = eq_point_helper(extra_hld[0], extra_hps[0], 19)
	width = 5
	i = 0

	headline = "Seal of Wisdom\t\tSeal of Light\t\t2-piece Tier 7\t\t4-piece Tier 7\t\tLibram of Renewal"
	pretty_printing(pretty_printing_helper_libram, tto[i:i+width], hld[i:i+width], hps[i:i+width], result_tto[i:i+width], result_hld[i:i+width], result_hps[i:i+width], headline)
	print("\n*************************************************** EQ POINTS *************************************************")
	pretty_printing_eqpts_libram(result_hld[i:i+width], result_hps[i:i+width], referenceValue, normalizingFactor)
	if i + width < numberOfItems:
		i += width
	else:
		while i < numberOfItems:
			i += 1

	headline = "2-piece Tier 6\t\t4-piece Tier 6\t\tLibram of Absolute...\tLibram of Mending\tLibram of Tolerance\t"
	pretty_printing(pretty_printing_helper_libram, tto[i:i+width], hld[i:i+width], hps[i:i+width], result_tto[i:i+width], result_hld[i:i+width], result_hps[i:i+width], headline)
	print("\n*************************************************** EQ POINTS *************************************************")
	pretty_printing_eqpts_libram(result_hld[i:i+width], result_hps[i:i+width], referenceValue, normalizingFactor)
	if i + width < numberOfItems:
		i += width
	else:
		while i < numberOfItems:
			i += 1

	headline = "Libram of Souls Red...\tLibram of the Lightbringer"
	pretty_printing(pretty_printing_helper_libram, tto[i:i+width], hld[i:i+width], hps[i:i+width], result_tto[i:i+width], result_hld[i:i+width], result_hps[i:i+width], headline)
	print("\n*************************************************** EQ POINTS *************************************************")
	pretty_printing_eqpts_libram(result_hld[i:i+width], result_hps[i:i+width], referenceValue, normalizingFactor)

def pretty_printing_helper_libram(arr, result):

	def single_cell(arr):
		baseline = arr[0,0]
		return roundStr(baseline) + "\t\t\t"
		
	def double_cell(arr, result):
		nextStep = arr[1,0]
		improvement = result
		return roundStr(nextStep) + "\t" + roundStrN(improvement, 3) + "%\t\t"
		
	baseline = ""
	improvement = ""

	for i in range(arr.shape[0]):
		baseline += single_cell(arr[i])

	for j in range(arr.shape[0]):
		improvement += double_cell(arr[j], result[j])

	print(baseline)
	print(improvement)

def pretty_printing_helper(arr, result):
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


