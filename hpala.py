import random
import statistics

mana_pool = 10000
crit = 0.2225
mp5 = 88
healing = 1900

def heal(lower, upper, cast, healing, critted):
	if critted:
		return random.randint(lower, upper) * 1.5 + (healing * cast / 3.5)
	else:
		return random.randint(lower, upper) + (healing * cast / 3.5)

def flash_of_light(healing, critted):
	return heal(458, 513, 1.5, healing, critted)

def holy_light(healing, critted):
	return heal(2196, 2446, 2.5, healing, critted)

def mana_source(lower, upper, modifier):
	return random.randint(lower,upper) * modifier

# mana from dark rune or demonic rune
def mana_rune():
	return mana_source(900, 1500, 1)

# mana from super mana pot with alchemist's stone
def mana_pot_alch():
	return mana_source(1800, 3000, 1.4)

# whether we get a crit on our spell
def spell_crit(crit_percentage):
	return random.random() < crit_percentage

def encounter(activity, ratio, mana_pool, mp5, base_crit):
	t = 0.0
	healed = 0

	fol_mana = 180
	fol_cast = 1.5
	hl_mana = 840
	hl_cast = 2.5

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

	# limit encounters to 600s (10min)
	while mana_pool >= fol_mana and t < 600:
		while last_tick < t:
			last_tick += mana_tick
			mana_pool += mp2

		if t > pot_delay and (pot_last_use + pot_cd) <= t:
			mana_pool += mana_pot_alch()
			pot_last_use = t
		if t > rune_delay and (rune_last_use + rune_cd) <= t:
			mana_pool += mana_rune()
			rune_last_use = t


		if random.random() < ratio:
			crit = base_crit
			spell_mana = fol_mana
			spell_cast = fol_cast
		else:
			crit = base_crit + 0.06
			spell_mana = hl_mana
			if (grace_last_use + grace_duration) >= t:
				spell_cast = hl_cast - grace_effect
			else:
				spell_cast = hl_cast
			grace = 1
			

		if t > favor_delay and (favor_last_use + favor_cd) <= t:
			favor = 1
			crit = 1.0

		if t > div_illu_delay and (div_illu_last_use + div_illu_cd) <= t:
			div_illu_last_use = t

		t += spell_cast
		if (div_illu_last_use + div_illu_duration) >= t:
			mana_pool -= spell_mana / 2
		else:
			mana_pool -= spell_mana

		if spell_crit(crit):
			mana_pool += spell_mana * illu
			if spell_mana == 180:
				healed += flash_of_light(healing, True)
			if spell_mana == 840:
				healed += holy_light(healing, True)
		else:
			if spell_mana == 180:
				healed += flash_of_light(healing, False)
			if spell_mana == 840:
				healed += holy_light(healing, False)

				


		if favor == 1:
			favor = 0
			favor_last_use = t

		if grace == 1:
			grace = 0
			grace_last_use = t

		# adds delay based on y = -(x-1) / x
		t += -(activity - 1) / activity * spell_cast

	return (t, healed)

def simulation():
	tto = []
	healList = []
	for i in range(1000):
		sim = encounter(0.8, 0.93, mana_pool, mp5, crit)
		tto.append(sim[0])
		healList.append(sim[1])

	tto_min = min(tto)
	tto_max = max(tto)
	tto_median = statistics.median(tto)
	heal_min = min(healList)
	heal_max = max(healList)
	heal_median = statistics.median(healList)
	hps_min = heal_min / tto_min
	hps_max = heal_max / tto_max
	hps_median = heal_median / tto_median
	
	print('TTO median: ' + str(round(tto_median)))
	print('HPS median: ' + str(round(hps_median)))
	print('healing median: ' + str(round(heal_median)) + '\n')


