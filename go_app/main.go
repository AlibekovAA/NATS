package main

import (
	"context"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"
)

func main() {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	logConfig := NewLogConfig()
	if err := SetLogger(logConfig); err != nil {
		log.Fatalf("Failed to setup logger: %v", err)
	}

	config := NewConfig()

	nc, err := ConnectToNATS(&NATSConfig{Addr: config.NATSAddr})
	if err != nil {
		Logger.Printf("Failed to connect to NATS: %v", err)
		return
	}
	defer nc.Close()

	err = SubscribeToAnalysis(nc)
	if err != nil {
		Logger.Printf("Failed to subscribe to analysis tasks: %v", err)
		return
	}

	Logger.Println("Go server starting...")

	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		sig := <-sigChan
		Logger.Printf("Received signal %v, initiating graceful shutdown", sig)
		cancel()
	}()

	<-ctx.Done()

	_, shutdownCancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer shutdownCancel()

	if err := nc.Drain(); err != nil {
		Logger.Printf("Error during NATS drain: %v", err)
	}

	Logger.Println("Server successfully stopped")
}
