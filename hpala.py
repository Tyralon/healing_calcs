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

while mana_pool >= fol_mana:
	while last_tick < t:
		last_tick += mana_tick
		mana_pool += mp2
	mana_pool -= fol_mana
	rng = random.randint(1,10000)
	if rng < crit_value:
		mana_pool += fol_mana * div_illu
	t += fol_cast

print('Time to OOM: ' + str(t))
