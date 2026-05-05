# -*- coding: utf-8 -*-
"""解码抖音私信 hex 数据，分析 Protobuf 结构"""

hex_data = """08 64 10 AB 4E 1A 05 30 2E 31 2E 36 22 00 28 03 30 00 3A 13 66 65 66 31 61 38 30 3A 70 2F 6C 7A 67 2F 73 74 6F 72 65 42 8C 03 A2 06 88 03 0A 21 30 3A 31 3A 31 31 31 32 36 32 37 34 35 30 32 33 3A 31 38 36 34 33 36 32 36 39 39 35 34 34 39 32 30 10 01 18 84 84 86 F0 E2 B6 C5 E4 63 22 41 7B 22 61 77 65 54 79 70 65 22 3A 37 30 30 2C 22 74 79 70 65 22 3A 30 2C 22 72 69 63 68 54 65 78 74 49 6E 66 6F 73 22 3A 5B 5D 2C 22 74 65 78 74 22 3A 22 E5 88 80 E5 93 A5 E6 9D A5 E4 BA 86 22 7D 2A 15 0A 11 73 3A 6D 65 6E 74 69 6F 6E 65 64 5F 75 73 65 72 73 12 00 2A 3B 0A 13 73 3A 63 6C 69 65 6E 74 5F 6D 65 73 73 61 67 65 5F 69 64 12 24 30 61 61 37 64 34 66 30 2D 35 37 63 64 2D 34 35 33 61 2D 39 66 32 35 2D 38 39 64 39 64 31 65 32 34 61 38 38 2A 1D 0A 07 73 3A 73 74 69 6D 65 12 12 31 37 37 37 39 36 32 31 35 30 34 36 35 2E 30 34 35 34 30 07 3A 79 31 6C 61 57 78 77 49 4F 77 52 4A 4F 77 56 6D 6B 61 77 77 6B 44 72 36 4B 46 77 6A 74 45 41 47 45 54 78 44 4A 52 6E 47 69 6F 49 46 45 67 4D 5A 4B 6C 31 63 64 73 74 77 74 4D 45 56 4F 46 37 76 67 6E 6F 58 48 70 5A 30 33 53 65 76 4B 32 74 59 5A 4B 33 6F 78 34 67 7A 31 43 77 76 46 5A 4E 62 31 6E 67 7A 58 56 65 5A 30 4C 41 30 6D 43 64 6D 42 4D 7A 4B 64 67 4C 32 4D 43 42 24 30 61 61 37 64 34 66 30 2D 35 37 63 64 2D 34 35 33 61 2D 39 66 32 35 2D 38 39 64 39 64 31 65 32 34 61 38 38 4A 01 30 5A 09 64 6F 75 79 69 6E 5F 70 63 72 06 33 36 30 30 30 30 7A E8 01 0A 17 69 64 65 6E 74 69 74 79 5F 73 65 63 75 72 69 74 79 5F 74 6F 6B 65 6E 12 CC 01 7B 22 74 6F 6B 65 6E 22 3A 22 43 6A 76 2D 33 72 54 57 59 6D 5A 76 6A 6F 58 52 73 30 63 74 5F 7A 63 50 72 4E 30 51 75 77 4D 43 38 4E 31 36 4B 7A 4E 79 41 76 62 37 66 6E 69 5F 4A 72 6B 70 57 77 47 4F 7A 62 7A 38 57 38 57 62 37 4D 37 69 75 38 34 5A 30 7A 61 63 31 70 48 52 7A 42 70 4B 43 6A 77 41 41 41 41 41 41 41 41 41 41 41 41 41 55 47 49 34 73 6D 50 39 58 65 6C 45 69 56 50 63 61 39 79 79 72 42 55 5A 44 70 6A 5F 56 2D 4C 61 67 38 4F 33 35 6A 36 48 72 53 41 5A 41 2D 38 77 74 51 59 44 46 56 5F 75 73 35 66 6B 5A 44 32 71 54 64 67 51 6A 64 43 51 44 68 6A 32 73 64 46 73 49 41 49 69 41 51 4E 58 54 6D 30 76 22 7D 7A 32 0A 1B 69 64 65 6E 74 69 74 79 5F 73 65 63 75 72 69 74 79 5F 64 65 76 69 63 65 5F 69 64 12 13 37 35 39 34 33 34 38 38 30 31 37 33 38 37 35 33 35 38 37 7A 19 0A 15 69 64 65 6E 74 69 74 79 5F 73 65 63 75 72 69 74 79 5F 61 69 64 12 00 7A 13 0A 0B 73 65 73 73 69 6F 6E 5F 61 69 64 12 04 36 33 38 33 7A 10 0A 0B 73 65 73 73 69 6F 6E 5F 64 69 64 12 01 30 7A 15 0A 08 61 70 70 5F 6E 61 6D 65 12 09 64 6F 75 79 69 6E 5F 70 63 7A 15 0A 0F 70 72 69 6F 72 69 74 79 5F 72 65 67 69 6F 6E 12 02 63 6E 7A 8B 01 0A 0A 75 73 65 72 5F 61 67 65 6E 74 12 7D 4D 6F 7A 69 6C 6C 61 2F 35 2E 30 20 28 57 69 6E 64 6F 77 73 20 4E 54 20 31 30 2E 30 3B 20 57 69 6E 36 34 3B 20 78 36 34 29 20 41 70 70 6C 65 57 65 62 4B 69 74 2F 35 33 37 2E 33 36 20 28 4B 48 54 4D 4C 2C 20 6C 69 6B 65 20 47 65 63 6B 6F 29 20 43 68 72 6F 6D 65 2F 31 34 37 2E 30 2E 30 2E 30 20 53 61 66 61 72 69 2F 35 33 37 2E 33 36 20 45 64 67 2F 31 34 37 2E 30 2E 30 2E 30 7A 16 0A 0E 63 6F 6F 6B 69 65 5F 65 6E 61 62 6C 65 64 12 04 74 72 75 65 7A 19 0A 10 62 72 6F 77 73 65 72 5F 6C 61 6E 67 75 61 67 65 12 05 7A 68 2D 43 4E 7A 19 0A 10 62 72 6F 77 73 65 72 5F 70 6C 61 74 66 6F 72 6D 12 05 57 69 6E 33 32 7A 17 0A 0C 62 72 6F 77 73 65 72 5F 6E 61 6D 65 12 07 4D 6F 7A 69 6C 6C 61 7A 88 01 0A 0F 62 72 6F 77 73 65 72 5F 76 65 72 73 69 6F 6E 12 75 35 2E 30 20 28 57 69 6E 64 6F 77 73 20 4E 54 20 31 30 2E 30 3B 20 57 69 6E 36 34 3B 20 78 36 34 29 20 41 70 70 6C 65 57 65 62 4B 69 74 2F 35 33 37 2E 33 36 20 28 4B 48 54 4D 4C 2C 20 6C 69 6E 65 20 47 65 63 6B 6F 29 20 43 68 72 6F 6D 65 2F 31 34 37 2E 30 2E 30 2E 30 20 53 61 66 61 72 69 2F 35 33 37 2E 33 36 20 45 64 67 2F 31 34 37 2E 30 2E 30 2E 30 7A 16 0A 0E 62 72 6F 77 73 65 72 5F 6F 6E 6C 69 6E 65 12 04 74 72 75 65 7A 14 0A 0C 73 63 72 65 65 6E 5F 77 69 64 74 68 12 04 31 39 32 30 7A 15 0A 0D 73 63 72 65 65 6E 5F 68 65 69 67 68 74 12 04 31 30 38 30 7A 2B 0A 07 72 65 66 65 72 65 72 12 20 68 74 74 70 73 3A 2F 2F 77 77 77 2E 64 6F 75 79 69 6E 2E 63 6F 6D 2F 75 73 65 72 2F 73 65 6C 66 7A 1E 0A 0D 74 69 6D 65 7A 6F 6E 65 5F 6E 61 6D 65 12 0D 41 73 69 61 2F 53 68 61 6E 67 68 61 69 7A 0D 0A 08 64 65 76 69 63 65 49 64 12 01 30 7A 0D 0A 08 69 73 2D 72 65 74 72 79 12 01 30 90 01 01 AA 01 0A 64 6F 75 79 69 6E 5F 77 65 62 B2 01 07 77 65 62 5F 73 64 6B"""

