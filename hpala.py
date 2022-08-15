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
		self.v = params
		self.healList = [self.v.p.flashOfLight, self.v.p.holyLight, self.v.p.holyShock]
		self.manaTick = 2
		self.mp2 = self.v.p.mp5 / 5 * 2 + self.v.p.manaPool * 0.25 / 60 * 2 * 0.75
		self.maxMana = self.v.p.manaPool
		self.illuminationFactor = 0.3
		self.divineIlluminationFactor = 0.5
		self.grace_effect = 0.5
		self.grace_duration = 15
		self.delayCoefficient = (1 - self.v.p.activity) / self.v.p.activity

	def reset(self):
		self.time = 0.0
		self.healed = 0
		self.manaPool = self.maxMana
		self.lastTick = 0.0
		self.favor = 0
		self.extraMana = self.v.extraMana

		self.sacred_shield_last_proc = -1 * self.v.p.sacredShield.getInterval() - 1
		self.v.p.divineFavor.setLastUse(self.v.p.divineFavor.getDelay() - self.v.p.divineFavor.getCooldown())
		self.v.p.divineIllumination.setLastUse(self.v.p.divineIllumination.getDelay() - self.v.p.divineIllumination.getCooldown())
		self.grace_last_use = -1 * self.grace_duration - 1
		self.v.p.beaconOfLight.setLastUse(-10)
		self.v.p.sacredShield.setLastUse(-8)
		self.v.p.avengingWrath.setLastUse(self.v.p.avengingWrath.getDelay() - self.v.p.avengingWrath.getCooldown())
		self.v.p.divinePlea.setLastUse(self.v.p.divinePlea.getDelay() - self.v.p.divinePlea.getCooldown())
		self.iol_activated = False
		self.limitReached = False

		self.v.p.flashOfLight.setHealIncreasePercent(self.v.overallHeal + self.v.FOLHealPercent)
		self.v.p.flashOfLight.setSpellPowerIncrease(self.v.FOLHeal)
		self.v.p.flashOfLight.setManaCostReductionPercent(self.v.overallMana)
		self.v.p.holyLight.setHealIncreasePercent(self.v.overallHeal)
		self.v.p.holyLight.setSpellPowerIncrease(self.v.HLHeal)
		self.v.p.holyLight.setExtraCrit(self.v.HLCrit)
		self.v.p.holyLight.setManaCostReduction(self.v.HLMana)
		self.v.p.holyLight.setManaCostReductionPercent(self.v.overallMana + self.v.HLManaPercent)
		self.v.p.holyShock.setHealIncreasePercent(self.v.overallHeal)
		self.v.p.holyShock.setSpellPowerIncrease(self.v.HSHeal)
		self.v.p.holyShock.setExtraCrit(self.v.HSCrit)
		self.v.p.holyShock.setManaCostReductionPercent(self.v.overallMana)



	def updateManaCost(self, spell, time):
		if self.isBuffActive(self.v.p.divineIllumination, time):
			return spell.getBaseManaCost() * (1 - self.divineIlluminationFactor - spell.getManaCostReductionPercent()) - spell.getManaCostReduction()
		else:
			return spell.getBaseManaCost() * (1 - spell.getManaCostReductionPercent()) - spell.getManaCostReduction()

	def updateCastTime(self, spell, time, haste, hasteRatingCoefficient):
		if isinstance(spell, Heal) and spell.getSpellType() == SpellType.HL and self.grace_last_use + self.grace_duration >= time and self.grace_last_use <= time:
			return (spell.getBaseCastTime() - self.grace_effect) / ( 1 + haste / hasteRatingCoefficient)
		else:
			return spell.getBaseCastTime() / ( 1 + haste / hasteRatingCoefficient)

	def updateSpell(self, spell, time, haste, hasteRatingCoefficient):
		spell.setManaCost(self.updateManaCost(spell, time))
		spell.setCastTime(self.updateCastTime(spell, time, haste, hasteRatingCoefficient))
	
	def pickSpell(self, healList, ratio):
		return random.choices(healList, weights=ratio, k=1)[0]

	def isBuffActive(self, spell, time):
		return spell.getLastUse() + spell.getDuration() >= time and spell.getLastUse() <= time

	def isBuffReady(self, spell, time):
		return spell.getLastUse() + spell.getCooldown() <= time and spell.getDelay() <= time

	def areWeOOM(self, spell, manaPool):
		return manaPool < spell.getManaCost()

	def updateLastTick(self, manaTick):
		self.lastTick += manaTick

	def updateManaTick(self, time, manaTick, mp2, manaPool, maxMana):
		while self.lastTick < time:
			self.updateLastTick(manaTick)
			self.addMana(mp2, manaPool, maxMana)

	def addMana(self, amount, manaPool, maxMana):
		if manaPool + amount > maxMana:
			#should use setter
			self.manaPool = maxMana
		else:
			self.manaPool += amount
	
	def returnMana(self, spell, manaPool, maxMana):
		if spell.getCritted():
			self.addMana(spell.getBaseManaCost() * self.illuminationFactor, manaPool, maxMana)

	def limitReachedCheck(self, time, limit):
		if time >= limit:
			self.setLimitReached(True)

	def popCooldowns(self, time, haste, hasteRatingCoefficient):
		self.updateSpell(self.v.p.divineFavor, time, haste, hasteRatingCoefficient)
		self.castBuffCD(self.v.p.divineFavor, time)

		self.updateSpell(self.v.p.avengingWrath, time, haste, hasteRatingCoefficient)
		self.castBuffCD(self.v.p.avengingWrath, time)

		self.updateSpell(self.v.p.divinePlea, time, haste, hasteRatingCoefficient)
		self.castBuffCD(self.v.p.divinePlea, time)

		self.updateSpell(self.v.p.beaconOfLight, time, haste, hasteRatingCoefficient)
		self.castBuff(self.v.p.beaconOfLight, time)

		self.updateSpell(self.v.p.sacredShield, time, haste, hasteRatingCoefficient)
		self.castBuff(self.v.p.sacredShield, time)

		self.updateSpell(self.v.p.judgement, time, haste, hasteRatingCoefficient)
		self.castBuff(self.v.p.judgement, time)

	def updateDivineFavor(self, divineFavor, time):
		if self.favor == 1:
			self.favor = 0
			divineFavor.setLastUse(time)

	def updateLightsGrace(self, spell, time):
		if spell.getSpellType() == SpellType.HL:
			#should use getters
			self.grace_last_use = time

	def incrementTime(self, spell):
		self.time += spell.getCastTime()
		
	def addHealing(self, amount):
		self.healed += amount
		
	def removeMana(self, amount):
		self.manaPool -= amount
		
	def consumeMana(self, spell):
		self.removeMana(spell.getManaCost())

	def activateInfusionOfLight(self, spell, holyLight):
		if spell.getSpellType() == SpellType.HS and spell.getCritted():
			self.iol_activated = True
			holyLight.setExtraCrit(self.v.HLCrit + 0.2)
	
	def deactivateInfusionOfLight(self, spell, holyLight):
		if self.iol_activated and (spell.getSpellType() == SpellType.FOL or spell.getSpellType() == SpellType.HL):
			self.iol_activated = False
			holyLight.setExtraCrit(self.v.HLCrit)

	def activateSacredShield(self, spell, flashOfLight, spellPower, time):
		if self.sacred_shield_last_proc + self.v.p.sacredShield.getInterval() >= time:
			self.sacred_shield_last_proc = time
			flashOfLight.setExtraCrit(0.5)

			# talent = 20%
			# SP scaling = 1.5 / 3.5
			self.addHealing((1000 + spellPower * 0.4286) * 1.2)

	def deactivateSacredShield(self, spell, flashOfLight):
		if spell.getSpellType() == SpellType.FOL:
			flashOfLight.setExtraCrit(0)

	def castBuffCD(self, spell, time):
		if self.isBuffReady(spell, time):
			spell.setLastUse(time)
			self.incrementTime(spell)
			self.consumeMana(spell)

	def castBuff(self, spell, time):
		if not self.isBuffActive(spell, time):
			spell.setLastUse(time)
			self.incrementTime(spell)
			self.consumeMana(spell)

	def castHeal(self, spell, spellPower):
		self.incrementTime(spell)
		
		heal = (random.randint(spell.getLowerHeal(), spell.getUpperHeal()) + (spellPower + spell.getSpellPowerIncrease()) * spell.getSpellPowerCoefficient() * 1.12) * spell.getHealIncreasePercent()

		# infusion of light
		# 1. a target is healed with SS
		# 2. the hot then likely overheals
		# 3. there is already an IoL HoT up (12s duration)
		if spell.getSpellType == SpellType.FOL:
			iol_factor = 1 + 0.7 * 0.4 * 0.2
		else:
			iol_factor = 1
		if random.random() > (1 - self.v.crit - spell.getExtraCrit() - self.favor):
			spell.setCritted(True)
			critFactor = 1.5
		else:
			critFactor = 1
			spell.setCritted(False)
	
		# remember IoL
		if self.isBuffActive(self.v.p.avengingWrath, self.time):
			wrathMultiplier = 1.2
		else:
			wrathMultiplier = 1

		# effect not implemented yet
		if self.isBuffActive(self.v.p.divinePlea, self.time):
			pleaMultiplier = 1
		else:
			pleaMultiplier = 1

		if self.isBuffActive(self.v.p.beaconOfLight, self.time) and self.v.p.beaconOfLight.getProbability() > random.random():
			beaconMultiplier = 2
		else:
			beaconMultiplier = 1

		self.addHealing(heal * wrathMultiplier * pleaMultiplier * beaconMultiplier * critFactor * iol_factor)
		self.consumeMana(spell)

	def addDelay(self, spell, delayCoefficient):
		# should use setter
		self.time += delayCoefficient * spell.getCastTime()
		#return delay_coeff # * (2 * (1 - random.random()))

	def addExtraMana(self, manaPool, extraMana):
		if manaPool < self.v.p.beaconOfLight.getBaseManaCost() and extraMana > 0:
			self.addMana(extraMana)
			# should use setter
			self.extraMana = 0

	def runEncounter(self):
		while not self.limitReached:
			spell = self.pickSpell(self.healList, self.v.p.ratio)
			self.castBuff(self.v.p.divineIllumination, self.time)
			self.updateManaCost(spell, self.time)
			if self.areWeOOM(spell, self.manaPool):
				break
			self.popCooldowns(self.time, self.v.haste, self.v.p.hasteRatingCoefficient)
			self.updateSpell(spell, self.time, self.v.haste, self.v.p.hasteRatingCoefficient)
			self.activateSacredShield(spell, self.v.p.flashOfLight, self.v.spellPower, self.time)
			self.castHeal(spell, self.v.spellPower)
			self.returnMana(spell, self.manaPool, self.maxMana)
			self.updateDivineFavor(self.v.p.divineFavor, self.time)
			self.updateLightsGrace(spell, self.time)
			self.activateInfusionOfLight(spell, self.v.p.holyLight)
			self.deactivateInfusionOfLight(spell, self.v.p.holyLight)
			self.deactivateSacredShield(spell, self.v.p.flashOfLight)
			self.addDelay(spell, self.delayCoefficient)
			self.updateManaTick(self.time, self.manaTick, self.mp2, self.manaPool, self.maxMana)
			self.addExtraMana(self.v.manaPool, self.extraMana)
			self.limitReachedCheck(self.time, self.v.p.limit)

	def getTime(self):
		return self.time

	def getHealed(self):
		return self.healed

	def setLimitReached(self, limitReached):
		self.limitReached = limitReached

	def getLimitReached(self):
		return self.limitReached

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
	def getManaCostReductionPercent(self): return self.manaCostReductionPercent
	def getManaCostReduction(self): return self.manaCostReduction
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
	
	def __init__(self, baseManaCost, baseCastTime, lowerHeal, upperHeal, spellPowerFactor, spellType):
		super().__init__(baseManaCost, baseCastTime)
		self.lowerHeal = lowerHeal
		self.upperHeal = upperHeal
		self.spellPowerCoefficient = baseCastTime / spellPowerFactor
		self.spellType = spellType
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
	def getSpellType(self): return self.spellType
	def setCritted(self, critted):
		self.critted = critted
	def getCritted(self): return self.critted

