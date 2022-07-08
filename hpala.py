import random
import statistics
import numpy as np
from multiprocessing import Pool
from functools import partial
from enum import Enum

class Encounter:

	def __init__(self, limit, activity, ratio, mana_pool, extra_mana, healing, fol_heal, hl_heal, fol_bol, hl_bol, reduction, mp5, base_crit, haste):
		self.fol = Healing(785, 879, 1.5, 288, 0, healing + fol_heal, 0, base_crit, haste, 1.045065, HealType.FOL)
		self.hs = Healing(2401, 2599, 1.5, 741, 0, healing, 0, base_crit + 0.06, haste, 1, HealType.HS)
		self.hl = Healing(4888, 5444, 2.5, 1193, reduction, healing + hl_heal, 0, base_crit + 0.06 + 0.05, haste, 1, HealType.HL)
		self.heals_list = [self.fol, self.hl, self.hs]
		self.time = 0.0
		self.healed = 0
		self.mana_tick = 2
		self.mp2 = mp5 / 5 * 2 + mana_pool * 0.25 / 30
		self.mana_pool = mana_pool
		self.max_mana = mana_pool
		self.extra_mana = extra_mana
		self.extra_mana_added = 0
		self.last_tick = 0.0
		self.activity = activity
		self.ratio = ratio
		self.limit = limit
		self.limit_reached = False
		self.illu_factor = 0.3
		self.favor = 0
		self.favor_mana_cost = 123
		self.favor_cd = 120
		self.favor_delay = 30
		self.favor_last_use = self.favor_delay - self.favor_cd
		self.div_illu_duration = 15
		self.div_illu_cd = 120
		self.div_illu_delay = 30
		self.div_illu_last_use = self.div_illu_delay - self.div_illu_cd
		self.grace_effect = 0.5
		self.grace_duration = 15
		self.grace_last_use = self.grace_duration - 1
		self.beacon_duration = 60
		self.beacon_last_use = self.beacon_duration - 1
		self.beacon_mana_cost = 1440
		self.beacon_probability = 0.3
		self.iol_activated = False
		self.sacred_shield_interval = 9
		self.sacred_shield_last_proc = self.sacred_shield_interval - 1
		self.sacred_shield_duration = 60
		self.sacred_shield_last_use = self.sacred_shield_duration - 1
		self.sacred_shield_mana_cost = 494
		self.wrath_cd = 180
		self.wrath_delay = 30
		self.wrath_last_use = self.wrath_delay - self.wrath_cd
		self.wrath_duration = 20
		self.wrath_mana_cost = 329
		self.divine_plea_cd = 60
		self.divine_plea_delay = 60
		self.divine_plea_last_use = self.divine_plea_delay - self.divine_plea_cd
		self.divine_plea_duration = 15
		self.delayCoefficient = (1 - activity) / activity
		self.spellPower = healing

	def refresh(self):
		self.time = 0.0
		self.healed = 0
		self.mana_pool = self.max_mana
		self.extra_mana_added = 0
		self.last_tick = 0.0
		self.favor = 0
		self.favor_last_use = self.favor_delay - self.favor_cd
		self.div_illu_last_use = self.div_illu_delay - self.div_illu_cd
		self.grace_last_use = self.grace_duration - 1
		self.beacon_last_use = self.beacon_duration - 1
		self.sacred_shield_last_proc = self.sacred_shield_interval - 1
		self.sacred_shield_last_use = self.sacred_shield_duration - 1
		self.wrath_last_use = self.wrath_delay - self.wrath_cd
		self.iol_activated = False
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

	def updateManaTick(self):
		while self.last_tick < self.time:
			self.last_tick += self.mana_tick
			self.addMana(self.mp2)

	def addMana(self, amount):
		if self.mana_pool + amount > self.max_mana:
			self.mana_pool = self.max_mana
		else:
			self.mana_pool += amount
	
	def removeMana(self, amount):
		self.mana_pool -= amount
		
	def returnMana(self, spell):
		if spell.getCritted():
			self.addMana(spell.getBaseManaCost() * self.illu_factor)

	def limitReachedCheck(self):
		if self.time >= self.limit:
			self.limit_reached = True

	def popCooldowns(self):
		if (self.favor_last_use + self.favor_cd) <= self.time and self.time > self.favor_delay:
			self.favor = 1
			self.removeMana(self.favor_mana_cost)

		if (self.div_illu_last_use + self.div_illu_cd) <= self.time and self.time > self.div_illu_delay:
			self.div_illu_last_use = self.time

		if (self.beacon_last_use + self.beacon_duration) <= self.time:
			self.beacon_last_use = self.time
			self.removeMana(self.beacon_mana_cost)

		if (self.sacred_shield_last_use + self.sacred_shield_duration) <= self.time:
			self.sacred_shield_last_use = self.time
			self.removeMana(self.sacred_shield_mana_cost)

		if (self.wrath_last_use + self.wrath_duration) <= self.time:
			self.wrath_last_use = self.time
			self.removeMana(self.wrath_mana_cost)

	def updateDivineFavor(self):
		if self.favor == 1:
			self.favor = 0
			self.favor_last_use = self.time

	def updateLightsGrace(self, spell):
		if spell.getHealType() == HealType.HL:
			self.grace_last_use = self.time

	def incrementTime(self, spell):
		self.time += spell.getCastTime()
		
	def incrementHealed(self, spell, multiplier):
		self.healed += spell.heal(self.favor) * multiplier
		
	def consumeMana(self, spell):
		if (self.div_illu_last_use + self.div_illu_duration) >= self.time:
			self.removeMana(spell.getBaseManaCost() / 2 - spell.getManaCostReduction())
		else:
			self.removeMana(spell.getManaCost())

	def activateInfusionOfLight(self, spell):
		if spell.getHealType() == HealType.HS and spell.getCritted:
			self.iol_activated = True
			self.hl.setExtraCrit(0.2)
	
	def deactivateInfusionOfLight(self, spell):
		if self.iol_activated and (spell.getHealType() == HealType.FOL or spell.getHealType() == HealType.HL):
			self.iol_activated = False
			self.hl.setExtraCrit(0)

	def activateSacredShield(self, spell):
		if self.sacred_shield_last_proc + self.sacred_shield_interval <= self.time:
			self.sacred_shield_last_proc = self.time
			self.fol.setExtraCrit(0.5)

			self.healed += (1000 + self.spellPower * 0.75) * 1.2

	def deactivateSacredShield(self, spell):
		if spell.getHealType() == HealType.FOL:
			self.fol.setExtraCrit(0)

	def castSpell(self, spell):
		self.incrementTime(spell)

		if self.wrath_last_use + self.wrath_duration >= self.time:
			wrathMultiplier = 1.2
		else:
			wrathMultiplier = 1

		if self.divine_plea_last_use + self.divine_plea_duration >= self.time:
			pleaMultiplier = 0.5
		else:
			pleaMultiplier = 1

		if self.beacon_last_use + self.beacon_duration >= self.time and self.beacon_probability > random.random():
			self.incrementHealed(spell, 2 * wrathMultiplier * pleaMultiplier)
		else:
			self.incrementHealed(spell, 1 * wrathMultiplier * pleaMultiplier)

		self.consumeMana(spell)
		
	def addDelay(self, spell):
		self.time += self.delayCoefficient * spell.getCastTime()
		#return delay_coeff # * (2 * (1 - random.random()))

	def addExtraMana(self, amount):
		if self.mana_pool < amount and self.extra_mana_added < self.extra_mana:
			self.addMana(amount)
			self.extra_mana_added += amount

	def getTime(self):
		return self.time

	def getHealed(self):
		return self.healed

	def getLimitReached(self):
		return self.limit_reached

	def runEncounter(self):
		while not self.limit_reached:
			spell = self.pickSpell()
			if self.areWeOOM(spell):
				break
			self.popCooldowns()
			spell.updateHaste(self.time, self.grace_effect, self.grace_duration, self.grace_last_use)
			self.deactivateInfusionOfLight(spell)
			self.activateSacredShield(spell)
			self.castSpell(spell)
			self.returnMana(spell)
			self.updateDivineFavor()
			self.updateLightsGrace(spell)
			self.activateInfusionOfLight(spell)
			self.deactivateSacredShield(spell)
			self.addDelay(spell)
			self.updateManaTick()
			self.addExtraMana(1000)
			self.limitReachedCheck()

