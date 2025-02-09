package analyzer

import (
	"encoding/base64"
	"encoding/hex"

	"go_app/internal/domain"
	"go_app/internal/infrastructure/logger"
)

type Service struct {
	log      *logger.Logger
	analyzer domain.PcapAnalyzer
	data     map[string][]byte
}

func NewService(log *logger.Logger, analyzer domain.PcapAnalyzer) *Service {
	return &Service{
		log:      log,
		analyzer: analyzer,
		data:     make(map[string][]byte),
	}
}

func (s *Service) decodeData(data, encoding string) ([]byte, error) {
	switch encoding {
	case "hex":
		return hex.DecodeString(data)
	case "base64":
		return base64.StdEncoding.DecodeString(data)
	default:
		return nil, domain.ErrUnsupportedEncoding
	}
}
