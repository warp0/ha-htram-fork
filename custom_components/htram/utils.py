import struct
from typing import List, Union

class CRC16:
    """CRC16 implementation matching the reference air_monitor.py."""
    # CRC16 Table with polynomial 0x8005 (Standard for Honeywell HTRAM)
    # This matches exactly the table from https://github.com/noname122021/honeywell-htram-v1w-ble-monitor/blob/main/air_monitor.py
    CRC16_TABLE = [
        0x0000, 0x8005, 0x800F, 0x000A, 0x801B, 0x001E, 0x0014, 0x8011,
        0x8033, 0x0036, 0x003C, 0x8039, 0x0028, 0x802D, 0x8027, 0x0022,
        0x8063, 0x0066, 0x006C, 0x8069, 0x0078, 0x807D, 0x8077, 0x0072,
        0x0050, 0x8055, 0x805F, 0x005A, 0x804B, 0x004E, 0x0044, 0x8041,
        0x80C3, 0x00C6, 0x00CC, 0x80C9, 0x00D8, 0x80DD, 0x80D7, 0x00D2,
        0x00F0, 0x80F5, 0x80FF, 0x00FA, 0x80EB, 0x00EE, 0x00E4, 0x80E1,
        0x00A0, 0x80A5, 0x80AF, 0x00AA, 0x80BB, 0x00BE, 0x00B4, 0x80B1,
        0x8093, 0x0096, 0x009C, 0x8099, 0x0088, 0x808D, 0x8087, 0x0082,
        0x8183, 0x0186, 0x018C, 0x8189, 0x0178, 0x817D, 0x8177, 0x0172,
        0x01B0, 0x81B5, 0x81BF, 0x01BA, 0x81AB, 0x01AE, 0x01A4, 0x81A1,
        0x01E0, 0x81E5, 0x81EF, 0x01EA, 0x81FB, 0x01FE, 0x01F4, 0x81F1,
        0x81D3, 0x01D6, 0x01DC, 0x81D9, 0x01C8, 0x81CD, 0x81C7, 0x01C2,
        0x0140, 0x8145, 0x814F, 0x014A, 0x815B, 0x015E, 0x0154, 0x8151,
        0x8173, 0x0176, 0x017C, 0x8179, 0x0168, 0x816D, 0x8167, 0x0162,
        0x8123, 0x0126, 0x012C, 0x8129, 0x0138, 0x813D, 0x8137, 0x0132,
        0x0110, 0x8115, 0x811F, 0x011A, 0x810B, 0x010E, 0x0104, 0x8101,
        0x8303, 0x0306, 0x030C, 0x8309, 0x0318, 0x831D, 0x8317, 0x0312,
        0x0330, 0x8335, 0x833F, 0x033A, 0x832B, 0x032E, 0x0324, 0x8321,
        0x0360, 0x8365, 0x836F, 0x036A, 0x837B, 0x037E, 0x0374, 0x8371,
        0x8353, 0x0356, 0x035C, 0x8359, 0x0348, 0x834D, 0x8347, 0x0342,
        0x03C0, 0x83C5, 0x83CF, 0x03CA, 0x83DB, 0x03DE, 0x03D4, 0x83D1,
        0x83F3, 0x03F6, 0x03FC, 0x83F9, 0x03E8, 0x83ED, 0x83E7, 0x03E2,
        0x83A3, 0x03A6, 0x03AC, 0x83A9, 0x03B8, 0x83BD, 0x83B7, 0x03B2,
        0x0390, 0x8395, 0x839F, 0x039A, 0x838B, 0x038E, 0x0384, 0x8381,
        0x0280, 0x8285, 0x828F, 0x028A, 0x829B, 0x029E, 0x0294, 0x8291,
        0x82B3, 0x02B6, 0x02BC, 0x82B9, 0x02A8, 0x82AD, 0x82A7, 0x02A2,
        0x82E3, 0x02E6, 0x02EC, 0x82E9, 0x02F8, 0x82FD, 0x82F7, 0x02F2,
        0x02D0, 0x82D5, 0x82DF, 0x02DA, 0x82CB, 0x02CE, 0x02C4, 0x82C1,
        0x8243, 0x0246, 0x024C, 0x8249, 0x0258, 0x825D, 0x8257, 0x0252,
        0x0270, 0x8275, 0x827F, 0x027A, 0x826B, 0x026E, 0x0264, 0x8261,
        0x0220, 0x8225, 0x822F, 0x022A, 0x823B, 0x023E, 0x0234, 0x8231,
        0x8213, 0x0216, 0x021C, 0x8219, 0x0208, 0x820D, 0x8207, 0x0202
    ]

    @staticmethod
    def crc16_short(data: bytes) -> int:
        """
        Calculates CRC16 using polynomial 0x8005.
        This matches the reference implementation from air_monitor.py:
        https://github.com/noname122021/honeywell-htram-v1w-ble-monitor/blob/main/air_monitor.py#L51-L56
        """
        crc = 0
        for byte in data:
            idx = ((crc >> 8) ^ byte) & 0xFF
            crc = ((crc << 8) ^ CRC16.CRC16_TABLE[idx]) & 0xFFFF
        return crc

    @staticmethod
    def crc16_bytes(data: bytes) -> bytes:
        """
        Calculate CRC16 and return as big-endian bytes (network byte order).
        This matches the reference: crc.to_bytes(2, byteorder="big")
        """
        crc = CRC16.crc16_short(data)
        return crc.to_bytes(2, byteorder='big')


