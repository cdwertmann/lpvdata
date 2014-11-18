#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $DIR
rrdtool graph "istwerte_day.png" -s "-1 day" --width '600' --height '150' \
	-t "heute und gestern" \
	-v "Leistung in Watt" \
	--units-exponent 0 --alt-y-grid \
	'DEF:todayKW=istwerte.rrd:P:AVERAGE' \
	'DEF:ydayKW=istwerte.rrd:P:AVERAGE:start=-2 days:end=-1 days' \
	'CDEF:today=todayKW,1000,*' 'CDEF:yday=ydayKW,1000,*' \
	'SHIFT:yday:86400' \
	'AREA:today#FF0000:heute' 'LINE1:yday#0000FF:gestern'

rrdtool graph "istwerte_week.png" -s "-1 week" --width '600' --height '150' \
	-t "diese und letzte Woche" \
	-v "Leistung in Watt" \
	--units-exponent 0 --alt-y-grid \
	'DEF:thisweekKW=istwerte.rrd:P:AVERAGE:start=-1 week' \
	'DEF:lastweekKW=istwerte.rrd:P:AVERAGE:start=-2 weeks:end=-1 week' \
	'CDEF:lastweek=lastweekKW,1000,*' 'CDEF:thisweek=thisweekKW,1000,*' \
	'SHIFT:lastweek:604800' \
	'AREA:thisweek#FF0000:diese Woche' 'LINE1:lastweek#0000FF:letzte Woche'

rrdtool graph "istwerte_month.png" -s "-1 month" --width '600' --height '150' \
	-t "dieser und letzter Monat" \
	-v "Leistung in Watt" \
	--units-exponent 0 --alt-y-grid \
	'DEF:thismonthKW=istwerte.rrd:P:AVERAGE:start=-4 weeks' \
	'DEF:lastmonthKW=istwerte.rrd:P:AVERAGE:start=-8 weeks:end=-4 weeks' \
	'CDEF:lastmonth=lastmonthKW,1000,*' 'CDEF:thismonth=thismonthKW,1000,*' \
	'SHIFT:lastmonth:2419200' \
	'AREA:thismonth#FF0000:dieser Monat' 'LINE1:lastmonth#0000FF:letzter Monat'

# example: http://www.semicomplete.com/blog/geekery/rrdtool-for-the-win.html
# rrdtool create istwerte.rrd --step '60' --start '-8 weeks' 'DS:P:GAUGE:120:U:2' 'RRA:AVERAGE:0.5:1:80640'

