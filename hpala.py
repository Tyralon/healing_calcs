import random
import statistics
import numpy as np
from multiprocessing import Pool
from functools import partial

class Encounter:

	def __init__(self, limit, activity, ratio, mana_pool, healing, fol_heal, hl_heal, fol_bol, hl_bol, reduction, mp5, base_crit, haste):
		self.fol = Healing(513, 574, 1.5, 180, 0, healing + fol_heal, fol_bol, base_crit, haste, 1.045065, False)
		self.hl9 = Healing(1813, 2015, 2.5, 660, reduction, healing + hl_heal, hl_bol, base_crit + 0.06 + 0.05, haste, 1, True)
		self.hl10 = Healing(1985, 2208, 2.5, 710, reduction, healing + hl_heal, hl_bol, base_crit + 0.06 + 0.05, haste, 1, True)
		self.hl11 = Healing(2459, 2740, 2.5, 840, reduction, healing + hl_heal, hl_bol, base_crit + 0.06 + 0.05, haste, 1, True)
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

	def pickSpell(self):
		return random.choices(self.heals_list, weights=self.ratio, k=1)[0]

	def areWeOOM(self, spell):
		return not self.mana_pool >= spell.mana and \
				not (self.div_illu_last_use + self.div_illu_duration) < time and \
				not self.mana_pool >= ((spell.base_mana / 2) - spell.reduction)

class Healing:
	
	def __init__(self, lower, upper, cast, mana, reduction, healing, flat_heal, crit, haste, percent, hl):
		self.lower = lower
		self.upper = upper
		self.cast = cast
		self.mana = mana - reduction
		self.reduction = reduction
		self.healing = healing
		self.flat_heal = flat_heal
		self.crit = crit
		self.haste = haste
		self.base_cast = cast
		self.base_mana = mana
		self.critted = False
		self.percent = percent
		self.isHL = hl

	def updateHaste(self, t, last_grace):
		if self.isHL and (last_grace + 15) >= t:
			self.cast = (self.base_cast - 0.5) / ( 1 + self.haste / 1577)
		else:
			self.cast = self.base_cast / (1 + self.haste / 1577)
	
	def heal(self, favor):
		if random.random() > (1 - self.crit - favor):
			self.critted = True
			return (random.randint(self.lower, self.upper) + ((self.healing * self.base_cast / 3.5 + self.flat_heal) * 1.12)) * self.percent * 1.5
		else:
			self.critted = False
			return (random.randint(self.lower, self.upper) + ((self.healing * self.base_cast / 3.5 + self.flat_heal) * 1.12)) * self.percent

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


	while mana_pool >= fol_mana and not limit_reached:
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

		spell = enc.pickSpell()
#		spell = random.choices(heals_list, weights=ratio, k=1)[0]	
		if enc.areWeOOM(spell):
			break

#		if mana_pool < spell.mana:
#			if (div_illu_last_use + div_illu_duration) >= time:
#				if  mana_pool < ((spell.base_mana / 2) - spell.reduction):
#					break
#			else:
#				break

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
			mana_pool -= (spell.base_mana / 2) - spell.reduction
		else:
			mana_pool -= spell.mana
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
		if time >= limit:
			limit_reached = True

	return (time, healed, limit_reached)

def simulation(runs, limit, activity, ratio, mana_pool, healing, fol_heal, hl_heal, fol_bol, hl_bol, reduction, mp5, crit, haste):
	tto = []
	hld = []
	over_limit = 0

	encounter_object = Encounter(limit, activity, ratio, mana_pool, healing, fol_heal, hl_heal, fol_bol, hl_bol, reduction, mp5, crit, haste)
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

def callback_fn_multi(result, n, i, tto, hld, hps):
	for m in range(5):
		tto[m, i, 0] = result[0]
		tto[m, i, 1] = result[3]
		hld[m, i, 0] = result[1]
		hld[m, i, 1] = result[3]
		hps[m, i, 0] = result[2]
		hps[m, i, 1] = result[3]


def callback_err(result):
	print(result)

