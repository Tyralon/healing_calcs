import random
import statistics
import numpy as np

class Healing:
	
	def __init__(self, lower, upper, cast, mana, healing, crit, coeff):
		self.lower = lower
		self.upper = upper
		self.cast = cast
		self.mana = mana
		self.healing = healing
		self.crit = crit
		self.base_cast = cast
		self.base_mana = mana
		self.critted = False
		self.coeff = coeff

	def getCast(self):
		return self.cast

	def updateGrace(self, t, last_use):
		if (last_use + 15) >= t:
			self.cast = self.base_cast - 0.5
		else:
			self.cast = self.base_cast
	
	def setCritted(self, boolean):
		self.critted = boolean

	def getCritted(self):
		return self.critted

	def getBaseMana(self):
		return self.base_mana

	def heal(self):
		if random.random() < self.crit:
			self.critted = True
			return (random.randint(self.lower, self.upper) + (self.healing * self.base_cast / 3.5 * 1.12 * self.coeff)) * 1.5
		else:
			self.critted = False
			return (random.randint(self.lower, self.upper) + (self.healing * self.base_cast / 3.5 * 1.12 * self.coeff))

def mana_source(lower, upper, modifier):
	return random.randint(lower,upper) * modifier

# mana from dark rune or demonic rune
def mana_rune():
	return mana_source(900, 1500, 1)

# mana from super mana pot with alchemist's stone
def mana_pot_alch():
	return mana_source(1800, 3000, 1.4)

def encounter(activity, ratio, mana_pool, healing, mp5, base_crit):
	assert sum(ratio) == 100
	t = 0.0
	healed = 0
	
	fol = Healing(513, 574, 1.5, 180, healing, base_crit, 1.0797)
	hl8 = Healing(1424, 1584, 2.5, 580, healing, base_crit + 0.06, 1.023)
	hl9 = Healing(1813, 2015, 2.5, 660, healing, base_crit + 0.06, 1.108)
	hl11 = Healing(2459, 2740, 2.5, 840, healing, base_crit + 0.06, 1.1323)
	
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
	
	fol_ratio = ratio[0] / 100
	hl9_ratio = fol_ratio + ratio[1] / 100

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

		rvar = random.random()
		if rvar < fol_ratio:
			spell = fol
		elif rvar < hl9_ratio:
			spell = hl9
			if mana_pool >= spell.getBaseMana():
				spell.updateGrace(t, grace_last_use)
				grace = 1
			else:
				spell = fol
		else:
			spell = hl11
			if mana_pool >= spell.getBaseMana():
				spell.updateGrace(t, grace_last_use)
				grace = 1
			else:
				spell = fol
			
		# whether to pop cooldowns
		if t > favor_delay and (favor_last_use + favor_cd) <= t:
			spell.setCritted(True)
			favor = 1
		if t > div_illu_delay and (div_illu_last_use + div_illu_cd) <= t:
			div_illu_last_use = t


		t += spell.getCast()

		# casts the spell and adds it to the total healing
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

		# randomly adds delay for next cast based on y = -(x-1) / x
		t += -(activity - 1) / activity * spell.getCast()

		# checks time limit
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
	activity = 0.98
	ratio = [97, 0, 3]
	mana_pool = 12723
	crit = 0.2278
	crit_step = 0.0036
	mp5 = 163
	mp5_step = 3
	healing = 2077
	healing_step = 18

	steps = 15
	a_tto = np.zeros([4, steps, 2], float)
	a_hld = np.zeros([4, steps, 2], float)
	a_hps = np.zeros([4, steps, 2], float)
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
	for l in range(steps):
#		mana_pool += l * 8 * 1.21 * 15
#		crit += l * 8 * 1.21 / 79.4
#		healing += l * 8 * 1.21 * 0.35
		a = simulation(runs,
			activity,
			ratio,
			mana_pool + l * 8 * 1.21 * 15,
			healing + l * 8 * 1.21 * 0.35,
			mp5,
			crit + l * 8 * 1.21 / 79.4 / 100)
		a_tto[3, l, 0] = a[0]
		a_tto[3, l, 1] = a[3]
		a_hld[3, l, 0] = a[1]
		a_hld[3, l, 1] = a[3]
		a_hps[3, l, 0] = a[2]
		a_hps[3, l, 1] = a[3]
	np.save("tto_15_steps_10000_iter", a_tto)
	np.save("hld_15_steps_10000_iter", a_hld)
	np.save("hps_15_steps_10000_iter", a_hps)

gathering_results()

