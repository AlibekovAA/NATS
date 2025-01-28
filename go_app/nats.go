package main

import (
	"fmt"
	"log"

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
    nc, err := nats.Connect(natsConfig.Addr)
    if err != nil {
        return nil, fmt.Errorf("failed to connect to NATS: %w", err)
    }
    log.Printf("Successfully connected to NATS")
    return nc, nil
}

func SubscribeToTopic(nc *nats.Conn, topic string) (*nats.Subscription, error) {
    log.Printf("Subscribing to topic: %s", topic)
    sub, err := nc.Subscribe(topic, func(m *nats.Msg) {
        log.Printf("Received message on topic %s: %s", topic, string(m.Data))
    })
    if err != nil {
        return nil, fmt.Errorf("failed to subscribe to topic %s: %w", topic, err)
    }
    log.Printf("Successfully subscribed to topic: %s", topic)
    return sub, nil
}

func PublishToTopic(nc *nats.Conn, topic string, data []byte) error {
	if err := nc.Publish(topic, data); err != nil {
		return err
	}
	return nil
}
