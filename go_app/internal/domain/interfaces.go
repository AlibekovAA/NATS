package domain

type PcapAnalyzer interface {
	Analyze(data []byte) (*AnalysisResult, error)
}

type MessageHandler interface {
	HandleStart(msg []byte) error
	HandleChunk(msg []byte) ([]byte, error)
	HandleFinish(msg []byte) ([]byte, error)
}
