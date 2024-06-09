import curses
import threading
import time
import asyncio
import websockets
import json
import sys
from datetime import datetime
import psutil  # 用于获取系统信息

stop_event = threading.Event()
content_lock = threading.Lock()

def draw_borders(window, color_pair):
    '''
    绘制窗口边框
    
    Args:
        window: 窗口对象
        color_pair: 颜色对
    '''
    max_y, max_x = window.getmaxyx()
    window.attron(color_pair)
    window.border()
    window.attroff(color_pair)


def update_content(window, content_list):
    '''
    更新窗口内容
    
    Args:
        window: 窗口对象
        content_list: 内容列表
    '''
    window.erase()
    max_y, max_x = window.getmaxyx()
    with content_lock:
        if not content_list:
            draw_borders(window, curses.color_pair(5))
        for i, line in enumerate(content_list):
            if i >= max_y - 2:  # 保证不会超出窗口大小
                break
            # 使用颜色对显示时间戳和用户名
            if '] ' in line:
                timestamp, rest = line.split('] ', 1)
                username, message = rest.split(': ', 1)
                window.addstr(i + 1, 1, timestamp + "] ", curses.color_pair(2))
                window.addstr(i + 1, len(timestamp) + 3, username + ': ', curses.color_pair(1))
                window.addstr(i + 1, len(timestamp) + len(username) + 5, message[:max_x - len(timestamp) - len(username) - 7])
            else:
                window.addstr(i + 1, 1, line[:max_x - 2])
    draw_borders(window, curses.color_pair(5))
    window.refresh()


async def websocket_handler(uri, content_list, window):
    '''
    WebSocket处理程序，接收消息并更新内容显示
    
    Args:
        uri: WebSocket服务器地址
        content_list: 内容列表
        window: 窗口对象
    '''
    async with websockets.connect(uri) as websocket:
        while not stop_event.is_set():
            try:
                message = await websocket.recv()
                data = json.loads(message)
                if data['type'] == 'message':
                    timestamp = data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    with content_lock:
                        content_list.append(f"[{timestamp}] {data['username']}: {data['message']}\n")
                    # 更新内容显示
                    update_content(window, content_list)
            except websockets.ConnectionClosed:
                break


def input_box(stdscr, content_list, username):
    '''
    输入框处理程序，处理用户输入并发送消息
    
    Args:
        stdscr: 主屏幕对象
        content_list: 内容列表
        username: 用户名
    '''
    curses.echo()
    
    # 初始化颜色
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)  # 用户名颜色
    curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)   # 时间戳颜色
    curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLACK)  # 默认消息颜色
    curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)    # 表头颜色
    curses.init_pair(5, curses.COLOR_CYAN, curses.COLOR_BLACK)   # 边框颜色

    # 设置窗口尺寸
    height, width = stdscr.getmaxyx()
    chat_width = int(width * 0.6)
    sysinfo_width = width - chat_width
    
    # 设置内容显示窗口
    content_height = height - 3
    content_window = curses.newwin(content_height, chat_width, 0, 0)
    content_window.scrollok(True)
    draw_borders(content_window, curses.color_pair(5))  # 绘制聊天内容窗口的矩形框
    
    # 设置输入框窗口
    input_box_window = curses.newwin(3, chat_width, height - 3, 0)
    draw_borders(input_box_window, curses.color_pair(5))
    
    # 设置系统信息窗口
    sysinfo_window = curses.newwin(height, sysinfo_width, 0, chat_width)
    draw_borders(sysinfo_window, curses.color_pair(5))
    
    prompt = f"{username}: "
    input_box_window.addstr(1, 1, prompt, curses.color_pair(1))  # 设置用户名颜色
    input_box_window.refresh()
    
    # 计算用户输入的起始位置
    start_x = len(prompt) + 1
    
    # 启动更新内容显示的线程
    threading.Thread(target=lambda: asyncio.run(websocket_handler("ws://tstwiki.cn:8765", content_list, content_window)), daemon=True).start()
    
    # 启动更新系统信息显示的线程
    threading.Thread(target=update_sysinfo, args=(sysinfo_window,), daemon=True).start()

    while True:
        # 确保光标在正确的位置并闪烁
        input_box_window.move(1, start_x)
        input_box_window.refresh()
        try:
            input_str = input_box_window.getstr(1, start_x, 100)
            input_decoded = input_str.decode('utf-8')
        except UnicodeDecodeError:
            continue  # 如果解码失败，跳过当前输入

        # 如果用户输入 ':q'，退出循环
        if input_decoded.lower() == ':q':
            break

        # 发送用户输入到 WebSocket 服务器
        asyncio.run(send_message(input_decoded, username))

        # 获取输入后清空输入框
        input_box_window.clear()
        draw_borders(input_box_window, curses.color_pair(5))
        input_box_window.addstr(1, 1, prompt, curses.color_pair(1))  # 保持用户名颜色
        input_box_window.move(1, start_x)  # 确保光标在正确的位置
        input_box_window.refresh()

        # 每次发送新消息后更新内容显示
        update_content(content_window, content_list)

    # 停止内容更新线程
    stop_event.set()


