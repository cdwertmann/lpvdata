# install.packages("RSQLite", dependencies=TRUE)

query <- dbSendQuery(connect, statement = "select monat,energie from monate where jahr=$year");
data <- fetch(query, n = -1)
fname <- paste(PATH, "lzgraph.png", sep = "")

png(filename=fname, height=400, width=800, bg="lightblue")

if (dbGetRowCount(query)>0) {
	max_num <- max(data$energie) + 0.5
	barplot(data$energie, main="Jahr 20$year", xlab="Monat",
	   ylab="Energie in kWh", names.arg=data$monat, 
	   col=heat.colors(3), xlim=c(0,15), ylim=c(0,max_num), las=1)
} else {
	frame()
	title(main="Keine Daten vorhanden")
}

sqliteCloseResult(query)
# Turn off device driver (to flush output to png)
dev.off()
