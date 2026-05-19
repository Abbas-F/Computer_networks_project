#!/usr/bin/env python3
"""
Mini Internet Protocol Stack Simulator - Main Entry Point
Orchestrates the network simulation for data transmission from Host A to Host B.
"""

import sys
from devices import Host, Router
from config import (
    IP_HOST_A,
    IP_ROUTER_R1_IF1,
    IP_ROUTER_R1_IF2,
    IP_HOST_B,
    MAC_HOST_A,
    MAC_ROUTER_R1_IF1,
    MAC_ROUTER_R1_IF2,
    MAC_HOST_B,
    ROUTING_TABLE_HOST_A,
    ROUTING_TABLE_ROUTER_R1,
    ROUTING_TABLE_HOST_B,
    MAC_TABLE_HOST_A,
    MAC_TABLE_ROUTER_R1,
    MAC_TABLE_HOST_B,
    PORT_SRC,
    PORT_DST,
    MAX_SEGMENT_DATA_SIZE,
)


def create_network():
    """
    Create and initialize the network topology:
    Host A -- Router R1 (if1) -- Router R1 (if2) -- Host B
    """
    # Create Host A
    host_a = Host(
        name="Host A",
        ip_addr=IP_HOST_A,
        mac_addr=MAC_HOST_A,
        routing_table=ROUTING_TABLE_HOST_A,
        mac_table=MAC_TABLE_HOST_A,
        port=PORT_SRC
    )
    
    # Create Router R1
    router_r1 = Router(
        name="Router R1",
        interfaces=[
            ("eth0", IP_ROUTER_R1_IF1, MAC_ROUTER_R1_IF1),
            ("eth1", IP_ROUTER_R1_IF2, MAC_ROUTER_R1_IF2),
        ],
        routing_table=ROUTING_TABLE_ROUTER_R1,
        mac_table=MAC_TABLE_ROUTER_R1
    )
    
    # Create Host B
    host_b = Host(
        name="Host B",
        ip_addr=IP_HOST_B,
        mac_addr=MAC_HOST_B,
        routing_table=ROUTING_TABLE_HOST_B,
        mac_table=MAC_TABLE_HOST_B,
        port=PORT_DST
    )
    
    return {
        "host_a": host_a,
        "router_r1": router_r1,
        "host_b": host_b,
    }