async def send_message(message, username):
    '''
    发送消息到 WebSocket 服务器
    
    Args:
        message: 消息内容
        username: 用户名
    '''
    async with websockets.connect("ws://tstwiki.cn:8765") as websocket:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        data = json.dumps({"type": "message", "username": username, "message": message, "timestamp": timestamp})
        await websocket.send(data)


def update_sysinfo(window):
    '''
    更新系统信息窗口内容
    
    Args:
        window: 窗口对象
    '''
    while not stop_event.is_set():
        window.erase()
        draw_borders(window, curses.color_pair(5))
        window.addstr(1, 1, "System Information", curses.A_BOLD)
        window.addstr(3, 1, f"CPU Usage: {psutil.cpu_percent():.1f}%")
        window.addstr(4, 1, f"Memory Usage: {psutil.virtual_memory().percent:.1f}%")
        window.addstr(5, 1, f"Disk Usage: {psutil.disk_usage('/').percent:.1f}%")
        
        # 添加表头
        header = f"{'PID':<6} {'COMMAND':<15} {'CPU%':>6}  {'TIME':<8} {'MEM%':>5} {'STATE'}"
        window.addstr(7, 1, header, curses.color_pair(4))

        # 获取进程信息
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status', 'create_time']):
            processes.append(proc.info)

        # 根据CPU使用率排序
        processes = sorted(processes, key=lambda p: p['cpu_percent'], reverse=True)

        # 显示前10个进程
        max_y, max_x = window.getmaxyx()
        max_processes = min(len(processes), max_y - 8 - 1)  # 保证不会超出窗口大小
        for i in range(max_processes):
            proc = processes[i]
            pid = proc['pid']
            name = proc['name'][:15]
            cpu = f"{proc['cpu_percent']:.1f}"
            mem = f"{proc['memory_percent']:.1f}"
            status = proc['status']
            runtime = datetime.now() - datetime.fromtimestamp(proc['create_time'])

            days = runtime.days
            hours, remainder = divmod(runtime.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            hours += 24 * days
            runtime_str = f"{hours:02}:{minutes:02}:{seconds:02}"

            line = f"{pid:<6} {name:<15} {cpu:>6}  {runtime_str:<8} {mem:>5} {status}"
            window.addstr(8 + i, 1, line[:max_x - 2])

        window.refresh()
        time.sleep(1)


def main(stdscr):
    '''
    主函数，初始化并启动输入框
    
    Args:
        stdscr: 主屏幕对象
    '''
    content_list = []

    # 默认用户名
    username = "Anonymous"
    
    # 检查是否传入了用户名参数
    if len(sys.argv) > 1:
        username = sys.argv[1]

    input_box(stdscr, content_list, username)

if __name__ == "__main__":
    curses.wrapper(main)
