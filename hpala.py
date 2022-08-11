import sys
import random
import statistics
import numpy as np
from multiprocessing import Pool
from functools import partial
from enum import Enum
from output import analysis, analysis_libram, pretty_printing_regular, pretty_printing_libram

class Encounter:

	def __init__(self, params):
		self.fol = Healing(785, 879, 1.5, 288, params.overallMana * 288, params.spellPower + params.FOLHeal, params.crit, params.haste, 1 + params.overallHeal + params.FOLHealPercent, SpellType.FOL)
		self.hs = Healing(2401, 2599, 1.5, 741, params.overallMana * 741, params.spellPower + params.HSHeal, params.crit + params.HSCrit + 0.06, params.haste, 1 + params.overallHeal, SpellType.HS)
		self.hl = Healing(4888, 5444, 2.5, 1193, params.overallMana * 1193 + params.HLManaPercent * 1193 + params.HLMana, params.spellPower + params.HLHeal, params.crit + params.HLCrit + 0.06, params.haste, 1 + params.overallHeal, SpellType.HL)
		self.gcd = Healing(0, 0, 1.5, 0, 0, params.spellPower, params.crit, params.haste, 1, SpellType.GCD)
		self.divineFavor = params.divineFavor
		self.divineIllumination = params.divineIllumination
		self.beaconOfLight = params.beaconOfLight
		self.sacredShield = params.sacredShield
		self.avengingWrath = params.avengingWrath
		self.divinePlea = params.divinePlea
		self.judgement = params.judgement
		self.heals_list = [self.fol, self.hl, self.hs]
		self.time = 0.0
		self.healed = 0
		self.mana_tick = 2
		self.mp2 = params.mp5 / 5 * 2 + params.manaPool * 0.25 / 60 * 2 * 0.75
		self.manaPool = params.manaPool
		self.max_mana = params.manaPool
		self.extraMana = params.extraMana
		self.last_tick = 0.0
		self.activity = params.activity
		self.ratio = params.ratio
		self.limit = params.limit
		self.limit_reached = False
		self.illu_factor = 0.3
		self.favor = 0
		self.favor_mana_cost = 123
		self.favor_cd = 120
		self.favor_delay = 20
		self.favor_last_use = self.favor_delay - self.favor_cd
		self.div_illu_duration = 15
		self.div_illu_cd = 120
		self.div_illu_delay = 20
		self.div_illu_last_use = self.div_illu_delay - self.div_illu_cd
		self.grace_effect = 0.5
		self.grace_duration = 15
		self.grace_last_use = -1 * self.grace_duration - 1
		self.beacon_duration = 55
		self.beacon_last_use = -10
		self.beacon_mana_cost = 1440
		self.beacon_probability = 0.3
		self.iol_activated = False
		self.sacred_shield_interval = 9
		self.sacred_shield_last_proc = -1 * self.sacred_shield_interval - 1
		self.sacred_shield_duration = 55
		self.sacred_shield_last_use = -8
		self.sacred_shield_mana_cost = 494
		self.wrath_cd = 180
		self.wrath_delay = 20
		self.wrath_last_use = self.wrath_delay - self.wrath_cd
		self.wrath_duration = 20
		self.wrath_mana_cost = 329
		self.divine_plea_cd = 60
		self.divine_plea_delay = 99999
		self.divine_plea_last_use = self.divine_plea_delay - self.divine_plea_cd
		self.divine_plea_duration = 15
		self.judgement_duration = 55
		self.judgement_last_use = -1 * self.judgement_duration - 1
		self.judgement_mana_cost = 206
		self.delayCoefficient = (1 - params.activity) / params.activity
		self.spellPower = params.spellPower

	def refresh(self):
		self.time = 0.0
		self.healed = 0
		self.manaPool = self.max_mana
		self.last_tick = 0.0
		self.favor = 0
		self.divineFavor.setLastUse(self.divineFavor.getDelay() - self.divineFavor.getCooldown())
		self.divineIllumination.setLastUse(self.divineIllumination.getDelay() - self.divineIllumination.getCooldown())
		self.grace_last_use = -1 * self.grace_duration - 1
		self.beaconOfLight.setLastUse(-10)
		self.sacred_shield_last_proc = -1 * self.sacredShield.getInterval() - 1
		self.sacredShield.setLastUse(-8)
		self.avengingWrath.setLastUse(self.avengingWrath.getDelay() - self.avengingWrath.getCooldown())
		self.divinePlea.setLastUse(self.divinePlea.getDelay() - self.divinePlea.getCooldown())
		self.iol_activated = False
		self.limit_reached = False

	def pickSpell(self):
		return random.choices(self.heals_list, weights=self.ratio, k=1)[0]

	def isDivineIlluminationActive(self):
		return self.isBuffActive(self.div_illu_last_use, self.div_illu_duration, self.time)

	def isBuffActive(self, spell, time):
		return spell.getLastUse + spell.getDuration >= time and spell.getLastUse <= time

