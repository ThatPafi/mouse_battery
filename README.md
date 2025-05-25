# Logitech G502 hero X battery checker
Used with command output KDE plasma widget.  
Supports error handling, verbose mode, logging and caching.  

Calls Solaar. This script does a very simple ``` match = re.search(r'Battery:\s+(\d+)%' ```, which means it only works if Solaar returns only 1 device battery. If you need it to handle multiple devices, it should be easy to modify. 

## Usage  
```
mouse_battery.py [-h] [--notify] [--ttl TTL] [--verbose {DEBUG,INFO,WARNING,ERROR}] [--log-file [LOG_FILE]]

Monitor Logitech mouse battery via Solaar.

options:
  -h, --help            show this help message and exit
  --notify              Enable critical battery notifications
  --ttl TTL             Cache TTL in hours (default: 24)
  --verbose {DEBUG,INFO,WARNING,ERROR}
                        Set log level
  --log-file [LOG_FILE]
                        Optional log file path (defaults to ~/.cache/mouse_battery.log if used without value)
```
## Alternative run_solaar_show()
There are 2 differents options for the same function. If there are timeout issues running the default one, switching to the commented one allow some handling of the child process. For more information check difference between ```subprocess.check_output()``` and ```subprocess.run()```.
