import random
import statistics
import numpy as np
from multiprocessing import Pool
from functools import partial

class Encounter:

	def __init__(self, limit, activity, ratio, mana_pool, healing, bol, mp5, base_crit, haste):
		self.fol = Healing(513, 574, 1.5, 180, healing, 185 * bol, base_crit, haste, 1, False)
		self.hl9 = Healing(1813, 2015, 2.5, 660-34, healing, 580 * bol, base_crit + 0.06 + 0.05, haste, 1, True)
		self.hl10 = Healing(1985, 2208, 2.5, 710-34, healing, 580 * bol, base_crit + 0.06 + 0.05, haste, 1, True)
		self.hl11 = Healing(2459, 2740, 2.5, 840-34, healing, 580 * bol, base_crit + 0.06 + 0.05, haste, 1, True)
		self.heals_list = [self.fol, self.hl9, self.hl10, self.hl11]
		self.fol_mana = 180
		self.time = 0.0
		self.healed = 0
		self.mana_tick = 2
		self.mp2 = mp5 / 5 * 2
		self.mana_pool = mana_pool
		self.max_mana = mana_pool
		self.last_tick = self.time
		self.activity = activity
		self.ratio = ratio
		self.limit = limit
		self.limit_reached = False
		self.pot_cd = 120
		self.pot_delay = 60
		self.pot_last_use = self.pot_delay - self.pot_cd
		self.rune_cd = 120
		self.rune_delay = 60
		self.rune_last_use = self.rune_delay - self.rune_cd
		self.illu_factor = 0.6
		self.favor = 0
		self.favor_cd = 120
		self.favor_delay = 60
		self.favor_last_use = self.favor_delay - self.favor_cd
		self.div_illu_duration = 15
		self.div_illu_cd = 120
		self.div_illu_delay = 60
		self.div_illu_last_use = self.div_illu_delay - self.div_illu_cd
		self.grace = 0
		self.grace_effect = 0.5
		self.grace_duration = 15
		self.grace_last_use = -16

	def refresh(self):
		self.time = 0.0
		self.healed = 0
		self.mana_pool = self.max_mana
		self.last_tick = self.time
		self.pot_last_use = self.pot_delay - self.pot_cd
		self.rune_last_use = self.rune_delay - self.rune_cd
		self.favor = 0
		self.favor_last_use = self.favor_delay - self.favor_cd
		self.div_illu_last_use = self.div_illu_delay - self.div_illu_cd
		self.grace = 0
		self.grace_last_use = -16
		self.limit_reached = False


class Healing:
	
	def __init__(self, lower, upper, cast, mana, healing, flat_heal, crit, haste, coeff, hl):
		self.lower = lower
		self.upper = upper
		self.cast = cast
		self.mana = mana
		self.healing = healing
		self.flat_heal = flat_heal
		self.crit = crit
		self.haste = haste
		self.base_cast = cast
		self.base_mana = mana
		self.critted = False
		self.coeff = coeff
		self.isHL = hl

	def updateHaste(self, t, last_grace):
		if self.isHL and (last_grace + 15) >= t:
			self.cast = (self.base_cast - 0.5) / ( 1 + self.haste / 1577)
		else:
			self.cast = self.base_cast / (1 + self.haste / 1577)
	
	def heal(self, favor):
		if random.random() > (1 - self.crit - favor):
			self.critted = True
			return (random.randint(self.lower, self.upper) + (self.healing * self.base_cast / 3.5) + self.flat_heal * self.coeff) * 1.12 * 1.5
		else:
			self.critted = False
			return random.randint(self.lower, self.upper) + ((self.healing * self.base_cast / 3.5) + self.flat_heal * self.coeff) * 1.12

def mana_source(lower, upper, modifier):
	return random.randint(lower,upper) * modifier

# mana from dark rune or demonic rune
def mana_rune():
	return mana_source(900, 1500, 1)

# mana from super mana pot with alchemist's stone
def mana_pot_alch():
	return mana_source(1800, 3000, 1.4)

def encounter(enc):
	heals_list = enc.heals_list
	fol_mana = enc.fol_mana
	fol = heals_list[0]
	time = enc.time
	healed = enc.healed
	mana_tick = enc.mana_tick
	mp2 = enc.mp2
	mana_pool = enc.mana_pool
	max_mana = enc.max_mana
	last_tick = enc.last_tick
	activity = enc.activity
	ratio = enc.ratio
	limit = enc.limit
	limit_reached = enc.limit_reached
#	pot_cd = enc.pot_cd
#	pot_delay = enc.pot_delay
#	pot_last_use = enc.pot_last_use
#	rune_cd = enc.rune_cd
#	rune_delay = enc.rune_delay
#	rune_last_use = enc.rune_last_use
	illu_factor = enc.illu_factor
	favor = enc.favor
	favor_cd = enc.favor_cd
	favor_delay = enc.favor_delay
	favor_last_use = enc.favor_last_use
	div_illu_duration = enc.div_illu_duration
	div_illu_cd = enc.div_illu_cd
	div_illu_delay = enc.div_illu_delay
	div_illu_last_use = enc.div_illu_last_use
	grace = enc.grace
	grace_effect = enc.grace_effect
	grace_duration = enc.grace_duration
	grace_last_use = enc.grace_last_use


	while mana_pool >= fol_mana:# and not limit_reached:
		# adds mana from mp5
		while last_tick < time:
			last_tick += mana_tick
			if (mana_pool) + mp2 > max_mana:
				mana_pool = max_mana
			else:
				mana_pool += mp2

		# whether to pot/rune
