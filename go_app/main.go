package main

import (
	"log"
)

func main() {
	logConfig := NewLogConfig()
	if err := CreateLogDir(logConfig); err != nil {
		log.Fatal(err)
	}
	logFile, err := CreateLogFile(logConfig)
	if err != nil {
		log.Fatal(err)
	}
	log.SetOutput(logFile)

	natsConfig := NewNATSConfig()
	nc, err := ConnectToNATS(natsConfig)
	if err != nil {
		log.Fatal(err)
	}
	defer nc.Close()

	sub, err := SubscribeToTopic(nc, "Data")
	if err != nil {
		log.Fatal(err)
	}
	defer sub.Unsubscribe()

	log.Println("Go server starting...")
}
