"""
Protocol Header Definitions
Defines the header structures and classes for Layers 2, 3, and 4.
"""

import struct
from config import ETHERNET_TYPE_IPV4, IP_PROTOCOL_UDP, DEFAULT_TTL


# ============================================================================
# Layer 4: Transport Layer (UDP-like with ACK support - rdt2.2)
# ============================================================================

class TransportSegment:
    """
    Represents a Layer 4 UDP-like segment with ACK support (rdt2.2).
    
    Header fields:
    - Source Port (2 bytes)
    - Destination Port (2 bytes)
    - Length (2 bytes) - header + data
    - Checksum (2 bytes) - computed over segment
    - Type (1 byte) - 0 = DATA, 1 = ACK
    - Sequence Number (1 byte) - 0 or 1 (alternating bit)
    - Data (variable) - application data (empty for ACK)
    """
    
    HEADER_SIZE = 10  # bytes
    TYPE_DATA = 0
    TYPE_ACK = 1
    
    def __init__(self, src_port, dst_port, seg_type, seq_num, data=b""):
        self.src_port = src_port
        self.dst_port = dst_port
        self.seg_type = seg_type
        self.seq_num = seq_num
        self.data = data
        self.checksum = 0
        self.compute_checksum()
    
    def compute_checksum(self):
        """Compute checksum over the entire segment (header + data)."""
        # Temporarily set checksum to 0
        checksum_backup = self.checksum
        self.checksum = 0
        
        # Serialize and compute checksum
        packet = self.serialize()
        checksum = sum(packet) % 65536
        self.checksum = checksum
    
    def verify_checksum(self):
        """Verify the checksum of the segment."""
        stored_checksum = self.checksum
        self.checksum = 0
        packet = self.serialize()
        computed_checksum = sum(packet) % 65536
        self.checksum = stored_checksum
        return stored_checksum == computed_checksum
    
    def serialize(self):
        """Serialize the segment into bytes."""
        length = self.HEADER_SIZE + len(self.data)
        header = struct.pack(
            "!HHHHBB",
            self.src_port,
            self.dst_port,
            length,
            self.checksum,
            self.seg_type,
            self.seq_num,
        )
        return header + self.data
    
    @staticmethod
    def deserialize(data):
        """Deserialize bytes into a TransportSegment."""
        if len(data) < TransportSegment.HEADER_SIZE:
            raise ValueError("Incomplete segment header")
        
        header = data[:TransportSegment.HEADER_SIZE]
        payload = data[TransportSegment.HEADER_SIZE:]

        src_port, dst_port, length, checksum, seg_type, seq_num = struct.unpack(
            "!HHHHBB",
            header
        )
        
        segment = TransportSegment(src_port, dst_port, seg_type, seq_num, payload)
        segment.checksum = checksum
        return segment
    
    def __repr__(self):
        type_str = "DATA" if self.seg_type == self.TYPE_DATA else "ACK"
        return f"TransportSegment(type={type_str}, seq={self.seq_num}, src_port={self.src_port}, dst_port={self.dst_port}, data_len={len(self.data)})"


# ============================================================================
# Layer 3: Network Layer (IP-like Packet)
# ============================================================================

class NetworkPacket:
    """
    Represents a Layer 3 IP-like packet.
    
    Header fields:
    - Source IP (4 bytes)
    - Destination IP (4 bytes)
    - TTL (1 byte) - decremented at each router
    - Protocol (1 byte) - 17 for UDP
    - Total Length (2 bytes) - header + payload
    - Payload (variable) - Layer 4 segment
    """
    
    HEADER_SIZE = 12  # bytes
    
    def __init__(self, src_ip, dst_ip, protocol, payload, ttl=DEFAULT_TTL):
        self.src_ip = src_ip
        self.dst_ip = dst_ip
        self.ttl = ttl
        self.protocol = protocol
        self.payload = payload
    
    def decrement_ttl(self):
        """Decrement TTL by 1. Returns False if TTL reaches 0."""
        self.ttl -= 1
        return self.ttl > 0
    
    def serialize(self):
        """Serialize the packet into bytes."""
        total_length = self.HEADER_SIZE + len(self.payload)
        
        # Convert dotted-decimal IP addresses to 4-byte integers
        src_ip_bytes = bytes(map(int, self.src_ip.split(".")))
        dst_ip_bytes = bytes(map(int, self.dst_ip.split(".")))
        
        header = src_ip_bytes + dst_ip_bytes + struct.pack(
            "!BBH",
            self.ttl,
            self.protocol,
            total_length
        )
        return header + self.payload
    
    @staticmethod
    def deserialize(data):
        """Deserialize bytes into a NetworkPacket."""
        if len(data) < NetworkPacket.HEADER_SIZE:
            raise ValueError("Incomplete packet header")
        
        src_ip_bytes = data[0:4]
        dst_ip_bytes = data[4:8]
        ttl, protocol, total_length = struct.unpack("!BBH", data[8:12])
        
        src_ip = ".".join(map(str, src_ip_bytes))
        dst_ip = ".".join(map(str, dst_ip_bytes))
        
        payload = data[12:]
        
        packet = NetworkPacket(src_ip, dst_ip, protocol, payload, ttl)
        return packet
    
    def __repr__(self):
        return f"NetworkPacket(src={self.src_ip}, dst={self.dst_ip}, ttl={self.ttl}, payload_len={len(self.payload)})"


# ============================================================================
# Layer 2: Data Link Layer (Ethernet-like Frame)
# ============================================================================

class DataLinkFrame:
    """
    Represents a Layer 2 Ethernet-like frame.
    
    Header fields:
    - Destination MAC (6 bytes) - AA:BB:CC:DD:EE:FF format
    - Source MAC (6 bytes) - AA:BB:CC:DD:EE:FF format
    - Type (2 bytes) - 0x0800 for IPv4
    - Payload (variable) - Layer 3 packet
    """
    
    HEADER_SIZE = 14  # 6 + 6 + 2 bytes
    
    def __init__(self, src_mac, dst_mac, frame_type, payload):
        self.src_mac = src_mac
        self.dst_mac = dst_mac
        self.frame_type = frame_type
        self.payload = payload
    
    def serialize(self):
        """Serialize the frame into bytes."""
        src_mac_bytes = bytes(int(x, 16) for x in self.src_mac.split(":"))
        dst_mac_bytes = bytes(int(x, 16) for x in self.dst_mac.split(":"))
        
        header = dst_mac_bytes + src_mac_bytes + struct.pack("!H", self.frame_type)
        return header + self.payload
    
    @staticmethod
    def deserialize(data):
        """Deserialize bytes into a DataLinkFrame."""
        if len(data) < DataLinkFrame.HEADER_SIZE:
            raise ValueError("Incomplete frame header")
        
        dst_mac_bytes = data[0:6]
        src_mac_bytes = data[6:12]
        frame_type = struct.unpack("!H", data[12:14])[0]
        payload = data[14:]
        
        src_mac = ":".join(f"{b:02X}" for b in src_mac_bytes)
        dst_mac = ":".join(f"{b:02X}" for b in dst_mac_bytes)
        
        frame = DataLinkFrame(src_mac, dst_mac, frame_type, payload)
        return frame
    
    def __repr__(self):
        return f"DataLinkFrame(src={self.src_mac}, dst={self.dst_mac}, type=0x{self.frame_type:04X}, payload_len={len(self.payload)})"