#	def isBuffActive(self, lastUse, duration, time):
#		return lastUse + duration >= time and lastUse <= time

	def isBuffReady(self, spell, time):
		return spell.getLastUse + spell.getCooldown <= time and spell.getDelay <= time

#	def isBuffReady(self, lastUse, delay, cd, time):
#		return lastUse + cd <= time and delay <= time

	def areWeOOM(self, spell):
		if self.isBuffActive(self.divineIllumination, self.time):
			temp_spell_cost = spell.getBaseManaCost() / 2 - spell.getManaCostReduction()
		else:
			temp_spell_cost = spell.getManaCost()

		return self.manaPool < temp_spell_cost

	def updateManaTick(self):
		while self.last_tick < self.time:
			self.last_tick += self.mana_tick
			self.addMana(self.mp2)

	def addMana(self, amount):
		if self.manaPool + amount > self.max_mana:
			self.manaPool = self.max_mana
		else:
			self.manaPool += amount
	
	def removeMana(self, amount):
		self.manaPool -= amount
		
	def returnMana(self, spell):
		if spell.getCritted():
			self.addMana(spell.getBaseManaCost() * self.illu_factor)

	def limitReachedCheck(self):
		if self.time >= self.limit:
			self.limit_reached = True

	def popCooldowns(self):
		if self.isBuffReady(self.divineFavor, self.time):
			self.favor = 1
			self.removeMana(self.divineFavor.getManaCost()) #no div illu

		if self.isBuffReady(self.divineIllumination, self.time):
			self.divineIllumination.setLastUse(self.time)

		if self.isBuffReady(self.avengingWrath, self.time):
			self.avengingWrath.setLastUse(self.time)
			self.removeMana(self.avengingWrath.getManaCost())

		if self.isBuffReady(self.divinePlea, self.time):
			self.divinePlea.setLastUse(self.time)
			self.gcd.updateHaste(0, 0, 0, 0)
			self.incrementTime(self.gcd)

		if not self.isBuffActive(self.beaconOfLight, self.time):
			self.beaconOfLight.setLastUse(self.time)
			self.removeMana(self.beaconOfLight.getManaCost())
			self.gcd.updateHaste(0, 0, 0, 0)
			self.incrementTime(self.gcd)

		if not self.isBuffActive(self.sacredShield, self.time):
			self.sacredShield.setLastUse(self.time)
			self.removeMana(self.sacredShield.getManaCost())
			self.gcd.updateHaste(0, 0, 0, 0)
			self.incrementTime(self.gcd)

		if not self.isBuffActive(self.judgement, self.time):
			self.judgement.setLastUse(self.time)
			self.removeMana(self.judgement.getManaCost())
			self.gcd.updateHaste(0, 0, 0, 0)
			self.incrementTime(self.gcd)

	def updateDivineFavor(self):
		if self.favor == 1:
			self.favor = 0
			self.favor_last_use = self.time

	def updateLightsGrace(self, spell):
		if spell.getSpellType() == SpellType.HL:
			self.grace_last_use = self.time

	def incrementTime(self, spell):
		self.time += spell.getCastTime()
		
	def incrementHealed(self, spell, multiplier):
		self.healed += spell.heal(self.favor) * multiplier
		
	def consumeMana(self, spell):
		if self.isDivineIlluminationActive():
			self.removeMana(spell.getBaseManaCost() / 2 - spell.getManaCostReduction())
		else:
			self.removeMana(spell.getManaCost())

	def activateInfusionOfLight(self, spell):
		if spell.getSpellType() == SpellType.HS and spell.getCritted:
			self.iol_activated = True
			self.hl.setExtraCrit(0.2)
	
	def deactivateInfusionOfLight(self, spell):
		if self.iol_activated and (spell.getSpellType() == SpellType.FOL or spell.getSpellType() == SpellType.HL):
			self.iol_activated = False
			self.hl.setExtraCrit(0)

	def activateSacredShield(self, spell):
		if not self.isBuffActive(self.sacredShield, self.time):
			self.sacred_shield_last_proc = self.time
			self.fol.setExtraCrit(0.5)

			self.healed += (1000 + self.spellPower * 0.75) * 1.2

	def deactivateSacredShield(self, spell):
		if spell.getSpellType() == SpellType.FOL:
			self.fol.setExtraCrit(0)

	def castSpell(self, spell):
		self.incrementTime(spell)

		if self.isBuffActive(self.avengingWrath, self.time):
			wrathMultiplier = 1.2
		else:
			wrathMultiplier = 1

		if self.isBuffActive(self.divinePlea, self.time):
			pleaMultiplier = 0.5
		else:
			pleaMultiplier = 1

		if self.isBuffActive(self.beaconOfLight, self.time) and self.beaconOfLight.getProbability() > random.random():
			self.incrementHealed(spell, 2 * wrathMultiplier * pleaMultiplier)
		else:
			self.incrementHealed(spell, 1 * wrathMultiplier * pleaMultiplier)

		self.consumeMana(spell)
		
	def addDelay(self, spell):
		self.time += self.delayCoefficient * spell.getCastTime()
		#return delay_coeff # * (2 * (1 - random.random()))

	def addExtraMana(self):
		if self.manaPool < self.hl.getBaseManaCost() and self.extraMana > 0:
			self.addMana(self.extraMana)
			self.extraMana = 0

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
			self.activateSacredShield(spell)
			self.castSpell(spell)
			self.returnMana(spell)
			self.updateDivineFavor()
			self.updateLightsGrace(spell)
			self.activateInfusionOfLight(spell)
			self.deactivateInfusionOfLight(spell)
			self.deactivateSacredShield(spell)
			self.addDelay(spell)
			self.updateManaTick()
			self.addExtraMana()
			self.limitReachedCheck()