def simulate_transmission(network, message_size):
    """
    Simulate the transmission of data from Host A to Host B.
    Handles segmentation, routing, and acknowledgments.
    """
    host_a = network["host_a"]
    router_r1 = network["router_r1"]
    host_b = network["host_b"]
    
    # Create test data
    test_data = b"X" * message_size
    
    print("=" * 80)
    print(f"Starting transmission: {message_size} bytes from Host A to Host B")
    print("=" * 80)
    print()
    
    # Calculate number of segments needed
    num_segments = (message_size + MAX_SEGMENT_DATA_SIZE - 1) // MAX_SEGMENT_DATA_SIZE
    print(f"Data will be segmented into {num_segments} segment(s)")
    print()
    
    # Process each segment
    seq_num = 0
    for seg_idx in range(num_segments):
        segment_start = seg_idx * MAX_SEGMENT_DATA_SIZE
        segment_end = min(segment_start + MAX_SEGMENT_DATA_SIZE, message_size)
        segment_data = test_data[segment_start:segment_end]
        segment_size = len(segment_data)
        
        print("=" * 80)
        print(f"SEGMENT {seg_idx + 1}/{num_segments} (seq={seq_num}, size={segment_size} bytes)")
        print("=" * 80)
        print()
        
        # ====================================================================
        # Step 1: Host A sends DATA segment
        # ====================================================================
        
        # Layer 4: Create segment
        from protocol import TransportSegment
        host_a.log("Layer 4: Data received from Application Layer. Data size=" + str(segment_size))
        
        transport_segment = TransportSegment(
            src_port=PORT_SRC,
            dst_port=PORT_DST,
            seg_type=TransportSegment.TYPE_DATA,
            seq_num=seq_num,
            data=segment_data
        )
        host_a.log("Layer 4: Checksum computed")
        host_a.log(f"Layer 4: Segment created by adding transport layer header (DATA, seq={seq_num}) (encapsulation)")
        host_a.log("Layer 4: Segment sent to Network Layer")
        
        # Layer 3: Encapsulate in packet
        from protocol import NetworkPacket
        from config import IP_PROTOCOL_UDP, DEFAULT_TTL
        
        host_a.log(f"Layer 3: Segment received from Transport Layer: SRC_IP={IP_HOST_A}, DST_IP={IP_HOST_B}, TTL={DEFAULT_TTL}")
        host_a.log(f"Layer 3: Destination IP read: {IP_HOST_B}")
        host_a.log("Layer 3: Routing table lookup performed")
        host_a.log(f"Layer 3: Next-hop IP determined: {IP_ROUTER_R1_IF1}")
        host_a.log("Layer 3: Outgoing interface selected")
        host_a.log("Layer 3: Packet forwarded to Data Link Layer")
        
        packet = NetworkPacket(
            src_ip=IP_HOST_A,
            dst_ip=IP_HOST_B,
            protocol=IP_PROTOCOL_UDP,
            payload=transport_segment.serialize(),
            ttl=DEFAULT_TTL
        )
        
        # Layer 2: Create frame and send from Host A to Router R1
        from protocol import DataLinkFrame
        from config import ETHERNET_TYPE_IPV4
        
        host_a.log("Layer 2: Packet received from Network Layer")
        host_a.log(f"Layer 2: Destination MAC lookup for next-hop IP ({IP_ROUTER_R1_IF1}) → {MAC_ROUTER_R1_IF1}")
        
        frame_a_to_r1 = DataLinkFrame(
            src_mac=MAC_HOST_A,
            dst_mac=MAC_ROUTER_R1_IF1,
            frame_type=ETHERNET_TYPE_IPV4,
            payload=packet.serialize()
        )
        host_a.log(f"Layer 2: Frame created: SRC_MAC={MAC_HOST_A}, DST_MAC={MAC_ROUTER_R1_IF1}")
        host_a.log("Layer 2: Frame sent")
        print()
        
        # ====================================================================
        # Step 2: Router R1 receives from Host A, forwards to Host B
        # ====================================================================
        
        frame_r1_to_b = router_r1.receive_frame(frame_a_to_r1, "eth0")
        print()
        
        # ====================================================================
        # Step 3: Host B receives frame from Router R1
        # ====================================================================
        
        frame_b_to_r1 = host_b.receive_frame(frame_r1_to_b)
        print()
        
        # ====================================================================
        # Step 5: Router R1 receives ACK from Host B, forwards to Host A
        # ====================================================================
        
        frame_r1_to_a = router_r1.receive_frame(frame_b_to_r1, "eth1")
        print()
        
        # ====================================================================
        # Step 6: Host A receives ACK from Router R1
        # ====================================================================
        
        host_a.receive_frame(frame_r1_to_a)
        print()
        
        # Alternate sequence number for next segment
        seq_num = 1 - seq_num
    
    print("=" * 80)
    print(f"Transmission Complete!")
    print(f"Total data received by Host B: {len(host_b.received_data)} bytes")
    print("=" * 80)


def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: python main.py <message_size>")
        print("Example: python main.py 100")
        sys.exit(1)
    
    try:
        message_size = int(sys.argv[1])
        if message_size <= 0:
            print("Error: Message size must be positive")
            sys.exit(1)
    except ValueError:
        print("Error: Message size must be an integer")
        sys.exit(1)
    
    # Create network
    network = create_network()
    
    # Run simulation
    simulate_transmission(network, message_size)


if __name__ == "__main__":
    main()
