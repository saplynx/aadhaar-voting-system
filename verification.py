import json
import time
import sys
import serial
from adafruit_fingerprint import AdafruitFingerprint
from adafruit_fingerprint.responses import *
import fingerprint
import config


def get_template():
    # Attempt to connect to serial port
    try:
        #port = '/dev/ttyUSB0'  # USB TTL converter port
        port = 'COM11'
        baud_rate = '57600'
        serial_port = serial.Serial(port, baud_rate)
    except Exception as e:
        print(e)
        sys.exit()

    # Initialize sensor library with serial port connection
    finger = AdafruitFingerprint(port=serial_port)

    response = finger.vfy_pwd()
    if response is not FINGERPRINT_PASSWORD_OK:
        print('Did not find fingerprint sensor :(')
        sys.exit()
    print('Found Fingerprint Sensor!\n')

    template = get_fingerprint(finger=finger)
    config.template = template
    config.status = 1
    #return template


def get_fingerprint(finger):
    # Buffer constants
    _CHAR_BUFF_1 = 0x01
    _CHAR_BUFF_2 = 0x02

    print('Waiting for a valid finger to enroll\n')
    sys.stdout.flush()

    # Read finger
    response = -1
    while response is not FINGERPRINT_OK:
        response = finger.gen_img()
        if response is FINGERPRINT_OK:
            print('Image taken')
            sys.stdout.flush()
        elif response is FINGERPRINT_NOFINGER:
            print('waiting...')
            sys.stdout.flush()
        elif response is FINGERPRINT_PACKETRECEIVER:
            print('Communication error')
            sys.stdout.flush()
        elif response is FINGERPRINT_IMAGEFAIL:
            print('Imaging Error')
            sys.stdout.flush()
        else:
            print('Unknown Error')
            sys.stdout.flush()

    response = finger.img_2Tz(buffer=_CHAR_BUFF_1)
    if response is FINGERPRINT_OK:
        print('Image Converted')
        sys.stdout.flush()
    elif response is FINGERPRINT_IMAGEMESS:
        print('Image too messy')
        return False
    elif response is FINGERPRINT_PACKETRECEIVER:
        print('Communication error')
        return False
    elif response is FINGERPRINT_FEATUREFAIL:
        print('Could not find fingerprint features')
        return False
    elif response is FINGERPRINT_INVALIDIMAGE:
        print('Could not find fingerprint features')
        return False
    else:
        print('Unknown Error')
        return False

    # Ensure finger has been removed
    print('Remove finger')
    time.sleep(1)
    response = -1
    while (response is not FINGERPRINT_NOFINGER):
        response = finger.gen_img()

    # Return template to upper computer
    response = finger.up_char(buffer=_CHAR_BUFF_1)
    if isinstance(response, tuple) and len(response) == 2 and response[0] is FINGERPRINT_OK:
        print('Template created successfully!')
        print('Enrollment done!\n')
        sys.stdout.flush()
        #print("printing response[1]: ", response[1])
        return response[1]
    if response is FINGERPRINT_PACKETRECEIVER:
        print('Communication error')
        return False
    if response is FINGERPRINT_TEMPLATEUPLOADFAIL:
        print('Template upload error')
        return False


def verify(template):

    # Attempt to connect to serial port
    try:
        #port = '/dev/ttyUSB0'  # USB TTL converter port
        port = 'COM11'
        baud_rate = '57600'
        serial_port = serial.Serial(port, baud_rate)
    except Exception as e:
        print(e)
        sys.exit()

    # Initialize sensor library with serial port connection
    finger = AdafruitFingerprint(port=serial_port)

    if fingerprint.store_from_upper_computer(finger=finger, template=template, page_id=1):
        print('Finished storing\n')
    
    print('\nWaiting for valid finger!\n')
    response = fingerprint.search(finger=finger, page_id=1, page_num=1)
    if response:
        config.status = 1
        id, confidence = response
        print(f'Found ID #{id}', end='')
        print(f' with confidence of {confidence}\n')
    else:
        config.status = 0
        
