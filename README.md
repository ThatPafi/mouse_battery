# Logitech G502 hero X battery checker
Used with command output KDE plasma widget.
Supports error handling, verbose mode, logging and caching.  

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
There are 2 differents options for the same function. If there are timeout issues running the default one, switch with the commented allow some handling of the child process. 