#		if (pot_last_use + pot_cd) <= time and time > pot_delay:
#			mana_pool += mana_pot_alch()
#			mana_pool += random.randint(900, 1500)
#			pot_last_use = time
#		if (rune_last_use + rune_cd) <= time and time > rune_delay:
#			mana_pool += mana_rune()
#			mana_pool += random.randint(2520, 4200)
#			rune_last_use = time
		
		# which heal/rank to cast

		spell = random.choices(heals_list, weights=ratio, k=1)[0]	
		if mana_pool < spell.base_mana:
			if (div_illu_last_use + div_illu_duration) >= time:
				if  mana_pool < (spell.base_mana / 2):
					break
			else:
				break

		if spell.isHL:
			grace = 1
#		else:
#			spell = fol
		spell.updateHaste(time, grace_last_use)

		# whether to pop cooldowns
		if (favor_last_use + favor_cd) <= time and time > favor_delay:
			favor = 1
		if (div_illu_last_use + div_illu_cd) <= time and time > div_illu_delay:
			div_illu_last_use = time


		# casts the spell. updates total healing and time elapsed.
		time += spell.cast
		healed += spell.heal(favor)
		
		# removes/adds mana from mana pool
		if (div_illu_last_use + div_illu_duration) >= time:
			mana_pool -= spell.base_mana / 2
		else:
			mana_pool -= spell.base_mana
		if spell.critted:
			mana_pool += spell.base_mana * illu_factor

		# puts DF on CD
		if favor == 1:
			favor = 0
			favor_last_use = time
		# updates last use for light's grace
		if grace == 1:
			grace = 0
			grace_last_use = time

		# adds delay for next cast
		delay_coeff = (1 - activity) / activity * spell.cast
		time += delay_coeff * 2 * (1 - random.random())

		# checks time limit
#		if time >= limit:
#			limit_reached = True

	return (time, healed, limit_reached)

def simulation(runs, limit, activity, ratio, mana_pool, healing, bol, mp5, crit, haste):
	tto = []
	hld = []
	over_limit = 0

	encounter_object = Encounter(limit, activity, ratio, mana_pool, healing, bol, mp5, crit, haste)
	assert sum(encounter_object.ratio) == 100

	for i in range(runs):
		encounter_object.refresh()
		sim = encounter(encounter_object)
		tto.append(sim[0])
		hld.append(sim[1])
		if sim[2]:
			over_limit += 1
	
	tto_median = statistics.median(tto)
	hld_median = statistics.median(hld)
	hps_median = hld_median / tto_median

	return [tto_median, hld_median, hps_median, over_limit / runs]
	
def callback_fn(result, n, i, tto, hld, hps):
	tto[n, i, 0] = result[0]
	tto[n, i, 1] = result[3]
	hld[n, i, 0] = result[1]
	hld[n, i, 1] = result[3]
	hps[n, i, 0] = result[2]
	hps[n, i, 1] = result[3]

def callback_err(result):
	print(result)

def gathering_results():
	runs = 10000
	activity = 0.80
	ratio = (25, 20, 0, 55)
	mana_pool = 16293
	crit = 0.29127
	crit_step = 0.00452 * 12
	mp5 = 265 + (140 + 50) * 0.8
	mp5_step = 4 * 12
	int_step = 10 * 12
	healing = 2074
	healing_step = 22 * 12
	haste = 0
	haste_step = 10 * 12
	bol = 1
	limit = 300

	steps = 2
	a_tto = np.zeros([5, steps, 2], float)
	a_hld = np.zeros([5, steps, 2], float)
	a_hps = np.zeros([5, steps, 2], float)

	with Pool(4) as pool:
		# +healing
		for i in range(steps):
			pool.apply_async(simulation, args=(runs, limit, activity, ratio, mana_pool, healing + i * healing_step, bol, mp5, crit, haste), callback=partial(callback_fn, n=0, i=i, tto=a_tto, hld=a_hld, hps=a_hps), error_callback=callback_err)

		# +mp5
		for i in range(steps):
			pool.apply_async(simulation, args=(runs, limit, activity, ratio, mana_pool, healing, bol, mp5 + i * mp5_step, crit, haste), callback=partial(callback_fn, n=1, i=i, tto=a_tto, hld=a_hld, hps=a_hps), error_callback=callback_err)

		# +crit
		for i in range(steps):
			pool.apply_async(simulation, args=(runs, limit, activity, ratio, mana_pool, healing, bol, mp5, crit + i * crit_step, haste), callback=partial(callback_fn, n=2, i=i, tto=a_tto, hld=a_hld, hps=a_hps), error_callback=callback_err)

		# +int
		for i in range(steps):
			pool.apply_async(simulation, args=(runs,
				limit,
				activity,
				ratio,
				mana_pool + i * int_step * 1.21 * 15,
				healing + i * int_step * 1.21 * 0.35,
				bol,
				mp5,
				crit + i * int_step * 1.21 / 80 / 100,
				haste),
				callback=partial(callback_fn, n=3, i=i, tto=a_tto, hld=a_hld, hps=a_hps), error_callback=callback_err)

		# +haste
		for i in range(steps):
			pool.apply_async(simulation, args=(runs, limit, activity, ratio, mana_pool, healing, bol, mp5, crit, haste + i * haste_step), callback=partial(callback_fn, n=4, i=i, tto=a_tto, hld=a_hld, hps=a_hps), error_callback=callback_err)

		pool.close()
		pool.join()
	np.save("tto_15_steps_10000_iter", a_tto)
	np.save("hld_15_steps_10000_iter", a_hld)
	np.save("hps_15_steps_10000_iter", a_hps)

if __name__ == '__main__':
	gathering_results()


#a = encounter(True, 0.88, (28, 45, 23, 4), 12723, 2077, 163, 0.2278, 0)
