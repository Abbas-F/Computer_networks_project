"""
Network Devices: Host and Router implementations
"""

from protocol import DataLinkFrame, NetworkPacket, TransportSegment
from config import (
    ETHERNET_TYPE_IPV4,
    IP_PROTOCOL_UDP,
    DEFAULT_TTL
)


# ============================================================================
# Base Node Class
# ============================================================================

class Node:
    """
    Base class for network nodes (Host and Router).
    Handles common functionality across layers.
    """
    
    def __init__(self, name, ip_addr, mac_addr, routing_table, mac_table):
        self.name = name
        self.ip_addr = ip_addr
        self.mac_addr = mac_addr
        self.routing_table = routing_table
        self.mac_table = mac_table
        self.learned_macs = {}  # MAC address learning table for Layer 2
    
    def log(self, message):
        """Print a log message with the node name."""
        print(f"{self.name}: {message}")


# ============================================================================
# Host Class
# ============================================================================

class Host(Node):
    """
    Represents a network host that sends and receives data.
    Implements rdt2.2 (alternating bit protocol) for reliable data transfer.
    """
    
    def __init__(self, name, ip_addr, mac_addr, routing_table, mac_table, port=5000):
        super().__init__(name, ip_addr, mac_addr, routing_table, mac_table)
        self.port = port
        self.received_data = b""
        self.last_ack_seq = None
        self.pending_ack_seq = None
    
    def send_data(self, destination_ip, destination_port, data, segment_size=500):
        """
        Send data to a destination (application layer interface).
        Segments data if necessary (max 500 bytes per segment).
        Implements rdt2.2 with alternating sequence numbers.
        """
        # Split data into segments if needed
        segments = []
        for i in range(0, len(data), segment_size):
            segment_data = data[i:i + segment_size]
            segments.append(segment_data)
        
        seq_num = 0
        for segment_data in segments:
            # Transport Layer: Create DATA segment
            self.log(f"Layer 4: Data received from Application Layer. Data size={len(segment_data)}")
            
            transport_segment = TransportSegment(
                src_port=self.port,
                dst_port=destination_port,
                seg_type=TransportSegment.TYPE_DATA,
                seq_num=seq_num,
                data=segment_data
            )
            self.log("Layer 4: Checksum computed")
            self.log(f"Layer 4: Segment created by adding transport layer header (DATA, seq={seq_num}) (encapsulation)")
            self.log("Layer 4: Segment sent to Network Layer")
            
            # Network Layer: Forward to Layer 3
            self.network_layer_send(
                src_ip=self.ip_addr,
                dst_ip=destination_ip,
                segment=transport_segment
            )
            
            # Wait for ACK (in synchronous simulation, process incoming ACK)
            # Note: In real scenario, this would be event-driven
            seq_num = 1 - seq_num  # Alternate between 0 and 1
    
    def network_layer_send(self, src_ip, dst_ip, segment):
        """
        Network Layer send: encapsulate segment into packet and forward to Layer 2.
        """
        self.log(f"Layer 3: Segment received from Transport Layer: SRC_IP={src_ip}, DST_IP={dst_ip}, TTL={DEFAULT_TTL}")
        
        packet_payload = segment.serialize()
        packet = NetworkPacket(
            src_ip=src_ip,
            dst_ip=dst_ip,
            protocol=IP_PROTOCOL_UDP,
            payload=packet_payload,
            ttl=DEFAULT_TTL
        )
        
        # Routing decision
        self.log(f"Layer 3: Destination IP read: {dst_ip}")
        self.log("Layer 3: Routing table lookup performed")
        
        if dst_ip in self.routing_table:
            next_hop_ip, interface, _ = self.routing_table[dst_ip]
            self.log(f"Layer 3: Next-hop IP determined: {next_hop_ip}")
            self.log("Layer 3: Outgoing interface selected")
            self.log("Layer 3: Packet forwarded to Data Link Layer")
            
            # Data Link Layer
            return self.data_link_layer_send(packet, next_hop_ip)
        else:
            self.log(f"Layer 3: No route to {dst_ip}")
            return None
    
    def data_link_layer_send(self, packet, next_hop_ip):
        """
        Data Link Layer send: lookup MAC, create frame, and send.
        """
        self.log("Layer 2: Packet received from Network Layer")
        
        # MAC lookup
        if next_hop_ip in self.mac_table:
            next_hop_mac = self.mac_table[next_hop_ip]
        else:
            self.log(f"Layer 2: MAC address not found for {next_hop_ip}")
            return
        
        self.log(f"Layer 2: Destination MAC lookup for next-hop IP ({next_hop_ip}) → {next_hop_mac}")
        
        frame = DataLinkFrame(
            src_mac=self.mac_addr,
            dst_mac=next_hop_mac,
            frame_type=ETHERNET_TYPE_IPV4,
            payload=packet.serialize()
        )
        
        self.log(f"Layer 2: Frame created: SRC_MAC={self.mac_addr}, DST_MAC={next_hop_mac}")
        self.log("Layer 2: Frame sent")
        
        # Simulate transmission (store for other nodes to receive)
        return frame
    
    def receive_frame(self, frame):
        """
        Receive a frame at Layer 2 and process up the stack.
        """
        self.log("Layer 2: Frame received")
        
        # Learn source MAC
        src_mac = frame.src_mac
        self.log(f"Layer 2: Source MAC learned: {src_mac}")
        self.learned_macs[src_mac] = src_mac
        
        # Deliver to Network Layer
        self.log("Layer 2: Packet delivered to Network Layer")
        return self.network_layer_receive(frame.payload)
    
    def network_layer_receive(self, packet_data):
        """
        Network Layer receive: parse packet and deliver to Layer 4.
        """
        packet = NetworkPacket.deserialize(packet_data)
        
        self.log(f"Layer 3: Packet received from Data Link Layer: SRC_IP={packet.src_ip}, DST_IP={packet.dst_ip}, TTL={packet.ttl}")
        self.log(f"Layer 3: Destination IP read: {packet.dst_ip}")
        
        # Check if packet is for this host
        if packet.dst_ip == self.ip_addr:
            self.log("Layer 3: Packet identified as local delivery")
            self.log("Layer 3: Segment delivered to Transport Layer")
            return self.transport_layer_receive(packet.payload, packet.src_ip)
        else:
            self.log(f"Layer 3: Packet not destined for this host")
            return None
    
    def transport_layer_receive(self, segment_data, source_ip=None):
        """
        Transport Layer receive: parse segment, verify checksum, and deliver to application.
        """
        segment = TransportSegment.deserialize(segment_data)
        
        self.log("Layer 4: Segment received from Network Layer")
        
        # Verify checksum
        if segment.verify_checksum():
            self.log("Layer 4: Checksum verified")
        else:
            self.log("Layer 4: Checksum verification FAILED - segment discarded")
            return
        
        if segment.seg_type == TransportSegment.TYPE_DATA:
            self.log(f"Layer 4: DATA segment delivered to Application Layer. Data size={len(segment.data)}")
            self.received_data += segment.data
            self.pending_ack_seq = segment.seq_num
            
            # Send ACK
            return self.send_ack(source_ip, segment.src_port, segment.seq_num)
        elif segment.seg_type == TransportSegment.TYPE_ACK:
            self.log(f"Layer 4: ACK received: seq={segment.seq_num}")
            self.last_ack_seq = segment.seq_num
            return None
    
    def send_ack(self, destination_ip, dst_port, seq_num):
        """
        Send an ACK segment for the received DATA segment.
        """
        ack_segment = TransportSegment(
            src_port=self.port,
            dst_port=dst_port,
            seg_type=TransportSegment.TYPE_ACK,
            seq_num=seq_num,
            data=b""
        )
        
        self.log(f"Layer 4: Segment created by adding transport layer header (ACK, seq={seq_num})")
        self.log("Layer 4: Segment sent to Network Layer")
        
        # Network Layer: forward ACK back to sender
        return self.network_layer_send(
            src_ip=self.ip_addr,
            dst_ip=destination_ip,
            segment=ack_segment
        )


