package main

import (
	"context"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/nats-io/nats.go"
)

func handleSignals(cancel context.CancelFunc) {
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
	go func() {
		sig := <-sigChan
		Logger.Printf("Received signal %v, initiating graceful shutdown", sig)
		cancel()
	}()
}

func gracefulShutdown(nc *nats.Conn) {
	_, shutdownCancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer shutdownCancel()
	if err := nc.Drain(); err != nil {
		Logger.Printf("Error during NATS drain: %v", err)
	}
	Logger.Println("Server successfully stopped")
}

func main() {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	logConfig := NewLogConfig()
	if err := SetLogger(logConfig); err != nil {
		return
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

	handleSignals(cancel)

	<-ctx.Done()

	gracefulShutdown(nc)
}
