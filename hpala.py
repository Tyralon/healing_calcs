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
		self.mana_tick = 2
		self.mp2 = params.mp5 / 5 * 2 + params.manaPool * 0.25 / 60 * 2 * 0.75
		self.manaPool = params.manaPool
		self.max_mana = params.manaPool
		self.extraMana = params.extraMana
		self.last_tick = 0.0
		self.activity = params.activity
		self.ratio = params.ratio
		self.limit = params.limit
		self.illu_factor = 0.3
		self.favor = 0
		self.grace_effect = 0.5
		self.grace_duration = 15
		self.sacred_shield_last_proc = -1 * self.sacredShield.getInterval() - 1
		self.delayCoefficient = (1 - params.activity) / params.activity
		self.spellPower = params.spellPower
		self.haste = params.haste
		self.crit = params.crit
		self.hasteRatingCoefficient = params.hasteRatingCoefficient

# all healing modifiers don't seem to need to be transfered through params
# also, can we transfer params object as a single variable perhaps?
		self.fol = params.fol
		self.hl = params.hl
		self.hs = params.hs

	def reset(self):
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
		self.fol.setHealIncreasePercent(params.overallHeal + params.FOLHealPercent)
		self.fol.setSpellPowerIncrease(params.FOLHeal)
		self.fol.setManaCostReductionPercent(params.overallMana)
		self.hl.setHealIncreasePercent(params.overallHeal)
		self.hl.setSpellPowerIncrease(params.HLHeal)
		self.hl.setExtraCrit(params.HLCrit)
		self.hl.setManaCostReduction(params.HLMana)
		self.hl.setManaCostReductionPercent(params.overallMana + params.HLManaPercent)
		self.hs.setHealIncreasePercent(params.overallHeal)
		self.hs.setSpellPowerIncrease(params.HSHeal)
		self.hs.setExtraCrit(params.HSCrit)
		self.hs.setManaCostReductionPercent(params.overallMana)



	def updateManaCost(self, spell):
		if self.isBuffActive(self.divineIllumination, self.time):
			return spell.getBaseManaCost() * (1 - 0.5 - spell.getManaCostReductionPercent()) - spell.getManaCostReduction()
		else:
			return spell.getBaseManaCost() * (1 - spell.getManaCostReductionPercent()) - spell.getManaCostReduction()

	def updateCastTime(self, spell):
		if self.healType == SpellType.HL and self.grace_last_use + self.grace_duration >= self.time and self.grace_last_use <= self.time:
			return (spell.getBaseCastTime() - self.grace_effect) / ( 1 + self.haste / self.hasteRatingCoefficient)
		else:
			return spell.getBaseCastTime() / ( 1 + self.haste / self.hasteRatingCoefficient)

	def updateSpell(self, spell):
		spell.setManaCost(self.updateManaCost(spell))
		spell.setCastTime(self.updateCastTime(spell))
	
	def pickSpell(self):
		return random.choices(self.heals_list, weights=self.ratio, k=1)[0]

	def isBuffActive(self, spell, time):
		return spell.getLastUse() + spell.getDuration() >= time and spell.getLastUse() <= time

	def isBuffReady(self, spell, time):
		return spell.getLastUse() + spell.getCooldown() <= time and spell.getDelay() <= time

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
			self.divineFavor.setLastUse(self.time)

	def updateLightsGrace(self, spell):
		if spell.getSpellType() == SpellType.HL:
			self.grace_last_use = self.time

	def incrementTime(self, spell):
		self.time += spell.getCastTime()
		
	def addHealing(self, amount):
		self.healed += amount
		
	def removeMana(self, amount):
		self.manaPool -= amount
		
	def consumeMana(self, spell):
		self.removeMana(spell.getManaCost())

	def activateInfusionOfLight(self, spell):
		if spell.getSpellType() == SpellType.HS and spell.getCritted():
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

			# talent = 20%
			# SP scaling = 1.5 / 3.5
			self.healed += (1000 + self.spellPower * 0.4286) * 1.2

	def deactivateSacredShield(self, spell):
		if spell.getSpellType() == SpellType.FOL:
			self.fol.setExtraCrit(0)

	def castBuff(self, spell):
		spell.setLastUse(self.time)
		self.incrementTime(spell)
		self.consumeMana(spell)

	def castHeal(self, spell):
		self.incrementTime(spell)
		
		heal = (random.randint(spell.getLowerHeal(), spell.getUpperHeal()) + (self.spellPower + spell.getSpellPowerIncrease()) * spell.getSpellPowerCoefficient() * 1.12) * spell.getHealingIncreasePercent() * iol_factor

		# infusion of light
		# 1. a target is healed with SS
		# 2. the hot then likely overheals
		# 3. there is already an IoL HoT up (12s duration)
		if self.healType == SpellType.FOL:
			iol_factor = 1 + 0.7 * 0.4 * 0.2
		else:
			iol_factor = 1
		if random.random() > (1 - self.crit - spell.getExtraCrit() - spell.getTempCrit() - self.favor):
			spell.setCritted(True)
			critFactor = 1.5
		else:
			critFactor = 1
			spell.setCritted(False)
	
		# remember IoL
		if self.isBuffActive(self.avengingWrath, self.time):
			wrathMultiplier = 1.2
		else:
			wrathMultiplier = 1

		if self.isBuffActive(self.divinePlea, self.time):
			pleaMultiplier = 0.5
		else:
			pleaMultiplier = 1

		if self.isBuffActive(self.beaconOfLight, self.time) and self.beaconOfLight.getProbability() > random.random():
			beaconMultiplier = 2
		else:
			beaconMultiplier = 1

		self.addHealing(heal * wrathMultiplier * pleaMultiplier * beaconMultiplier * critFactor)
		self.consumeMana(spell)

	def castSpell(self, spell):
		self.incrementTime(spell)

		# remember IoL
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
#			self.updateSpell(spell)
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
	def __init__(self, baseManaCost, baseCastTime):
		self.baseManaCost = baseManaCost
		self.baseCastTime = baseCastTime
		self.manaCostReduction = 0
		self.manaCostReductionPercent = 0
		self.manaCost = baseManaCost
		self.castTime = baseCastTime
	def getBaseManaCost(self): return self.baseManaCost
	def getBaseCastTime(self): return self.baseCastTime
	def getManaCost(self): return self.manaCost
	def getCastTime(self): return self.castTime
	def setManaCostReduction(self, reduction):
		self.manaCostReduction = reduction
	def setManaCostReductionPercent(self, reduction):
		self.manaCostReductionPercent = reduction
	def setManaCost(self, manaCost):
		self.manaCost = manaCost
	def setCastTime(self, castTime):
		self.castTime = castTime


