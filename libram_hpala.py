import random
import statistics
import numpy as np

class Healing:
	
	def __init__(self, lower, upper, cast, mana, healing, crit, haste, coeff, hl, flat_fol, flat_hl):
		self.lower = lower
		self.upper = upper
		self.cast = cast
		self.mana = mana
		self.healing = healing
		self.crit = crit
		self.haste = haste
		self.base_cast = cast
		self.base_mana = mana
		self.critted = False
		self.coeff = coeff
		self.isHL = hl
		self.flat_fol = flat_fol
		self.flat_hl = flat_hl

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
			if self.isHL:
				return random.randint(self.lower, self.upper) * 2 + (self.healing * self.base_cast / 3.5 * 1.12 * self.coeff) + self.flat_hl
			else:
				return random.randint(self.lower, self.upper) * 2 + (self.healing * self.base_cast / 3.5 * 1.12 * self.coeff) + self.flat_fol
		else:
			self.critted = False
			if self.isHL:
				return random.randint(self.lower, self.upper) + (self.healing * self.base_cast / 3.5 * 1.12 * self.coeff) + self.flat_hl
			else:
				return random.randint(self.lower, self.upper) + (self.healing * self.base_cast / 3.5 * 1.12 * self.coeff) + self.flat_fol

def mana_source(lower, upper, modifier):
	return random.randint(lower,upper) * modifier

# mana from dark rune or demonic rune
def mana_rune():
	return mana_source(900, 1500, 1)

# mana from super mana pot with alchemist's stone
def mana_pot_alch():
	return mana_source(1800, 3000, 1.4)

def encounter(debug, activity, ratio, mana_pool, healing, heal_fol, heal_hl, mp5, base_crit, haste, flat_fol, flat_hl, mana_reduce):
	assert sum(ratio) == 100
	t = 0.0
	healed = 0
	
	fol = Healing(513, 574, 1.5, 180, healing + heal_fol, base_crit, haste, 1.0797, False, flat_fol, flat_hl)
	hl8 = Healing(1424, 1584, 2.5, 580 - mana_reduce, healing + heal_hl, base_crit + 0.06, haste, 1.023, True, flat_fol, flat_hl)
	hl9 = Healing(1813, 2015, 2.5, 660 - mana_reduce, healing + heal_hl, base_crit + 0.06, haste, 1.108, True, flat_fol, flat_hl)
	hl11 = Healing(2459, 2740, 2.5, 840 - mana_reduce, healing + heal_hl, base_crit + 0.06, haste, 1.1323, True, flat_fol, flat_hl)
	
	listOfHeals = [fol, hl8, hl9, hl11]

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

def simulation(runs, activity, ratio, mana_pool, healing, heal_fol, heal_hl, mp5, crit, haste, flat_fol, flat_hl, mana_reduce):
	tto = []
	healList = []
	over_limit = 0
	for i in range(runs):
		sim = encounter(False, activity, ratio, mana_pool, healing, heal_fol, heal_hl, mp5, crit, haste, flat_fol, flat_hl, mana_reduce)
		tto.append(sim[0])
		healList.append(sim[1])
		if sim[2]:
			over_limit += 1

	tto_median = statistics.median(tto)
	heal_median = statistics.median(healList)
	hps_median = heal_median / tto_median

	return [tto_median, heal_median, hps_median, over_limit / runs]

