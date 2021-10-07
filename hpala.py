t = 0.0
mana_pool = 10000
fol_mana = 180
fol_cast = 1.5
mp5 = 100
mana_tick = 2
mp2 = mp5 / 5 * 2
last_tick = t

while mana_pool >= fol_mana:
	while last_tick < t:
		last_tick += mana_tick
		mana_pool += mp2
	mana_pool -= fol_mana
	t += fol_cast

print('Time to OOM: ' + str(t))
