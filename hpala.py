import random
import statistics

mana_pool = 10000
crit = 22.25
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
	return random.randint(1,10000) < (crit_percentage * 100)

def simulation(mana_pool, mp5, crit):
	t = 0.0
	fol_mana = 180
	fol_cast = 1.5

	mana_tick = 2
	mp2 = mp5 / 5 * 2
	last_tick = t

	pot_cd = 120
	pot_delay = 60
	pot_last_use = pot_delay - pot_cd

	rune_cd = 120
	rune_delay = 60
	rune_last_use = rune_delay - rune_cd

	div_illu = 0.6

	while mana_pool >= fol_mana:
		while last_tick < t:
			last_tick += mana_tick
			mana_pool += mp2

		if t > pot_delay and (pot_last_use + pot_cd) <= t:
			mana_pool += mana_pot_alch()
			pot_last_use = t
		if t > rune_delay and (rune_last_use + rune_cd) <= t:
			mana_pool += mana_rune()
			rune_last_use = t

		mana_pool -= fol_mana
	
		if spell_crit(crit):
			mana_pool += fol_mana * div_illu

		t += fol_cast
	return t


sims = []
for i in range(50):
	sims.append(simulation(mana_pool, mp5, crit))

print('TTO min: ' + str(min(sims)))
print('TTO max: ' + str(max(sims)))
print('TTO mode: ' + str(statistics.median(sims)))