def build_command_packet(cmd_head: bytes, payload_parts: List[bytes]) -> bytes:
    """
    Constructs a command packet following the app's structure:
    Merge(Head, Payload..., CRC(Head+Payload), Tail)
    """
    # Merge all parts
    merged = cmd_head
    for part in payload_parts:
        merged += part
        
    # Calculate CRC of the merged data
    crc = CRC16.crc16_bytes(merged)
    
    # Append CRC and Tail
    # Tail is always {125} -> 0x7D
    return merged + crc + b'\x7D'


def construct_submit_ssid(ssid: str, password: str) -> bytes:
    """
    Constructs the 7460 command (submitSSID).
    Structure from CMBLERequest.java:
    Head: {123, 65, 0, 12, 116, 96, 1} -> 7B 41 00 0C 74 60 01
    Payload:
      - 22 bytes of zeros
      - 1 byte: Password Length
      - Password bytes (padded to 64 bytes with zeros)
      - SSID bytes (padded to 33 bytes with zeros)
      - 33 bytes of zeros
    
    Total packet is wrapped with CRC and 0x7D.
    Note: The java code updates byte[3] (length?) before sending?
    `bArrByteMergerAll[3] = (byte) ((bArrByteMergerAll.length - 1) & 255);`
    Yes, byte 3 is the length of the packet (excluding the last byte? or something).
    It effectively sets the length field in the header.
    """
    
    pwd_bytes = password.encode('utf-8')
    ssid_bytes = ssid.encode('utf-8')
    
    # Base Head
    # 0x7B (123), 0x41 (65), 0x00, 0x0C (Length placeholder), 0x74, 0x60, 0x01
    head = bytearray([0x7B, 0x41, 0x00, 0x0C, 0x74, 0x60, 0x01])
    
    # Zeros 22 bytes
    zeros_22 = b'\x00' * 22
    
    # Password Length
    pwd_len = len(pwd_bytes) & 0xFF
    
    # Password Padded (64 bytes)
    pwd_padded = pwd_bytes + b'\x00' * (64 - len(pwd_bytes))
    
    # SSID Padded (33 bytes)
    ssid_padded = ssid_bytes + b'\x00' * (33 - len(ssid_bytes))
    
    # Zeros 33 bytes
    zeros_33 = b'\x00' * 33
    
    # Merge for CRC calculation (and Length fix)
    # Note: `byteMergerAll` in Java merges everything BEFORE CRC.
    # The logic:
    # 1. Merge Head + Zeros22 + PwdLen + Pwd + SSID + Zeros33
    # 2. Update Head[3] with (TotalLength - 1)
    # 3. Append CRC
    # 4. Append 0x7D
    
    content = head + zeros_22 + bytes([pwd_len]) + pwd_padded + ssid_padded + zeros_33
    
    # Update length
    # In Java: bArrByteMergerAll[3] = (byte) ((bArrByteMergerAll.length - 1) & 255);
    # This implies the length byte covers everything except the CRC and Tail? Or maybe up to that point?
    # Actually, in general, packet length fields usually cover the payload.
    # But here, `bArrByteMergerAll` contains EVERYTHING so far.
    # Let's count.
    content_len = len(content)
    content[3] = (content_len - 1) & 0xFF
    
    crc = CRC16.crc16_bytes(content)
    
    # Checksum verification with Java logic:
    # Java does `crc16Bytes` on the `content`.
    
    return content + crc + b'\x7D'