class HealType(Enum):
	FOL = 0
	HL = 1
	HS = 2

class Healing:
	
	def __init__(self, lower, upper, cast, mana, reduction, healing, flat_heal, crit, haste, percent, healType):
		self.lower = lower
		self.upper = upper
		self.cast = cast
		self.mana = mana - reduction
		self.reduction = reduction
		self.healing = healing
		self.flat_heal = flat_heal
		self.crit = crit
		self.extraCrit = 0
		self.haste = haste
		self.base_cast = cast
		self.base_mana = mana
		self.critted = False
		self.percent = percent
		self.healType = healType
		self.hasteCoefficient = 2523
		self.healingCoefficient = self.base_cast / 3.5 / 0.53

	def updateHaste(self, time, grace_effect, grace_duration, grace_last_use):
		if self.healType == HealType.HL and (grace_last_use + grace_duration) >= time:
			self.cast = (self.base_cast - grace_effect) / ( 1 + self.haste / self.hasteCoefficient)
		else:
			self.cast = self.base_cast / (1 + self.haste / self.hasteCoefficient)
	
	def heal(self, favor):
		if self.healType == HealType.FOL:
			iol_factor = 1 + 0.7 * 0.4
		else:
			iol_factor = 1
		if random.random() > (1 - self.crit - self.extraCrit - favor):
			self.critted = True
			return (random.randint(self.lower, self.upper) + ((self.healing * self.healingCoefficient + self.flat_heal) * 1.12)) * self.percent * iol_factor * 1.5
		else:
			self.critted = False
			return (random.randint(self.lower, self.upper) + ((self.healing * self.healingCoefficient + self.flat_heal) * 1.12)) * self.percent * iol_factor 

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

	def setExtraCrit(self, value):
		self.extraCrit = value

	def getHealType(self):
		return self.healType

