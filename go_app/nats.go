package main

import (
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
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
		Logger.Printf("Failed to connect to NATS: %v", err)
		return nil, err
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
		Logger.Printf("Starting analysis ID: %s, expecting %d chunks", start.AnalysisID, start.TotalChunks)
		partialData[start.AnalysisID] = make([]byte, 0)
	})
	if err != nil {
		Logger.Printf("Failed to subscribe to start: %v", err)
		return err
	}

	_, err = nc.Subscribe("network.analysis.chunk", func(m *nats.Msg) {
		var chunk struct {
			AnalysisID   string `json:"analysis_id"`
			ChunkNumber  int    `json:"chunk_number"`
			TotalChunks  int    `json:"total_chunks"`
			Data         string `json:"data"`
			Encoding     string `json:"encoding"`
		}
		if err := json.Unmarshal(m.Data, &chunk); err != nil {
			Logger.Printf("Error parsing chunk message: %v", err)
			m.Respond([]byte(`{"error": "invalid json format"}`))
			return
		}
		Logger.Printf("Received chunk %d/%d for analysis ID: %s", chunk.ChunkNumber+1, chunk.TotalChunks, chunk.AnalysisID)

		var decodedData []byte
		var err error

		if chunk.Encoding == "hex" {
			decodedData, err = hex.DecodeString(chunk.Data)
		} else if chunk.Encoding == "base64" {
			decodedData, err = base64.StdEncoding.DecodeString(chunk.Data)
		} else {
			m.Respond([]byte(`{"error": "unsupported encoding"}`))
			return
		}

		if err != nil {
			m.Respond([]byte(err.Error()))
			return
		}

		if chunk.ChunkNumber == 0 {
			partialData[chunk.AnalysisID] = decodedData
		} else {
			partialData[chunk.AnalysisID] = append(partialData[chunk.AnalysisID], decodedData...)
		}

		Logger.Printf("Successfully processed chunk %d/%d", chunk.ChunkNumber+1, chunk.TotalChunks)
		m.Respond([]byte(`{"status": "ok"}`))
	})
	if err != nil {
		Logger.Printf("Failed to subscribe to chunk: %v", err)
		return err
	}

	_, err = nc.Subscribe("network.analysis.finish", func(m *nats.Msg) {
		var finish struct {
			AnalysisID string `json:"analysis_id"`
		}
		if err := json.Unmarshal(m.Data, &finish); err != nil {
			Logger.Printf("Error parsing finish message: %v", err)
			m.Respond([]byte(`{"error": "invalid finish message"}`))
			return
		}
		Logger.Printf("Starting final analysis for ID: %s", finish.AnalysisID)

		data := partialData[finish.AnalysisID]
		result, err := analyzePcapData(data)
		if err != nil {
			Logger.Printf("Error analyzing data: %v", err)
			m.Respond([]byte(err.Error()))
			return
		}

		Logger.Printf("Analysis completed successfully. Processed %d packets", len(result.Packets))
		response, _ := json.Marshal(result)
		m.Respond(response)
		delete(partialData, finish.AnalysisID)
	})
	if err != nil {
		Logger.Printf("Failed to subscribe to finish: %v", err)
		return err
	}

	return nil
}
