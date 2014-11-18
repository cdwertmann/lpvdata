Dependencies: R, rrdtool, sqlite3 headers

To install R database support:
sudo R
install.packages(c("DBI"))
install.packages(c("RSQLite"))

To initialize sqlite DB:
run dbinit.py
