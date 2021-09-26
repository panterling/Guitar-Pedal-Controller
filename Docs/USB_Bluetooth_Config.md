## USB/Bluetooth Setup
Run this prior to starting any application processes that require the Bluetooth service:
`sudo hciconfig hci0 piscan`

Alternatively, add the following line to `/lib/systemd/system/bluetooth.service` to ensure its state every time the RPi boots:
 - `ExecStartPost=/bin/hciconfig hci0 piscan`

## Troubleshooting

 - **Issue**: `usb.core.USBError: [Errno 13] Access denied (insufficient permissions)`
     - **Fix**: Python needs to execute with `sudo` - Within PyCharm, set the interpretor to execute with these privileges 