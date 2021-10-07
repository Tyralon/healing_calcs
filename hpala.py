t = 0.0
mana_pool = 10000
fol_mana = 180
fol_cast = 1.5

while mana_pool >= fol_mana:
	mana_pool -= fol_mana
	t += fol_cast

print(t)
