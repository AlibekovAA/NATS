package domain

import "time"

type NetworkPacket struct {
    SourceIP      string            `json:"source_ip"`
    DestinationIP string            `json:"destination_ip"`
    Protocol      string            `json:"protocol"`
    Size          int               `json:"size"`
    Timestamp     time.Time         `json:"timestamp"`
    ExtraInfo     map[string]any    `json:"additional_info,omitempty"`
}

type AnalysisResult struct {
    Packets []NetworkPacket `json:"packets"`
    Summary map[string]any  `json:"summary"`
}

type ChunkMessage struct {
    AnalysisID  string `json:"analysis_id"`
    ChunkNumber int    `json:"chunk_number"`
    TotalChunks int    `json:"total_chunks"`
    Data        string `json:"data"`
    Encoding    string `json:"encoding"`
}