class Buff(Spell):
	def __init__(self, baseManaCost, baseCastTime, duration, lastUse):
		super().__init__(baseManaCost, baseCastTime)
		self.duration = duration
		self.lastUse = lastUse
	def getDuration(self): return self.duration
	def getLastUse(self): return self.lastUse
	def setLastUse(self, lastUse):
		self.lastUse = lastUse

class BuffBeacon(Buff):
	def __init__(self, baseManaCost, duration, baseCastTime, lastUse, probability):
		super().__init__(baseManaCost, duration, baseCastTime, lastUse)
		self.probability = probability
	def getProbability(self): return self.probability

class BuffShield(Buff):
	def __init__(self, baseManaCost, duration, baseCastTime, lastUse, interval):
		super().__init__(baseManaCost, duration, baseCastTime, lastUse)
		self.interval = interval
	def getInterval(self): return self.interval

class BuffExtended(Buff):
	def __init__(self, baseManaCost, duration, baseCastTime, cooldown, delay, lastUse):
		super().__init__(baseManaCost, duration, baseCastTime, lastUse)
		self.delay = delay
		self.cooldown = cooldown
	def getDelay(self): return self.delay
	def getCooldown(self): return self.cooldown

class Heal(Spell):
	
	def __init__(self, baseManaCost, baseCastTime, lowerHeal, upperHeal, spellPowerFactor, healType):
		super().__init__(baseManaCost, baseCastTime)
		self.lowerHeal = lowerHeal
		self.upperHeal = upperHeal
		self.spellPowerCoefficient = baseCastTime / spellPowerFactor
		self.healType = healType
		self.extraCrit = 0
		self.spellPowerIncrease = 0
		self.healIncreasePercent = 0
		self.critted = False
	def getLowerHeal(self): return self.lowerHeal
	def getUpperHeal(self): return self.upperHeal
	def setExtraCrit(self, extraCrit):
		self.extraCrit = extraCrit
	def getExtraCrit(self): return self.extraCrit
	def getSpellPowerCoefficient(self): return self.spellPowerCoefficient
	def setSpellPowerIncrease(self, spellPowerIncrease):
		self.spellPowerIncrease = spellPowerIncrease 
	def getSpellPowerIncrease(self): return self.spellPowerIncrease
	def setHealIncreasePercent(self, healIncreasePercent):
		self.healIncreasePercent = healIncreasePercent 
	def getHealIncreasePercent(self): return self.healIncreasePercent
	def getSpellType(self): return self.healType
	def setCritted(self, critted):
		self.critted = critted
	def getCritted(self): return self.critted