class SpellType(Enum):
	FOL = 0
	HL = 1
	HS = 2
	GCD = 3

class Spell:
	def __init__(self, manaCost, duration, lastUse):
		self.manaCost = manaCost
		self.duration = duration
		self.lastUse = lastUse
	def getManaCost(self): return self.manaCost
	def getDuration(self): return self.duration
	def getLastUse(self): return self.lastUse
	def setLastUse(self, lastUse):
		self.lastUse = lastUse

class SpellBeacon(Spell):
	def __init__(self, manaCost, duration, lastUse, probability):
		super().__init__(manaCost, duration, lastUse)
		self.probability = probability
	def getProbability(self): return self.probability

class SpellShield(Spell):
	def __init__(self, manaCost, duration, lastUse, interval):
		super().__init__(manaCost, duration, lastUse)
		self.interval = interval
	def getInterval(self): return self.interval

class SpellExtended(Spell):
	def __init__(self, manaCost, duration, cooldown, delay, lastUse):
		super().__init__(manaCost, duration, lastUse)
		self.delay = delay
		self.cooldown = cooldown
	def getDelay(self): return self.delay
	def getCooldown(self): return self.cooldown

class Healing:
	
	def __init__(self, lower, upper, cast, mana, reduction, healing, crit, haste, percent, healType):
		self.lower = lower
		self.upper = upper
		self.cast = cast
		self.mana = mana - reduction
		self.reduction = reduction
		self.healing = healing
		self.crit = crit
		self.extraCrit = 0
		self.haste = haste
		self.base_cast = cast
		self.base_mana = mana
		self.critted = False
		self.percent = percent
		self.healType = healType
		self.hasteCoefficient = 3280
		self.healingCoefficient = self.base_cast / 3.5 / 0.53

	def updateHaste(self, time, grace_effect, grace_duration, grace_last_use):
		if self.healType == SpellType.HL and grace_last_use + grace_duration >= time and grace_last_use <= time:
			self.cast = (self.base_cast - grace_effect) / ( 1 + self.haste / self.hasteCoefficient)
		else:
			self.cast = self.base_cast / (1 + self.haste / self.hasteCoefficient)
	
	def heal(self, favor):
		if self.healType == SpellType.FOL:
			iol_factor = 1 + 0.7 * 0.4
		else:
			iol_factor = 1
		if random.random() > (1 - self.crit - self.extraCrit - favor):
			self.critted = True
			return (random.randint(self.lower, self.upper) + self.healing * self.healingCoefficient * 1.12) * self.percent * iol_factor * 1.5
		else:
			self.critted = False
			return (random.randint(self.lower, self.upper) + self.healing * self.healingCoefficient * 1.12) * self.percent * iol_factor 

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

	def getSpellType(self):
		return self.healType