def simulation(runs, limit, activity, ratio, mana_pool, extra_mana, healing, fol_heal, hl_heal, fol_bol, hl_bol, reduction, mp5, crit, haste):
	tto = []
	hld = []
	over_limit = 0

	encounter_object = Encounter(limit, activity, ratio, mana_pool, extra_mana, healing, fol_heal, hl_heal, fol_bol, hl_bol, reduction, mp5, crit, haste)
	assert sum(encounter_object.ratio) == 100

	for i in range(runs):
		encounter_object.refresh()
		encounter_object.runEncounter()
		tto.append(encounter_object.getTime())
		hld.append(encounter_object.getHealed())
		if encounter_object.getLimitReached():
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
	fol_bol = 0
	hl_bol = 0
	reduction = 0
	loat = 34
	fol_heal = 0
	hl_heal = 0
	holy_guidance = 0.2
	int_crit_coeff = 1 / 200 / 100

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
			healing + int_step * num_gems * 1.21 * holy_guidance,
			fol_heal,
			hl_heal,
			fol_bol,
			hl_bol,
			loat,
			mp5,
			crit + int_step * num_gems * 1.21 * int_crit_coeff,
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
		pool2.apply_async(simulation, args=(runs, limit, activity, ratio, mana_pool, extra_mana, healing, 89, hl_heal, fol_bol, hl_bol, reduction, mp5, crit, haste), callback=partial(callback_fn, n=1, i=1, tto=b_tto, hld=b_hld, hps=b_hps), error_callback=callback_err)

		# Book of Nagrand
		pool2.apply_async(simulation, args=(runs, limit, activity, ratio, mana_pool, extra_mana, healing, 79, hl_heal, fol_bol, hl_bol, reduction, mp5, crit, haste), callback=partial(callback_fn, n=2, i=1, tto=b_tto, hld=b_hld, hps=b_hps), error_callback=callback_err)

		# Libram of the Lightbringer
		pool2.apply_async(simulation, args=(runs, limit, activity, ratio, mana_pool, extra_mana, healing, fol_heal, 47, fol_bol, hl_bol, reduction, mp5, crit, haste), callback=partial(callback_fn, n=3, i=1, tto=b_tto, hld=b_hld, hps=b_hps), error_callback=callback_err)

		# Libram of Mending
		pool2.apply_async(simulation, args=(runs, limit, activity, ratio, mana_pool, extra_mana, healing, fol_heal, hl_heal, fol_bol, hl_bol, reduction, mp5 + 28, crit, haste), callback=partial(callback_fn, n=4, i=1, tto=b_tto, hld=b_hld, hps=b_hps), error_callback=callback_err)

		pool2.close()
		pool2.join()
	np.save("tto_libram", b_tto)
	np.save("hld_libram", b_hld)
	np.save("hps_libram", b_hps)


if __name__ == '__main__':
	# magic numbers
	runs = 10000
	activity = 0.90
	crit_rating = 1 / 45 / 100
	
	# fol r7, hl r9, hl r10, hl r11
	ratio = (65, 27, 8)
	# encounter limit in seconds
	limit = 480
	
	mana_pool = 21349
	extra_mana = 4300 * 1.25
	spell_power = 1475
	# adding pot/rune as static mp5
	mp5_raidbuffs = 92 * 1.2 + 91
	mp5 = 159 + mp5_raidbuffs
	crit = 0.198639
	haste = 176 + 378

	healing_step = 19
	mp5_step = 8
	crit_step = 16 * crit_rating
	int_step = 16
	haste_step = 16


	gathering_results(runs, activity, ratio, limit, mana_pool, extra_mana, spell_power, mp5, crit, haste, healing_step, mp5_step, crit_step, int_step, haste_step)

#	debug_run(limit, activity, ratio, mana_pool + extra_mana, healing, 0, 0, 185, 580, 34, mp5, crit, haste)

#a = encounter(True, 0.88, (28, 45, 23, 4), 12723, 2077, 163, 0.2278, 0)
