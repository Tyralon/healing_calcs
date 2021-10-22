import random
import statistics
import numpy as np


def heal(lower, upper, cast, healing, critted):
	if critted:
		return (random.randint(lower, upper) + (healing * cast / 3.5 * 1.12)) * 1.5
	else:
		return random.randint(lower, upper) + healing * cast / 3.5 * 1.12

def flash_of_light(healing, critted):
	return heal(513, 574, 1.5, healing, critted)

def holy_light_r9(healing, critted):
	return heal(1813, 2015, 2.5, healing, critted)

def holy_light_r11(healing, critted):
	return heal(2459, 2740, 2.5, healing, critted)

def mana_source(lower, upper, modifier):
	return random.randint(lower,upper) * modifier

# mana from dark rune or demonic rune
def mana_rune():
	return mana_source(900, 1500, 1)

# mana from super mana pot with alchemist's stone
def mana_pot_alch():
	return mana_source(1800, 3000, 1.4)

# whether we get a crit on our spell
def spell_crit(crit_percentage):
	return random.random() < crit_percentage

def encounter(activity, ratio, mana_pool, healing, mp5, base_crit):
	assert sum(ratio) == 100
	t = 0.0
	healed = 0

	fol_mana = 180
	fol_cast = 1.5
	hl9_mana = 660
	hl11_mana = 840
	hl_cast = 2.5

	grace = 0
	grace_effect = 0.5
	grace_duration = 15
	grace_last_use = -16

	mana_tick = 2
	mp2 = mp5 / 5 * 2
	last_tick = t

	pot_cd = 120
	pot_delay = 60
	pot_last_use = pot_delay - pot_cd

	rune_cd = 120
	rune_delay = 60
	rune_last_use = rune_delay - rune_cd

	illu = 0.6
	
	favor = 0
	favor_cd = 120
	favor_delay = 30
	favor_last_use = favor_delay - favor_cd

	div_illu_duration = 15
	div_illu_cd = 180
	div_illu_delay = 30
	div_illu_last_use = div_illu_delay - div_illu_cd
	
	fol_ratio = ratio[0] / 100
	hl9_ratio = fol_ratio + ratio[1] / 100

	limit = 420
	# limit encounters to 420s (7 mins)
	limit_reached = False

	while mana_pool >= fol_mana and not limit_reached:
		while last_tick < t:
			last_tick += mana_tick
			mana_pool += mp2

		if t > pot_delay and (pot_last_use + pot_cd) <= t:
			mana_pool += mana_pot_alch()
			pot_last_use = t
		if t > rune_delay and (rune_last_use + rune_cd) <= t:
			mana_pool += mana_rune()
			rune_last_use = t
		
		rvar = random.random()
		if rvar < fol_ratio:
			crit = base_crit
			spell_mana = fol_mana
			spell_cast = fol_cast
		elif rvar < hl9_ratio:
			crit = base_crit + 0.06
			spell_mana = hl9_mana
			if (grace_last_use + grace_duration) >= t:
				spell_cast = hl_cast - grace_effect
			else:
				spell_cast = hl_cast
			grace = 1
		else:
			crit = base_crit + 0.06
			spell_mana = hl11_mana
			if (grace_last_use + grace_duration) >= t:
				spell_cast = hl_cast - grace_effect
			else:
				spell_cast = hl_cast
			grace = 1
			

		if t > favor_delay and (favor_last_use + favor_cd) <= t:
			favor = 1
			crit = 1.0

		if t > div_illu_delay and (div_illu_last_use + div_illu_cd) <= t:
			div_illu_last_use = t

		t += spell_cast
		if (div_illu_last_use + div_illu_duration) >= t:
			mana_pool -= spell_mana / 2
		else:
			mana_pool -= spell_mana

		if spell_crit(crit):
			mana_pool += spell_mana * illu
			if spell_mana == 180:
				healed += flash_of_light(healing, True)
			if spell_mana == 660:
				healed += holy_light_r9(healing, True)
			if spell_mana == 840:
				healed += holy_light_r11(healing, True)
		else:
			if spell_mana == 180:
				healed += flash_of_light(healing, False)
			if spell_mana == 660:
				healed += holy_light_r9(healing, False)
			if spell_mana == 840:
				healed += holy_light_r11(healing, False)

		if favor == 1:
			favor = 0
			favor_last_use = t

		if grace == 1:
			grace = 0
			grace_last_use = t

		# adds delay based on y = -(x-1) / x
		t += -(activity - 1) / activity * spell_cast
		if t >= limit:
			limit_reached = True
#			print("Limit reached! - Mana left: " + str(round(mana_pool)))
	return (t, healed, limit_reached)

def simulation(runs, activity, ratio, mana_pool, healing, mp5, crit):
	tto = []
	healList = []
	over_limit = 0
	for i in range(runs):
		sim = encounter(activity, ratio, mana_pool, healing, mp5, crit)
		tto.append(sim[0])
		healList.append(sim[1])
		if sim[2]:
			over_limit += 1

	tto_median = statistics.median(tto)
	heal_median = statistics.median(healList)
	hps_median = heal_median / tto_median

	return [tto_median, heal_median, hps_median, over_limit / runs]

def gathering_results():
	runs = 5000
	activity = 0.9
	ratio = [75, 20, 5]
	mana_pool = 11000
	crit = 0.1900
	crit_step = 0.0036
	mp5 = 150
	mp5_step = 3
	healing = 1900
	healing_step = 18

	steps = 15
	a_tto = np.zeros([3, steps, 2], float)
	a_hld = np.zeros([3, steps, 2], float)
	a_hps = np.zeros([3, steps, 2], float)
	for i in range(steps):
		a = simulation(runs, activity, ratio, mana_pool, healing + i * healing_step, mp5, crit)
		a_tto[0, i, 0] = a[0]
		a_tto[0, i, 1] = a[3]
		a_hld[0, i, 0] = a[1]
		a_hld[0, i, 1] = a[3]
		a_hps[0, i, 0] = a[2]
		a_hps[0, i, 1] = a[3]
	for j in range(steps):
		a = simulation(runs, activity, ratio, mana_pool, healing, mp5 + j * mp5_step, crit)
		a_tto[1, j, 0] = a[0]
		a_tto[1, j, 1] = a[3]
		a_hld[1, j, 0] = a[1]
		a_hld[1, j, 1] = a[3]
		a_hps[1, j, 0] = a[2]
		a_hps[1, j, 1] = a[3]
	for k in range(steps):
		a = simulation(runs, activity, ratio, mana_pool, healing, mp5, crit + k * crit_step)
		a_tto[2, k, 0] = a[0]
		a_tto[2, k, 1] = a[3]
		a_hld[2, k, 0] = a[1]
		a_hld[2, k, 1] = a[3]
		a_hps[2, k, 0] = a[2]
		a_hps[2, k, 1] = a[3]
	np.save("tto_15_steps_10000_iter", a_tto)
	np.save("hld_15_steps_10000_iter", a_hld)
	np.save("hps_15_steps_10000_iter", a_hps)

gathering_results()

