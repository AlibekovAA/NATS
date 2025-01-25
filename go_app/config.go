package main

type Config struct {
	NATSAddr string
}

func NewConfig() *Config {
	return &Config{
		NATSAddr: "nats://nats:4222",
	}
}
