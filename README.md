# Mini Internet Protocol Stack Simulator

A Python implementation of a simplified network stack demonstrating Layer 2 (Data Link), Layer 3 (Network), and Layer 4 (Transport) operations. This simulator models how data is encapsulated and transmitted across a network topology consisting of two hosts (A and B) connected via a router (R1).

## Features

- **Layer 2 (Data Link)**: Ethernet-like frame encapsulation, MAC addressing, frame forwarding, and MAC address learning
- **Layer 3 (Network)**: IP-like packet encapsulation, routing, TTL management, and inter-network packet forwarding
- **Layer 4 (Transport)**: UDP-like segment creation, checksum computation/verification, and reliable data transfer using rdt2.2 (alternating-bit protocol)
- **Reliable Data Transfer**: Implements rdt2.2 with sequence numbers (0/1) and ACK-based retransmission
- **Data Segmentation**: Automatically segments messages larger than 500 bytes into multiple transport segments
- **Detailed Logging**: Comprehensive output showing operations at each layer (frame creation, routing decisions, MAC learning, etc.)

## Network Topology

```
Host A (10.0.1.10)
    |
    | MAC: AA:AA:AA:AA:AA:AA
    |
    +---- Router R1 ----+
    |                   |
eth0: 10.0.1.1      eth1: 10.0.2.1
MAC: BB:BB:BB:BB:BB:BB  MAC: CC:CC:CC:CC:CC:CC
    |                   |
    +---- Host B (10.0.2.20)
         MAC: DD:DD:DD:DD:DD:DD
```

### Network Configuration

- **Subnet 1**: 10.0.1.0/24 (Host A and Router R1 Interface 1)
- **Subnet 2**: 10.0.2.0/24 (Router R1 Interface 2 and Host B)

## Protocol Header Definitions

### Layer 2 - Data Link Frame (Ethernet-like)
- Destination MAC (6 bytes)
- Source MAC (6 bytes)
- Type (2 bytes) - 0x0800 for IPv4
- Payload (variable) - Layer 3 packet

### Layer 3 - Network Packet (IP-like)
- Source IP (4 bytes)
- Destination IP (4 bytes)
- TTL (1 byte) - decremented at each router
- Protocol (1 byte) - 17 for UDP
- Total Length (2 bytes)
- Payload (variable) - Layer 4 segment

### Layer 4 - Transport Segment (UDP-like with ACK)
- Source Port (2 bytes)
- Destination Port (2 bytes)
- Length (2 bytes)
- Checksum (2 bytes) - computed over entire segment
- Type (1 byte) - 0 for DATA, 1 for ACK
- Sequence Number (1 byte) - alternates between 0 and 1 (rdt2.2)
- Data (variable) - application data (empty for ACK segments)

## Project Structure

```
computer_networks/
├── main.py          # Entry point - orchestrates the simulation
├── config.py        # Network configuration (IPs, MACs, routing tables)
├── protocol.py      # Protocol header definitions (Layers 2, 3, 4)
├── devices.py       # Host and Router implementations
└── README.md        # This file
```

## How to Run

### Basic Usage
```bash
python main.py 10
```

This command simulates sending a 10-byte message from Host A to Host B.

### Examples

Send 100 bytes:
```bash
python main.py 100
```

Send 1000 bytes (will be segmented into 2 segments of 500 bytes each):
```bash
python main.py 1000
```

Send 50 bytes:
```bash
python main.py 50
```

## Output Explanation

The simulator produces detailed logs showing the flow of data through the network stack. Each log entry is prefixed with the device name (Host A, Router R1, or Host B) and the layer (Layer 2, 3, or 4).

Example output for `python main.py 10`:
```
Host A: Layer 4: Data received from Application Layer. Data size=10
Host A: Layer 4: Checksum computed
Host A: Layer 4: Segment created by adding transport layer header (DATA, seq=0) (encapsulation)
Host A: Layer 4: Segment sent to Network Layer
Host A: Layer 3: Segment received from Transport Layer: SRC_IP=10.0.1.10, DST_IP=10.0.2.20, TTL=100
Host A: Layer 3: Destination IP read: 10.0.2.20
Host A: Layer 3: Routing table lookup performed
Host A: Layer 3: Next-hop IP determined: 10.0.1.1
Host A: Layer 3: Outgoing interface selected
Host A: Layer 3: Packet forwarded to Data Link Layer
Host A: Layer 2: Packet received from Network Layer
Host A: Layer 2: Destination MAC lookup for next-hop IP (10.0.1.1) → BB:BB:BB:BB:BB:BB
Host A: Layer 2: Frame created: SRC_MAC=AA:AA:AA:AA:AA:AA, DST_MAC=BB:BB:BB:BB:BB:BB
Host A: Layer 2: Frame sent
... (continues through Router R1 to Host B)
```

