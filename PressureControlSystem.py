"""
气压测控仿真系统 PC上位机软件
功能：GUI界面、串口通信、学号发送、气压显示
开发语言：Python + tkinter + pyserial
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import serial
import serial.tools.list_ports
import threading
import time
from datetime import datetime

class PressureControlSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("气压测控仿真系统 - 学号： 姓名：")
        self.root.geometry("800x600")
        self.root.resizable(True, True)

        # 串口相关变量
        self.serial_port = None
        self.is_connected = False
        self.receive_thread = None
        self.stop_receiving = False

        # 学生信息 (请修改为你的学号和姓名)
        self.student_name = ""
        self.student_id = ""

        # 创建GUI界面
        self.create_widgets()

        # 刷新串口列表
        self.refresh_ports()

        # 窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        """创建GUI组件"""

        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)

        # 标题标签
        title_label = ttk.Label(main_frame, text="气压测控仿真系统",
                                font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # 串口控制区域
        port_frame = ttk.LabelFrame(main_frame, text="串口设置", padding="10")
        port_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        port_frame.columnconfigure(1, weight=1)

        # 串口选择
        ttk.Label(port_frame, text="串口:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.port_combobox = ttk.Combobox(port_frame, width=15)
        self.port_combobox.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))

        # 刷新串口按钮
        refresh_btn = ttk.Button(port_frame, text="刷新", command=self.refresh_ports)
        refresh_btn.grid(row=0, column=2, padx=(0, 10))

        # 波特率选择
        ttk.Label(port_frame, text="波特率:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.baudrate_combobox = ttk.Combobox(port_frame, values=["9600", "19200", "38400", "115200"], width=10)
        self.baudrate_combobox.set("9600")
        self.baudrate_combobox.grid(row=1, column=1, sticky=tk.W, pady=(5, 0))

        # 连接/断开按钮
        self.connect_btn = ttk.Button(port_frame, text="连接串口", command=self.toggle_connection)
        self.connect_btn.grid(row=1, column=2, pady=(5, 0))

        # 学号发送区域
        send_frame = ttk.LabelFrame(main_frame, text="学号发送", padding="10")
        send_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        send_frame.columnconfigure(1, weight=1)

        # 学号输入
        ttk.Label(send_frame, text="学号:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.student_id_entry = ttk.Entry(send_frame, width=20)
        self.student_id_entry.insert(0, self.student_id)
        self.student_id_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))

        # 发送按钮
        send_btn = ttk.Button(send_frame, text="发送学号", command=self.send_student_id)
        send_btn.grid(row=0, column=2)

        # 发送记录显示
        send_record_label = ttk.Label(send_frame, text="发送记录:")
        send_record_label.grid(row=1, column=0, sticky=tk.W, pady=(10, 0), padx=(0, 5))
        self.send_text = scrolledtext.ScrolledText(send_frame, height=3, width=50)
        self.send_text.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))

        # 气压接收区域
        receive_frame = ttk.LabelFrame(main_frame, text="气压数据接收", padding="10")
        receive_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        receive_frame.columnconfigure(0, weight=1)
        receive_frame.rowconfigure(1, weight=1)

        # 气压值显示标签
        self.pressure_label = ttk.Label(receive_frame, text="当前气压: --.- hPa",
                                       font=("Arial", 14, "bold"))
        self.pressure_label.grid(row=0, column=0, pady=(0, 10))

        # 接收数据显示区域
        self.receive_text = scrolledtext.ScrolledText(receive_frame, height=15, width=70)
        self.receive_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 清空按钮
        clear_btn = ttk.Button(receive_frame, text="清空记录", command=self.clear_receive_text)
        clear_btn.grid(row=2, column=0, pady=(10, 0))

        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))

    def refresh_ports(self):
        """刷新可用串口列表"""
        ports = serial.tools.list_ports.comports()
        port_list = [port.device for port in ports]
        self.port_combobox['values'] = port_list
        if port_list:
            self.port_combobox.set(port_list[0])
        else:
            self.port_combobox.set("")

    def toggle_connection(self):
        """切换串口连接状态"""
        if not self.is_connected:
            self.connect_serial()
        else:
            self.disconnect_serial()

    def connect_serial(self):
        """连接串口"""
        port = self.port_combobox.get()
        if not port:
            messagebox.showerror("错误", "请选择串口！")
            return

        try:
            baudrate = int(self.baudrate_combobox.get())
            self.serial_port = serial.Serial(port, baudrate, timeout=1)
            self.is_connected = True
            self.connect_btn.config(text="断开串口")
            self.status_var.set(f"已连接到 {port} ({baudrate} bps)")

            # 启动接收线程
            self.stop_receiving = False
            self.receive_thread = threading.Thread(target=self.receive_data)
            self.receive_thread.daemon = True
            self.receive_thread.start()

            # 记录连接信息
            self.add_receive_message(f"[{datetime.now().strftime('%H:%M:%S')}] 连接到 {port}")

        except Exception as e:
            messagebox.showerror("连接错误", f"无法连接到串口: {str(e)}")

    def disconnect_serial(self):
        """断开串口连接"""
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()

        self.is_connected = False
        self.connect_btn.config(text="连接串口")
        self.status_var.set("串口已断开")

        # 停止接收线程
        self.stop_receiving = True
        if self.receive_thread:
            self.receive_thread.join(timeout=1)

        # 记录断开信息
        self.add_receive_message(f"[{datetime.now().strftime('%H:%M:%S')}] 串口已断开")

    def send_student_id(self):
        """发送学号到Arduino"""
        if not self.is_connected:
            messagebox.showwarning("警告", "请先连接串口！")
            return

        student_id = self.student_id_entry.get().strip()
        if not student_id:
            messagebox.showwarning("警告", "请输入学号！")
            return

        try:
            # 发送学号
            message = student_id + '\n'
            self.serial_port.write(message.encode('utf-8'))
            self.serial_port.flush()

            # 记录发送信息
            timestamp = datetime.now().strftime('%H:%M:%S')
            send_message = f"[{timestamp}] 发送学号: {student_id}"
            self.send_text.insert(tk.END, send_message + '\n')
            self.send_text.see(tk.END)
            self.add_receive_message(f"[{timestamp}] 已发送学号: {student_id}")

            # 更新状态
            self.status_var.set(f"已发送学号: {student_id}")

        except Exception as e:
            messagebox.showerror("发送错误", f"发送失败: {str(e)}")

    def receive_data(self):
        """接收数据的线程函数"""
        while not self.stop_receiving and self.is_connected:
            try:
                if self.serial_port.in_waiting > 0:
                    data = self.serial_port.readline().decode('utf-8').strip()
                    if data:
                        self.root.after(0, self.process_received_data, data)
                time.sleep(0.1)  # 避免CPU占用过高
            except Exception as e:
                if not self.stop_receiving:
                    self.root.after(0, self.handle_receive_error, str(e))
                break

    def process_received_data(self, data):
        """处理接收到的数据"""
        timestamp = datetime.now().strftime('%H:%M:%S')

        # 检查是否为气压数据
        if data.startswith("PRESSURE:"):
            try:
                # 提取气压值
                pressure_str = data.replace("PRESSURE:", "").replace("hPa", "").strip()
                pressure_value = float(pressure_str)

                # 更新气压显示
                self.pressure_label.config(text=f"当前气压: {pressure_value:.1f} hPa")

                # 添加到接收记录
                receive_message = f"[{timestamp}] {data}"
                self.add_receive_message(receive_message)

                # 更新状态
                self.status_var.set(f"接收气压: {pressure_value:.1f} hPa")

            except ValueError:
                # 处理其他消息
                receive_message = f"[{timestamp}] {data}"
                self.add_receive_message(receive_message)
        else:
            # 普通消息
            receive_message = f"[{timestamp}] {data}"
            self.add_receive_message(receive_message)

    def handle_receive_error(self, error_msg):
        """处理接收错误"""
        self.add_receive_message(f"[错误] 接收数据时出错: {error_msg}")
        self.status_var.set("接收数据出错")

    def add_receive_message(self, message):
        """添加消息到接收显示区域"""
        self.receive_text.insert(tk.END, message + '\n')
        self.receive_text.see(tk.END)

    def clear_receive_text(self):
        """清空接收记录"""
        self.receive_text.delete(1.0, tk.END)
        self.pressure_label.config(text="当前气压: --.- hPa")

    def on_closing(self):
        """窗口关闭时的处理"""
        if self.is_connected:
            self.disconnect_serial()
        self.root.destroy()

def main():
    """主函数"""
    root = tk.Tk()
    app = PressureControlSystem(root)

    # 注意：请将下面这行代码中的学号和姓名修改为你自己的信息
    root.title("气压测控仿真系统 - 学号： 姓名：")

    root.mainloop()

if __name__ == "__main__":
    main()