class Parameters:

	def __init__(self, iterations, numberOfGems, numberOfItems, limit, activity, ratio, hasteRatingCoefficient, intCritCoefficient, critRatingCoefficient, manaPool, spellPower, mp5, crit, haste, spellPowerStep, mp5Step, critStep, intStep, hasteStep, divineFavor, divineIllumination, beaconOfLight, sacredShield, avengingWrath, divinePlea, judgement, flashOfLight, holyLight, holyShock):
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
		self.flashOfLight = flashOfLight
		self.holyLight = holyLight
		self.holyShock = holyShock

	def getIterations(self):
		try:
			return self.iterations
		except AttributeError:
			return self.p.iterations

	def getLimit(self):
		return self.limit

	def getActivity(self):
		return self.activity

	def getRatio(self):
		try:
			return self.ratio
		except AttributeError:
			return self.p.ratio

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
		self.p = args
		self.manaPool = args.manaPool + manaPool
		self.spellPower = args.spellPower + spellPower
		self.mp5 = args.mp5 + mp5
		self.crit = args.crit + crit
		self.haste = args.haste + haste
		#self.intellect = args.intellect

		self.extraMana = extraMana
		self.FOLHeal = FOLHeal
		self.FOLHealPercent = FOLHealPercent
		self.HLMana = HLMana
		self.HLManaPercent = HLManaPercent
		self.HLHeal = HLHeal
		self.HLCrit = HLCrit + 0.06
		self.HSHeal = HSHeal
		self.HSCrit = HSCrit + 0.06
		self.overallHeal = overallHeal
		self.overallMana = overallMana

