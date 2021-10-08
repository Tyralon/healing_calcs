import random

t = 0.0
mana_pool = 10000
fol_mana = 180
fol_cast = 1.5

mp5 = 100
mana_tick = 2
mp2 = mp5 / 5 * 2
last_tick = t

crit = 16.12
div_illu = 0.6
crit_value = crit * 100
rng = 0

pot_min = 1800
pot_max = 3000
pot_cd = 120
pot_delay = 60
pot_factor = 1.4
pot_last_use = pot_delay - pot_cd

rune_min = 900
rune_max = 1500
rune_cd = 120
rune_delay = 60
rune_last_use = rune_delay - rune_cd

while mana_pool >= fol_mana:
	while last_tick < t:
		last_tick += mana_tick
		mana_pool += mp2
	if t > pot_delay and (pot_last_use + pot_cd) <= t:
		rng = random.randint(pot_min,pot_max)
		mana_pool += rng * pot_factor
		pot_last_use = t
	if t > rune_delay and (rune_last_use + rune_cd) <= t:
		rng = random.randint(rune_min,rune_max)
		mana_pool += rng
		rune_last_use = t
	mana_pool -= fol_mana
	rng = random.randint(1,10000)
	if rng < crit_value:
		mana_pool += fol_mana * div_illu
	t += fol_cast

print('Time to OOM: ' + str(t))
