import logging
import warnings
import os
import random
from datetime import datetime
from ipaddress import IPv4Address
from typing import List, Tuple

from scapy.all import Ether, IP, TCP, UDP, ICMP, Raw, PcapWriter

logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", message=".*manuf.*")


def generate_ip_pool(count: int = 5) -> List[str]:
    base_ip = int(IPv4Address('192.168.1.1'))
    return [str(IPv4Address(base_ip + i)) for i in range(count)]


def generate_port_pool(count: int = 10) -> Tuple[List[int], List[int]]:
    src_ports = random.sample(range(1024, 65535), count)
    dst_ports = random.sample(range(1, 1023), count)
    return src_ports, dst_ports


def generate_packet(ip_pool: List[str], src_ports: List[int], dst_ports: List[int]) -> Ether:
    protocol = random.choice(['TCP', 'UDP', 'ICMP'])

    ip_layer = IP(
        src=random.choice(ip_pool),
        dst=random.choice(ip_pool)
    )
    eth_layer = Ether()

    if protocol == 'TCP':
        transport = TCP(
            sport=random.choice(src_ports),
            dport=random.choice(dst_ports)
        )
    elif protocol == 'UDP':
        transport = UDP(
            sport=random.choice(src_ports),
            dport=random.choice(dst_ports)
        )
    else:
        transport = ICMP()

    payload = Raw(load=os.urandom(500))
    return eth_layer / ip_layer / transport / payload


def main() -> None:
    target_size = 900 * 1024 * 1024
    filename = f"../../example_pcaps/output_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pcap"
    dir_path = os.path.dirname(filename)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    if os.path.exists(filename):
        os.remove(filename)
    writer = PcapWriter(filename, append=True, sync=False)
    ip_pool = generate_ip_pool()
    src_ports, dst_ports = generate_port_pool()
    packets_written = 0
    try:
        while os.path.getsize(filename) < target_size:
            packets = [generate_packet(ip_pool, src_ports, dst_ports) for _ in range(1000)]
            for pkt in packets:
                writer.write(pkt)
            packets_written += 1000
            if packets_written % 10000 == 0:
                print(f"Сгенерировано пакетов: {packets_written}, размер файла: {os.path.getsize(filename) / (1024 * 1024):.2f} MB")
    finally:
        writer.close()
        print(f"Готово! Сгенерировано пакетов: {packets_written}")


if __name__ == "__main__":
    main()