class Parameters:

	def __init__(self, iterations, numberOfGems, numberOfItems, limit, activity, ratio, hasteCoefficient, intCoefficient, critRating, manaPool, spellPower, mp5, crit, haste, spellPowerStep, mp5Step, critStep, intStep, hasteStep, divineFavor, divineIllumination, beaconOfLight, sacredShield, avengingWrath, divinePlea, judgement):
		self.iterations = iterations
		self.numberOfGems = numberOfGems
		self.numberOfItems = numberOfItems
		self.limit = limit
		self.activity = activity
		self.ratio = ratio
		self.hasteCoefficient = hasteCoefficient
		self.intCoefficient = intCoefficient
		self.critRating = critRating
		self.manaPool = manaPool
		self.spellPower = spellPower
		self.mp5 = mp5
		self.crit = crit
		self.haste = haste
		self.spellPowerStep = spellPowerStep
		self.mp5Step = mp5Step
		self.critStep = critStep
		self.intStep = intStep
		self.hasteStep = hasteStep
		self.divineFavor = divineFavor
		self.divineIllumination = divineIllumination
		self.beaconOfLight = beaconOfLight
		self.sacredShield = sacredShield
		self.avengingWrath = avengingWrath
		self.divinePlea = divinePlea
		self.judgement = judgement

	def getIterations(self):
		return self.iterations

	def getLimit(self):
		return self.limit

	def getActivity(self):
		return self.activity

	def getRatio(self):
		return self.ratio

	def getHasteCoefficient(self):
		return self.hasteCoefficient

	def getIntCoefficient(self):
		return self.intCoefficient

	def getCritRating(self):
		return self.critRating

	def getSpellPower(self):
		return self.spellPower

class ParametersVariable(Parameters):

	def __init__(self, args, manaPool=0, spellPower=0, mp5=0, crit=0, haste=0, extraMana=0, FOLHeal=0, FOLHealPercent=0, HLMana=0, HLManaPercent=0, HLHeal=0, HLCrit=0, HSHeal=0, HSCrit=0, overallHeal=0, overallMana=0):
		self.iterations = args.iterations
		self.limit = args.limit
		self.activity = args.activity
		self.ratio = args.ratio
		self.hasteCoefficient = args.hasteCoefficient
		self.intCoefficient = args.intCoefficient
		self.critRating = args.critRating

		self.manaPool = args.manaPool + manaPool
		self.spellPower = args.spellPower + spellPower
		self.mp5 = args.mp5 + mp5
		self.crit = args.crit + crit
		self.haste = args.haste + haste
	
		self.divineFavor = args.divineFavor
		self.divineIllumination = args.divineIllumination
		self.beaconOfLight = args.beaconOfLight
		self.sacredShield = args.sacredShield
		self.avengingWrath = args.avengingWrath
		self.divinePlea = args.divinePlea
		self.judgement = args.judgement


		#self.intellect = args.intellect

		self.extraMana = extraMana
		self.FOLHeal = FOLHeal
		self.FOLHealPercent = FOLHealPercent
		self.HLMana = HLMana
		self.HLManaPercent = HLManaPercent
		self.HLHeal = HLHeal
		self.HLCrit = HLCrit
		self.HSHeal = HSHeal
		self.HSCrit = HSCrit
		self.overallHeal = overallHeal
		self.overallMana = overallMana

