package main

import (
	"log"
	"os"
	"path/filepath"

	"github.com/nats-io/nats.go"

)

func main() {
	logDir := "logs"
	err := os.MkdirAll(logDir, os.ModePerm)
	if err != nil {
		log.Fatal("Error creating log directory:", err)
	}

	logFilepath := filepath.Join(logDir, "app.log")
	logFile, err := os.OpenFile(logFilepath, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0666)
	if err != nil {
		log.Fatal("Error opening log file:", err)
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

	_, err = nc.Subscribe("Data", func(m *nats.Msg) {
		log.Printf("Received message: %s", string(m.Data))
	})
	if err != nil {
		log.Fatal("Error subscribing to topic: ", err)
	}

	log.Println("Go server ready and listening for messages")

	select {}
}
