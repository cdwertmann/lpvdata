Data logger and graphing tool for SMA PV-WR 1500/1800 solar energy inverters
============================================================================

Fetches statistics and system status from inverters with installed serial port/data logger module.

pvdata-serial.py: read directly from serial port
pvdata-tcp.py: read from a TCP socket (when using serial<->TCP converter box)
pvdata-twisted.py: read from a TCP socket (when using serial<->TCP converter box), serving web pages via python-twisted


pvdata-serial.py: 

Dependencies for the graphs: R, rrdtool, sqlite3 headers

To install R database support:
sudo R
install.packages(c("DBI"))
install.packages(c("RSQLite"))

To initialize sqlite DB:
python dbinit.py
