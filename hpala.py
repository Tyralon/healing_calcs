import random
import statistics

mana_pool = 10000
crit = 0.2225
mp5 = 88

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

def simulation(activity, ratio, mana_pool, mp5, base_crit):
	t = 0.0

	fol_mana = 180
	fol_cast = 1.5
	hl_mana = 840
	hl_cast = 2.5

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
			spell_cast = hl_cast

		if t > favor_delay and (favor_last_use + favor_cd) <= t:
			favor = 1
			crit = 1.0

		mana_pool -= spell_mana
	
		if spell_crit(crit):
			mana_pool += spell_mana * illu

		t += spell_cast
		if favor == 1:
			favor = 0
			favor_last_use = t
		# adds delay based on y = -(x-1) / x
		t += -(activity - 1) / activity * spell_cast

	return t


sims = []
for i in range(50):
	sims.append(simulation(0.8, 0.93, mana_pool, mp5, crit))

print('TTO min: ' + str(round(min(sims))))
print('TTO max: ' + str(round(max(sims))))
print('TTO mode: ' + str(round(statistics.median(sims))))
