import random
import statistics
import numpy as np
from multiprocessing import Pool
from functools import partial

class Encounter:

	def __init__(self, limit, activity, ratio, mana_pool, extra_mana, healing, fol_heal, hl_heal, fol_bol, hl_bol, reduction, mp5, base_crit, haste):
		self.fol = Healing(513, 574, 1.5, 180, 0, healing + fol_heal, fol_bol, base_crit, haste, 1.045065, False)
		self.hl9 = Healing(1813, 2015, 2.5, 660, reduction, healing + hl_heal, hl_bol, base_crit + 0.06 + 0.05, haste, 1, True)
		self.hl10 = Healing(1985, 2208, 2.5, 710, reduction, healing + hl_heal, hl_bol, base_crit + 0.06 + 0.05, haste, 1, True)
		self.hl11 = Healing(2459, 2740, 2.5, 840, reduction, healing + hl_heal, hl_bol, base_crit + 0.06 + 0.05, haste, 1, True)
		self.heals_list = [self.fol, self.hl9, self.hl10, self.hl11]
		self.time = 0.0
		self.healed = 0
		self.mana_tick = 2
		self.mp2 = mp5 / 5 * 2
		self.mana_pool = mana_pool
		self.max_mana = mana_pool
		self.extra_mana = extra_mana
		self.extra_mana_added = 0
		self.last_tick = 0.0
		self.activity = activity
		self.ratio = ratio
		self.limit = limit
		self.limit_reached = False
		self.illu_factor = 0.6
		self.favor = 0
		self.favor_cd = 120
		self.favor_delay = 60
		self.favor_last_use = self.favor_delay - self.favor_cd
		self.div_illu_duration = 15
		self.div_illu_cd = 120
		self.div_illu_delay = 60
		self.div_illu_last_use = self.div_illu_delay - self.div_illu_cd
		self.grace_effect = 0.5
		self.grace_duration = 15
		self.grace_last_use = -16
		self.delayCoefficient = (1 - activity) / activity

	def refresh(self):
		self.time = 0.0
		self.healed = 0
		self.mana_pool = self.max_mana
		self.extra_mana_added = 0
		self.last_tick = 0.0
		self.favor = 0
		self.favor_last_use = self.favor_delay - self.favor_cd
		self.div_illu_last_use = self.div_illu_delay - self.div_illu_cd
		self.grace_last_use = -16
		self.limit_reached = False

	def pickSpell(self):
		return random.choices(self.heals_list, weights=self.ratio, k=1)[0]

	def isDivineIlluminationActive(self):
		return self.div_illu_last_use + self.div_illu_duration >= self.time

	def areWeOOM(self, spell):
		if self.isDivineIlluminationActive():
			temp_spell_cost = spell.getBaseManaCost() / 2 - spell.getManaCostReduction()
		else:
			temp_spell_cost = spell.getManaCost()

		return self.mana_pool < temp_spell_cost

	def updateManaTick(self, debug):
		while self.last_tick < self.time:
			self.last_tick += self.mana_tick
			self.addMana(self.mp2, debug)

	def addMana(self, amount, debug):
		if self.mana_pool + amount > self.max_mana:
			self.mana_pool = self.max_mana
		else:
			self.mana_pool += amount
			if debug:
				print("Increment mana by: " + str(round(amount)))
		
	def returnMana(self, spell, debug):
		if spell.getCritted():
			self.addMana(spell.getBaseManaCost() * self.illu_factor, debug)

	def limitReachedCheck(self):
		if self.time >= self.limit:
			self.limit_reached = True

	def popCooldowns(self):
		if (self.favor_last_use + self.favor_cd) <= self.time and self.time > self.favor_delay:
			self.favor = 1

		if (self.div_illu_last_use + self.div_illu_cd) <= self.time and self.time > self.div_illu_delay:
			self.div_illu_last_use = self.time

	def updateDivineFavor(self):
		if self.favor == 1:
			self.favor = 0
			self.favor_last_use = self.time

	def updateLightsGrace(self, spell):
		if spell.isHL:
			self.grace_last_use = self.time

	def incrementTime(self, spell, debug):
		temp_time = spell.getCastTime()
		self.time += temp_time
		if debug:
			print("Incremented time by: " + str(round(temp_time, 2)))
		
	def incrementHealed(self, spell, debug):
		temp_healed = spell.heal(self.favor)
		self.healed += temp_healed
		if debug:
			print("Incremented healing done by: " + str(round(temp_healed)))
		
	def consumeMana(self, spell, debug):
		if (self.div_illu_last_use + self.div_illu_duration) >= self.time:
			temp_mana = spell.getBaseManaCost() / 2 - spell.getManaCostReduction()
			self.mana_pool -= temp_mana
		else:
			temp_mana = spell.getManaCost()
			self.mana_pool -= temp_mana
		if debug:
			print("Decrement mana by: " + str(round(temp_mana)))
		

	def castSpell(self, spell, debug):
		self.incrementTime(spell, debug)
		self.incrementHealed(spell, debug)
		self.consumeMana(spell, debug)
		
	def addDelay(self, spell, debug):
		temp_time = self.delayCoefficient * spell.getCastTime()
		self.time += temp_time 
		#return delay_coeff # * (2 * (1 - random.random()))
		if debug:
			print("Increment time by: " + str(round(temp_time, 2)))

	def addExtraMana(self, amount, debug):
		if self.mana_pool < amount and self.extra_mana_added < self.extra_mana:
			self.addMana(amount, debug)
			self.extra_mana_added += amount

	def getTime(self):
		return self.time

	def getHealed(self):
		return self.healed

	def getLimitReached(self):
		return self.limit_reached

	def runEncounter(self, debug):
		while not self.limit_reached:
			spell = self.pickSpell()
			if self.areWeOOM(spell):
				break
			self.popCooldowns()
			spell.updateHaste(self.time, self.grace_effect, self.grace_duration, self.grace_last_use)
			self.castSpell(spell, debug)
			self.returnMana(spell, debug)
			self.updateDivineFavor()
			self.updateLightsGrace(spell)
			self.addDelay(spell, debug)
			self.updateManaTick(debug)
			self.addExtraMana(1000, debug)
			self.limitReachedCheck()

			if debug:
				print("Current mana pool: " + str(round(self.mana_pool)))
				print("Elapsed time: " + str(round(self.time)) + "\n")

		

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
		self.hasteCoefficient = 1577
		self.healingCoefficient = self.base_cast / 3.5

	def updateHaste(self, time, grace_effect, grace_duration, grace_last_use):
		if self.isHL and (grace_last_use + grace_duration) >= time:
			self.cast = (self.base_cast - grace_effect) / ( 1 + self.haste / self.hasteCoefficient)
		else:
			self.cast = self.base_cast / (1 + self.haste / self.hasteCoefficient)
	
	def heal(self, favor):
		if random.random() > (1 - self.crit - favor):
			self.critted = True
			return (random.randint(self.lower, self.upper) + ((self.healing * self.healingCoefficient + self.flat_heal) * 1.12)) * self.percent * 1.5
		else:
			self.critted = False
			return (random.randint(self.lower, self.upper) + ((self.healing * self.healingCoefficient + self.flat_heal) * 1.12)) * self.percent

	def getCastTime(self):
		return self.cast

	def getManaCost(self):
		return self.mana

	def getBaseManaCost(self):
		return self.base_mana

	def getManaCostReduction(self):
		return self.reduction
	
	def getCritted(self):
		return self.critted

