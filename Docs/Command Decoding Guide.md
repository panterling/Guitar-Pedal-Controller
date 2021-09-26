# How to sniff/decode a command from the GT-1

## Example
 - A script has been written to ease the process of decoding a command:
    - `Pedal/Dev__ProtocolSniffer.py`
    
 - The process is (you are guided by the script):
   - It inits the device and gets the current state of all parameters
   - You are asked for the 'command name' - not essential, just a convenience
   - You're asked to `Move to lowest value` - turn the dial/buttons to the lowest possible value
   - It re-reads the state of all parameters internally
   - You're asked to `Move to highest value` - turn the dial/buttons to the highest possible value
   - It re-reads the state of all parameters internally - looking for changing 'values'
   - ...TODO...
    
   