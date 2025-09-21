
# Run

```
mpremote connect /dev/tty.usbmodem211301 run ./IRremote.py
```

# Free space on device

```
mpremote connect /dev/tty.usbmodem211301 exec "import os; s=os.statvfs('/'); total=s[0]*s[2]; free=s[0]*s[3]; print(f'Free: {free/1024/1024:.2f} MB out of {total/1024/1024:.2f} MB ({free/total*100:.1f}%)')"
```
