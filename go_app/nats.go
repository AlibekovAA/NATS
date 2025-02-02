package main

import (
	"encoding/hex"
	"encoding/json"
	"fmt"
	"time"

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
	Logger.Printf("Connecting to NATS at %s", natsConfig.Addr)

	opts := []nats.Option{
		nats.MaxReconnects(5),
		nats.ReconnectWait(2 * time.Second),
	}

	nc, err := nats.Connect(natsConfig.Addr, opts...)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to NATS: %w", err)
	}
	Logger.Printf("Successfully connected to NATS")
	return nc, nil
}

func SubscribeToAnalysis(nc *nats.Conn) error {
	partialData := make(map[string][]byte)

	_, err := nc.Subscribe("network.analysis.start", func(m *nats.Msg) {
		var start struct {
			AnalysisID   string `json:"analysis_id"`
			TotalChunks  int    `json:"total_chunks"`
		}
		if err := json.Unmarshal(m.Data, &start); err != nil {
			Logger.Printf("Error parsing start message: %v", err)
			return
		}
		partialData[start.AnalysisID] = make([]byte, 0)
	})
	if err != nil {
		return fmt.Errorf("failed to subscribe to start: %w", err)
	}

	_, err = nc.Subscribe("network.analysis.chunk", func(m *nats.Msg) {
		var chunk struct {
			AnalysisID   string `json:"analysis_id"`
			ChunkNumber  int    `json:"chunk_number"`
			TotalChunks  int    `json:"total_chunks"`
			Data         string `json:"data"`
		}
		if err := json.Unmarshal(m.Data, &chunk); err != nil {
			m.Respond([]byte(`{"error": "invalid json format"}`))
			return
		}

		if int64(len(chunk.Data)) > nc.MaxPayload() {
			m.Respond([]byte(`{"error": "chunk size exceeds maximum payload size"}`))
			return
		}

		data, err := hex.DecodeString(chunk.Data)
		if err != nil {
			m.Respond([]byte(`{"error": "invalid hex data"}`))
			return
		}

		partialData[chunk.AnalysisID] = append(partialData[chunk.AnalysisID], data...)
		m.Respond([]byte(`{"status": "ok"}`))
	})
	if err != nil {
		return fmt.Errorf("failed to subscribe to chunks: %w", err)
	}

	_, err = nc.Subscribe("network.analysis.finish", func(m *nats.Msg) {
		var finish struct {
			AnalysisID string `json:"analysis_id"`
		}
		if err := json.Unmarshal(m.Data, &finish); err != nil {
			errorResponse := map[string]string{"error": "invalid finish message"}
			response, _ := json.Marshal(errorResponse)
			m.Respond(response)
			return
		}

		data := partialData[finish.AnalysisID]
		result, err := analyzePcapData(data)
		if err != nil {
			errorResponse := map[string]string{"error": err.Error()}
			response, _ := json.Marshal(errorResponse)
			m.Respond(response)
			return
		}

		response, _ := json.Marshal(result)
		m.Respond(response)

		delete(partialData, finish.AnalysisID)
	})

	return err
}
