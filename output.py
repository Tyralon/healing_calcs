import random
import statistics
import numpy as np

def analysis(arr, steps):
    print("\nincreased healing")
    x = np.arange(0, steps)
    for i in range(steps):
        print(str(round(arr[0, i, 0], 2)) + ", " + str(round(arr[0, i, 1] * 100)) + "% ")
    z = np.polyfit(x, arr[0][:,0], 1)
    print("OLS: " + str(round(z[0], 2)))
    print("\nincreased mp5")
    for i in range(steps):
        print(str(round(arr[1, i, 0], 2)) + ", " + str(round(arr[1, i, 1] * 100)) + "% ")
    z = np.polyfit(x, arr[1][:,0], 1)
    print("OLS: " + str(round(z[0], 2)))
    print("\nincreased crit")
    for i in range(steps):
        print(str(round(arr[2, i, 0], 2)) + ", " + str(round(arr[2, i, 1] * 100)) + "% ")
    z = np.polyfit(x, arr[2][:,0], 1)
    print("OLS: " + str(round(z[0], 2)))



l_tto = np.load("tto_15_steps_10000_iter.npy")
l_hps = np.load("hps_15_steps_10000_iter.npy")
l_hld = np.load("hld_15_steps_10000_iter.npy")
print("\nTTO")
analysis(l_tto, 15)
print("\nhealed")
analysis(l_hld, 15)
print("\nHPS")
analysis(l_hps, 15)