def gathering_results_libram():
	runs = 5000
	activity = 0.98
	ratio = (96, 1, 2, 1)
	mana_pool = 12723
	crit = 0.2278
	mp5 = 163
	healing = 2077
	haste = 0

	a_tto = np.zeros([5, 2, 2], float)
	a_hld = np.zeros([5, 2, 2], float)
	a_hps = np.zeros([5, 2, 2], float)
	# no libram
	a = simulation(runs, activity, ratio, mana_pool, healing, 0, 0, mp5, crit, haste, 0, 0, 0)
	a_tto[0, 0, 0] = a[0]
	a_tto[0, 0, 1] = a[3]
	a_hld[0, 0, 0] = a[1]
	a_hld[0, 0, 1] = a[3]
	a_hps[0, 0, 0] = a[2]
	a_hps[0, 0, 1] = a[3]
	a_tto[2, 0, 0] = a[0]
	a_tto[2, 0, 1] = a[3]
	a_hld[2, 0, 0] = a[1]
	a_hld[2, 0, 1] = a[3]
	a_hps[2, 0, 0] = a[2]
	a_hps[2, 0, 1] = a[3]
	a_tto[3, 0, 0] = a[0]
	a_tto[3, 0, 1] = a[3]
	a_hld[3, 0, 0] = a[1]
	a_hld[3, 0, 1] = a[3]
	a_hps[3, 0, 0] = a[2]
	a_hps[3, 0, 1] = a[3]
	a_tto[4, 0, 0] = a[0]
	a_tto[4, 0, 1] = a[3]
	a_hld[4, 0, 0] = a[1]
	a_hld[4, 0, 1] = a[3]
	a_hps[4, 0, 0] = a[2]
	a_hps[4, 0, 1] = a[3]
	# Absolute Truth
	a = simulation(runs, activity, ratio, mana_pool, healing, 0, 0, mp5, crit, haste, 0, 0, 34)
	a_tto[0, 1, 0] = a[0]
	a_tto[0, 1, 1] = a[3]
	a_hld[0, 1, 0] = a[1]
	a_hld[0, 1, 1] = a[3]
	a_hps[0, 1, 0] = a[2]
	a_hps[0, 1, 1] = a[3]
	# no libram with BoL
	a = simulation(runs, activity, ratio, mana_pool, healing, 185, 580, mp5, crit, haste, 0, 0, 0)
	a_tto[1, 0, 0] = a[0]
	a_tto[1, 0, 1] = a[3]
	a_hld[1, 0, 0] = a[1]
	a_hld[1, 0, 1] = a[3]
	a_hps[1, 0, 0] = a[2]
	a_hps[1, 0, 1] = a[3]
	# Souls Redeemed with BoL
	a = simulation(runs, activity, ratio, mana_pool, healing, 185, 580, mp5, crit, haste, 60, 120, 0)
	a_tto[1, 1, 0] = a[0]
	a_tto[1, 1, 1] = a[3]
	a_hld[1, 1, 0] = a[1]
	a_hld[1, 1, 1] = a[3]
	a_hps[1, 1, 0] = a[2]
	a_hps[1, 1, 1] = a[3]
	# Nagrand 
	a = simulation(runs, activity, ratio, mana_pool, healing, 79, 0, mp5, crit, haste, 0, 0, 0)
	a_tto[2, 1, 0] = a[0]
	a_tto[2, 1, 1] = a[3]
	a_hld[2, 1, 0] = a[1]
	a_hld[2, 1, 1] = a[3]
	a_hps[2, 1, 0] = a[2]
	a_hps[2, 1, 1] = a[3]
	# Lightbringer
	a = simulation(runs, activity, ratio, mana_pool, healing, 0, 87, mp5, crit, haste, 0, 0, 0)
	a_tto[3, 1, 0] = a[0]
	a_tto[3, 1, 1] = a[3]
	a_hld[3, 1, 0] = a[1]
	a_hld[3, 1, 1] = a[3]
	a_hps[3, 1, 0] = a[2]
	a_hps[3, 1, 1] = a[3]
	# Mending
	a = simulation(runs, activity, ratio, mana_pool, healing, 0, 0, mp5 + 22, crit, haste, 0, 0, 0)
	a_tto[4, 1, 0] = a[0]
	a_tto[4, 1, 1] = a[3]
	a_hld[4, 1, 0] = a[1]
	a_hld[4, 1, 1] = a[3]
	a_hps[4, 1, 0] = a[2]
	a_hps[4, 1, 1] = a[3]


	np.save("tto_libram", a_tto)
	np.save("hld_libram", a_hld)
	np.save("hps_libram", a_hps)

gathering_results_libram()


#a = encounter(True, 0.88, (28, 45, 23, 4), 12723, 2077, 163, 0.2278, 0)
