package main

import (
	"log"
	"os"
	"path/filepath"
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

func CreateLogDir(logConfig *LogConfig) error {
	if _, err := os.Stat(logConfig.Dir); os.IsNotExist(err) {
		if err := os.MkdirAll(logConfig.Dir, os.ModePerm); err != nil {
			return err
		}
	}
	return nil
}

func CreateLogFile(logConfig *LogConfig) (*os.File, error) {
	logFilepath := filepath.Join(logConfig.Dir, logConfig.File)
	if _, err := os.Stat(logFilepath); os.IsNotExist(err) {
		return os.OpenFile(logFilepath, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0666)
	}
	return os.OpenFile(logFilepath, os.O_APPEND|os.O_WRONLY, 0666)
}

func SetLogger(logConfig *LogConfig) (*log.Logger, error) {
	logFile, err := CreateLogFile(logConfig)
	if err != nil {
		return nil, err
	}
	return log.New(logFile, "", log.Ldate|log.Ltime|log.Lshortfile), nil
}
