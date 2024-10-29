import cv2
import numpy as np
import time
import threading
import mss
import pygetwindow as gw
from pynput import keyboard
from pynput.mouse import Button, Controller

# Флаг для зупинки та запуску скрипта
running = False
mouse = Controller()

# Швидкість руху миші для швидкого натискання
mouse_speed = 2 

# Діапазон кольорів для пошуку оранжевих об’єктів
orange_lower = np.array([5, 150, 150])
orange_upper = np.array([15, 255, 255])

# Змінна для зберігання вибраного вікна
selected_window = None

def capture_screen(region=None):
    """Захоплює скріншот екрану або частини екрана."""
    with mss.mss() as sct:
        monitor = sct.monitors[1] if region is None else {"top": region[1], "left": region[0], "width": region[2], "height": region[3]}
        screenshot = sct.grab(monitor)
        img = np.array(screenshot)
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

def list_open_windows():
    """Повертає список усіх відкритих вікон з номерами."""
    windows = gw.getAllTitles()
    window_titles = [title for title in windows if title.strip()]
    print("Available Windows:")
    for i, title in enumerate(window_titles):
        print(f"{i + 1}. {title}")
    return window_titles

def select_window_by_index(index):
    """Вибирає вікно за індексом зі списку."""
    global selected_window
    windows = [w for w in gw.getAllTitles() if w.strip()]
    if 0 <= index < len(windows):
        selected_window = gw.getWindowsWithTitle(windows[index])[0]
        print(f"Selected window: {selected_window.title}")
    else:
        print("Invalid window index")

def get_selected_window_region():
    """Отримує координати вибраного вікна."""
    if selected_window is not None:
        return (selected_window.left, selected_window.top, selected_window.width, selected_window.height)
    else:
        print("No window selected!")
        return None

def find_orange_objects(frame):
    """Функція для пошуку оранжевих об'єктів на основі кольору."""
    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv_frame, orange_lower, orange_upper)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    centers = []
    for contour in contours:
        if cv2.contourArea(contour) > 100:
            M = cv2.moments(contour)
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                centers.append((cX, cY))
    return centers

def smooth_move_to(x, y, steps=mouse_speed):
    """Функція швидкого руху мишки до заданих координат."""
    current_pos = mouse.position
    step_x = (x - current_pos[0]) / steps
    step_y = (y - current_pos[1]) / steps
    
    for i in range(steps):
        mouse.position = (current_pos[0] + step_x * i, current_pos[1] + step_y * i)
        time.sleep(0.005)  # Мінімальна затримка для швидшого руху

def auto_click():
    """Основна функція автоматичного клікування."""
    global running
    while running:
        region = get_selected_window_region() if selected_window else None
        frame = capture_screen(region)
        
        if frame is not None:
            orange_objects = find_orange_objects(frame)
            for (x, y) in orange_objects:
                smooth_move_to(x, y, steps=mouse_speed)
                mouse.click(Button.left, 1)
        time.sleep(0.01)  # Мінімальна затримка між циклами для максимальної продуктивності

def start_auto_click():
    """Функція для старту автоматичного клікування."""
    global running
    if not running:
        running = True
        threading.Thread(target=auto_click).start()

def stop_auto_click():
    """Функція для зупинки автоматичного клікування."""
    global running
    running = False

def on_press(key):
    """Обробка натискання клавіш для управління скриптом."""
    try:
        # Підтримка різних розкладок для 's' (старт) і 'q' (стоп)
        if key.char.lower() in ['s', 'ы', 'і']:  # 's' в англійській, російській, українській розкладках
            start_auto_click()
        elif key.char.lower() in ['q', 'й']:  # 'q' в англійській та російській розкладках
            stop_auto_click()
        elif key.char.lower() == 'e':  # 'e' для вибору вікна
            window_titles = list_open_windows()
            index = int(input("Enter window number to select: ")) - 1
            select_window_by_index(index)
    except AttributeError:
        pass

# Запуск слухача клавіатури в окремому потоці
def start_keyboard_listener():
    listener = keyboard.Listener(on_press=on_press)
    listener.start()

# Основна частина програми
if __name__ == "__main__":
    print("Press 's' to start, 'q' to stop, 'e' to list and select window")
    
    # Запуск слухача клавіатури
    keyboard_thread = threading.Thread(target=start_keyboard_listener)
    keyboard_thread.start()

    # Безкінечний цикл, поки працює програма
    while True:
        time.sleep(1)