# 去除空格，转换为字节
raw = bytes.fromhex(hex_data.replace(" ", "").replace("\n", ""))

print(f"总字节数: {len(raw)}")
print(f"\n{'='*80}")
print("提取所有可打印 ASCII 字符串（≥4 字符）：")
print(f"{'='*80}\n")

# 提取可读字符串
current = bytearray()
strings = []
for i, b in enumerate(raw):
    if 0x20 <= b <= 0x7E:
        current.append(b)
    else:
        if len(current) >= 4:
            try:
                s = current.decode('ascii')
                strings.append((i - len(current), s))
            except:
                pass
        current = bytearray()

if len(current) >= 4:
    strings.append((len(raw) - len(current), current.decode('ascii', errors='ignore')))

for offset, s in strings:
    print(f"  偏移 0x{offset:04X}: {s}")

# 尝试提取 UTF-8 中文内容
print(f"\n{'='*80}")
print("提取 UTF-8 编码中文内容：")
print(f"{'='*80}\n")

# 查找 JSON 消息体
import json
text = raw.decode('utf-8', errors='ignore')
# 查找 JSON 片段
idx = 0
while True:
    start = text.find('{', idx)
    if start == -1:
        break
    depth = 0
    end = start
    for i in range(start, len(text)):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    
    json_str = text[start:end]
    try:
        parsed = json.loads(json_str)
        print(f"  JSON 片段 (偏移 ~{start}): {json.dumps(parsed, ensure_ascii=False, indent=2)}")
    except:
        pass
    idx = end

