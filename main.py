import platform
import psutil
import subprocess
import sys
import tkinter as tk
from tkinter import scrolledtext, messagebox
import tkinter.font as tkFont


# Hardware Information Functions (Windows Only)

def get_cpu_info():
    try:
        import cpuinfo
    except ImportError:
        return "Error: Install 'py-cpuinfo' (pip install py-cpuinfo)"
    info = cpuinfo.get_cpu_info()
    brand = info.get('brand_raw', 'Unknown CPU')
    physical_cores = psutil.cpu_count(logical=False)
    logical_cores = psutil.cpu_count(logical=True)
    return f"{brand}\nCores: {physical_cores}, Threads: {logical_cores}"


def get_motherboard_info():
    try:
        import wmi  # Import locally
    except ImportError:
        return "Error: Install 'wmi' (pip install WMI)"
    c = wmi.WMI()
    for board in c.Win32_BaseBoard():
        return board.Product
    return "Motherboard info not found"


def get_ram_info():
    total_ram = psutil.virtual_memory().total
    total_ram_gb = total_ram / (1024 ** 3)
    sticks_info = []
    try:
        import wmi  # Import locally
    except ImportError:
        return total_ram_gb, ["Error: Install WMI (pip install WMI)"]
    c = wmi.WMI()
    for stick in c.Win32_PhysicalMemory():
        capacity_gb = float(stick.Capacity) / (1024 ** 3) if stick.Capacity else 0
        speed = stick.Speed if stick.Speed else "Unknown"
        sticks_info.append(f"Capacity: {capacity_gb:.2f} GB, Speed: {speed} MHz")
    return total_ram_gb, sticks_info


def get_gpu_info():
    try:
        import wmi  # Import locally
    except ImportError:
        return "Error: Install wmi (pip install WMI)"
    c = wmi.WMI()
    gpus = c.Win32_VideoController()
    gpu_names = [gpu.Name for gpu in gpus]
    return ", ".join(gpu_names) if gpu_names else "No GPU found"


def get_storage_info():
    """
    Retrieves physical disk drive information using the Windows Storage namespace.
    This queries the MSFT_PhysicalDisk class to get the media type (SSD/HDD) and size.
    """
    try:
        import wmi
        storage_info = {}
        c = wmi.WMI(namespace="root\\Microsoft\\Windows\\Storage")
        for disk in c.MSFT_PhysicalDisk():
            friendly_name = disk.FriendlyName.strip() if disk.FriendlyName else disk.DeviceId
            media_type = disk.MediaType
            if media_type == 4:
                media = "SSD"
            elif media_type == 3:
                media = "HDD"
            else:
                media = "Unknown"
            try:
                size_gb = float(disk.Size) / (1024 ** 3)
            except Exception:
                size_gb = 0
            storage_info[friendly_name] = f"{size_gb:.2f} GB ({media})"
        return storage_info
    except Exception as e:
        return {"Error": str(e)}


def gather_system_info():
    sys_info = {}
    sys_info["CPU"] = get_cpu_info()
    sys_info["Motherboard"] = get_motherboard_info()
    total_ram, sticks = get_ram_info()
    sys_info["RAM"] = {"total": total_ram, "sticks": sticks}
    sys_info["GPU"] = get_gpu_info()
    sys_info["Storage"] = get_storage_info()
    return sys_info


# UI Functions