def construct_submit_aes_key(aes_key: str, aes_iv: str, mqtt_server: str) -> bytes:
    """
    Constructs the 20b0 command (submitAESKey).
    This seemingly handles MOV1 (Single packet?) but `WifiListPrecenter` has logic for MOV2 (Multipart).
    Let's implement the simpler MOV1 logic first which is `submitAESKey`.
    
    Head: {123, 65, 0, 12, 32, -80 (0xB0), 1} -> 7B 41 00 0C 20 B0 01
    Payload:
      - Key Length (1 byte)
      - Key Bytes
      - IV Length (1 byte)
      - IV Bytes
      - Server Length (1 byte)
      - Server Bytes
      
    Java Code notes: `Base64.decode(str, 0)` for Key. Wait.
    `submitAESKey(preferenceStringValue, ...)`
    The `preferenceStringValue` (Key) seems to be stored as Base64 string?
    In `WifiListPrecenter.java`, `enrollResponse` stores `aesKey`.
    Usually `aesKey` from API is hex or base64. 
    `CMBLERequest.submitAESKey`: `byte[] bArrDecode = Base64.decode(str, 0);`
    So yes, the input `aes_key` string is expected to be Base64.
    
    IV: `byte[] bytes = str2.getBytes();` -> IV is passed as raw string bytes? 
    Wait. `aesKey` is Base64 decoded. `aesIv` is `getBytes()`.
    That's inconsistent but that's what the code says:
    `byte[] bytes = str2.getBytes();` (str2 is aesIv)
    `byte[] bytes2 = str3.getBytes();` (str3 is mqttServer)
    
    So Key is binary (decoded from B64), IV is String-as-bytes, URL is String-as-bytes.
    
    Wait, `aesIv` is usually hex or base64 too.
    In `WifiListPrecenter.java`:
    `PreferenceUtils.setPreferenceStringValue(..., PreferenceUtils.KEY_AESIV, enrollDeviceInfo.getAesIv());`
    
    If `enrollDeviceInfo` comes from JSON, it's a string.
    If the device expects `str2.getBytes()`, then it expects the ASCII characters of the IV string?
    Or is `aesIv` actually a simple string like "1234567890123456"?
    
    Let's assume for our custom provisioning we will pass everything as expected.
    If we generate a key, we should encode it as Base64 before passing to this function if we want to mimic the signature,
    OR we just change this function to accept bytes.
    Let's accept strings to be safe, but be aware of the Base64 decoding for Key.
    """
    import base64
    
    # Key is Base64 encoded string in the Input, but we decode it to bytes for the packet
    # If the user provides a raw 16-char string key, we might need to handle that.
    # The Java code strictly does Base64.decode.
    # So if we want to set key="1234...", we should Base64 encode it first if we use this function strictly.
    # BUT, to make `utils.py` friendly, let's allow `aes_key` to be a hex string or raw bytes?
    # No, the device receives BYTES. The wrapper function just prepares them.
    # Let's support `aes_key` as Hex String or Base64 String?
    # The Java app treats it as Base64.
    
    try:
        key_bytes = base64.b64decode(aes_key)
    except:
        # Fallback: maybe it's just raw bytes in a string?
        key_bytes = aes_key.encode('utf-8')
        
    iv_bytes = aes_iv.encode('utf-8')
    server_bytes = mqtt_server.encode('utf-8')
    
    head = bytearray([0x7B, 0x41, 0x00, 0x0C, 0x20, 0xB0, 0x01])
    
    payload = (
        bytes([len(key_bytes)]) + key_bytes +
        bytes([len(iv_bytes)]) + iv_bytes +
        bytes([len(server_bytes)]) + server_bytes
    )
    
    content = head + payload
    
    # Update length
    content_len = len(content)
    content[3] = (content_len - 1) & 0xFF
    
    crc = CRC16.crc16_bytes(content)
    
    return content + crc + b'\x7D'
