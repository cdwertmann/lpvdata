#!/usr/bin/python
import sqlite3, time
istdb = sqlite3.connect('istwerte.sq3')

istc=istdb.cursor()

istc.execute('''create table istwerte
(epoch numeric, upv_ist numeric, upv_soll numeric, uac_netz numeric, iac_netz numeric,
pac_netz numeric, fac_netz numeric, r_iso numeric, t_kk numeric)''')

# Save (commit) the changes
istdb.commit()

# We can also close the cursor if we are done with it
istc.close()

lzdb = sqlite3.connect('lzwerte.sq3')

lzc=lzdb.cursor()

lzc.execute('''create table tage
(tag numeric, monat numeric, jahr numeric, startzyklen numeric, betriebszeit numeric,
energie numeric, p_min numeric, p_min_zeitpunk text, p_max numeric, p_max_zeitpunk text)''')

lzc.execute('''create table wochen
(woche numeric, jahr numeric, startzyklen numeric, betriebszeit numeric,
energie numeric, p_min numeric, p_min_zeitpunk text, p_max numeric, p_max_zeitpunk text)''')

lzc.execute('''create table monate
(monat numeric, jahr numeric, startzyklen numeric, betriebszeit numeric,
energie numeric, p_min numeric, p_min_zeitpunk text, p_max numeric, p_max_zeitpunk text)''')

# Save (commit) the changes
lzdb.commit()

# We can also close the cursor if we are done with it
lzc.close()