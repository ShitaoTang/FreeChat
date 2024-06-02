import curses
import threading
import time
import asyncio
import websockets
import json
import sys

stop_event = threading.Event()

def update_content(window, content_list):
    while not stop_event.is_set():
        window.erase()
        for i, line in enumerate(content_list):
            if i >= curses.LINES - 3:  # 保证不会超出窗口大小
                break
            # 使用颜色对显示用户名
            if ': ' in line:
                username, message = line.split(': ', 1)
                window.addstr(i, 0, username + ': ', curses.color_pair(1))
                window.addstr(i, len(username) + 2, message)
            else:
                window.addstr(i, 0, line)
        window.refresh()
        time.sleep(0.1)  # Update every 0.1 seconds

async def websocket_handler(uri, content_list):
    async with websockets.connect(uri) as websocket:
        while not stop_event.is_set():
            try:
                message = await websocket.recv()
                data = json.loads(message)
                if data['type'] == 'message':
                    content_list.append(data['username'] + ': ' + data['message'] + '\n')
            except websockets.ConnectionClosed:
                break

def input_box(stdscr, content_list, username):
    curses.echo()
    
    # 初始化颜色
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)  # 1是用户名颜色对

    # Setup the window for content display
    content_height = curses.LINES - 3
    content_window = curses.newwin(content_height, curses.COLS, 0, 0)
    content_window.scrollok(True)
    
    # Setup the window for input box
    input_box_window = curses.newwin(3, curses.COLS, curses.LINES - 3, 0)
    input_box_window.box()
    
    prompt = f"{username}: "
    input_box_window.addstr(1, 1, prompt, curses.color_pair(1))  # 设置用户名颜色
    input_box_window.refresh()
    
    # Calculate the starting position for user input
    start_x = len(prompt) + 1
    
    # Start thread for updating content display
    threading.Thread(target=update_content, args=(content_window, content_list), daemon=True).start()

    while True:
        # 确保光标在正确的位置并闪烁
        input_box_window.move(1, start_x)
        input_box_window.refresh()
        try:
            input_str = input_box_window.getstr(1, start_x, 100)
            input_decoded = input_str.decode('utf-8')
        except UnicodeDecodeError:
            continue  # 如果解码失败，跳过当前输入

        # Exit the loop if the user types ':q'
        if input_decoded.lower() == ':q':
            break

        # Send the user input to the WebSocket server
        asyncio.run(send_message(input_decoded, username))

        # Clear the input box after getting input
        input_box_window.clear()
        input_box_window.box()
        input_box_window.addstr(1, 1, prompt, curses.color_pair(1))  # 保持用户名颜色
        input_box_window.move(1, start_x)  # 确保光标在正确的位置
        input_box_window.refresh()

    # Stop the content update thread
    stop_event.set()

async def send_message(message, username):
    async with websockets.connect("ws://tstwiki.cn:8765") as websocket:
        data = json.dumps({"type": "message", "username": username, "message": message})
        await websocket.send(data)

def main(stdscr):
    content_list = []
    uri = "ws://tstwiki.cn:8765"

    # Default username
    username = "Anonymous"
    
    # Check if a username is passed as an argument
    if len(sys.argv) > 1:
        username = sys.argv[1]

    # Start websocket handler in a separate thread
    threading.Thread(target=lambda: asyncio.run(websocket_handler(uri, content_list)), daemon=True).start()

    input_box(stdscr, content_list, username)

if __name__ == "__main__":
    curses.wrapper(main)