def gathering_results():
	runs = 100
	activity = 0.60
	ratio = (65, 5, 0, 30)
	limit = 600
	mana_pool = 16293 + 12000
	crit = 0.32318
	crit_step = 0.00452 * 12
	mp5 = 269 + (100 + 50) * 0.8 # adding pot/rune as static mp5
	mp5_step = 4 * 12
	int_step = 10 * 12
	healing = 2174
	healing_step = 22 * 12
	haste = 0
	haste_step = 10 * 12
	fol_heal = 0
	hl_heal = 0
	fol_bol = 185
	hl_bol = 580
	reduction = 34

	steps = 2
	a_tto = np.zeros([5, steps, 2], float)
	a_hld = np.zeros([5, steps, 2], float)
	a_hps = np.zeros([5, steps, 2], float)

	with Pool(6) as pool:
		# no gems
		pool.apply_async(simulation, args=(runs, limit, activity, ratio, mana_pool, healing, fol_heal, hl_heal, fol_bol, hl_bol, reduction, mp5, crit, haste), callback=partial(callback_fn_multi, n=0, i=0, tto=a_tto, hld=a_hld, hps=a_hps), error_callback=callback_err)

		# +healing
		pool.apply_async(simulation, args=(runs, limit, activity, ratio, mana_pool, healing + healing_step, fol_heal, hl_heal, fol_bol, hl_bol, reduction, mp5, crit, haste), callback=partial(callback_fn, n=0, i=1, tto=a_tto, hld=a_hld, hps=a_hps), error_callback=callback_err)

		# +mp5
		pool.apply_async(simulation, args=(runs, limit, activity, ratio, mana_pool, healing, fol_heal, hl_heal, fol_bol, hl_bol, reduction, mp5 + mp5_step, crit, haste), callback=partial(callback_fn, n=1, i=1, tto=a_tto, hld=a_hld, hps=a_hps), error_callback=callback_err)

		# +crit
		pool.apply_async(simulation, args=(runs, limit, activity, ratio, mana_pool, healing, fol_heal, hl_heal, fol_bol, hl_bol, reduction, mp5, crit + crit_step, haste), callback=partial(callback_fn, n=2, i=1, tto=a_tto, hld=a_hld, hps=a_hps), error_callback=callback_err)

		# +int
		pool.apply_async(simulation, args=(runs,
			limit,
			activity,
			ratio,
			mana_pool + int_step * 1.21 * 15,
			healing + int_step * 1.21 * 0.35,
			fol_heal,
			hl_heal,
			fol_bol,
			hl_bol,
			reduction,
			mp5,
			crit + int_step * 1.21 / 80 / 100,
			haste),
			callback=partial(callback_fn, n=3, i=1, tto=a_tto, hld=a_hld, hps=a_hps), error_callback=callback_err)

		# +haste
		pool.apply_async(simulation, args=(runs, limit, activity, ratio, mana_pool, healing, fol_heal, hl_heal, fol_bol, hl_bol, reduction, mp5, crit, haste + haste_step), callback=partial(callback_fn, n=4, i=1, tto=a_tto, hld=a_hld, hps=a_hps), error_callback=callback_err)

		pool.close()
		pool.join()
	np.save("tto_12_gems", a_tto)
	np.save("hld_12_gems", a_hld)
	np.save("hps_12_gems", a_hps)
	
def gathering_results_libram():
	runs = 10000
	activity = 0.90
	ratio = (38, 25, 0, 37)
	limit = 480
	mana_pool = 16293 + 36000
	crit = 0.32318
	crit_step = 0.00452 * 12
	mp5 = 269 + (100 + 50) * 0.8 # adding pot/rune as static mp5
	mp5_step = 4 * 12
	int_step = 10 * 12
	healing = 2174
	healing_step = 22 * 12
	haste = 0
	haste_step = 10 * 12
	fol_heal = 0
	hl_heal = 0
	fol_bol = 185
	hl_bol = 580
	reduction = 0

	steps = 2
	a_tto = np.zeros([5, steps, 2], float)
	a_hld = np.zeros([5, steps, 2], float)
	a_hps = np.zeros([5, steps, 2], float)

	with Pool(6) as pool:
		# no libram
		pool.apply_async(simulation, args=(runs, limit, activity, ratio, mana_pool, healing, fol_heal, hl_heal, fol_bol, hl_bol, reduction, mp5, crit, haste), callback=partial(callback_fn_multi, n=0, i=0, tto=a_tto, hld=a_hld, hps=a_hps), error_callback=callback_err)
		
		# Libram of Absolute Truth
		pool.apply_async(simulation, args=(runs, limit, activity, ratio, mana_pool, healing, fol_heal, hl_heal, fol_bol, hl_bol, 34, mp5, crit, haste), callback=partial(callback_fn, n=0, i=1, tto=a_tto, hld=a_hld, hps=a_hps), error_callback=callback_err)

		# Libram of Souls Redeemed
		pool.apply_async(simulation, args=(runs, limit, activity, ratio, mana_pool, healing, fol_heal, hl_heal, fol_bol + 60, hl_bol + 120, reduction, mp5, crit, haste), callback=partial(callback_fn, n=1, i=1, tto=a_tto, hld=a_hld, hps=a_hps), error_callback=callback_err)

		# Book of Nagrand
		pool.apply_async(simulation, args=(runs, limit, activity, ratio, mana_pool, healing, 79, hl_heal, fol_bol, hl_bol, reduction, mp5, crit, haste), callback=partial(callback_fn, n=2, i=1, tto=a_tto, hld=a_hld, hps=a_hps), error_callback=callback_err)

		# Libram of the Lightbringer
		pool.apply_async(simulation, args=(runs, limit, activity, ratio, mana_pool, healing, fol_heal, 87, fol_bol, hl_bol, reduction, mp5, crit, haste), callback=partial(callback_fn, n=3, i=1, tto=a_tto, hld=a_hld, hps=a_hps), error_callback=callback_err)

		# Libram of Mending
		pool.apply_async(simulation, args=(runs, limit, activity, ratio, mana_pool, healing, fol_heal, hl_heal, fol_bol, hl_bol, reduction, mp5 + 22, crit, haste), callback=partial(callback_fn, n=4, i=1, tto=a_tto, hld=a_hld, hps=a_hps), error_callback=callback_err)

		pool.close()
		pool.join()
	np.save("tto_libram", a_tto)
	np.save("hld_libram", a_hld)
	np.save("hps_libram", a_hps)


if __name__ == '__main__':
	# magic numbers
	runs = 10000
	activity = 0.90
	
	# fol r7, hl r9, hl r10, hl r11
	ratio = (38, 25, 0, 37)

	# encounter limit in seconds
	limit = 480
	mana_pool = 16293
	healing_step = 22
	mp5_step = 4
	crit_step = 0.00452
	int_step = 10
	haste_step = 10

	healing = 2174
	# adding pot/rune as static mp5
	mp5 = 269 + (100 + 50) * 0.8
	crit = 0.32318
	haste = 0

	fol_bol = 185
	hl_bol = 580

	gathering_results()
#	gathering_results_libram()


#a = encounter(True, 0.88, (28, 45, 23, 4), 12723, 2077, 163, 0.2278, 0)