def simulation(runs, limit, activity, ratio, mana_pool, extra_mana, healing, fol_heal, hl_heal, fol_bol, hl_bol, reduction, mp5, crit, haste):
	tto = []
	hld = []
	over_limit = 0

	encounter_object = Encounter(limit, activity, ratio, mana_pool, extra_mana, healing, fol_heal, hl_heal, fol_bol, hl_bol, reduction, mp5, crit, haste)
	assert sum(encounter_object.ratio) == 100

	for i in range(runs):
		encounter_object.refresh()
		encounter_object.runEncounter(False)
		tto.append(encounter_object.getTime())
		hld.append(encounter_object.getHealed())
		if encounter_object.getLimitReached():
			over_limit += 1
	
	tto_median = statistics.median(tto)
	hld_median = statistics.median(hld)
	hps_median = hld_median / tto_median

	return [tto_median, hld_median, hps_median, over_limit / runs]
	
def debug_run(limit, activity, ratio, mana_pool, healing, fol_heal, hl_heal, fol_bol, hl_bol, reduction, mp5, crit, haste):

	encounter_object = Encounter(limit, activity, ratio, mana_pool, healing, fol_heal, hl_heal, fol_bol, hl_bol, reduction, mp5, crit, haste)
	assert sum(encounter_object.ratio) == 100

	encounter_object.runEncounter(True)