def simulation(params):
	tto = []
	hld = []
	over_limit = 0

	encounterObject = Encounter(params)
	assert sum(params.getRatio()) == 100

	for i in range(params.getIterations()):
		encounterObject.reset()
		encounterObject.runEncounter()
		tto.append(encounterObject.getTime())
		hld.append(encounterObject.getHealed())
		if encounterObject.getLimitReached():
			over_limit += 1
	
	ttoMedian = statistics.median(tto)
	hldMedian = statistics.median(hld)
	hpsMedian = hldMedian / ttoMedian

	return [ttoMedian, hldMedian, hpsMedian, over_limit / params.getIterations()]
	

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

def debug(params):

	paramsVar = ParametersVariable(params)
	encounterObject = Encounter(paramsVar)
	assert sum(encounterObject.v.p.ratio) == 100

	encounterObject.reset()
	encounterObject.runEncounter()

if __name__ == '__main__':
	# magic numbers
	critRatingCoefficient = 1 / 45 / 100
	intCritCoefficient = 1 / 200 / 100
	hasteRatingCoefficient = 3280
#	holyGuidance = 0.2
#	illuminationFactor = 0.3
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

	parametersObject = Parameters(iterations, numberOfGems, numberOfItems, limit, activity, ratio, hasteRatingCoefficient, intCritCoefficient, critRatingCoefficient, manaPool, spell_power, mp5, crit, haste, spellPowerStep, mp5Step, critStep, intStep, hasteStep, divineFavor, divineIllumination, beaconOfLight, sacredShield, avengingWrath, divinePlea, judgement, flashOfLight, holyLight, holyShock)
	
	if "sim" in sys.argv:
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

	elif "debug" in sys.argv:
		debug(parametersObject)
                                                               	
	else:
		print("missing arguments.\n\"sim\" for running the simulation and \"print\" to print the results.")

#	gathering_results(runs, activity, ratio, limit, mana_pool, extra_mana, spell_power, mp5, crit, haste, healing_step, mp5_step, crit_step, int_step, haste_step)

#	debug_run(limit, activity, ratio, mana_pool + extra_mana, healing, 0, 0, 185, 580, 34, mp5, crit, haste)

#a = encounter(True, 0.88, (28, 45, 23, 4), 12723, 2077, 163, 0.2278, 0)