def simulation(params):
	tto = []
	hld = []
	over_limit = 0

	encounterObject = Encounter(params)
	#encounter_object = Encounter(limit, activity, ratio, mana_pool, extra_mana, FOL_SP, HL_SP, HLReduction, HLReductionPercent, overallReduction, overallHealing, healing, mp5, base_crit, haste)
	assert sum(encounterObject.ratio) == 100

	for i in range(params.iterations):
		encounterObject.refresh()
		encounterObject.runEncounter()
		tto.append(encounterObject.getTime())
		hld.append(encounterObject.getHealed())
		if encounterObject.getLimitReached():
			over_limit += 1
	
	ttoMedian = statistics.median(tto)
	hldMedian = statistics.median(hld)
	hpsMedian = hldMedian / ttoMedian

	return [ttoMedian, hldMedian, hpsMedian, over_limit / params.iterations]
	

def callback_fn(result, n, i, tto, hld, hps):
	tto[n, i, 0] = result[0]
	tto[n, i, 1] = result[3]
	hld[n, i, 0] = result[1]
	hld[n, i, 1] = result[3]
	hps[n, i, 0] = result[2]
	hps[n, i, 1] = result[3]

def callback_fn_multi(result, n, tto, hld, hps):
	for m in range(n):
		tto[m, 0, 0] = result[0]
		tto[m, 0, 1] = result[3]
		hld[m, 0, 0] = result[1]
		hld[m, 0, 1] = result[3]
		hps[m, 0, 0] = result[2]
		hps[m, 0, 1] = result[3]


def callback_err(result):
	print(result)