def callback_fn(result, n, i, tto, hld, hps):
	tto[n, i, 0] = result[0]
	tto[n, i, 1] = result[3]
	hld[n, i, 0] = result[1]
	hld[n, i, 1] = result[3]
	hps[n, i, 0] = result[2]
	hps[n, i, 1] = result[3]

def callback_fn_multi(result, tto, hld, hps):
	for m in range(5):
		tto[m, 0, 0] = result[0]
		tto[m, 0, 1] = result[3]
		hld[m, 0, 0] = result[1]
		hld[m, 0, 1] = result[3]
		hps[m, 0, 0] = result[2]
		hps[m, 0, 1] = result[3]


def callback_err(result):
	print(result)

def gathering_results(runs, activity, ratio, limit, mana_pool, extra_mana, healing, mp5, crit, haste, healing_step, mp5_step, crit_step, int_step, haste_step):
	num_gems = 12
	fol_bol = 185
	hl_bol = 580
	reduction = 0
	loat = 34
	fol_heal = 0
	hl_heal = 0

	steps = 2
	a_tto = np.zeros([5, steps, 2], float)
	a_hld = np.zeros([5, steps, 2], float)
	a_hps = np.zeros([5, steps, 2], float)

	with Pool(6) as pool:
		# no gems
		pool.apply_async(simulation, args=(runs, limit, activity, ratio, mana_pool, extra_mana, healing, fol_heal, hl_heal, fol_bol, hl_bol, loat, mp5, crit, haste), callback=partial(callback_fn_multi, tto=a_tto, hld=a_hld, hps=a_hps), error_callback=callback_err)

		# +healing
		pool.apply_async(simulation, args=(runs, limit, activity, ratio, mana_pool, extra_mana, healing + healing_step * num_gems, fol_heal, hl_heal, fol_bol, hl_bol, loat, mp5, crit, haste), callback=partial(callback_fn, n=0, i=1, tto=a_tto, hld=a_hld, hps=a_hps), error_callback=callback_err)

		# +mp5
		pool.apply_async(simulation, args=(runs, limit, activity, ratio, mana_pool, extra_mana, healing, fol_heal, hl_heal, fol_bol, hl_bol, loat, mp5 + mp5_step * num_gems, crit, haste), callback=partial(callback_fn, n=1, i=1, tto=a_tto, hld=a_hld, hps=a_hps), error_callback=callback_err)

		# +crit
		pool.apply_async(simulation, args=(runs, limit, activity, ratio, mana_pool, extra_mana, healing, fol_heal, hl_heal, fol_bol, hl_bol, loat, mp5, crit + crit_step * num_gems, haste), callback=partial(callback_fn, n=2, i=1, tto=a_tto, hld=a_hld, hps=a_hps), error_callback=callback_err)

		# +int
		pool.apply_async(simulation, args=(runs,
			limit,
			activity,
			ratio,
			mana_pool + int_step * num_gems * 1.21 * 15,
			extra_mana,
			healing + int_step * num_gems * 1.21 * 0.35,
			fol_heal,
			hl_heal,
			fol_bol,
			hl_bol,
			loat,
			mp5,
			crit + int_step * num_gems * 1.21 / 80 / 100,
			haste),
			callback=partial(callback_fn, n=3, i=1, tto=a_tto, hld=a_hld, hps=a_hps), error_callback=callback_err)

		# +haste
		pool.apply_async(simulation, args=(runs, limit, activity, ratio, mana_pool, extra_mana, healing, fol_heal, hl_heal, fol_bol, hl_bol, loat, mp5, crit, haste + haste_step * num_gems), callback=partial(callback_fn, n=4, i=1, tto=a_tto, hld=a_hld, hps=a_hps), error_callback=callback_err)

		pool.close()
		pool.join()
	np.save("tto_12_gems", a_tto)
	np.save("hld_12_gems", a_hld)
	np.save("hps_12_gems", a_hps)
	
	b_tto = np.zeros([5, steps, 2], float)
	b_hld = np.zeros([5, steps, 2], float)
	b_hps = np.zeros([5, steps, 2], float)

	with Pool(6) as pool2:
		# no libram
		pool2.apply_async(simulation, args=(runs, limit, activity, ratio, mana_pool, extra_mana, healing, fol_heal, hl_heal, fol_bol, hl_bol, reduction, mp5, crit, haste), callback=partial(callback_fn_multi, tto=b_tto, hld=b_hld, hps=b_hps), error_callback=callback_err)
		
		# Libram of Absolute Truth
		pool2.apply_async(simulation, args=(runs, limit, activity, ratio, mana_pool, extra_mana, healing, fol_heal, hl_heal, fol_bol, hl_bol, 34, mp5, crit, haste), callback=partial(callback_fn, n=0, i=1, tto=b_tto, hld=b_hld, hps=b_hps), error_callback=callback_err)

		# Libram of Souls Redeemed
		pool2.apply_async(simulation, args=(runs, limit, activity, ratio, mana_pool, extra_mana, healing, fol_heal, hl_heal, fol_bol + 60, hl_bol + 120, reduction, mp5, crit, haste), callback=partial(callback_fn, n=1, i=1, tto=b_tto, hld=b_hld, hps=b_hps), error_callback=callback_err)

		# Book of Nagrand
		pool2.apply_async(simulation, args=(runs, limit, activity, ratio, mana_pool, extra_mana, healing, 79, hl_heal, fol_bol, hl_bol, reduction, mp5, crit, haste), callback=partial(callback_fn, n=2, i=1, tto=b_tto, hld=b_hld, hps=b_hps), error_callback=callback_err)

		# Libram of the Lightbringer
		pool2.apply_async(simulation, args=(runs, limit, activity, ratio, mana_pool, extra_mana, healing, fol_heal, 87, fol_bol, hl_bol, reduction, mp5, crit, haste), callback=partial(callback_fn, n=3, i=1, tto=b_tto, hld=b_hld, hps=b_hps), error_callback=callback_err)

		# Libram of Mending
		pool2.apply_async(simulation, args=(runs, limit, activity, ratio, mana_pool, extra_mana, healing, fol_heal, hl_heal, fol_bol, hl_bol, reduction, mp5 + 22, crit, haste), callback=partial(callback_fn, n=4, i=1, tto=b_tto, hld=b_hld, hps=b_hps), error_callback=callback_err)

		pool2.close()
		pool2.join()
	np.save("tto_libram", b_tto)
	np.save("hld_libram", b_hld)
	np.save("hps_libram", b_hps)


if __name__ == '__main__':
	# magic numbers
	runs = 1000
	activity = 0.90
	
	# fol r7, hl r9, hl r10, hl r11
	ratio = (38, 25, 0, 37)
	# encounter limit in seconds
	limit = 480
	
	mana_pool = 16293
	extra_mana = 36000
	healing = 2174
	# adding pot/rune as static mp5
	mp5 = 269 + (140 + 50) * 0.8
	crit = 0.32318
	haste = 100

	healing_step = 22
	mp5_step = 4
	crit_step = 0.00452
	int_step = 10
	haste_step = 10

	gathering_results(runs, activity, ratio, limit, mana_pool, extra_mana, healing, mp5, crit, haste, healing_step, mp5_step, crit_step, int_step, haste_step)

#	debug_run(limit, activity, ratio, mana_pool + extra_mana, healing, 0, 0, 185, 580, 34, mp5, crit, haste)

#a = encounter(True, 0.88, (28, 45, 23, 4), 12723, 2077, 163, 0.2278, 0)
