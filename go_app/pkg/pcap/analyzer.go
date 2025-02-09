package pcap

import (
	"os"

	"go_app/internal/domain"
	"go_app/internal/infrastructure/logger"

	"github.com/google/gopacket"
	"github.com/google/gopacket/pcap"
)

type Analyzer struct {
	log *logger.Logger
}

func New(log *logger.Logger) *Analyzer {
	return &Analyzer{log: log}
}

func (a *Analyzer) Analyze(data []byte) (*domain.AnalysisResult, error) {
	tmpfile, err := a.createTempPcap(data)
	if err != nil {
		return nil, err
	}
	defer os.Remove(tmpfile.Name())
	defer tmpfile.Close()

	handle, err := pcap.OpenOffline(tmpfile.Name())
	if err != nil {
		return nil, err
	}
	defer handle.Close()

	packets, stats := a.processPackets(handle)
	return &domain.AnalysisResult{
		Packets: packets,
		Summary: stats,
	}, nil
}

func (a *Analyzer) processPackets(handle *pcap.Handle) ([]domain.NetworkPacket, map[string]any) {
	var packets []domain.NetworkPacket
	stats := make(map[string]any)
	protocolCount := make(map[string]int)
	totalSize := 0

	packetSource := gopacket.NewPacketSource(handle, handle.LinkType())
	for packet := range packetSource.Packets() {
		if netPacket := a.processPacket(packet); netPacket != nil {
			packets = append(packets, *netPacket)
			protocolCount[netPacket.Protocol]++
			totalSize += netPacket.Size
		}
	}

	stats["total_packets"] = len(packets)
	stats["total_size"] = totalSize
	stats["protocol_distribution"] = protocolCount

	return packets, stats
}

func (a *Analyzer) processPacket(packet gopacket.Packet) *domain.NetworkPacket {
	networkLayer := packet.NetworkLayer()
	if networkLayer == nil {
		return nil
	}

	transportLayer := packet.TransportLayer()
	protocol := a.getProtocol(networkLayer, transportLayer)

	netPacket := &domain.NetworkPacket{
		SourceIP:      networkLayer.NetworkFlow().Src().String(),
		DestinationIP: networkLayer.NetworkFlow().Dst().String(),
		Protocol:      protocol,
		Size:          len(packet.Data()),
		Timestamp:     packet.Metadata().Timestamp,
		ExtraInfo:     make(map[string]any),
	}

	if transportLayer != nil {
		netPacket.ExtraInfo["transport"] = map[string]string{
			"src_port": transportLayer.TransportFlow().Src().String(),
			"dst_port": transportLayer.TransportFlow().Dst().String(),
		}
	}

	return netPacket
}

func (a *Analyzer) getProtocol(networkLayer gopacket.NetworkLayer, transportLayer gopacket.TransportLayer) string {
	if transportLayer != nil {
		return transportLayer.LayerType().String()
	}
	return networkLayer.LayerType().String()
}

func (a *Analyzer) createTempPcap(data []byte) (*os.File, error) {
	tmpfile, err := os.CreateTemp("", "pcap-*.pcap")
	if err != nil {
		return nil, err
	}

	if _, err := tmpfile.Write(data); err != nil {
		tmpfile.Close()
		os.Remove(tmpfile.Name())
		return nil, err
	}

	if _, err := tmpfile.Seek(0, 0); err != nil {
		tmpfile.Close()
		os.Remove(tmpfile.Name())
		return nil, err
	}

	return tmpfile, nil
}