def gathering_results(params):
	holyGuidance = 0.2

	steps = 2
	a_tto = np.zeros([5, 2, 2], float)
	a_hld = np.zeros([5, 2, 2], float)
	a_hps = np.zeros([5, 2, 2], float)

	with Pool(6) as pool:
		# no gems
		paramStandard = ParametersVariable(params, HLMana=34, overallMana=0.05)
		pool.apply_async(simulation, \
			 args=(paramStandard,), \
			 callback=partial(callback_fn_multi, n=5, tto=a_tto, hld=a_hld, hps=a_hps), \
			 error_callback=callback_err)

		# +spell power
		paramSpellPower = ParametersVariable(params, HLMana=34, overallMana=0.05, spellPower=params.numberOfGems * params.spellPowerStep)
		pool.apply_async(simulation, \
			 args=(paramSpellPower,), \
			 callback=partial(callback_fn, n=0, i=1, tto=a_tto, hld=a_hld, hps=a_hps), \
			 error_callback=callback_err)

		# +mp5
		paramMp5 = ParametersVariable(params, HLMana=34, overallMana=0.05, mp5=params.numberOfGems * params.mp5Step)
		pool.apply_async(simulation, \
			 args=(paramMp5,), \
			 callback=partial(callback_fn, n=1, i=1, tto=a_tto, hld=a_hld, hps=a_hps), \
			 error_callback=callback_err)

		# +crit
		paramCrit = ParametersVariable(params, HLMana=34, overallMana=0.05, crit=params.numberOfGems * params.critStep)
		pool.apply_async(simulation, \
			 args=(paramCrit,), \
			 callback=partial(callback_fn, n=2, i=1, tto=a_tto, hld=a_hld, hps=a_hps), \
			 error_callback=callback_err)

		# +int
		paramInt = ParametersVariable(params, HLMana=34, overallMana=0.05, \
					manaPool=params.numberOfGems * params.intStep * 1.21 * 15, \
					spellPower=params.numberOfGems * params.intStep * 1.21 * holyGuidance, \
					crit=params.numberOfGems * 1.21 * params.intCoefficient)
		pool.apply_async(simulation, \
			 args=(paramInt,), \
			 callback=partial(callback_fn, n=3, i=1, tto=a_tto, hld=a_hld, hps=a_hps), \
			 error_callback=callback_err)

		# +haste
		paramHaste = ParametersVariable(params, HLMana=34, overallMana=0.05, haste=params.numberOfGems * params.hasteStep)
		pool.apply_async(simulation, \
			 args=(paramHaste,), \
			 callback=partial(callback_fn, n=4, i=1, tto=a_tto, hld=a_hld, hps=a_hps), \
			 error_callback=callback_err)

		pool.close()
		pool.join()

	np.save("tto_12_gems", a_tto)
	np.save("hld_12_gems", a_hld)
	np.save("hps_12_gems", a_hps)

	b_tto = np.ones([params.numberOfItems, 2, 2], float)
	b_hld = np.ones([params.numberOfItems, 2, 2], float)
	b_hps = np.ones([params.numberOfItems, 2, 2], float)
	
	with Pool(6) as pool2:
		# nothing extra
		paramNothing = ParametersVariable(params)
		pool2.apply_async(simulation, \
			 args=(paramNothing,), \
			 callback=partial(callback_fn_multi, n=params.numberOfItems, tto=b_tto, hld=b_hld, hps=b_hps), \
			 error_callback=callback_err)

		# seal of wisdom
		paramWisdom = ParametersVariable(params, overallMana=0.05)
		pool2.apply_async(simulation, \
			 args=(paramWisdom,), \
			 callback=partial(callback_fn, n=0, i=1, tto=b_tto, hld=b_hld, hps=b_hps), \
			 error_callback=callback_err)

		# seal of light
		paramLight = ParametersVariable(params, overallHeal=0.05)
		pool2.apply_async(simulation, \
			 args=(paramLight,), \
			 callback=partial(callback_fn, n=1, i=1, tto=b_tto, hld=b_hld, hps=b_hps), \
			 error_callback=callback_err)

		# 2 piece Tier 7
		param2PT7 = ParametersVariable(params, HSCrit=0.1)
		pool2.apply_async(simulation, \
			 args=(param2PT7,), \
			 callback=partial(callback_fn, n=2, i=1, tto=b_tto, hld=b_hld, hps=b_hps), \
			 error_callback=callback_err)

		# 4 piece Tier 7 (without 2 piece)
		param4PT7 = ParametersVariable(params, HLManaPercent=0.05)
		pool2.apply_async(simulation, \
			 args=(param4PT7,), \
			 callback=partial(callback_fn, n=3, i=1, tto=b_tto, hld=b_hld, hps=b_hps), \
			 error_callback=callback_err)

		# libram of renewal
		paramRenewal = ParametersVariable(params, HLMana=113)
		pool2.apply_async(simulation, \
			 args=(paramRenewal,), \
			 callback=partial(callback_fn, n=4, i=1, tto=b_tto, hld=b_hld, hps=b_hps), \
			 error_callback=callback_err)
		
		# 2 piece Tier 6
		param2PT6 = ParametersVariable(params, FOLHealPercent=0.05)
		pool2.apply_async(simulation, \
			 args=(param2PT6,), \
			 callback=partial(callback_fn, n=5, i=1, tto=b_tto, hld=b_hld, hps=b_hps), \
			 error_callback=callback_err)
		
		# 4 piece Tier 6 (without 2 piece)
		param4PT6 = ParametersVariable(params, HLCrit=0.05)
		pool2.apply_async(simulation, \
			 args=(param4PT6,), \
			 callback=partial(callback_fn, n=6, i=1, tto=b_tto, hld=b_hld, hps=b_hps), \
			 error_callback=callback_err)

		# libram of absolute truth
		paramTruth = ParametersVariable(params, HLMana=34)
		pool2.apply_async(simulation, \
			 args=(paramTruth,), \
			 callback=partial(callback_fn, n=7, i=1, tto=b_tto, hld=b_hld, hps=b_hps), \
			 error_callback=callback_err)

		# libram of mending
		paramMending = ParametersVariable(params, mp5=28)
		pool2.apply_async(simulation, \
			 args=(paramMending,), \
			 callback=partial(callback_fn, n=8, i=1, tto=b_tto, hld=b_hld, hps=b_hps), \
			 error_callback=callback_err)

		# libram of tolerance
		paramTolerance = ParametersVariable(params, HLHeal=141)
		pool2.apply_async(simulation, \
			 args=(paramTolerance,), \
			 callback=partial(callback_fn, n=9, i=1, tto=b_tto, hld=b_hld, hps=b_hps), \
			 error_callback=callback_err)

		# libram of souls redeemed
		paramRedeemed = ParametersVariable(params, FOLHeal=89)
		pool2.apply_async(simulation, \
			 args=(paramRedeemed,), \
			 callback=partial(callback_fn, n=10, i=1, tto=b_tto, hld=b_hld, hps=b_hps), \
			 error_callback=callback_err)

		# libram of the lightbringer
		paramLightbringer = ParametersVariable(params, HLHeal=42)
		pool2.apply_async(simulation, \
			 args=(paramLightbringer,), \
			 callback=partial(callback_fn, n=11, i=1, tto=b_tto, hld=b_hld, hps=b_hps), \
			 error_callback=callback_err)

		pool2.close()
		pool2.join()

	np.save("tto_libram", b_tto)
	np.save("hld_libram", b_hld)
	np.save("hps_libram", b_hps)