class Parameters:

	def __init__(self, iterations, numberOfGems, numberOfItems, limit, activity, ratio, hasteRatingCoefficient, intCritCoefficient, critRatingCoefficient, manaPool, spellPower, mp5, crit, haste, spellPowerStep, mp5Step, critStep, intStep, hasteStep, divineFavor, divineIllumination, beaconOfLight, sacredShield, avengingWrath, divinePlea, judgement):
		self.iterations = iterations
		self.numberOfGems = numberOfGems
		self.numberOfItems = numberOfItems
		self.limit = limit
		self.activity = activity
		self.ratio = ratio
		self.hasteRatingCoefficient = hasteRatingCoefficient
		self.intCritCoefficient = intCritCoefficient
		self.critRatingCoefficient = critRatingCoefficient
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
		self.hasteRatingCoefficient = args.hasteRatingCoefficient
		self.intCritCoefficient = args.intCritCoefficient
		self.critRatingCoefficient = critRatingCoefficient

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
		encounterObject.reset()
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
					crit=params.numberOfGems * 1.21 * params.intCritCoefficient)
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
	critRatingCoefficient = 1 / 45 / 100
	intCritCoefficient = 1 / 200 / 100
	hasteRatingCoefficient = 3280
#	holyGuidance = 0.2
#	illumination = 0.3
#	divineIlluminationFactor = 0.5


	# Spell(ManaCost, Duration, CD, Delay, LastUse, Interval, Probability)

	divineFavorManaCost = 123
	divineFavorDuration = 0
	divineFavorCD = 120
	divineFavorDelay = 20
	divineFavorBaseCastTime = 0
	divineFavorLastUse = divineFavorDelay - divineFavorCD
	divineFavor = BuffExtended(divineFavorManaCost, divineFavorDuration, divineFavorCD, divineFavorDelay, divineFavorBaseCastTime, divineFavorLastUse)
	
	divineIlluminationManaCost = 0
	divineIlluminationDuration = 15
	divineIlluminationCD = 120
	divineIlluminationDelay = 20
	divineIlluminationBaseCastTime = 0
	divineIlluminationLastUse = divineIlluminationDelay - divineIlluminationCD
	divineIllumination = BuffExtended(divineIlluminationManaCost, divineIlluminationDuration, divineIlluminationCD, divineIlluminationDelay, divineIlluminationBaseCastTime, divineIlluminationLastUse)

	beaconOfLightManaCost = 1440
	beaconOfLightDuration = 55
	beaconOfLightBaseCastTime = 1.5
	beaconOfLightLastUse = -10
	beaconOfLightProbability = 0.3
	beaconOfLight = BuffBeacon(beaconOfLightManaCost, beaconOfLightDuration, beaconOfLightBaseCastTime, beaconOfLightLastUse, beaconOfLightProbability)

	sacredShieldManaCost = 494
	sacredShieldDuration = 55
	sacredShieldBaseCastTime = 1.5
	sacredShieldLastUse = -8
	sacredShieldInterval = 9
