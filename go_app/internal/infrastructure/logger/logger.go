package logger

import (
	"log"
	"os"
	"path/filepath"
	"time"
)

type Logger struct {
	*log.Logger
}

func New(dir, file string) (*Logger, error) {
	if err := os.MkdirAll(dir, os.ModePerm); err != nil {
		return nil, err
	}

	logFile, err := os.OpenFile(
		filepath.Join(dir, file),
		os.O_APPEND|os.O_CREATE|os.O_WRONLY,
		0666,
	)
	if err != nil {
		return nil, err
	}

	time.Local = getMoscowLocation()
	return &Logger{
		Logger: log.New(logFile, "", log.Ldate|log.Ltime|log.Lshortfile),
	}, nil
}

func getMoscowLocation() *time.Location {
	loc, err := time.LoadLocation("Europe/Moscow")
	if err != nil {
		return time.FixedZone("MSK", 3*60*60)
	}
	return loc
}
