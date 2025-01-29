package main

import (
	"encoding/json"
	"fmt"
	"log"
	"time"

	"github.com/nats-io/nats.go"
)

type NATSConfig struct {
	Addr string
}

func NewNATSConfig() *NATSConfig {
	return &NATSConfig{
		Addr: "nats://nats:4222",
	}
}

func ConnectToNATS(natsConfig *NATSConfig) (*nats.Conn, error) {
	log.Printf("Connecting to NATS at %s", natsConfig.Addr)

	opts := []nats.Option{
		nats.MaxReconnects(5),
		nats.ReconnectWait(2 * time.Second),
	}

	nc, err := nats.Connect(natsConfig.Addr, opts...)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to NATS: %w", err)
	}
	log.Printf("Successfully connected to NATS")
	return nc, nil
}

func SubscribeToAnalysis(nc *nats.Conn) (*nats.Subscription, error) {
	log.Printf("Subscribing to network analysis tasks")

	sub, err := nc.Subscribe("network.analysis.task", func(m *nats.Msg) {
		log.Printf("Received PCAP data for analysis, size: %d bytes", len(m.Data))

		result, err := analyzePcapData(m.Data)
		if err != nil {
			log.Printf("Error analyzing PCAP data: %v", err)
			response := []byte(fmt.Sprintf(`{"error": "%v"}`, err))
			m.Respond(response)
			return
		}

		response, err := json.Marshal(result)
		if err != nil {
			log.Printf("Error marshaling result: %v", err)
			m.Respond([]byte(`{"error": "internal server error"}`))
			return
		}

		if err := m.Respond(response); err != nil {
			log.Printf("Error sending response: %v", err)
		}

		log.Printf("Successfully analyzed PCAP data with %d packets", len(result.Packets))
	})

	if err != nil {
		return nil, fmt.Errorf("failed to subscribe to analysis tasks: %w", err)
	}

	log.Printf("Successfully subscribed to network analysis tasks")
	return sub, nil
}