# 手动解析关键 Protobuf 结构
print(f"\n{'='*80}")
print("Protobuf 结构分析：")
print(f"{'='*80}\n")

# 尝试用 protobuf 的 raw 解析
def decode_varint(data, pos):
    result = 0
    shift = 0
    while pos < len(data):
        b = data[pos]
        result |= (b & 0x7F) << shift
        pos += 1
        if (b & 0x80) == 0:
            break
        shift += 7
    return result, pos

def parse_protobuf(data, indent=0):
    pos = 0
    prefix = "  " * indent
    while pos < len(data):
        if pos >= len(data):
            break
        tag, pos = decode_varint(data, pos)
        field_number = tag >> 3
        wire_type = tag & 0x07
        
        if wire_type == 0:  # Varint
            value, pos = decode_varint(data, pos)
            print(f"{prefix}字段 {field_number} (Varint): {value}")
        elif wire_type == 2:  # Length-delimited
            length, pos = decode_varint(data, pos)
            if pos + length > len(data):
                print(f"{prefix}字段 {field_number} (Bytes): 长度={length} [截断]")
                break
            value = data[pos:pos+length]
            pos += length
            
            # 尝试解码为 UTF-8 字符串
            try:
                s = value.decode('utf-8')
                if all(c.isprintable() or c in '\n\r\t' for c in s):
                    if len(s) > 100:
                        print(f"{prefix}字段 {field_number} (String[{length}]): \"{s[:80]}...\"")
                    else:
                        print(f"{prefix}字段 {field_number} (String[{length}]): \"{s}\"")
                    continue
            except:
                pass
            
            # 尝试递归解析为嵌套 protobuf
            if length > 2:
                try:
                    print(f"{prefix}字段 {field_number} (Message[{length}]):")
                    parse_protobuf(value, indent + 1)
                except:
                    print(f"{prefix}字段 {field_number} (Bytes[{length}]): {value[:50].hex()}")
            else:
                print(f"{prefix}字段 {field_number} (Bytes[{length}]): {value.hex()}")
        elif wire_type == 1:  # 64-bit
            if pos + 8 > len(data):
                break
            value = int.from_bytes(data[pos:pos+8], 'little')
            pos += 8
            print(f"{prefix}字段 {field_number} (Fixed64): {value}")
        elif wire_type == 5:  # 32-bit
            if pos + 4 > len(data):
                break
            value = int.from_bytes(data[pos:pos+4], 'little')
            pos += 4
            print(f"{prefix}字段 {field_number} (Fixed32): {value}")
        else:
            print(f"{prefix}字段 {field_number} (未知线类型 {wire_type}) - 停止解析")
            break

print("=== 顶层 Protobuf 解析 ===\n")
try:
    parse_protobuf(raw)
except Exception as e:
    print(f"解析终止: {e}")
