import random

t = 0.0
mana_pool = 10000
fol_mana = 180
fol_cast = 1.5

mp5 = 88
mana_tick = 2
mp2 = mp5 / 5 * 2
last_tick = t

crit = 22.25
div_illu = 0.6

pot_min = 1800
pot_max = 3000
pot_cd = 120
pot_delay = 60
pot_modifier = 1.4
pot_last_use = pot_delay - pot_cd

rune_min = 900
rune_max = 1500
rune_cd = 120
rune_delay = 60
rune_last_use = rune_delay - rune_cd

def mana_source(lower, upper, modifier):
	return random.randint(lower,upper) * modifier

def spell_crit(crit_percentage):
	return random.randint(1,10000) < (crit_percentage * 100)

while mana_pool >= fol_mana:
	while last_tick < t:
		last_tick += mana_tick
		mana_pool += mp2

	if t > pot_delay and (pot_last_use + pot_cd) <= t:
		mana_pool += mana_source(pot_min, pot_max, pot_modifier)
		pot_last_use = t
	if t > rune_delay and (rune_last_use + rune_cd) <= t:
		mana_pool += mana_source(rune_min, rune_max, 1)
		rune_last_use = t

	mana_pool -= fol_mana
	
	if spell_crit(crit):
		mana_pool += fol_mana * div_illu

	t += fol_cast

print('Time to OOM: ' + str(t))
