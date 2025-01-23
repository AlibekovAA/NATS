package main

import (
	"log"
	"os"

	"github.com/nats-io/nats.go"
)

func main() {
	logFile, err := os.OpenFile("logs/app.log", os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0666)
	if err != nil {
		log.Fatal(err)
	}
	defer logFile.Close()

	log.SetOutput(logFile)
	log.Println("Go server starting...")

	nc, err := nats.Connect("nats://nats:4222")
	if err != nil {
		log.Fatal("Error connecting to NATS: ", err)
	}
	defer nc.Close()

	log.Println("Connected to NATS")

	_, err = nc.Subscribe("greet", func(m *nats.Msg) {
		log.Printf("Received message: %s", string(m.Data))
	})
	if err != nil {
		log.Fatal("Error subscribing to topic: ", err)
	}

	log.Println("Go server ready and listening for messages")

	select {}
}