#	sacredShieldLastProc = -1 * sacredShieldInterval - 1
	sacredShield = BuffShield(sacredShieldManaCost, sacredShieldDuration, sacredShieldBaseCastTime, sacredShieldLastUse, sacredShieldInterval)

	avengingWrathManaCost = 329
	avengingWrathDuration = 20
	avengingWrathCD = 180
	avengingWrathDelay = 20
	avengingWrathBaseCastTime = 0
	avengingWrathLastUse = avengingWrathDelay - avengingWrathCD
	avengingWrath = BuffExtended(avengingWrathManaCost, avengingWrathDuration, avengingWrathCD, avengingWrathDelay, avengingWrathBaseCastTime, avengingWrathLastUse)

	divinePleaManaCost = 0
	divinePleaDuration = 15
	divinePleaCD = 60
	divinePleaDelay = 99999
	divinePleaBaseCastTime = 1.5
	divinePleaLastUse = divinePleaDelay - divinePleaCD
	divinePlea = BuffExtended(divinePleaManaCost, divinePleaDuration, divinePleaCD, divinePleaDelay, divinePleaBaseCastTime, divinePleaLastUse)

	judgementManaCost = 206
	judgementDuration = 55
	judgementBaseCastTime = 1.5
	judgementLastUse = -1 * judgementDuration - 1
	judgement = Buff(judgementManaCost, judgementBaseCastTime, judgementDuration, judgementLastUse)
	
	# common for all heals
	spellPowerFactor = 1.5

	flashOfLightManaCost = 288
	flashOfLightCastTime = 1.5
	flashOfLightLowerHeal = 785
	flashOfLightUpperHeal = 879
	flashOfLight = Heal(flashOfLightManaCost, flashOfLightCastTime, flashOfLightLowerHeal, flashOfLightUpperHeal, spellPowerFactor, SpellType.FOL)

	holyShockManaCost = 741
	holyShockCastTime = 1.5
	holyShockLowerHeal = 2401
	holyShockUpperHeal = 2599
	holyShock = Heal(holyShockManaCost, holyShockCastTime, holyShockLowerHeal, holyShockUpperHeal, spellPowerFactor, SpellType.HS)

	holyLightManaCost = 1193
	holyLightCastTime = 2.5
	holyLightLowerHeal = 4888
	holyLightUpperHeal = 5444
	holyLight = Heal(holyLightManaCost, holyLightCastTime, holyLightLowerHeal, holyLightUpperHeal, spellPowerFactor, SpellType.HL)

	numberOfItems = 12
	numberOfGems = 12
	spellPowerStep = 19
	mp5Step = 8
	critStep = 16 * critRatingCoefficient
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
	haste_raidbuffs = 0.03 + 0.05
	haste_selfbuffs = 0.15
	haste = 176 + (haste_selfbuffs + haste_raidbuffs) * hasteRatingCoefficient

	normalizingFactor = 10

	
	if "sim" in sys.argv:
		parametersObject = Parameters(iterations, numberOfGems, numberOfItems, limit, activity, ratio, hasteRatingCoefficient, intCritCoefficient, critRatingCoefficient, manaPool, spell_power, mp5, crit, haste, spellPowerStep, mp5Step, critStep, intStep, hasteStep, divineFavor, divineIllumination, beaconOfLight, sacredShield, avengingWrath, divinePlea, judgement)
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
