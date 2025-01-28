package main

import (
	"log"
	"os"
	"path/filepath"
	"time"
)

type LogConfig struct {
	Dir  string
	File string
}

func NewLogConfig() *LogConfig {
	return &LogConfig{
		Dir:  "logs",
		File: "app.log",
	}
}

func SetLogger(logConfig *LogConfig) (*log.Logger, error) {
	if err := os.MkdirAll(logConfig.Dir, os.ModePerm); err != nil {
		return nil, err
	}

	logFilepath := filepath.Join(logConfig.Dir, logConfig.File)
	logFile, err := os.OpenFile(logFilepath, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0666)
	if err != nil {
		return nil, err
	}

	moscow, err := time.LoadLocation("Europe/Moscow")
	if err != nil {
		moscow = time.FixedZone("MSK", 3*60*60)
	}
	time.Local = moscow

	return log.New(logFile, "", log.Ldate|log.Ltime|log.Lshortfile), nil
}