def test_func(args, a="aaa", b="bbb", c="ccc"):
	print(a,b,c)

if __name__ == '__main__':
	# magic numbers
	criticalStrikeRating = 1 / 45 / 100
	intCritCoefficient = 1 / 200 / 100
#	hasteRating = 3280
#	holyGuidance = 0.2
#	illumination = 0.3
#	healCoeff = 0.53


	# Spell(ManaCost, Duration, CD, Delay, LastUse, Interval, Probability)

	divineFavorManaCost = 123
	divineFavorCD = 120
	divineFavorDelay = 20
	divineFavorLastUse = divineFavorDelay - divineFavorCD
	divineFavor = SpellExtended(divineFavorManaCost, 0, divineFavorCD, divineFavorDelay, divineFavorLastUse)
	
	divineIlluminationDuration = 15
	divineIlluminationCD = 120
	divineIlluminationDelay = 20
	divineIlluminationLastUse = divineIlluminationDelay - divineIlluminationCD
	divineIllumination = SpellExtended(0, divineIlluminationDuration, divineIlluminationCD, divineIlluminationDelay, divineIlluminationLastUse)

	beaconOfLightManaCost = 1440
	beaconOfLightDuration = 55
	beaconOfLightLastUse = -10
	beaconOfLightProbability = 0.3
	beaconOfLight = SpellBeacon(beaconOfLightManaCost, beaconOfLightDuration, beaconOfLightLastUse, beaconOfLightProbability)

	sacredShieldManaCost = 494
	sacredShieldDuration = 55
	sacredShieldLastUse = -8
	sacredShieldInterval = 9