def create_boxed_ui():
    window = tk.Tk()
    window.title("System Hardware Info - Dark Mode")
    # Maximize the window
    window.state("zoomed")

    # Determine screen resolution and compute a scale factor.
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    baseline_width = 1920
    baseline_height = 1080
    scale = min(screen_width / baseline_width, screen_height / baseline_height)

    # Define dynamic fonts based on the scaling factor.
    header_font = tkFont.Font(family="Comic Sans MS", size=int(20 * scale), weight="bold")
    label_font = tkFont.Font(family="Comic Sans MS", size=int(14 * scale))

    # Define colors
    bg_color = "#2e2e2e"
    box_bg = "#3c3c3c"
    fg_color = "#ffffff"

    title_colors = {
        "CPU": "#1abc9c",
        "Motherboard": "#3498db",
        "RAM": "#9b59b6",
        "GPU": "#e74c3c",
        "Storage": "#f1c40f"
    }

    window.configure(bg=bg_color)

    header = tk.Label(window, text="System Hardware Information", bg=bg_color, fg=fg_color, font=header_font)
    header.grid(row=0, column=0, columnspan=2, pady=(int(10 * scale), int(20 * scale)))

    sys_info = gather_system_info()

    def create_box(parent, title, content, row, column):
        box = tk.LabelFrame(parent, text=title, bg=box_bg, fg=title_colors.get(title, fg_color),
                            font=label_font, bd=2, relief="groove", labelanchor="n")
        box.grid(row=row, column=column, padx=int(10 * scale), pady=int(10 * scale), sticky="nsew")

        if title == "RAM":
            total_ram = content["total"]
            sticks_list = content["sticks"]
            total_label = tk.Label(box, text=f"Total: {total_ram:.2f} GB", bg=box_bg, fg=fg_color, font=label_font)
            total_label.pack(padx=int(10 * scale), pady=int(5 * scale))
            sticks_frame = tk.Frame(box, bg=box_bg)
            sticks_frame.pack(padx=int(10 * scale), pady=int(5 * scale), fill="x", expand=True)
            for stick_info in sticks_list:
                mini_box = tk.LabelFrame(sticks_frame, bg=box_bg, fg=fg_color, font=label_font,
                                         bd=1, relief="ridge")
                mini_box.pack(side="top", padx=int(5 * scale), pady=int(5 * scale), fill="x", expand=True)
                stick_label = tk.Label(mini_box, text=stick_info, bg=box_bg, fg=fg_color, font=label_font,
                                       wraplength=int(600 * scale), justify="left")
                stick_label.pack(padx=int(5 * scale), pady=int(5 * scale))
        elif title == "Storage":
            storage_frame = tk.Frame(box, bg=box_bg)
            storage_frame.pack(padx=int(10 * scale), pady=int(10 * scale), fill="both", expand=True)
            for idx, (disk, info_str) in enumerate(content.items()):
                row_idx = idx // 3
                col_idx = idx % 3
                mini_box = tk.LabelFrame(storage_frame, text=disk, bg=box_bg,
                                         fg=title_colors.get("Storage", fg_color), font=label_font,
                                         bd=1, relief="ridge", labelanchor="n")
                mini_box.grid(row=row_idx, column=col_idx, padx=int(5 * scale), pady=int(5 * scale), sticky="nsew")
                part_label = tk.Label(mini_box, text=info_str, bg=box_bg, fg=fg_color, font=label_font,
                                      wraplength=int(150 * scale), justify="left")
                part_label.pack(padx=int(5 * scale), pady=int(5 * scale))
            for col in range(3):
                storage_frame.grid_columnconfigure(col, weight=1)
        else:
            content_label = tk.Label(box, text=content, bg=box_bg, fg=fg_color, font=label_font,
                                     wraplength=int(300 * scale), justify="left")
            content_label.pack(padx=int(10 * scale), pady=int(10 * scale))
        return box

    create_box(window, "CPU", sys_info["CPU"], row=1, column=0)
    create_box(window, "Motherboard", sys_info["Motherboard"], row=1, column=1)
    create_box(window, "RAM", sys_info["RAM"], row=2, column=0)
    create_box(window, "GPU", sys_info["GPU"], row=2, column=1)
    create_box(window, "Storage", sys_info["Storage"], row=3, column=0)

    window.grid_columnconfigure(0, weight=1)
    window.grid_columnconfigure(1, weight=1)

    window.mainloop()


def main():
    create_boxed_ui()


if __name__ == "__main__":
    import multiprocessing

    multiprocessing.freeze_support()
    main()
