package analyzer

import (
	"encoding/json"

	"go_app/internal/domain"
)

func (s *Service) HandleStart(msg []byte) error {
	var start struct {
		AnalysisID  string `json:"analysis_id"`
		TotalChunks int    `json:"total_chunks"`
	}
	if err := json.Unmarshal(msg, &start); err != nil {
		return err
	}

	s.data[start.AnalysisID] = make([]byte, 0)
	s.log.Printf("Starting analysis ID: %s, expecting %d chunks", start.AnalysisID, start.TotalChunks)
	return nil
}

func (s *Service) HandleChunk(msg []byte) ([]byte, error) {
	var chunk domain.ChunkMessage
	if err := json.Unmarshal(msg, &chunk); err != nil {
		return nil, err
	}

	decodedData, err := s.decodeData(chunk.Data, chunk.Encoding)
	if err != nil {
		return nil, err
	}

	if chunk.ChunkNumber == 0 {
		s.data[chunk.AnalysisID] = decodedData
	} else {
		s.data[chunk.AnalysisID] = append(s.data[chunk.AnalysisID], decodedData...)
	}

	s.log.Printf("Processed chunk %d/%d for analysis ID: %s",
		chunk.ChunkNumber+1, chunk.TotalChunks, chunk.AnalysisID)

	return []byte(`{"status":"ok"}`), nil
}

func (s *Service) HandleFinish(msg []byte) ([]byte, error) {
	var finish struct {
		AnalysisID string `json:"analysis_id"`
	}
	if err := json.Unmarshal(msg, &finish); err != nil {
		return nil, err
	}

	data := s.data[finish.AnalysisID]
	result, err := s.analyzer.Analyze(data)
	if err != nil {
		return nil, err
	}

	delete(s.data, finish.AnalysisID)
	s.log.Printf("Analysis completed for ID: %s, processed %d packets",
		finish.AnalysisID, len(result.Packets))

	return json.Marshal(result)
}
