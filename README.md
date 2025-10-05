# Kompressori
This is an app for compressing videos to a desired size, by calculating the approximate file size using information about the video, using ffmpeg and PySide6 for the front-end. This was made with ChatGPT, so there's probably very idiotic stuff here.
## Dependencies

To run the app, you need to have ffmpeg installed and in your PATH, as it's essentially just a front-end for it. On Windows you have to manually install and add ffmpeg to your path. You also need python to test and build it. 
## Development and building

To build the application, just run `makepkg -si` in the root (requires Arch-based distro)  
  
For other distros, you can create a venv using the requirements.txt and using pyinstaller create a binary application.  
1. Create venv `python3 -m venv venv`  
2. Activate it `source venv/bin/activate` or on Windows `venv/Scripts/activate`  
3. Install requirements `pip install -r requirements.txt`  
4. (Linux) Run `pyinstaller --noconfirm --onefile --windowed --icon=kompressori.png kompressori.py`  
5. (Windows) Run `pyinstaller --noconfirm --onefile --windowed --icon=kompressori.ico --add-data "kompressori.png;." kompressori.py`  
5. The app can be found under `./dist/kompressori`  

To test the app, run `python3 kompressori.py` in the directory
