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
		Logger.Printf("[Analysis %s] Starting new analysis, expecting %d chunks", start.AnalysisID, start.TotalChunks)
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
			Logger.Printf("[Analysis Error] Failed to parse chunk data: %v", err)
			m.Respond([]byte(`{"error": "invalid json format"}`))
			return
		}

		Logger.Printf("[Analysis %s] Received chunk %d/%d (size: %d bytes)",
			chunk.AnalysisID, chunk.ChunkNumber+1, chunk.TotalChunks, len(chunk.Data))

		if int64(len(chunk.Data)) > nc.MaxPayload() {
			Logger.Printf("[Analysis %s] Chunk %d exceeds maximum payload size", chunk.AnalysisID, chunk.ChunkNumber)
			m.Respond([]byte(`{"error": "chunk size exceeds maximum payload size"}`))
			return
		}

		data, err := hex.DecodeString(chunk.Data)
		if err != nil {
			Logger.Printf("[Analysis %s] Invalid hex data in chunk %d: %v", chunk.AnalysisID, chunk.ChunkNumber, err)
			m.Respond([]byte(`{"error": "invalid hex data"}`))
			return
		}

		currentSize := len(partialData[chunk.AnalysisID])
		partialData[chunk.AnalysisID] = append(partialData[chunk.AnalysisID], data...)
		newSize := len(partialData[chunk.AnalysisID])
		Logger.Printf("[Analysis %s] Added chunk %d/%d. Total data size: %d bytes (+%d bytes)",
			chunk.AnalysisID, chunk.ChunkNumber+1, chunk.TotalChunks, newSize, newSize-currentSize)

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
			Logger.Printf("[Analysis Error] Invalid finish message: %v", err)
			errorResponse := map[string]string{"error": "invalid finish message"}
			response, _ := json.Marshal(errorResponse)
			m.Respond(response)
			return
		}

		Logger.Printf("[Analysis %s] Received finish signal. Starting final analysis", finish.AnalysisID)
		data := partialData[finish.AnalysisID]
		Logger.Printf("[Analysis %s] Total data size for analysis: %d bytes", finish.AnalysisID, len(data))

		result, err := analyzePcapData(data)
		if err != nil {
			Logger.Printf("[Analysis %s] Analysis failed: %v", finish.AnalysisID, err)
			errorResponse := map[string]string{"error": err.Error()}
			response, _ := json.Marshal(errorResponse)
			m.Respond(response)
			return
		}

		Logger.Printf("[Analysis %s] Analysis completed successfully:", finish.AnalysisID)
		Logger.Printf("  - Total packets analyzed: %d", result.Summary["total_packets"])
		Logger.Printf("  - Total data size: %d bytes", result.Summary["total_size"])
		Logger.Printf("  - Unique sources: %d", result.Summary["unique_sources"])
		Logger.Printf("  - Unique destinations: %d", result.Summary["unique_destinations"])
		Logger.Printf("  - Protocol distribution: %v", result.Summary["protocol_distribution"])

		response, _ := json.Marshal(result)
		m.Respond(response)

		delete(partialData, finish.AnalysisID)
		Logger.Printf("[Analysis %s] Analysis data cleaned up", finish.AnalysisID)
	})

	return err
}
