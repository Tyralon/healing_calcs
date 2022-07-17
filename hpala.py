import random
import statistics
import numpy as np
from multiprocessing import Pool
from functools import partial
from enum import Enum

class Encounter:

	def __init__(self, params):
		self.fol = Healing(785, 879, 1.5, 288, params.overallMana * 288, params.spellPower + params.FOLHeal, params.crit, params.haste, 1 + params.overallHeal + params.FOLHealPercent, HealType.FOL)
		self.hs = Healing(2401, 2599, 1.5, 741, params.overallMana * 741, params.spellPower + params.HSHeal, params.crit + params.HSCrit + 0.06, params.haste, 1 + params.overallHeal, HealType.HS)
		self.hl = Healing(4888, 5444, 2.5, 1193, params.overallMana * 1193 + params.HLManaPercent * 1193 + params.HLMana, params.spellPower + params.HLHeal, params.crit + params.HLCrit + 0.06, params.haste, 1 + params.overallHeal, HealType.HL)
		self.gcd = Healing(0, 0, 1.5, 0, 0, params.spellPower, params.crit, params.haste, 1, HealType.GCD)
		self.heals_list = [self.fol, self.hl, self.hs]
		self.time = 0.0
		self.healed = 0
		self.mana_tick = 2
		self.mp2 = params.mp5 / 5 * 2 + params.manaPool * 0.25 / 30 * 0.75
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
		self.beacon_last_use = -1 * self.beacon_duration - 1
		self.beacon_mana_cost = 1440
		self.beacon_probability = 0.5
		self.iol_activated = False
		self.sacred_shield_interval = 9
		self.sacred_shield_last_proc = -1 * self.sacred_shield_interval - 1
		self.sacred_shield_duration = 55
		self.sacred_shield_last_use = -1 * self.sacred_shield_duration - 1
		self.sacred_shield_mana_cost = 494
		self.wrath_cd = 180
		self.wrath_delay = 20
		self.wrath_last_use = self.wrath_delay - self.wrath_cd
		self.wrath_duration = 20
		self.wrath_mana_cost = 329
		self.divine_plea_cd = 60
		self.divine_plea_delay = 60
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
		self.favor_last_use = self.favor_delay - self.favor_cd
		self.div_illu_last_use = self.div_illu_delay - self.div_illu_cd
		self.grace_last_use = -1 * self.grace_duration - 1
		self.beacon_last_use = -1 * self.beacon_duration - 1
		self.sacred_shield_last_proc = -1 * self.sacred_shield_interval - 1
		self.sacred_shield_last_use = -1 * self.sacred_shield_duration - 1
		self.wrath_last_use = self.wrath_delay - self.wrath_cd
		self.divine_plea_last_use = self.divine_plea_delay - self.divine_plea_cd
		self.iol_activated = False
		self.limit_reached = False

	def pickSpell(self):
		return random.choices(self.heals_list, weights=self.ratio, k=1)[0]

	def isDivineIlluminationActive(self):
		return self.isBuffActive(self.div_illu_last_use, self.div_illu_duration, self.time)
	
	def isBuffActive(self, lastUse, duration, time):
		return lastUse + duration >= time and lastUse <= time

	def isBuffReady(self, lastUse, delay, cd, time):
		return lastUse + cd <= time and delay <= time

	def areWeOOM(self, spell):
		if self.isDivineIlluminationActive():
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
		if self.isBuffReady(self.favor_last_use, self.favor_cd, self.favor_delay, self.time):
			self.favor = 1
			self.removeMana(self.favor_mana_cost)

		if self.isBuffReady(self.div_illu_last_use, self.div_illu_cd, self.div_illu_delay, self.time):
			self.div_illu_last_use = self.time

		if self.isBuffReady(self.wrath_last_use, self.wrath_cd, self.wrath_delay, self.time):
			self.wrath_last_use = self.time
			self.removeMana(self.wrath_mana_cost)

		if self.isBuffReady(self.divine_plea_last_use, self.divine_plea_cd, self.divine_plea_delay, self.time):
			self.divine_plea_last_use = self.time
			self.gcd.updateHaste(0, 0, 0, 0)
			self.incrementTime(self.gcd)

		if not self.isBuffActive(self.beacon_last_use, self.beacon_duration, self.time):
			self.beacon_last_use = self.time
			self.removeMana(self.beacon_mana_cost)
			self.gcd.updateHaste(0, 0, 0, 0)
			self.incrementTime(self.gcd)

		if not self.isBuffActive(self.sacred_shield_last_use, self.sacred_shield_duration, self.time):
			self.sacred_shield_last_use = self.time
			self.removeMana(self.sacred_shield_mana_cost)
			self.gcd.updateHaste(0, 0, 0, 0)
			self.incrementTime(self.gcd)

		if not self.isBuffActive(self.judgement_last_use, self.judgement_duration, self.time):
			self.judgement_last_use = self.time
			self.removeMana(self.judgement_mana_cost)
			self.gcd.updateHaste(0, 0, 0, 0)
			self.incrementTime(self.gcd)

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
		if self.isDivineIlluminationActive():
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
		if not self.isBuffActive(self.sacred_shield_last_proc, self.sacred_shield_interval, self.time):
			self.sacred_shield_last_proc = self.time
			self.fol.setExtraCrit(0.5)

			self.healed += (1000 + self.spellPower * 0.75) * 1.2

	def deactivateSacredShield(self, spell):
		if spell.getHealType() == HealType.FOL:
			self.fol.setExtraCrit(0)

	def castSpell(self, spell):
		self.incrementTime(spell)

		if self.isBuffActive(self.wrath_last_use, self.wrath_duration, self.time):
			wrathMultiplier = 1.2
		else:
			wrathMultiplier = 1

		if self.isBuffActive(self.divine_plea_last_use, self.divine_plea_duration, self.time):
			pleaMultiplier = 0.5
		else:
			pleaMultiplier = 1

		if self.isBuffActive(self.beacon_last_use, self.beacon_duration, self.time) and self.beacon_probability > random.random():
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

