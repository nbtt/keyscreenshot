import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox
from pynput import keyboard
from PIL import Image, ImageTk, ImageGrab
import ctypes
from io import BytesIO
import win32clipboard
import json

class MainApplication:
    def __init__(self, master: tk.Tk):
        self.master = master
        # Load key data
        with open("config.json") as file:
            data = json.load(file)
            self.gird_key_horiz = data["horiz.key"]
            self.grid_key_vert = data["vert.key"]
            self.key_relative_raw = data["key"]

            # Directions and their corresponding movements in x-axis and y-axis
            direction_map = {"left" : (-1, 0), "down" : (0, 1), "up" : (0, -1), "right" : (1, 0),
                "t.left" : (-1, -1), "b.left" : (-1, 1), "b.right" : (1, 1), "t.right" : (1, -1)}

            self.key_relative = {}
            for key in self.key_relative_raw:
                self.key_relative[key] = direction_map[self.key_relative_raw[key]]

        # GUI of application
        self.width = root.winfo_screenwidth()
        self.height = root.winfo_screenheight()
        self.canvas = tk.Canvas(self.master, width=self.width, height=self.height)
        self.canvas.pack()
        # Image place holder
        self.image = self.canvas.create_image(0, 0, anchor=tk.NW)
        self.image_raw = None
        self.image_data = None
        # Image cover (i.e. a nearly transparent layer on top of the image)
        self.cover_img = self.create_cover_img(0, 0, self.width, self.height, fill="black", alpha=.5)
        self.cover = self.canvas.create_image(0, 0, image=self.cover_img, anchor=tk.NW)
        # Cropped image place holder
        self.image_cropped = self.canvas.create_image(0, 0, state='hidden', anchor=tk.NW)
        self.image_cropped_raw = None
        self.image_cropped_data = None

        # Draw grid
        self.grid_state = True # True indicates grid is shown, False indicates grid is hidden
        self.num_grid_horiz = 7
        self.num_grid_vert = 10
        self.grid_gap_horiz = self.height // (self.num_grid_horiz + 1)
        self.grid_gap_vert = self.width // (self.num_grid_vert + 1)

        # Store line and text id for show/hide function later
        self.grid_items = []
        self.text_items = []
        # Draw vertical line
        for line_id in range(1, self.num_grid_vert + 1):
            line_x = line_id*self.grid_gap_vert
            current_line = self.canvas.create_line(line_x, 0, line_x, self.height, fill="white")
            # current_text = self.canvas.create_text(line_x + 10, 0, anchor=tk.NW, text=self.grid_key_vert[line_id - 1])
            current_text = ttk.Label(self.canvas, anchor=tk.W, text=self.grid_key_vert[line_id - 1], font=("bold"))
            current_text.place(x=line_x + 10, y=0)
            current_text._place_info = current_text.place_info()
            self.grid_items.append(current_line)
            # self.grid_items.append(current_text)
            self.text_items.append(current_text)

        # Draw horizontal line
        for line_id in range(1, self.num_grid_horiz + 1):
            line_y = line_id*self.grid_gap_horiz
            current_line = self.canvas.create_line(0, line_y, self.width, line_y, fill="white")
            # current_text = self.canvas.create_text(10, line_y, anchor=tk.SW, text=self.gird_key_horiz[line_id - 1])
            current_text = ttk.Label(self.canvas, anchor=tk.W, text=self.gird_key_horiz[line_id - 1], font=("bold"))
            current_text.place(x=10, y=line_y + current_text.winfo_height())
            current_text._place_info = current_text.place_info()
            self.grid_items.append(current_line)
            # self.grid_items.append(current_text)
            self.text_items.append(current_text)

        # Top-left and bottom-right points (start point and end point) for cropping
        self.start_point_orig = [self.grid_gap_vert, self.grid_gap_horiz]
        self.end_point_orig = [self.grid_gap_vert, self.grid_gap_horiz]
        self.start_point = [self.grid_gap_vert, self.grid_gap_horiz]
        self.end_point = [self.grid_gap_vert, self.grid_gap_horiz]

        # Draw start_point end end_point
        self.point_img_len = min(self.grid_gap_vert, self.grid_gap_horiz) // 10
        self.start_point_img = self.create_point_img(self.start_point)
        self.end_point_img = self.create_point_img(self.end_point)
        self.hide_end_point()

        self.point_state = True # True indicates start_point, False indicates end_point

        # Relative move distance. `1 distance` ~ 1*self.point_img_len
        self.move_distance = 1

        self.bind_key()

        self.master.withdraw() # Hide

    def bind_key(self):
        # Hold space to hide_grid, release to show_grid
        self.master.bind_all("<KeyPress-space>", func=self.hide_grid)
        self.master.bind_all("<KeyRelease-space>", func=self.show_grid)
        
        # Enter when finishing adjust start_point, Enter again when finishing adjust end_point
        self.master.bind_all("<Return>", func=self.change_focused_point)

        # Esc to hide the application
        self.master.bind_all("<Escape>", func=self.reset)

        # Bind move point on grid events
        for i, key in enumerate(self.gird_key_horiz):
            self.master.bind_all(key, func=self.jump_point(jump_y=(i + 1)*self.grid_gap_horiz))
        for i, key in enumerate(self.grid_key_vert):
            self.master.bind_all(key, func=self.jump_point(jump_x=(i + 1)*self.grid_gap_vert))

        # Bind relative move to current position events
        for key in self.key_relative.keys():
            self.master.bind_all(key, func=self.jump_point_relative(*self.key_relative[key]))

        # Bind key 1 -> 9 to change self.move_distance event
        for key in range(ord('1'), ord('9') + 1):
            self.master.bind_all(chr(key), func=self.set_move_distance(key - ord('0')))

    # Hide the application and reset the application status
    def reset(self, e=None):
        self.master.withdraw()
        self.start_point = list.copy(self.start_point_orig)
        self.end_point = list.copy(self.end_point_orig)
        self.set_point_img(self.start_point, self.start_point_img)
        self.set_point_img(self.end_point, self.end_point_img)
        self.move_distance = 1
        self.canvas.itemconfig(self.image_cropped, state="hidden")

    def create_cover_img(self, x1, y1, x2, y2, **kwargs):
        if 'alpha' in kwargs:
            alpha = int(kwargs.pop('alpha') * 255)
            fill = kwargs.pop('fill')
            fill = root.winfo_rgb(fill) + (alpha,)
            image = Image.new('RGBA', (x2-x1, y2-y1), fill)
            return ImageTk.PhotoImage(image)
        return None

    def show_grid(self, e):
        if not self.grid_state:
            for item in self.grid_items:
                self.canvas.itemconfig(item, state='normal')
            for item in self.text_items:
                item.place(**item._place_info)
            self.grid_state = True

    def hide_grid(self, e):
        if self.grid_state:
            for item in self.grid_items:
                self.canvas.itemconfig(item, state='hidden')
            for item in self.text_items:
                item.place_forget()
            self.grid_state = False

    # Create an image to represent start_point/end_point
    # Draw 2 lines whose intersection are their midpoints and also start_point/end_point
    def create_point_img(self, point):
        horiz_line = self.canvas.create_line(point[0] - self.point_img_len, point[1],
            point[0] + self.point_img_len, point[1], fill='white', width=3)
        vert_line = self.canvas.create_line(point[0], point[1] - self.point_img_len,
            point[0], point[1] + self.point_img_len, fill='white', width=3)
        # diag_line1 = self.canvas.create_line(point[0] - self.point_img_len//2, point[1] - self.point_img_len//2,
        #     point[0] + self.point_img_len//2, point[1] + self.point_img_len//2, fill='white', width=3)
        # diag_line2 = self.canvas.create_line(point[0] + self.point_img_len//2, point[1] - self.point_img_len//2,
        #     point[0] - self.point_img_len//2, point[1] + self.point_img_len//2, fill='white', width=3)
        return [horiz_line, vert_line]

    def set_point_img(self, point, point_img):
        self.canvas.coords(point_img[0], point[0] - self.point_img_len, point[1],
            point[0] + self.point_img_len, point[1])
        self.canvas.coords(point_img[1], point[0], point[1] - self.point_img_len,
            point[0], point[1] + self.point_img_len)
        # self.canvas.coords(point_img[2], point[0] - self.point_img_len//2, point[1] - self.point_img_len//2,
        #     point[0] + self.point_img_len//2, point[1] + self.point_img_len//2)
        # self.canvas.coords(point_img[3], point[0] + self.point_img_len//2, point[1] - self.point_img_len//2,
        #     point[0] - self.point_img_len//2, point[1] + self.point_img_len//2)

    def show_end_point(self):
        for line in self.end_point_img:
            self.canvas.itemconfig(line, state='normal')

    def hide_end_point(self):
        for line in self.end_point_img:
            self.canvas.itemconfig(line, state='hidden')

    # If current focused point is start_point then change it to end_point
    # else save the image and hide the application
    def change_focused_point(self, e):
        if self.point_state:
            self.show_end_point()
            self.canvas.coords(self.image_cropped, self.start_point[0], self.start_point[1])
            self.point_state = False
            self.canvas.itemconfig(self.image_cropped, state="normal")
            self.update_image()
        else:
            if self.start_point[0] >= self.end_point[0] or self.start_point[1] >= self.end_point[1]: # Cannot generate image
                return
            self.point_state = True
            # Save image
            output = BytesIO()
            self.image_cropped_raw.convert("RGB").save(output, "BMP")
            data = output.getvalue()[14:]
            output.close()
            self.send_to_clipboard(win32clipboard.CF_DIB, data)
            # Reset
            self.reset()

    def send_to_clipboard(self, clip_type, data):
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(clip_type, data)
        win32clipboard.CloseClipboard()

    # Return a function that jump to somewhere in the grid
    def jump_point(self, jump_x=None, jump_y=None):
        if jump_x is None and jump_y is None:
            return None

        def jump(e):
            if self.point_state:
                point = self.start_point
                point_img = self.start_point_img
            else:
                point = self.end_point
                point_img = self.end_point_img
            if jump_x is not None:
                point[0] = jump_x
            if jump_y is not None:
                point[1] = jump_y
            self.set_point_img(point, point_img)
            self.update_image()

        return jump

    # Return a function that jump from point (x, y) to (x + more_x, y + more_y)
    def jump_point_relative(self, more_x, more_y):
        if more_x is None and more_y is None:
            return None
        
        def jump(e):
            if self.point_state:
                point = self.start_point
                point_img = self.start_point_img
            else:
                point = self.end_point
                point_img = self.end_point_img
            point[0] += more_x * self.move_distance * self.point_img_len
            point[1] += more_y * self.move_distance * self.point_img_len
            # Make sure they are in the screen
            point[0] = max(point[0], 0)
            point[0] = min(point[0], self.width)
            point[1] = max(point[1], 0)
            point[1] = min(point[1], self.height)

            self.set_point_img(point, point_img)
            self.update_image()

        return jump

    def set_move_distance(self, value):
        def set_move(e):
            self.move_distance = value
        return set_move

    # Update the cropped image
    # If start_point is not top-left point and end_point is not bottom-right point then change them to the right one.
    def update_image(self):
        if self.image_raw is not None and not self.point_state: # currently changing end_point
            real_start = [min(self.start_point[0], self.end_point[0]), min(self.start_point[1], self.end_point[1])]
            real_end = [max(self.start_point[0], self.end_point[0]), max(self.start_point[1], self.end_point[1])]
            self.image_cropped_raw = self.image_raw.crop(tuple([*real_start, *real_end]))
            self.image_cropped_data = ImageTk.PhotoImage(self.image_cropped_raw)
            self.canvas.coords(self.image_cropped, *real_start)
            self.canvas.itemconfig(self.image_cropped, image=self.image_cropped_data)

    def set_image(self, img):
        self.image_raw = img
        self.image_data = ImageTk.PhotoImage(self.image_raw)
        self.canvas.itemconfig(self.image, image=self.image_data)

    def size(self):
        return (self.width, self.height)

