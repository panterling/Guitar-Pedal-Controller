import binascii

import usb.core
import usb.util

dev = usb.core.find(idVendor=0x0582, idProduct=0x01d6)

if dev is None:
    raise ValueError('Device not found')


for i in range(4):
    if dev.is_kernel_driver_active(i):
        dev.detach_kernel_driver(i)


#dev.set_configuration()
cfg = dev.get_active_configuration()


#a = dev[0][(0, 0)]
#b = dev[0][(1, 0)]
#c = dev[0][(2, 0)]
d = dev[0][(3, 0)]

bulkIn = d[1]
bulkOut = d[0]

# Has Endpoints
interfaceIdx = 3
alternateSetting = 0 # BULK
alternateSetting = 1 # Interrupt





# claim the device

usb.util.claim_interface(dev, interfaceIdx)
endpoint = dev[0][(interfaceIdx,0)]
endpointAlt = dev[0][(interfaceIdx,alternateSetting)]

collected = 0
attempts = 500000


def sendHexString(s):
    payload = bytearray.fromhex(s)
    print("Tx:: " + str(binascii.hexlify(bytearray(payload))))
    endpoint[0].write(payload)


def attemptToRead(ep = endpoint[1]):
    try:
        data = dev.read(ep.bEndpointAddress, ep.wMaxPacketSize)
        if sum(data) > 0:
            print("Rx:: " + str(binascii.hexlify(bytearray(data))))
            return data
    except usb.core.USBError as e:
        data = None
        if e.args == ('Operation timed out',):
            return None


##################################################
def selectUserPatchById(id):
    if id < 1 or id > 99:
        raise Exception("Invalid Patch Id: 1 - 99 only")

    hexValue = hex(id - 1)
    tailValue = hex(0x7f - (id - 1))

    hexValue = str(hexValue[2:]).rjust(2, "0")
    tailValue = str(tailValue[2:]).rjust(2, "0")

    sendHexString("04f041000400000004301200040100000400{}{}05f70000".format(hexValue, tailValue))
    attemptToRead()


def selectPermenantPatchById(id):
    if id < 1 or id > 99:
        raise Exception("Invalid Patch Id: 1 - 99 only")

    if id < 30:
        leadHex = hex(0)
        hexValue = hex(id + 99 - 1)
        tailValue = hex(0x7f - (id + 99 - 1))
    else:
        leadHex = hex(1)
        hexValue = hex((id - 29) + - 1)
        tailValue = hex(0x7e - (id - 30))

    leadHex = str(leadHex[2:]).rjust(2, "0")
    hexValue = str(hexValue[2:]).rjust(2, "0")
    tailValue = str(tailValue[2:]).rjust(2, "0")


    sendHexString("04f0410004000000043012000401000004{}{}{}05f70000".format(leadHex, hexValue, tailValue))
    attemptToRead()

def tunerOn():
    sendHexString("04f04100040000000430127f0400000207017ef7")
    attemptToRead()

def tunerOff():
    sendHexString("04f04100040000000430127f0400000207007ff7")
    attemptToRead()
    pass


def getPatchNames():
    patchDict = {}

    # User-Defined
    for i in range(99):
        hexValue = hex(i)
        tailValue = hex(96 - i) if i < 97 else hex(127 - (i - 97))

        hexValue = str(hexValue[2:]).rjust(2, "0")
        tailValue = str(tailValue[2:]).rjust(2, "0")

        sendHexString("04f04100040000000430111004{}0000040000000710{}f7".format(hexValue, tailValue))
        r = attemptToRead()
        patchName = "".join([chr(x) for x in r[17:len(r) - 2] if x not in [4, 7]])
        patchDict["U" + str(i + 1)] = patchName

    # Permenant
    for i in range(99):
        hexValue = hex(i)
        tailValue = hex(80 - i) if i < 81 else hex(127 - (i - 81))

        hexValue = str(hexValue[2:]).rjust(2, "0")
        tailValue = str(tailValue[2:]).rjust(2, "0")

        sendHexString("04f04100040000000430112004{}0000040000000710{}f7".format(hexValue, tailValue))
        r = attemptToRead()
        patchName = "".join([chr(x) for x in r[17:len(r) - 2] if x not in [4, 7]])
        patchDict["P" + str(i + 1)] = patchName

    return patchDict


##################################################






# First
sendHexString("04f07e7f070601f7")
attemptToRead()

# Second
sendHexString("04f07e00070601f7")
attemptToRead()

# Third
sendHexString("04f04100040000000430117f0400000004000000070100f7")
attemptToRead()

# Fourth
sendHexString("04f04100040000000430127f0400000107017ff7")
attemptToRead()

# Fifth
sendHexString("04f0410004000000043011100400000004000000071060f7")
attemptToRead()


##################
# Turn on OD/DS
##################
#sendHexString("04f04100040000000430126004000030070070f7") # OS/DS > Off
#sendHexString("04f0410004000000043012600400003007016ff7")  # OS/DS > On
#attemptToRead()


##################
# Advance the patch by 1
##################
#sendHexString("") # Next
#attemptToRead()

##################
# Advance to a patch by ID
##################
#selectUserPatchById(1)
#selectUserPatchById(99)
#selectPermenantPatchById(1)
#selectPermenantPatchById(99)


#tunerOn()
#tunerOff()

#setPatchLevel()


patchDict = getPatchNames()

i = 0

while collected < attempts :

    for ep in [endpoint[0], endpoint[1], endpointAlt[0], endpointAlt[1]]:
        try:
            data = dev.read(ep.bEndpointAddress, ep.wMaxPacketSize)
            if sum(data) > 0 :
                print("Rx:: " + str(binascii.hexlify(bytearray(data))))
        except usb.core.USBError as e:
            data = None
            if e.args == ('Operation timed out',):
                continue

    collected += 1


# release the device
usb.util.release_interface(dev, interfaceIdx)

print("ok")