#!/usr/bin/python

import serial


# Crealte class rims
class rims:

    # Register offsets
    REG_SYS_ID          = 0x00 # System Id
    REG_FW_VER          = 0x01 # FW version
    REG_PID_SV          = 0x08 # PID set value
    REG_PID_KP          = 0x09 # KP
    REG_PID_KI          = 0x0A # KI
    REG_PID_KD          = 0x0B # KD
    REG_PID_SET_MODE    = 0x0C # PID set mode
    REG_PID_NV_SETTINGS = 0x0F # PID non-volatile settings read/write control
    REG_PID_OP_MODE     = 0x0D # PID operating mode
    REG_RIMS_OUT_T      = 0x80 # RIMS output temperature
    REG_HEATER_PWM      = 0x81 # Heater PWM
    REG_ALARMS          = 0x82 # Alarms

    # Constructor
    def __init__(self, port):
        self.ser = serial.Serial(port or 0, 57600, timeout = 1)

    # Send command
    def send_command(self, cmd_id, address, data):
        # Start
        cmd = '?'
        # Command Id
        cmd += cmd_id
        # Address
        cmd += "{0:02X}".format(address)
        # Data
        if data is not None:
            cmd += "{0:02X}".format(data)
        # Checksum
        checksum = 0
        for c in cmd:
            checksum += ord(c)
        cmd += "{0:02X}".format(checksum & 0xff)
        # Ending
        cmd += "\r\n"

        # Clear serial buffer
        self.ser.flushInput()

        # Write command and get response
        retry=0
        while retry < 3:
            self.ser.write(cmd)
            self.ser.flush()
            resp = self.ser.readline()
            if resp != '':

                # Checksum
                checksum = 0
                for c in resp[0: len(resp) - 4]:
                    checksum += ord(c)

                if checksum == int(resp[len(resp) - 4 : len(resp) - 2], 16):
                    break

            retry += 1

        if len(resp) >= 6:
            return resp[1:len(resp) - 4] ## remove start, checksum and CR/LF

        print "Command error"
        return ''

    # Write register
    def write_reg(self, address, data):
        resp = self.send_command('W', address, data)
        if len(resp) > 0:
            if resp[0] == 'K':
                return 1
        return -1

    # Read register
    def read_reg(self, address):
        resp = self.send_command('R', address, None)
        if len(resp) < 2:
            raise Exception("Invalid response length")
            return -1

        if resp[0] != 'R':
            raise Exception("Invalid response type")

        return int(resp[1:len(resp)], 16)

    # Print register
    def print_reg(self, address):
        data = self.read_reg(address)
        print "0x{0:02X}\n".format(data)

    # Read System ID
    def get_id(self):
        return self.read_reg(self.REG_SYS_ID)

    # Print System ID
    def print_id(self):
        sys_id = self.get_id()
        id_string = ""

        print "System ID = 0x{0:08X}".format(sys_id),

        for i in range(4):
            id_string = chr(sys_id&0xff) + id_string
            sys_id >>= 8

        print "(" + id_string + ")"

    # Set PID configuration
    def set_pid_config(self, sv = None, kp = None, ki = None, kd = None, mode = None):
        if sv:
            self.write_reg(self.REG_PID_SV, int(sv*2**16))
        if kp:
            self.write_reg(self.REG_PID_KP, int(kp*2**16))
        if ki:
            self.write_reg(self.REG_PID_KI, int(ki*2**16))
        if kd:
            self.write_reg(self.REG_PID_KD, int(kd*2**16))
        if mode:
            self.write_reg(self.REG_PID_SET_MODE, mode)

    # Get PID config
    def get_pid_config(self):
        sv = self.read_reg(self.REG_PID_SV)/2.0**16
        kp = self.read_reg(self.REG_PID_KP)/2.0**16
        ki = self.read_reg(self.REG_PID_KI)/2.0**16
        kd = self.read_reg(self.REG_PID_KD)/2.0**16
        mode = self.read_reg(self.REG_PID_SET_MODE)

        return sv, kp, ki, kd, mode

    # Print PID config
    def print_pid_config(self):
        sv, kp, ki, kd, mode = self.get_pid_config()
        print "  SV = {0:.2f}".format(sv)
        print "  Kp = {0:.2f}".format(kp)
        print "  Ki = {0:.2f}".format(ki)
        print "  Kd = {0:.2f}".format(kd)
        print "Mode = {0:0d}".format(mode)

    # Save config to EE2PROM
    def save_config(self):
        self.write_reg(self.REG_PID_NV_SETTINGS, 1)

    # Load config from EEPROM
    def load_config(self):
        self.write_reg(self.REG_PID_NV_SETTINGS, 2)

    # Get temperature
    def get_temp(self):
        return self.read_reg(self.REG_RIMS_OUT_T)/2.0**16

    # Print temperature
    def print_temp(self):
        print "{0:2f} degC\n".format(self.get_temp)

    # Get PWM
    def get_pwm(self):
        return self.read_reg(self.REG_HEATER_PWM)/2.0**16

    # Print PWM
    def print_pwm(self):
        print "{0:1f}%\n".format(self.get_pwm)