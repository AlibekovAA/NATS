package main

import (
	"os"
	"os/signal"
	"syscall"

	"go_app/internal/analyzer"
	"go_app/internal/config"
	"go_app/internal/infrastructure/logger"
	natsclient "go_app/internal/infrastructure/nats"
	"go_app/pkg/pcap"
)

func main() {
	cfg := config.New()
	log, err := logger.New(cfg.LogDir, cfg.LogFile)
	if err != nil {
		panic(err)
	}

	natsClient, err := natsclient.New(cfg.NatsAddr, log)
	if err != nil {
		log.Printf("Failed to connect to NATS: %v", err)
		return
	}

	pcapAnalyzer := pcap.New(log)
	service := analyzer.NewService(log, pcapAnalyzer)

	if err := setupSubscriptions(natsClient, service); err != nil {
		log.Printf("Failed to setup subscriptions: %v", err)
		return
	}

	log.Println("Server started successfully")
	waitForShutdown(natsClient, log)
}

func setupSubscriptions(client *natsclient.Client, service *analyzer.Service) error {
	topics := map[string]func([]byte) ([]byte, error){
		"network.analysis.start": func(msg []byte) ([]byte, error) {
			return nil, service.HandleStart(msg)
		},
		"network.analysis.chunk":  service.HandleChunk,
		"network.analysis.finish": service.HandleFinish,
	}

	for topic, handler := range topics {
		if err := client.Subscribe(topic, handler); err != nil {
			return err
		}
	}
	return nil
}

func waitForShutdown(client *natsclient.Client, log *logger.Logger) {
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
	<-sigChan

	log.Println("Shutting down...")
	if err := client.Close(); err != nil {
		log.Printf("Error during shutdown: %v", err)
	}
}
