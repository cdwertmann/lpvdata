# install.packages("RSQLite", dependencies=TRUE)

query <- dbSendQuery(connect, statement = "select tag,energie from tage where monat=$month and jahr=$year");
data <- fetch(query, n = -1)
fname <- paste(PATH, "lzgraph.png", sep = "")

png(filename=fname, height=400, width=1000, bg="lightblue")

if (dbGetRowCount(query)>0) {
	max_num <- max(data$energie) + 0.5
	barplot(data$energie, main="Monat $month/20$year", xlab="Tag",
	   ylab="Energie in kWh", names.arg=data$tag, 
	   col=heat.colors(3), xlim=c(1,35), ylim=c(0,max_num), las=1)
} else {
	frame()
	title(main="Keine Daten vorhanden")
}

sqliteCloseResult(query)
# Turn off device driver (to flush output to png)
dev.off()
