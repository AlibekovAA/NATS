package main

import (
	"log"

)

func main() {
	logConfig := NewLogConfig()
	logger, err := SetLogger(logConfig)
	if err != nil {
		log.Fatal(err)
	}
	log.SetOutput(logger.Writer())

	config := NewConfig()
	nc, err := ConnectToNATS(&NATSConfig{Addr: config.NATSAddr})
	if err != nil {
		log.Fatal(err)
	}
	defer nc.Close()

	sub, err := SubscribeToTopic(nc, "Data")
	if err != nil {
		log.Fatal(err)
	}
	defer sub.Unsubscribe()

	logger.Println("Go server starting...")
	select {}
}
