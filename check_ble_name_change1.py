import asyncio
from bleak import BleakScanner, BleakClient

DEVICE_NAME_UUID = "00002a00-0000-1000-8000-00805f9b34fb"

async def scan_ble_devices():
    print("⏳ 正在深度扫描 BLE 设备（请耐心等待 15 秒）...")

    # 优化参数：延长扫描时间 + 主动模式
    devices = await BleakScanner.discover(
        timeout=60.0,
        scanning_mode="active",
        return_adv=True  # 返回广播数据
    )

    if not devices:
        print("❌ 未找到任何 BLE 设备！请检查：")
        print("  1. 蓝牙是否已开启？")
        print("  2. 设备是否在可发现模式（如闪烁蓝灯）？")
        print("  3. 是否被其他程序占用（如手机蓝牙 App）？")
        return

    print(f"\n🔍 共发现 {len(devices)} 个设备：")
    for addr, (dev, adv) in devices.items():
        name = dev.name or "未知设备"
        print(f"  - {name} (地址: {addr}, RSSI: {adv.rssi})")

    print("\n⚡ 正在检测设备名称修改权限...")
    for addr, (dev, _) in devices.items():
        try:
            async with BleakClient(dev, timeout=60.0) as client:
                if not client.is_connected:
                    continue

                # 检查 GAP Service 和 Device Name 特征
                gap_service = client.services.get_service("00001800-0000-1000-8000-00805f9b34fb")
                if not gap_service:
                    continue

                name_char = gap_service.get_characteristic(DEVICE_NAME_UUID)
                if name_char and "write" in name_char.properties:
                    print(f"\n✅ [{dev.name}] 支持修改名称！")
                    print(f"   - 地址: {addr}")
                    print(f"   - 特征权限: {name_char.properties}")
                else:
                    print(f"\n❌ [{dev.name}] 不支持直接修改名称")
        except Exception as e:
            print(f"\n⚠️ 检测 {dev.name} 时出错: {str(e)}")

if __name__ == "__main__":
    asyncio.run(scan_ble_devices())