class HotKey:
    def __init__(self, master, app):
        self.master = master
        self.app = app
        self.hotkey = keyboard.GlobalHotKeys({
        '<cmd>+<alt>+w': self.on_closing,
        '<ctrl>+<shift>+<alt>+x': self.on_closing,
        '<ctrl>+<alt>+z': self.on_activate_app,
        '<cmd>+<ctrl>+<shift>+z': self.on_activate_app
        })

    def on_activate_app(self):
        image = ImageGrab.grab((0, 0, *self.app.size()))
        self.master.lift()
        self.app.set_image(image)
        self.master.deiconify()
        self.master.lift()
        self.master.after(1, lambda: self.master.focus_force()) # Focus

    def on_closing(self):
        exit_app = tk.messagebox.askokcancel("Exit keyscreenshot?", "Do you want to exit keyscreenshot?", icon="warning")
        if exit_app:
            self.master.destroy()
    
    def start(self):
        self.hotkey.start()

if __name__ == "__main__":
    # Enable Process DPI Awareness
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2) # if your windows version >= 8.1
    except:
        ctypes.windll.user32.SetProcessDPIAware() # win 8.0 or less 
    
    root = tk.Tk()
    root.title = "KeyScreenshot"
    root.overrideredirect(True) # Hide icon in taskbar

    main_app = MainApplication(root)
    # Wait for hotkey
    hotkey = HotKey(root, main_app)
    hotkey.start()
    root.mainloop()