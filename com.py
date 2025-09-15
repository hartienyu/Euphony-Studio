import serial
import serial.tools.list_ports
import time

def list_com_ports():
    """List available COM ports."""
    ports = serial.tools.list_ports.comports()
    if not ports:
        print("未找到任何串口设备。")
        return None
    print("可用串口：")
    for port in ports:
        print(f" - {port.device}: {port.description}")
    return [port.device for port in ports]

def initialize_serial(port='COM7', baud_rate=9600):
    """Initialize serial connection to HC-05."""
    available_ports = list_com_ports()
    if available_ports and port not in available_ports:
        print(f"警告: {port} 未在可用串口中。请检查设备管理器或尝试以下端口：{available_ports}")
        return None
    
    try:
        ser = serial.Serial(port, baud_rate, timeout=1)
        print(f"已连接到 {port}")
        return ser
    except serial.SerialException as e:
        print(f"无法打开串口 {port}: {e}")
        print("请检查：")
        print("1. 串口号是否正确（在设备管理器中查看）")
        print("2. HC-05 是否已配对并连接")
        print("3. 串口是否被其他程序占用")
        print("4. 是否以管理员身份运行脚本")
        return None

def read_serial(ser):
    """Read frequency data from serial port and return as float."""
    if ser and ser.in_waiting > 0:
        try:
            data = ser.readline().decode('utf-8').strip()
            freq = float(data)  # Convert to float
            if 20 <= freq <= 20000:
                print(f"接收到频率: {freq} Hz")
                return freq
            else:
                print(f"频率 {freq} Hz 超出可听范围 (20-20000 Hz)")
                return None
        except ValueError:
            print(f"无效数据: {data}")
            return None
        except Exception as e:
            print(f"读取错误: {e}")
            return None
    return None

def close_serial(ser):
    """Close serial connection."""
    if ser and ser.is_open:
        ser.close()
        print("串口已关闭")