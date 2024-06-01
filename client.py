import curses
import threading
import time

def update_content(window, content_list, stop_event):
    while not stop_event.is_set():
        window.erase()
        for i, line in enumerate(content_list):
            if i >= curses.LINES - 3:  # 保证不会超出窗口大小
                break
            window.addstr(i, 0, line)
        window.refresh()
        time.sleep(0.1)  # Update every 0.1 seconds

def input_box(stdscr):
    curses.echo()
    
    # Setup the window for content display
    content_height = curses.LINES - 3
    content_window = curses.newwin(content_height, curses.COLS, 0, 0)
    content_window.scrollok(True)
    
    # Setup the window for input box
    input_box_window = curses.newwin(3, curses.COLS, curses.LINES - 3, 0)
    input_box_window.box()
    input_box_window.addstr(1, 1, "Input: ")
    input_box_window.refresh()
    
    # List to store user inputs
    content_list = []

    # Event to stop the thread
    stop_event = threading.Event()
    
    # Start thread for updating content display
    threading.Thread(target=update_content, args=(content_window, content_list, stop_event), daemon=True).start()
    
    while True:
        # Get input from the user
        input_str = input_box_window.getstr(1, 8, 100)
        input_decoded = input_str.decode('utf-8')

        # Exit the loop if the user types ':q'
        if input_decoded.lower() == ':q':
            break

        # Append user input to the content list
        content_list.append(input_decoded + '\n')

        # Clear the input box after getting input
        input_box_window.clear()
        input_box_window.box()
        input_box_window.addstr(1, 1, "Input: ")
        input_box_window.refresh()

    # Stop the content update thread
    stop_event.set()

def main():
    curses.wrapper(input_box)

if __name__ == "__main__":
    main()