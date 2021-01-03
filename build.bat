python -O -m PyInstaller --noconfirm --version-file .\main_module.version.txt --hidden-import=engineio.async_drivers.aiohttp .\main_module.py
