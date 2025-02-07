package main

import (
	"os"
	"time"

	"github.com/google/gopacket"
	"github.com/google/gopacket/pcap"
)

type NetworkPacket struct {
    SourceIP       string                 `json:"source_ip"`
    DestinationIP  string                 `json:"destination_ip"`
    Protocol       string                 `json:"protocol"`
    Size           int                    `json:"size"`
    Timestamp      string                 `json:"timestamp"`
    AdditionalInfo map[string]interface{} `json:"additional_info,omitempty"`
}

type AnalysisResult struct {
    Packets []NetworkPacket        `json:"packets"`
    Summary map[string]interface{} `json:"summary"`
}

func createTempPcap(data []byte) (*os.File, error) {
    tmpfile, err := os.CreateTemp("", "pcap-*.pcap")
    if err != nil {
        Logger.Printf("error creating temp file: %v", err)
        return nil, err
    }
    if _, err := tmpfile.Write(data); err != nil {
        tmpfile.Close()
        os.Remove(tmpfile.Name())
        return nil, err
    }
    if err := tmpfile.Sync(); err != nil {
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

func processPackets(handle *pcap.Handle) ([]NetworkPacket, map[string]int, int) {
    var packets []NetworkPacket
    protocolCount := make(map[string]int)
    totalSize := 0
    packetCount := 0
    packetSource := gopacket.NewPacketSource(handle, handle.LinkType())
    for packet := range packetSource.Packets() {
        packetCount++
        if packetCount%1000 == 0 {
            Logger.Printf("[Packet Analysis] Processed %d packets...", packetCount)
        }
        networkLayer := packet.NetworkLayer()
        if networkLayer == nil {
            continue
        }
        transportLayer := packet.TransportLayer()
        protocol := ""
        if transportLayer != nil {
            protocol = transportLayer.LayerType().String()
        } else {
            protocol = networkLayer.LayerType().String()
        }
        netPacket := NetworkPacket{
            SourceIP:       networkLayer.NetworkFlow().Src().String(),
            DestinationIP:  networkLayer.NetworkFlow().Dst().String(),
            Protocol:       protocol,
            Size:           len(packet.Data()),
            Timestamp:      packet.Metadata().Timestamp.Format(time.RFC3339),
            AdditionalInfo: make(map[string]interface{}),
        }
        if transportLayer != nil {
            netPacket.AdditionalInfo["transport_info"] = map[string]interface{}{
                "src_port": transportLayer.TransportFlow().Src().String(),
                "dst_port": transportLayer.TransportFlow().Dst().String(),
            }
        }
        packets = append(packets, netPacket)
        protocolCount[protocol]++
        totalSize += netPacket.Size
    }
    return packets, protocolCount, totalSize
}

func analyzePcapData(data []byte) (*AnalysisResult, error) {
    tmpfile, err := createTempPcap(data)
    if err != nil {
        return nil, err
    }
    defer os.Remove(tmpfile.Name())
    defer tmpfile.Close()
    handle, err := pcap.OpenOffline(tmpfile.Name())
    if err != nil {
        Logger.Printf("error opening pcap file: %v", err)
        return nil, err
    }
    defer handle.Close()
    packets, protocolCount, totalSize := processPackets(handle)
    stats := make(map[string]interface{})
    stats["total_packets"] = len(packets)
    stats["total_size"] = totalSize
    stats["protocol_distribution"] = protocolCount
    stats["unique_sources"] = countUniqueSources(packets)
    stats["unique_destinations"] = countUniqueDestinations(packets)
    return &AnalysisResult{
        Packets: packets,
        Summary: stats,
    }, nil
}

func countUniqueSources(packets []NetworkPacket) int {
    sources := make(map[string]bool)
    for _, p := range packets {
        sources[p.SourceIP] = true
    }
    return len(sources)
}

func countUniqueDestinations(packets []NetworkPacket) int {
    destinations := make(map[string]bool)
    for _, p := range packets {
        destinations[p.DestinationIP] = true
    }
    return len(destinations)
}
