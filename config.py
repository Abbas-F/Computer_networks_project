"""
Network Configuration
Defines IP addresses, MAC addresses, and routing tables for the network topology.
"""

# ============================================================================
# IP Addresses
# ============================================================================
IP_HOST_A = "10.0.1.10"
IP_ROUTER_R1_IF1 = "10.0.1.1"  # Interface 1 on subnet 10.0.1.0/24
IP_ROUTER_R1_IF2 = "10.0.2.1"  # Interface 2 on subnet 10.0.2.0/24
IP_HOST_B = "10.0.2.20"

# ============================================================================
# MAC Addresses
# ============================================================================
MAC_HOST_A = "AA:AA:AA:AA:AA:AA"
MAC_ROUTER_R1_IF1 = "BB:BB:BB:BB:BB:BB"
MAC_ROUTER_R1_IF2 = "CC:CC:CC:CC:CC:CC"
MAC_HOST_B = "DD:DD:DD:DD:DD:DD"

# ============================================================================
# Network Subnets (CIDR notation)
# ============================================================================
SUBNET_1 = "10.0.1.0/24"
SUBNET_2 = "10.0.2.0/24"

# ============================================================================
# Routing Tables
# Format: {destination_ip: (next_hop_ip, outgoing_interface, interface_ip)}
# ============================================================================

# Host A routing table
ROUTING_TABLE_HOST_A = {
    IP_HOST_B: (IP_ROUTER_R1_IF1, "eth0", IP_HOST_A),  # To reach 10.0.2.20, go to router
}

# Router R1 routing tables (per interface)
# Interface 1 (10.0.1.0/24)
# Interface 2 (10.0.2.0/24)
ROUTING_TABLE_ROUTER_R1 = {
    IP_HOST_A: (IP_HOST_A, "eth0", IP_ROUTER_R1_IF1),          # Host A is directly connected
    IP_HOST_B: (IP_HOST_B, "eth1", IP_ROUTER_R1_IF2),          # Host B is directly connected
}

# Host B routing table
ROUTING_TABLE_HOST_B = {
    IP_HOST_A: (IP_ROUTER_R1_IF2, "eth0", IP_HOST_B),  # To reach 10.0.1.10, go to router
}

# ============================================================================
# MAC Address Table (ARP-like mapping: IP → MAC)
# Used at Layer 2 to determine destination MAC from next-hop IP
# ============================================================================

# Host A MAC table
MAC_TABLE_HOST_A = {
    IP_ROUTER_R1_IF1: MAC_ROUTER_R1_IF1,
}

# Router R1 MAC tables
MAC_TABLE_ROUTER_R1 = {
    IP_HOST_A: MAC_HOST_A,
    IP_HOST_B: MAC_HOST_B,
}

# Host B MAC table
MAC_TABLE_HOST_B = {
    IP_ROUTER_R1_IF2: MAC_ROUTER_R1_IF2,
}

# ============================================================================
# Protocol Constants
# ============================================================================
ETHERNET_TYPE_IPV4 = 0x0800
IP_PROTOCOL_UDP = 17

# Default TTL
DEFAULT_TTL = 100

# Max data size per UDP-like segment
MAX_SEGMENT_DATA_SIZE = 500

# Default ports for testing
PORT_SRC = 5000
PORT_DST = 80
