import asyncio
from bleak import BleakScanner, BleakClient

# 标准 GAP 设备名称 UUID
DEVICE_NAME_UUID = "00002a00-0000-1000-8000-00805f9b34fb"

# 常见蓝牙厂商代码（中文版）
MANUFACTURERS = {
    0x004C: "苹果",
    0x0075: "三星",
    0xFE95: "小米",
    0xFFFF: "ESP32(自定义)",
    0x00E0: "谷歌",
    0x0060: "微软"
}

def parse_manufacturer_data(mfg_id: int, data: bytes) -> str:
    """解析厂商特定数据（中文版）"""
    if mfg_id == 0xFE95:  # 小米设备
        if len(data) >= 3:
            battery = data[2] & 0x7F
            return f"电量: {battery}%"
    elif mfg_id == 0x004C:  # 苹果设备
        if len(data) >= 5:
            device_type = data[0]
            return f"设备类型: 0x{device_type:02X}"
    return f"原始数据: {data.hex()}"

async def scan_and_check_devices():
    print("🔍 正在扫描BLE设备...（请确保蓝牙已开启，扫描将持续60秒）")
    
    # 扫描配置：主动模式 + 超时60秒 + 返回广播数据
    devices = await BleakScanner.discover(
        timeout=60.0,
        scanning_mode="active",
        return_adv=True
    )

    if not devices:
        print("❌ 未发现任何BLE设备！请检查：")
        print("  1. 设备是否处于可发现模式（如闪烁蓝灯）")
        print("  2. 系统蓝牙是否正常工作")
        return

    print(f"\n✅ 共发现 {len(devices)} 个设备：")
    for i, (addr, (dev, adv)) in enumerate(devices.items()):
        # 显示基础信息
        print(f"\n【设备 {i+1}】")
        print(f"  名称: {dev.name or '未知设备'}")
        print(f"  地址: {addr}")
        print(f"  信号强度: {adv.rssi} dBm")
        
        # 显示厂商信息
        if adv.manufacturer_data:
            for mfg_id, data in adv.manufacturer_data.items():
                mfg_name = MANUFACTURERS.get(mfg_id, f"未知厂商(0x{mfg_id:04X})")
                print(f"  厂商: {mfg_name}")
                print(f"  {parse_manufacturer_data(mfg_id, data)}")
        
        # 显示服务信息
        if adv.service_uuids:
            print("  支持的服务UUID:")
            for uuid in adv.service_uuids:
                print(f"    - {uuid}")

    print("\n⚙️ 正在检查设备名称修改权限...")
    for addr, (dev, adv) in devices.items():
        try:
            print(f"\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬")
            print(f"正在检测: {dev.name or '未知设备'} ({addr})")
            
            async with BleakClient(dev, timeout=10.0) as client:
                if not client.is_connected:
                    print("  ⚠️ 连接失败，跳过检测")
                    continue

                # 检查GAP服务
                gap_service = client.services.get_service("00001800-0000-1000-8000-00805f9b34fb")
                if not gap_service:
                    print("  ❌ 不支持GAP服务（无法修改名称）")
                    continue
                
                # 检查设备名称特征
                name_char = gap_service.get_characteristic(DEVICE_NAME_UUID)
                if name_char:
                    if "write" in name_char.properties:
                        print("  ✅ 支持修改设备名称！详细信息：")
                        print(f"    - 服务UUID: {gap_service.uuid}")
                        print(f"    - 特征UUID: {name_char.uuid}")
                        print(f"    - 权限: {name_char.properties}")
                    else:
                        print("  ❌ 检测到名称特征，但不可写（只读）")
                else:
                    print("  ❌ 未找到设备名称特征")
                    
        except Exception as e:
            print(f"  ⚠️ 检测过程中出错: {str(e)}")

if __name__ == "__main__":
    asyncio.run(scan_and_check_devices())
