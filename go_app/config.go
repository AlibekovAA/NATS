package main

import "os"

type Config struct {
	NATSAddr string
}

func NewConfig() *Config {
	natsAddr := os.Getenv("NATS_ADDR")
	if natsAddr == "" {
		natsAddr = "nats://nats:4222"
	}
	return &Config{
		NATSAddr: natsAddr,
	}
}