class HealType(Enum):
	FOL = 0
	HL = 1
	HS = 2
	GCD = 3

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
		if self.healType == HealType.HL and grace_last_use + grace_duration >= time and grace_last_use <= time:
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

	def getHealType(self):
		return self.healType

class Parameters:

	def __init__(self, iterations, limit, activity, ratio, hasteCoefficient, intCoefficient, critRating, manaPool, spellPower, mp5, crit, haste, spellPowerStep, mp5Step, critStep, intStep, hasteStep):
		self.iterations = iterations
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
	numberOfSteps = 12
	holyGuidance = 0.2

	steps = 2
	a_tto = np.zeros([5, steps, 2], float)
	a_hld = np.zeros([5, steps, 2], float)
	a_hps = np.zeros([5, steps, 2], float)

	with Pool(6) as pool:
		# no gems
		paramStandard = ParametersVariable(params, HLMana=34, overallMana=0.05)
		pool.apply_async(simulation, \
			 args=(paramStandard,), \
			 callback=partial(callback_fn_multi, n=5, tto=a_tto, hld=a_hld, hps=a_hps), \
			 error_callback=callback_err)

		# +spell power
		paramSpellPower = ParametersVariable(params, HLMana=34, overallMana=0.05, spellPower=numberOfSteps * params.spellPowerStep)
		pool.apply_async(simulation, \
			 args=(paramSpellPower,), \
			 callback=partial(callback_fn, n=0, i=1, tto=a_tto, hld=a_hld, hps=a_hps), \
			 error_callback=callback_err)

		# +mp5
		paramMp5 = ParametersVariable(params, HLMana=34, overallMana=0.05, mp5=numberOfSteps * params.mp5Step)
		pool.apply_async(simulation, \
			 args=(paramMp5,), \
			 callback=partial(callback_fn, n=1, i=1, tto=a_tto, hld=a_hld, hps=a_hps), \
			 error_callback=callback_err)

		# +crit
		paramCrit = ParametersVariable(params, HLMana=34, overallMana=0.05, crit=numberOfSteps * params.critStep)
		pool.apply_async(simulation, \
			 args=(paramCrit,), \
			 callback=partial(callback_fn, n=2, i=1, tto=a_tto, hld=a_hld, hps=a_hps), \
			 error_callback=callback_err)

		# +int
		paramInt = ParametersVariable(params, HLMana=34, overallMana=0.05, \
					manaPool=numberOfSteps * params.intStep * 1.21 * 15, \
					spellPower=numberOfSteps * params.intStep * 1.21 * holyGuidance, \
					crit=numberOfSteps * 1.21 * params.intCoefficient)
		pool.apply_async(simulation, \
			 args=(paramInt,), \
			 callback=partial(callback_fn, n=3, i=1, tto=a_tto, hld=a_hld, hps=a_hps), \
			 error_callback=callback_err)

		# +haste
		paramHaste = ParametersVariable(params, HLMana=34, overallMana=0.05, haste=numberOfSteps * params.hasteStep)
		pool.apply_async(simulation, \
			 args=(paramHaste,), \
			 callback=partial(callback_fn, n=4, i=1, tto=a_tto, hld=a_hld, hps=a_hps), \
			 error_callback=callback_err)

		pool.close()
		pool.join()

	np.save("tto_12_gems", a_tto)
	np.save("hld_12_gems", a_hld)
	np.save("hps_12_gems", a_hps)

	numItems = 10
	b_tto = np.ones([numItems, steps, 2], float)
	b_hld = np.ones([numItems, steps, 2], float)
	b_hps = np.ones([numItems, steps, 2], float)
	
	with Pool(5) as pool2:
		# nothing extra
		paramNothing = ParametersVariable(params)
		pool2.apply_async(simulation, \
			 args=(paramNothing,), \
			 callback=partial(callback_fn_multi, n=numItems, tto=b_tto, hld=b_hld, hps=b_hps), \
			 error_callback=callback_err)

		# seal of wisdom
		paramWisdom = ParametersVariable(params, overallMana=0.05)
		pool2.apply_async(simulation, \
			 args=(paramWisdom,), \
			 callback=partial(callback_fn, n=0, i=1, tto=b_tto, hld=b_hld, hps=b_hps), \
			 error_callback=callback_err)

		# seal of light
		paramLight= ParametersVariable(params, overallHeal=0.05)
		pool2.apply_async(simulation, \
			 args=(paramLight,), \
			 callback=partial(callback_fn, n=1, i=1, tto=b_tto, hld=b_hld, hps=b_hps), \
			 error_callback=callback_err)

		# 4 piece Tier 7
		paramLight= ParametersVariable(params, HLManaPercent=0.05, HSCrit=0.1)
		pool2.apply_async(simulation, \
			 args=(paramLight,), \
			 callback=partial(callback_fn, n=2, i=1, tto=b_tto, hld=b_hld, hps=b_hps), \
			 error_callback=callback_err)

		# libram of renewal
		paramRenewal= ParametersVariable(params, HLMana=113)
		pool2.apply_async(simulation, \
			 args=(paramRenewal,), \
			 callback=partial(callback_fn, n=3, i=1, tto=b_tto, hld=b_hld, hps=b_hps), \
			 error_callback=callback_err)

		# libram of absolute truth
		paramTruth= ParametersVariable(params, HLMana=34)
		pool2.apply_async(simulation, \
			 args=(paramTruth,), \
			 callback=partial(callback_fn, n=4, i=1, tto=b_tto, hld=b_hld, hps=b_hps), \
			 error_callback=callback_err)

		# libram of mending
		paramMending= ParametersVariable(params, mp5=28)
		pool2.apply_async(simulation, \
			 args=(paramMending,), \
			 callback=partial(callback_fn, n=5, i=1, tto=b_tto, hld=b_hld, hps=b_hps), \
			 error_callback=callback_err)

		# libram of tolerance
		paramTolerance= ParametersVariable(params, HLHeal=141)
		pool2.apply_async(simulation, \
			 args=(paramTolerance,), \
			 callback=partial(callback_fn, n=6, i=1, tto=b_tto, hld=b_hld, hps=b_hps), \
			 error_callback=callback_err)

		# libram of souls redeemed
		paramRedeemed= ParametersVariable(params, FOLHeal=89)
		pool2.apply_async(simulation, \
			 args=(paramRedeemed,), \
			 callback=partial(callback_fn, n=7, i=1, tto=b_tto, hld=b_hld, hps=b_hps), \
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
	iterations = 10000
	activity = 0.90
	crit_rating = 1 / 45 / 100
	intCritCoefficient = 1 / 200 / 100
	
	# fol, hl, hs
	ratio = (65, 27, 8)
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

	spellPowerStep = 19
	mp5Step = 8
	critStep = 16 * crit_rating
	intStep = 16
	hasteStep = 16


	parametersObject = Parameters(iterations, limit, activity, ratio, haste_coeff, intCritCoefficient, crit_rating, manaPool, spell_power, mp5, crit, haste, spellPowerStep, mp5Step, critStep, intStep, hasteStep)

	#parametersVariableObject = ParametersVariable(parametersObject, spellPower=100)
	#print(parametersVariableObject.spellPower)

	gathering_results(parametersObject)

#	gathering_results(runs, activity, ratio, limit, mana_pool, extra_mana, spell_power, mp5, crit, haste, healing_step, mp5_step, crit_step, int_step, haste_step)

#	debug_run(limit, activity, ratio, mana_pool + extra_mana, healing, 0, 0, 185, 580, 34, mp5, crit, haste)

#a = encounter(True, 0.88, (28, 45, 23, 4), 12723, 2077, 163, 0.2278, 0)