#	sacredShieldLastProc = -1 * sacredShieldInterval - 1
	sacredShield = SpellShield(sacredShieldManaCost, sacredShieldDuration, sacredShieldLastUse, sacredShieldInterval)

	avengingWrathManaCost = 329
	avengingWrathDuration = 20
	avengingWrathCD = 180
	avengingWrathDelay = 20
	avengingWrathLastUse = avengingWrathDelay - avengingWrathCD
	avengingWrath = SpellExtended(avengingWrathManaCost, avengingWrathDuration, avengingWrathCD, avengingWrathDelay, avengingWrathLastUse)

	divinePleaDuration = 15
	divinePleaCD = 60
	divinePleaDelay = 99999
	divinePleaLastUse = divinePleaDelay - divinePleaCD
	divinePlea = SpellExtended(0, divinePleaDuration, divinePleaCD, divinePleaDelay, divinePleaLastUse)

	judgementManaCost = 206
	judgementDuration = 55
	judgementLastUse = -1 * judgementDuration - 1
	judgement = Spell(judgementManaCost, judgementDuration, judgementLastUse)
	
	numberOfItems = 12
	numberOfGems = 12
	spellPowerStep = 19
	mp5Step = 8
	critStep = 16 * criticalStrikeRating
	intStep = 16
	hasteStep = 16

	iterations = 100
	activity = 0.8
	# fol, hl, hs
	ratio = (35, 45, 20)
	# encounter limit in seconds
	limit = 480
	
	manaPool = 21349
	extraMana = 4300 * 1.25
	spell_power = 1475
	# adding pot/rune as static mp5
	mp5_raidbuffs = 92 * 1.2 + 91
	mp5 = 159 + mp5_raidbuffs
	crit = 0.198639
	haste_coeff = 3280
	haste_raidbuffs = 0.03 + 0.05
	haste_selfbuffs = 0.15
	haste = 176 + (haste_selfbuffs + haste_raidbuffs) * haste_coeff

	normalizingFactor = 10

	
	if "sim" in sys.argv:
		parametersObject = Parameters(iterations, numberOfGems, numberOfItems, limit, activity, ratio, haste_coeff, intCritCoefficient, criticalStrikeRating, manaPool, spell_power, mp5, crit, haste, spellPowerStep, mp5Step, critStep, intStep, hasteStep, divineFavor, divineIllumination, beaconOfLight, sacredShield, avengingWrath, divinePlea, judgement)
		gathering_results(parametersObject)

	elif "print" in sys.argv:
		print("Spell ratio: FoL " + str(ratio[0]) + "% - HL " + str(ratio[1]) + "% - HS " + str(ratio[2]) + "%")
		print("Activity level: " + str(round(activity * 100)) + "%")
		l_tto = np.load("tto_12_gems.npy")
		l_hps = np.load("hps_12_gems.npy")
		l_hld = np.load("hld_12_gems.npy")
		result_tto = np.zeros([5], float)
		result_hld = np.zeros([5], float)
		result_hps = np.zeros([5], float)
		analysis(l_tto, l_hld, l_hps, result_tto, result_hld, result_hps, numberOfGems)
		pretty_printing_regular(l_tto, l_hld, l_hps, result_tto, result_hld, result_hps, normalizingFactor)

		libram_tto = np.load("tto_libram.npy")
		libram_hps = np.load("hps_libram.npy")
		libram_hld = np.load("hld_libram.npy")
		result_libram_tto = np.ones([numberOfItems], float)
		result_libram_hld = np.ones([numberOfItems], float)
		result_libram_hps = np.ones([numberOfItems], float)
		analysis_libram(libram_tto, libram_hld, libram_hps, result_libram_tto, result_libram_hld, result_libram_hps)
		pretty_printing_libram(libram_tto, libram_hld, libram_hps, result_libram_tto, result_libram_hld, result_libram_hps, result_hld, result_hps, numberOfItems, normalizingFactor)
                                                               	
	else:
		print("missing arguments.\n\"sim\" for running the simulation and \"print\" to print the results.")

#	gathering_results(runs, activity, ratio, limit, mana_pool, extra_mana, spell_power, mp5, crit, haste, healing_step, mp5_step, crit_step, int_step, haste_step)

#	debug_run(limit, activity, ratio, mana_pool + extra_mana, healing, 0, 0, 185, 580, 34, mp5, crit, haste)

#a = encounter(True, 0.88, (28, 45, 23, 4), 12723, 2077, 163, 0.2278, 0)
