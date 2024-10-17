import psutil
import cpuinfo
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn
from collections import deque
import platform
import time
try:
    from nvitop import Device  # NVIDIA GPU ONLY
except ImportError:
    Device = None  # kills it if you dont have one
# Store history for the graph
cpu_history = deque(maxlen=60)
ram_history = deque(maxlen=60)
gpu_history = deque(maxlen=60)
def get_system_info():
    data = {"CPU": {}, "RAM": {}, "GPU": {}}
    # CPU
    cpu_freq = psutil.cpu_freq()
    data["CPU"]["Usage"] = psutil.cpu_percent(interval=0.1)
    data["CPU"]["Freq"] = cpu_freq.current if cpu_freq else 0
    data["CPU"]["Cores"] = psutil.cpu_count(logical=True)
    data["CPU"]["Temp"] = get_cpu_temp()
    # RAM
    memory = psutil.virtual_memory()
    data["RAM"]["Used"] = memory.used / (1024 ** 3)  #converts to gigs for convenience
    data["RAM"]["Total"] = memory.total / (1024 ** 3)
    data["RAM"]["Usage"] = memory.percent
    if Device:
        gpu = Device(0)  # nvidia only
        data["GPU"]["Name"] = gpu.name()
        data["GPU"]["Temp"] = gpu.temperature()
        data["GPU"]["Usage"] = gpu.utilization()
    return data
def get_cpu_temp():
    """Get CPU temperature cross-platform."""
    try:
        if platform.system() == "Windows":
            return psutil.sensors_temperatures()["coretemp"][0].current
        elif platform.system() == "Linux":
            temps = psutil.sensors_temperatures()
            return temps["coretemp"][0].current if "coretemp" in temps else None
        elif platform.system() == "Darwin":  # macOS fucking sucks
            return None  
    except:
        return None
def sparkline(data, max_value=100):
    # graph drawing 
    blocks = " ▁▂▃▄▅▆▇█"
    return "".join(
        blocks[min(int(x / max_value * (len(blocks) - 1)), len(blocks) - 1)] for x in data
    )
def create_table(data): # self explanatory table creation
    table = Table(title="Real-Time System Monitor", expand=True)
    table.add_column("Component", justify="center", style="cyan", no_wrap=True)
    table.add_column("Usage", justify="center", style="magenta")
    table.add_column("Graph", justify="center", style="green")
    # CPU 
    cpu_temp = f"{data['CPU']['Temp']} °C" if data['CPU']['Temp'] else "N/A"
    cpu_graph = sparkline(cpu_history)
    table.add_row("CPU", f"{data['CPU']['Usage']}% @ {data['CPU']['Freq']} MHz", cpu_graph)
    table.add_row("Cores", f"{data['CPU']['Cores']}", cpu_temp)
    # RAM 
    ram_usage = f"{data['RAM']['Used']:.2f} / {data['RAM']['Total']:.2f} GB ({data['RAM']['Usage']}%)"
    ram_graph = sparkline(ram_history)
    table.add_row("RAM", ram_usage, ram_graph)
    # ONLY WORKS AND ONLY WILL WORK WITH NVIDIA IF YOU HAVE INTEL OR AMD YOU CAN GO FUCK YOURSELF
    if data["GPU"]:
        gpu_graph = sparkline(gpu_history)
        table.add_row("GPU", f"{data['GPU']['Usage']}% ({data['GPU']['Name']})", gpu_graph)
        gpu_temp = f"{data['GPU']['Temp']} °C" if data["GPU"]["Temp"] else "N/A"
        table.add_row("GPU Temp", gpu_temp, "")
    else:
        table.add_row("GPU", "No GPU detected", "")
    return table
def main():
    with Live(refresh_per_second=1) as live:
        while True:
            data = get_system_info()
            cpu_history.append(data["CPU"]["Usage"])
            ram_history.append(data["RAM"]["Usage"])
            if data["GPU"]:
                gpu_history.append(data["GPU"]["Usage"])
            table = create_table(data)
            live.update(Panel(table, title="System Monitor"))
            time.sleep(1)  
if __name__ == "__main__":
    main()