package config

import "os"

type Config struct {
    NatsAddr string
    LogDir   string
    LogFile  string
}

func New() *Config {
    return &Config{
        NatsAddr: getEnv("NATS_ADDR", "nats://nats:4222"),
        LogDir:   getEnv("LOG_DIR", "logs"),
        LogFile:  getEnv("LOG_FILE", "app.log"),
    }
}

func getEnv(key, defaultValue string) string {
    if value := os.Getenv(key); value != "" {
        return value
    }
    return defaultValue
}
