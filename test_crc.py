#!/usr/bin/env python3
"""
Test CRC16 calculation against known good values from the reference implementation.
This verifies our CRC implementation matches the device's expectations.
"""

import sys
sys.path.insert(0, '/Users/rfedo/Documents/Personal/ha-htram-fork/custom_components/htram')

from utils import CRC16

# Test cases from the reference implementation
# These are the actual packet structures used by the device

def test_realtime_command():
    """Test the real-time data request command."""
    # Command: 7B 41 00 07 40 44 02 00 [CRC] 7D
    packet_pre_crc = bytes([0x7B, 0x41, 0x00, 0x07, 0x40, 0x44, 0x02, 0x00])
    expected_crc = bytes([0xFC, 0x3E])  # From reference
    
    calculated_crc = CRC16.crc16_bytes(packet_pre_crc)
    
    print(f"Real-time command CRC test:")
    print(f"  Input:     {packet_pre_crc.hex()}")
    print(f"  Expected:  {expected_crc.hex()}")
    print(f"  Calculated: {calculated_crc.hex()}")
    print(f"  Result:    {'✓ PASS' if calculated_crc == expected_crc else '✗ FAIL'}")
    print()
    
    return calculated_crc == expected_crc

def test_heartbeat_command():
    """Test the heartbeat/keep-alive command."""
    # Command: 7B 41 00 06 24 01 01 [CRC] 7D
    packet_pre_crc = bytes([0x7B, 0x41, 0x00, 0x06, 0x24, 0x01, 0x01])
    expected_crc = bytes([0x78, 0x22])  # From const.py
    
    calculated_crc = CRC16.crc16_bytes(packet_pre_crc)
    
    print(f"Heartbeat command CRC test:")
    print(f"  Input:     {packet_pre_crc.hex()}")
    print(f"  Expected:  {expected_crc.hex()}")
    print(f"  Calculated: {calculated_crc.hex()}")
    print(f"  Result:    {'✓ PASS' if calculated_crc == expected_crc else '✗ FAIL'}")
    print()
    
    return calculated_crc == expected_crc

def test_sound_off_command():
    """Test the sound off command."""
    # Command: 7B 41 00 09 26 43 01 00 00 00 [CRC] 7D
    packet_pre_crc = bytes([0x7B, 0x41, 0x00, 0x09, 0x26, 0x43, 0x01, 0x00, 0x00, 0x00])
    expected_crc = bytes([0xAB, 0x63])  # From const.py
    
    calculated_crc = CRC16.crc16_bytes(packet_pre_crc)
    
    print(f"Sound off command CRC test:")
    print(f"  Input:     {packet_pre_crc.hex()}")
    print(f"  Expected:  {expected_crc.hex()}")
    print(f"  Calculated: {calculated_crc.hex()}")
    print(f"  Result:    {'✓ PASS' if calculated_crc == expected_crc else '✗ FAIL'}")
    print()
    
    return calculated_crc == expected_crc

def test_build_packet():
    """Test the build_packet function from reference."""
    # Simulate the build_packet function
    def build_packet(cmd_id: bytes, body: bytes = b""):
        length = 2 + len(body) + 3
        packet_pre_crc = bytes([0x7B, 0x41, 0x00, length]) + cmd_id + body
        crc = CRC16.crc16_bytes(packet_pre_crc)
        return packet_pre_crc + crc + b"\x7D"
    
    # Build real-time command
    cmd = build_packet(b"\x40\x44", b"\x02\x00")
    expected = bytes([0x7B, 0x41, 0x00, 0x07, 0x40, 0x44, 0x02, 0x00, 0xFC, 0x3E, 0x7D])
    
    print(f"Build packet test (real-time):")
    print(f"  Expected:  {expected.hex()}")
    print(f"  Built:     {cmd.hex()}")
    print(f"  Result:    {'✓ PASS' if cmd == expected else '✗ FAIL'}")
    print()
    
    return cmd == expected

if __name__ == "__main__":
    print("=" * 60)
    print("CRC16 Implementation Verification")
    print("=" * 60)
    print()
    
    results = [
        test_realtime_command(),
        test_heartbeat_command(),
        test_sound_off_command(),
        test_build_packet()
    ]
    
    print("=" * 60)
    total = len(results)
    passed = sum(results)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests PASSED - CRC implementation is correct!")
        sys.exit(0)
    else:
        print(f"✗ {total - passed} test(s) FAILED - CRC implementation needs fixing")
        sys.exit(1)
