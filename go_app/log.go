package main

import (
	"log"
	"os"
	"path/filepath"
	"time"
)

var Logger *log.Logger

type LogConfig struct {
	Dir  string
	File string
}

func NewLogConfig() *LogConfig {
	dir := os.Getenv("LOG_DIR")
	if dir == "" {
		dir = "logs"
	}

	file := os.Getenv("LOG_FILE")
	if file == "" {
		file = "app.log"
	}

	return &LogConfig{
		Dir:  dir,
		File: file,
	}
}

func SetLogger(logConfig *LogConfig) error {
	if err := os.MkdirAll(logConfig.Dir, os.ModePerm); err != nil {
		return err
	}

	logFilepath := filepath.Join(logConfig.Dir, logConfig.File)
	logFile, err := os.OpenFile(logFilepath, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0666)
	if err != nil {
		return err
	}

	moscow, err := time.LoadLocation("Europe/Moscow")
	if err != nil {
		moscow = time.FixedZone("MSK", 3*60*60)
	}
	time.Local = moscow

	Logger = log.New(logFile, "", log.Ldate|log.Ltime|log.Lshortfile)
	return nil
}
