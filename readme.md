# Keyscreenshot
An application that take the screenshot only by keyboard.
## Quick start
- Download `keyscreenshot.pyw` and `config.json`
- Install python and make sure these packages are installed: `tkinter`, `PIL`, `pynput`, `pywin32`.
- Open `keyscreenshot.pyw`.
- To start taking screenshot. Either press `cmd + ctrl + shift + z` or `ctrl + alt + z`.
    - Use the key labeled near the line of the grid to jump to them.
        - For example, by default, jump to the last horizontal line on the bottom by press `m`.
    - By default, press `h`, `j`, `k`, `l` to move to the left, down, up, right respectively.
    - By default, press `x`, `c`, `v`, `b` to move to the top-left, bottom-left, bottom-right and top-right, respectively.
    - Press number `1` to `9` to change the move distance.
- We need to place 2 opposite points of a rectangle to specify the screenshot region. After placing 1 of these 2 points properly, press `Enter` to place the other one.
- After place 2 points properly, press `Enter` to finish. The screenshot is saved on your clipboard.
- To cancel to screenshot taking process, press `Esc`.
- To exit the application, press `cmd + alt + w` or `ctrl + shift + alt + x`.
## Configuration
Currently we can only change the keyboard binding for moves. Edit `config.json`:
- `horiz.key` is the key to jump to 7 horizontal line of the grid.
- `vert.key` is the key to jump to 10 vertical line of the grid.
- `key` is the key to move around.
    - `up`, `down`, `left`, `right` is the up, down, left, right move, respectively.
    - `t.left`, `b.left`, `b.right`, `t.right` is the top-left, bottom-left, bottom-right, top-right move, respectively.
## Notes
- `cmd` is the Windows key on Windows keyboard, the command key on Apple keyboard.
- We currently support exactly 7 horizontal line and 10 vertical line. If `config.json` is not properly edited, the program will crash, so do not remove any fields, just edit them.
- This is an beta version so there may be some errors. Also, there are no way to know if the program is opened properly. Users can check by press `cmd + ctrl + shift + z` or `ctrl + alt + z`.
- If there are an error, please close all apps that use python (likes IDE) and close python task on Windows Task Manager to forcibly exit the application.