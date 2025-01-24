package main

import (
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
	nc, err := nats.Connect(natsConfig.Addr)
	if err != nil {
		return nil, err
	}
	return nc, nil
}

func SubscribeToTopic(nc *nats.Conn, topic string) (*nats.Subscription, error) {
	sub, err := nc.Subscribe(topic, func(m *nats.Msg) {
		log.Printf("Received message: %s", string(m.Data))
	})
	if err != nil {
		return nil, err
	}
	return sub, nil
}

func PublishToTopic(nc *nats.Conn, topic string, data []byte) error {
	if err := nc.Publish(topic, data); err != nil {
		return err
	}
	return nil
}
