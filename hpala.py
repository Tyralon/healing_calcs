import random
import statistics
import numpy as np
from multiprocessing import Pool
from functools import partial

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

	def getCast(self):
		return self.cast

	def updateGrace(self, t, last_use):
		if (last_use + 15) >= t:
			self.cast = self.base_cast - 0.5
		else:
			self.cast = self.base_cast
	
	def updateHaste(self, t, last_grace):
		if self.isHL and (last_grace + 15) >= t:
			self.cast = (self.base_cast - 0.5) / ( 1 + self.haste / 1577)
		else:
			self.cast = self.base_cast / (1 + self.haste / 1577)
	
	def setCritted(self, boolean):
		self.critted = boolean

	def getCritted(self):
		return self.critted

	def getBaseMana(self):
		return self.base_mana

	def getHL(self):
		return self.isHL

	def heal(self):
		if random.random() < self.crit:
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

def encounter(debug, activity, ratio, mana_pool, healing, bol, mp5, base_crit, haste):
	assert sum(ratio) == 100
	t = 0.0
	healed = 0
	
	fol = Healing(513, 574, 1.5, 180, healing, 185 * bol, base_crit, haste, 1, False)
	hl9 = Healing(1813, 2015, 2.5, 660, healing, 580 * bol, base_crit + 0.06, haste, 1, True)
	hl10 = Healing(1985, 2208, 2.5, 710, healing, 580 * bol, base_crit + 0.06, haste, 1, True)
	hl11 = Healing(2459, 2740, 2.5, 840, healing, 580 * bol, base_crit + 0.06, haste, 1, True)
	
	listOfHeals = [fol, hl9, hl10, hl11]

	fol_mana = 180

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
	
	limit = 420
	# limit encounters to 420s (7 mins)
	limit_reached = False

	while mana_pool >= fol_mana and not limit_reached:
		# adds mana from mp5
		while last_tick < t:
			last_tick += mana_tick
			mana_pool += mp2

		# whether to pot/rune
		if t > pot_delay and (pot_last_use + pot_cd) <= t:
			mana_pool += mana_pot_alch()
			pot_last_use = t
		if t > rune_delay and (rune_last_use + rune_cd) <= t:
			mana_pool += mana_rune()
			rune_last_use = t
		
		# which heal/rank to cast

		spell = random.choices(listOfHeals, weights=ratio, k=1)[0]	
		if spell.getHL() and mana_pool >= spell.getBaseMana():
			grace = 1
		else:
			spell = fol
		spell.updateHaste(t, grace_last_use)

		# whether to pop cooldowns
		if t > favor_delay and (favor_last_use + favor_cd) <= t:
			spell.setCritted(True)
			favor = 1
		if t > div_illu_delay and (div_illu_last_use + div_illu_cd) <= t:
			div_illu_last_use = t


		# casts the spell. updates total healing and time elapsed.
		if debug:
			print("Time:\t" + str(round(t, 1)))
		t += spell.getCast()
		if debug:
			temp_heal = spell.heal()
			print("Heal:\t\t" + str(round(temp_heal)))
			healed += temp_heal
			print("Total healed:\t\t" + str(round(healed)) + "\n")
			temp_heal = 0
		else:
			healed += spell.heal()
		
		# removes/adds mana from mana pool
		if (div_illu_last_use + div_illu_duration) >= t:
			mana_pool -= spell.getBaseMana() / 2
		else:
			mana_pool -= spell.getBaseMana()
		if spell.getCritted():
			mana_pool += spell.getBaseMana() * illu

		# puts DF on CD
		if favor == 1:
			favor = 0
			favor_last_use = t
		# updates last use for light's grace
		if grace == 1:
			grace = 0
			grace_last_use = t

		# adds delay for next cast
		t += (1 - activity) / activity * spell.getCast()

		# checks time limit
		if t >= limit:
			limit_reached = True
#			print("Limit reached! - Mana left: " + str(round(mana_pool)))

	return (t, healed, limit_reached)

def encounter_proc(tto, hld, counter, over_limit, c_lock, l_lock, runs, activity, ratio, mana_pool, healing, bol, mp5, crit, haste):

	while True:
		c_lock.acquire()
		if counter.value >= runs:
			c_lock.release()
			break
		else:
			counter.value += 1
		c_lock.release()

		result = encounter(False, activity, ratio, mana_pool, healing, bol, mp5, crit, haste)

		tto.append(result[0])
		hld.append(result[1])
		
		if result[2]:
			l_lock.acquire()
			over_limit.value += 1
			l_lock.release()


def simulation(runs, activity, ratio, mana_pool, healing, bol, mp5, crit, haste):
	tto = []
	hld = []
	over_limit = 0

	for i in range(runs):
		sim = encounter(False, activity, ratio, mana_pool, healing, bol, mp5, crit, haste)
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

def callback_er(result):
	print(result)
		

def gathering_results():
	runs = 5000
	activity = 0.75
	ratio = (10, 45, 20, 25)
	mana_pool = 16293
	crit = 0.29127
	crit_step = 0.0036
	mp5 = 265
	mp5_step = 3
	healing = 2074
	healing_step = 18
	haste = 0
	haste_step = 8
	bol = 1

	steps = 15
	a_tto = np.zeros([5, steps, 2], float)
	a_hld = np.zeros([5, steps, 2], float)
	a_hps = np.zeros([5, steps, 2], float)
	with Pool(4) as pool:
		# +healing
		for i in range(steps):
			pool.apply_async(simulation, args=(runs, activity, ratio, mana_pool, healing + i * healing_step, bol, mp5, crit, haste), callback=partial(callback_fn, n=0, i=i, tto=a_tto, hld=a_hld, hps=a_hps))

		# +mp5
		for i in range(steps):
			pool.apply_async(simulation, args=(runs, activity, ratio, mana_pool, healing, bol, mp5 + i * mp5_step, crit, haste), callback=partial(callback_fn, n=1, i=i, tto=a_tto, hld=a_hld, hps=a_hps))

		# +crit
		for i in range(steps):
			pool.apply_async(simulation, args=(runs, activity, ratio, mana_pool, healing, bol, mp5, crit + i * crit_step, haste), callback=partial(callback_fn, n=2, i=i, tto=a_tto, hld=a_hld, hps=a_hps))

		# +int
		for i in range(steps):
			pool.apply_async(simulation, args=(runs,
				activity,
				ratio,
				mana_pool + i * 8 * 1.21 * 15,
				healing + i * 8 * 1.21 * 0.35,
				bol,
				mp5,
				crit + i * 8 * 1.21 / 80 / 100,
				haste),
				callback=partial(callback_fn, n=3, i=i, tto=a_tto, hld=a_hld, hps=a_hps))

		# +haste
		for i in range(steps):
			pool.apply_async(simulation, args=(runs, activity, ratio, mana_pool, healing, bol, mp5, crit, haste + i * haste_step), callback=partial(callback_fn, n=4, i=i, tto=a_tto, hld=a_hld, hps=a_hps))

		pool.close()
		pool.join()
	np.save("tto_15_steps_10000_iter", a_tto)
	np.save("hld_15_steps_10000_iter", a_hld)
	np.save("hps_15_steps_10000_iter", a_hps)

if __name__ == '__main__':
	gathering_results()


#a = encounter(True, 0.88, (28, 45, 23, 4), 12723, 2077, 163, 0.2278, 0)