# ============================================================================
# Router Class
# ============================================================================

class Router(Node):
    """
    Represents a network router that forwards packets between subnets.
    Handles MAC learning, routing, and TTL management.
    """
    
    def __init__(self, name, interfaces, routing_table, mac_table):
        """
        Initialize router with multiple interfaces.
        
        Args:
            name: Router name (e.g., 'Router R1')
            interfaces: List of tuples (interface_name, ip_address, mac_address)
            routing_table: Routing table dict
            mac_table: MAC address table dict
        """
        # Use first interface as primary IP/MAC for base class
        primary_ip = interfaces[0][1]
        primary_mac = interfaces[0][2]
        super().__init__(name, primary_ip, primary_mac, routing_table, mac_table)
        
        self.interfaces = {name: {"ip": ip, "mac": mac} for name, ip, mac in interfaces}
        self.interface_mac_learning = {name: {} for name in self.interfaces}
    
    def receive_frame(self, frame, incoming_interface):
        """
        Receive a frame at Layer 2 and process routing/forwarding.
        """
        self.log(f"Layer 2: Frame received on {incoming_interface}")
        
        # Learn source MAC on incoming interface
        src_mac = frame.src_mac
        self.log(f"Layer 2: Source MAC learned: {src_mac} on {incoming_interface}")
        self.interface_mac_learning[incoming_interface][src_mac] = src_mac
        
        # Deliver to Network Layer
        self.log("Layer 2: Packet delivered to Network Layer")
        return self.network_layer_receive(frame.payload, incoming_interface)
    
    def network_layer_receive(self, packet_data, incoming_interface):
        """
        Network Layer receive: parse packet, route, and forward.
        """
        packet = NetworkPacket.deserialize(packet_data)
        
        self.log(f"Layer 3: Packet received from Data Link Layer: SRC_IP={packet.src_ip}, DST_IP={packet.dst_ip}, TTL={packet.ttl}")
        self.log(f"Layer 3: Destination IP read: {packet.dst_ip}")
        
        # Decrement TTL
        old_ttl = packet.ttl
        if not packet.decrement_ttl():
            self.log(f"Layer 3: TTL decremented: {old_ttl} → 0 (packet dropped)")
            return
        else:
            self.log(f"Layer 3: TTL decremented: {old_ttl} → {packet.ttl}")
        
        # Routing lookup
        self.log("Layer 3: Routing table lookup performed")
        
        if packet.dst_ip in self.routing_table:
            next_hop_ip, outgoing_interface, interface_ip = self.routing_table[packet.dst_ip]
            self.log(f"Layer 3: Next-hop IP determined: {next_hop_ip}")
            self.log(f"Layer 3: Outgoing interface selected ({outgoing_interface})")
            self.log("Layer 3: Packet forwarded to Data Link Layer")
            
            # Data Link Layer
            return self.data_link_layer_send(packet, next_hop_ip, outgoing_interface)
        else:
            self.log(f"Layer 3: No route to {packet.dst_ip}")
            return None
    
    def data_link_layer_send(self, packet, next_hop_ip, outgoing_interface):
        """
        Data Link Layer send: lookup MAC on interface and create frame.
        """
        self.log("Layer 2: Packet received from Network Layer")
        
        # Get source MAC for outgoing interface
        src_mac = self.interfaces[outgoing_interface]["mac"]
        
        # MAC lookup
        if next_hop_ip in self.mac_table:
            next_hop_mac = self.mac_table[next_hop_ip]
        else:
            self.log(f"Layer 2: MAC address not found for {next_hop_ip}")
            return
        
        self.log(f"Layer 2: Destination MAC lookup for next-hop IP ({next_hop_ip}) → {next_hop_mac}")
        
        frame = DataLinkFrame(
            src_mac=src_mac,
            dst_mac=next_hop_mac,
            frame_type=ETHERNET_TYPE_IPV4,
            payload=packet.serialize()
        )
        
        self.log(f"Layer 2: Frame created: SRC_MAC={src_mac}, DST_MAC={next_hop_mac}")
        self.log(f"Layer 2: Frame forwarded on {outgoing_interface}")
        
        return frame