## Implementation Details

### Layer 2 - Data Link
- **Frame Creation**: Encapsulates Layer 3 packets into frames with MAC addressing
- **MAC Learning**: Learns source MAC addresses from received frames on each interface
- **MAC Lookup**: Uses a MAC address table to determine the destination MAC for a given next-hop IP
- **Frame Forwarding**: Forwards frames based on the routing decision made by Layer 3

### Layer 3 - Network
- **Packet Creation**: Encapsulates Layer 4 segments into packets with IP addressing
- **Routing**: Performs routing table lookups to determine the outgoing interface and next-hop IP
- **TTL Management**: Decrements TTL at each hop; drops packets when TTL reaches 0
- **Local Delivery**: Identifies when packets are destined for the local host and delivers them to Layer 4

### Layer 4 - Transport
- **Segment Creation**: Encapsulates application data into segments with port-based addressing
- **Checksum Computation**: Computes a simple checksum over the entire segment for error detection
- **Checksum Verification**: Verifies checksums on received segments; discards corrupted segments
- **Data Segmentation**: Splits messages larger than 500 bytes into multiple segments
- **rdt2.2 Protocol**: Implements reliable data transfer with:
  - Sequence numbers (0 or 1) that alternate for each DATA segment
  - ACK segments sent by the receiver upon successful reception
  - Retransmission triggered by incorrect or duplicate ACKs

## Key Classes

### `TransportSegment` (protocol.py)
Represents a Layer 4 UDP-like segment with ACK support. Handles checksum computation/verification and serialization.

**Methods**:
- `compute_checksum()`: Computes checksum over the segment
- `verify_checksum()`: Verifies checksum integrity
- `serialize()`: Converts segment to bytes
- `deserialize()`: Converts bytes to segment

### `NetworkPacket` (protocol.py)
Represents a Layer 3 IP-like packet. Handles IP addressing and TTL management.

**Methods**:
- `decrement_ttl()`: Decrements TTL, returns False if TTL reaches 0
- `serialize()`: Converts packet to bytes
- `deserialize()`: Converts bytes to packet

### `DataLinkFrame` (protocol.py)
Represents a Layer 2 Ethernet-like frame. Handles MAC addressing.

**Methods**:
- `serialize()`: Converts frame to bytes
- `deserialize()`: Converts bytes to frame

### `Host` (devices.py)
Represents a network host with full stack implementation.

**Methods**:
- `send_data()`: Sends data with automatic segmentation and rdt2.2
- `receive_frame()`: Receives frame at Layer 2
- `send_ack()`: Sends ACK segment for received data

### `Router` (devices.py)
Represents a network router with multiple interfaces.

**Methods**:
- `receive_frame()`: Receives frame on specific interface
- `network_layer_receive()`: Performs routing decisions and TTL management

## Constraints and Assumptions

- **No Real Networking**: This is a logical simulation only; no socket or external networking libraries are used
- **Deterministic Operation**: Assumes no packet loss, frame corruption, or transmission delays
- **Maximum Segment Size**: Limited to 500 bytes of data per transport-layer segment
- **Reliable Delivery**: Implements rdt2.2, so all data is reliably delivered in order
- **Standard Library Only**: Uses only Python's standard library (struct, sys)

## Design Decisions

1. **Layered Architecture**: Each layer (2, 3, 4) is clearly separated with distinct responsibilities
2. **Object-Oriented Design**: Network entities (frames, packets, segments) are represented as classes
3. **Synchronous Simulation**: Data flows synchronously through the network without event-driven mechanics
4. **Detailed Logging**: All significant operations are logged to match the specification
5. **Configuration File**: Network parameters are externalized in `config.py` for easy modification

## Limitations and Future Enhancements

- **No Fragmentation**: Assumes segments fit within frame payload
- **Single Sender**: Currently designed for Host A → Host B communication (unidirectional after initial setup)
- **Simplified MAC Learning**: Uses simple in-memory dictionaries rather than ARP protocol
- **Fixed Routing**: Routing tables are static and pre-configured
- **No Error Recovery**: No retransmission due to timeout (relies on deterministic simulation)

## Group Members

This is a template. Replace with actual student IDs and names:
- [Student ID 1]: [Student Name 1]
- [Student ID 2]: [Student Name 2]

## License

This project is for educational purposes as part of the Computer Networks unit at UWA.
