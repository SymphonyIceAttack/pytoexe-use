#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import hashlib
import argparse
import binascii
import struct


def encrypt_v1(imei, key):
    """
    The V1 unlock system

    This system uses hardcoded keys.
    """
    salt = hashlib.md5(key).hexdigest()[8:24]
    digest = hashlib.md5((imei + salt).lower()).digest()

    code = 0
    for i in range(0, 4):
        code += (ord(digest[i]) ^ ord(digest[4 + i]) ^
                 ord(digest[8 + i]) ^ ord(digest[12 + i])) << (3 - i) * 8
    return str((code & 0x1ffffff) | 0x2000000)


def encrypt_v2_1(imei, version):

    # Magic bytes from somewhere
    key_2 = [
        0x01966A9, 0x021058F, 0x02AEDA9, 0x037CE91, 0x0488C9F, 0x05E507D,
        0x07A9BE5, 0x09F644B, 0x0CF35A1, 0x10D5F55, 0x15E2F25, 0x1C73D6B,
        0x24FCFDD, 0x3015B47, 0x3E829E9, 0x5143685
    ]

    key_201 = [
        0x06E9C2A, 0x3CA2B3C, 0x01080DC, 0x30855EE, 0x3D3283A, 0x2F4F85A,
        0x1F8808E, 0x3147D10, 0x34BBBB5, 0x29EEADD, 0x2318616, 0x50F3ADC,
        0x0D11F38, 0x2123BD2, 0x4276C86, 0x355CAAD
    ]

    if version == 201:
        magic_bytes = key_201
    else:
        magic_bytes = key_2

    csum = 0
    for i, digit in enumerate(imei):
        csum += ((ord(digit) * magic_bytes[i]))
        # Truncate to an unsigned long
        csum &= 0xffffffff

    # Extract bit integers from the checksum, get mod 10
    zvar = []
    for i in range(8):
        zvar.append(((csum & (0xf << (i * 4))) >> (i * 4)) % 10)

    # Add 1 to not have leading zero
    if zvar[0] == 0:
        zvar[0] = 1

    # Join the array of integers
    return ''.join([str(i) for i in zvar])


def encrypt_v2_2(imei, version):
    """This algorithim is two CRC32 implementation."""

    def custom_crc32(imei):
        """
        Non standard CRC32 used in v201 and v3
        """
        crc_table_v201 = [
             0x00000000, 0x77073096, 0xEE0E612C, 0x990951BA, 0x76DC419,
             0x196C3671, 0x6E6B06E7, 0xFED41B76, 0x89D32BE0, 0x10DA7A5A,
             0xFBD44C65, 0x4DB26158, 0x3AB551CE, 0xA3BC0074, 0xD4BB30E2,
             0x4ADFA541, 0x3DD895D7, 0xA4D1C46D, 0xD3D6F4FB, 0x4369E96A,
             0xD6D6A3E8, 0xA1D1937E, 0x38D8C2C4, 0x4FDFF252, 0xD1BB67F1,
             0xA6BC5767, 0x3FB506DD, 0x48B2364B, 0xD80D2BDA, 0xAF0A1B4C,
             0x36034AF6, 0x41047A60, 0xDF60EFC3, 0xA867DF55, 0x316E8EEF,
             0x90BF1D91, 0x1DB71064, 0x6AB020F2, 0xF3B97148, 0x84BE41DE,
             0x1ADAD47D, 0x6DDDE4EB, 0xF4D4B551, 0x83D385C7, 0x136C9856,
             0xFA0F3D63, 0x8D080DF5, 0x3B6E20C8, 0x4C69105E, 0xD56041E4,
             0xA2677172, 0x3C03E4D1, 0x4B04D447, 0xD20D85FD, 0xA50AB56B,
             0x646BA8C0, 0xFD62F97A, 0x8A65C9EC, 0x14015C4F, 0x63066CD9,
             0x45DF5C75, 0xDCD60DCF, 0xABD13D59, 0x26D930AC, 0x51DE003A,
             0xC8D75180, 0xBFD06116, 0x21B4F4B5, 0x56B3C423, 0xCFBA9599,
             0x706AF48F, 0xE963A535, 0x9E6495A3, 0x0EDB8832, 0x79DCB8A4,
             0xE0D5E91E, 0x97D2D988, 0x09B64C2B, 0x7EB17CBD, 0xE7B82D07,
             0x35B5A8FA, 0x42B2986C, 0xDBBBC9D6, 0xACBCF940, 0x32D86CE3,
             0xB8BDA50F, 0x2802B89E, 0x5F058808, 0xC60CD9B2, 0xB10BE924,
             0x2F6F7C87, 0x58684C11, 0xC1611DAB, 0xB6662D3D, 0x76DC4190,
             0x4969474D, 0x3E6E77DB, 0xAED16A4A, 0xD9D65ADC, 0x40DF0B66,
             0x37D83BF0, 0xA9BCAE53, 0xDEBB9EC5, 0x47B2CF7F, 0x30B5FFE9,
             0xBDBDF21C, 0xCABAC28A, 0x53B39330, 0x24B4A3A6, 0xBAD03605,
             0x03B6E20C, 0x74B1D29A, 0xEAD54739, 0x9DD277AF, 0x04DB2615,
             0xE10E9818, 0x7F6A0DBB, 0x086D3D2D, 0x91646C97, 0xE6635C01,
             0x6B6B51F4, 0x1C6C6162, 0x856530D8, 0xF262004E, 0x6C0695ED,
             0x1B01A57B, 0x8208F4C1, 0xF50FC457, 0x65B0D9C6, 0x12B7E950,
             0x8BBEB8EA, 0xFCB9887C, 0x62DD1DDF, 0x15DA2D49, 0x8CD37CF3,
             0xE40ECF0B, 0x9309FF9D, 0x0A00AE27, 0x7D079EB1, 0xF00F9344,
             0x4669BE79, 0xCB61B38C, 0xBC66831A, 0x256FD2A0, 0x5268E236,
             0xCC0C7795, 0xBB0B4703, 0x220216B9, 0x5505262F, 0xC5BA3BBE,
             0x68DDB3F8, 0x1FDA836E, 0x81BE16CD, 0xF6B9265B, 0x6FB077E1,
             0x18B74777, 0x88085AE6, 0xFF0F6A70, 0x66063BCA, 0x11010B5C,
             0x8F659EFF, 0xF862AE69, 0x616BFFD3, 0x166CCF45, 0xA00AE278,
             0xB2BD0B28, 0x2BB45A92, 0x5CB36A04, 0xC2D7FFA7, 0xB5D0CF31,
             0x2CD99E8B, 0x5BDEAE1D, 0x9B64C2B0, 0xEC63F226, 0x756AA39C,
             0x026D930A, 0x9C0906A9, 0xEB0E363F, 0x72076785, 0x05005713,
             0x346ED9FC, 0xAD678846, 0xDA60B8D0, 0x44042D73, 0x33031DE5,
             0xAA0A4C5F, 0xDD0D7CC9, 0x5005713C, 0x270241AA, 0xBE0B1010,
             0x01DB7106, 0x98D220BC, 0xEFD5102A, 0x71B18589, 0x06B6B51F,
             0x9FBFE4A5, 0xE8B8D433, 0x7807C9A2, 0x0F00F934, 0x9609A88E,
             0xC90C2086, 0x5768B525, 0x206F85B3, 0xB966D409, 0xCE61E49F,
             0x5EDEF90E, 0x29D9C998, 0xB0D09822, 0xC7D7A8B4, 0x59B33D17,
             0xCDD70693, 0x54DE5729, 0x23D967BF, 0xB3667A2E, 0xC4614AB8,
             0x5D681B02, 0x2A6F2B94, 0xB40BBE37, 0xC30C8EA1, 0x5A05DF1B,
             0x2EB40D81, 0xB7BD5C3B, 0xC0BA6CAD, 0xEDB88320, 0x9ABFB3B6,
             0x73DC1683, 0xE3630B12, 0x94643B84, 0x0D6D6A3E, 0x7A6A5AA8,
             0x67DD4ACC, 0xF9B9DF6F, 0x8EBEEFF9, 0x17B7BE43, 0x60B08ED5,
             0x8708A3D2, 0x1E01F268, 0x6906C2FE, 0xF762575D, 0x806567CB,
             0x95BF4A82, 0xE2B87A14, 0x7BB12BAE, 0x0CB61B38, 0x92D28E9B,
             0xE5D5BE0D, 0x7CDCEFB7, 0x0BDBDF21, 0x86D3D2D4, 0xF1D4E242,
             0xD70DD2EE, 0x4E048354, 0x3903B3C2, 0xA7672661, 0xD06016F7,
             0x2D02EF8D,
        ]

        csum = 0xffffffff
        for i, digit in enumerate(imei):
            csum = crc_table_v201[(csum & 0xff) ^ ord(digit)] ^ (csum >> 8)
            # Truncate to unsigned int
            csum &= 0xffffffff
        return csum

    if version == 201:
        # Version 201/3 uses a custom CRC32 block
        crc32 = custom_crc32(imei)

        # Represent unsigned crc32 as signed int
        crc32 = struct.unpack('>i', struct.pack('>I', ~crc32 & 0xffffffff))[0]
        crc32 = abs(crc32)

    else:
        # Version 2 uses a standard CRC32 block
        crc32 = abs(binascii.crc32(imei)) & 0xffffffff

    if crc32 == 0:
        return '99999999'
    else:

        # Reverse the crc32 number, and pad on left with '9's
        result = list(str(crc32)[-8:])

        # Replace a leading zero with nine
        if result[0] == '0':
            result[0] = '9'

        # Join result and pad left with 9's
        return ''.join(result).rjust(8, '9')


def encrypt_v2_3(imei, version):
    """
    MD5 digest algorithim
    """

    digest = hashlib.md5(imei).digest()
    if version == 201:
        digest_bytes = list(digest[5:5+8])
    else:
        digest_bytes = list(digest[0:8])

    # Replace first digit if it begins with zero
    first_digit = ord(digest_bytes[0]) % 10
    if (first_digit) == 0:
        digest_bytes[0] = '5'
    else:
        digest_bytes[0] = str(first_digit)

    # Use suitable digits or base 10 bytes to get a single decimal digit
    result = []
    for byte in digest_bytes:
        # Byte is already a single digit character, don't mod
        if (byte >= '0') and (byte <= '9'):
            result.append(byte)
        else:
            result.append(ord(byte) % 10)

    return ''.join([str(i) for i in result])


def encrypt_v2_4(imei, version):
    """
    MD5 with version specific salt
    """

    def md5_hash(imei, key):
        salt = hashlib.md5(key).digest()
        return hashlib.md5(imei + salt).digest()

    if version == 201:
        digest = md5_hash(imei, key="dfkdkfllekkodk")
    else:
        digest = md5_hash(imei, key="hwideadatacard")

    code = 0
    for i in range(0, 4):
        digit = ((ord(digest[i]) ^ ord(digest[i+4]) ^
                 ord(digest[i+8]) ^ ord(digest[i+12])))
        code = (code << 8) | (digit & 0xff)
    return str((code & 0x1ffffff) | 0x2000000)


def encrypt_v2_5(imei, version):
    """
    Substitution cipher based on IMEI
    """
    pw_table = "5739146280098765432112345678905\000"

    result = []
    imei_str = imei + 'Z'
    for i in range(0, 8):
        digit = ((ord(imei_str[i]) ^ ord(imei_str[i+8])) & 0xff)
        result.append(int(pw_table[(digit >> 4) + (digit & 0x0f)]))

    # Dont start with zero, set first digit to the offset of the first
    # non-zero digit.
    if result[0] == 0:
        for i, digit in enumerate(result):
            if digit != 0:
                break
        result[0] = i

    return ''.join([str(i) for i in result])


def encrypt_v2_6(imei, version):
    """
    SHA1 digest of IMEI
    """
    digest = hashlib.sha1(imei).digest()

    # Chunk hash as unsigned integers, unpack four bytes as an unsigned int
    int_array = []
    for i in range(0, len(digest), 4):
        int_array.append(str(struct.unpack(">I", digest[i:i+4])[0]))

    if version == 2:
        result = int_array[0] + int_array[1]
    elif version == 5:
        result = int_array[1] + int_array[4]
    elif version == 6:
        result = int_array[2] + int_array[3]

    # Pad the result with zeros to make 8 digit code
    return result[0:8].ljust(8, '0')


def encrypt_v2_7(imei, version):
    """
    Keyed cipher and MD5 digest
    """

    cb_2 = [
        0x01, 0x01, 0x02, 0x03, 0x05, 0x08, 0x0D, 0x15, 0x22, 0x37, 0x59, 0x90
    ]

    cb_201 = [
        0x0B, 0x0D, 0x11, 0x13, 0x17, 0x1D, 0x1F, 0x25, 0x29, 0x2B, 0x3B, 0x61
    ]

    if version == 201:
        key = cb_201
    else:
        key = cb_2

    result = []
    for i, digit in enumerate(imei):
        digit = ord(digit)
        if (i % 3) == 0:
            result.append(((digit << 6) | (digit >> 2)) & 0xff)
        elif (i % 3) == 1:
            result.append(((digit << 5) | (digit >> 3)) & 0xff)
        else:
            result.append(((digit >> 4) | (digit << 4)) & 0xff)

    hsum = 0
    for i in range(0, 7):
        hsum += result[14-i] + (result[i] << 8)
    hsum += result[8]

    # Pad buffer with 0's
    buf128 = result + ([0] * (128 - len(result)))

    # TODO: Understand what this chunk of code does:
    # Appears to do divison by 6.
    r8 = 0
    for i in range(15, 0x80):
        r6 = i
        r3 = i >> 31
        lr = 0x2AAAAAAB
        cx = 0x2AAAAAAB * i
        r1 = cx >> 32
        cx = lr * r8
        lr = cx >> 32

        r0 = r8 >> 31
        r2 = r0
        r5 = (r1 >> 1) - r3
        r12 = r5 << 4
        r0 = (lr >> 1) - r0
        r2 = (lr >> 1) - r2
        r1 = r0 << 4
        r12 = r12 - (r5 << 2)
        r3 = r2 << 4
        lr = r6 - r12
        r1 = r1 - (r0 << 2)
        r7 = r5 + lr
        r3 = r3 - (r2 << 2)
        r1 = r8 - r1
        r2 = r5 + r1
        r3 = r8 - r3

        r12 = r12 - 0x18
        if r7 > 0xb:
            r7 = r7 - 0xc
        r3 += r5
        if r5 > 1:
            r3 = r2 + r12
        r0 = hsum
        r1 = r6

        if r8 == 0:
            r4 = buf128[r3]
            r0 = r0 % r1
            r1 = key[r7]
            r4 = r4 & r1
            r12 = buf128[r0]
            r3 = buf128[r0+1]
            r4 |= r12
        else:
            r1 = r6
            r0 = hsum
            r4 = buf128[r3]
            r0 = r0 % r1
            r1 = r8
            r5 = buf128[r0]
            r0 = hsum
            r0 = r0 % r1
            r3 = buf128[r0]
            r2 = key[r7]
            r4 = r4 & r2
            r4 = r4 | r5

        r3 = ~r3
        r3 = r3 | r4
        r3 &= 0xff
        buf128[i] = r3
        r8 += 1

    byte_array = ''.join([chr(b) for b in buf128])

    csum = 0
    for i in range(0, 7):
        csum += (ord(imei[i+1]) | (ord(imei[i]) << 8))
    csum += ord(imei[14])

    digest = hashlib.md5(byte_array).digest()

    # Pick bytes from the digest which are integers
    result = []
    for byte in digest:
        if (byte >= '0') and (byte <= '9'):
            result.append(byte)
        if len(result) > 7:
            break

    def int_from_bytestream(byte_stream):
        """Convert a 4 byte chunk to an integer"""
        return struct.unpack("<I", byte_stream[0:4])[0]

    # Extract an integer from the hash
    offset = (csum & 3) << 2
    extra_num = str(int_from_bytestream(digest[offset:]))

    # Cycle 1
    if len(result) < 8:
        # Don't have enough numbers, read more digits from the end
        # of extra_number until we have 8 digits.
        while len(result) < 8:
            extra_num, last_digit = extra_num[:-1], extra_num[-1]
            result.append(last_digit)

            # If still nor enough digits, pick a new integer from digest
            if not extra_num:
                offset = (3 - (csum & 3)) << 2
                extra_num = str(int_from_bytestream(digest[offset:]))

    # Replace any leading zeros
    if result[0] == '0':
        if csum != 0:
            offset = 1
        else:
            offset = 0

        # Add one to digit to ensure non zero
        result[0] = str((ord(digest[offset]) & 7) + 1)

    return ''.join([str(i) for i in result])


def proc_index(imei, version):
    """
    Determine `index` for the IMEI

    The index determines which of the 7 algorithims should be usedbytes
    for the unlock code generation.
    """
    csum = 0
    for i, digit in enumerate(imei, 1):
        ch = ord(digit)
        if version == 201:
            csum += (ch + i) * ch * (ch + 313)
        else:
            csum += (ch+i) * i

    cx = (-0x6db6db6d * csum) >> 32
    c1 = ((cx + csum) >> 2) - (csum >> 31)
    return csum - ((c1 << 3) - c1)


def calc_2(imei, version):
    """
    Select the correct crypto algorithim based on the IMEI
    """

    # Algorithim set for v2
    encryption_algo_v2 = {
        0: (encrypt_v2_1, 2),
        1: (encrypt_v2_2, 2),
        2: (encrypt_v2_3, 2),
        3: (encrypt_v2_4, 2),
        4: (encrypt_v2_5, None),
        5: (encrypt_v2_6, 2),
        6: (encrypt_v2_7, 2),
    }

    # Algorithim set for v201 / v3
    encryption_algo_v201 = {
        0: (encrypt_v2_1, 201),
        1: (encrypt_v2_2, 201),
        2: (encrypt_v2_3, 201),
        3: (encrypt_v2_4, 201),
        4: (encrypt_v2_6, 5),
        5: (encrypt_v2_6, 6),
        6: (encrypt_v2_7, 201),
    }

    index = proc_index(imei, version)
    if version == 2:
        algorithim, algo_version = encryption_algo_v2[index]
    elif version == 201 or version == 3:
        algorithim, algo_version = encryption_algo_v201[index]

    return algorithim(imei, algo_version)


def unlock(imei, version):
    """
    Public unlock function

    Choose the correct unlock algorithim based on the version
    """
    if version == 1:
        return encrypt_v1(imei, 'hwe620datacard')

    elif version == 2:
        # Version v2
        return calc_2(imei, 2)

    elif version == 201 or version == 3:
        # Version v201/v3
        return calc_2(imei, 201)

    elif version == 'flash':
        return encrypt_v1(imei, 'e630upgrade')


def run_tests():
    """
    Run tests
    """

    # These are test case which check some tricky cases.
    assert(encrypt_v2_1('166794546749343', 201) == '31572464')

    assert(encrypt_v2_2('867010022091625', 2) == '89740701')
    assert(encrypt_v2_2('867010022093346', 2) == '90496577')
    assert(encrypt_v2_2('867010022091336', 201) == '43479313')
    assert(encrypt_v2_2('486043736169958', 201) == '20766653')
    assert(encrypt_v2_2('152782107774300', 201) == '99353390')

    assert(encrypt_v2_3('867010022091626', 2) == '55760904')
    assert(encrypt_v2_3('867010022091545', 2) == '77395563')
    assert(encrypt_v2_3('867010022091566', 201) == '98820346')
    assert(encrypt_v2_3('133887909865624', 201) == '13553393')

    assert(encrypt_v2_4('867010022091677', 2) == '50284150')
    assert(encrypt_v2_4('867010022091677', 201) == '48425064')

    assert(encrypt_v2_5('867010022091661', 2) == '16672676')
    assert(encrypt_v2_5('867010022091698', 2) == '16672086')

    assert(encrypt_v2_6('867010022091692', 2) == '16678430')
    assert(encrypt_v2_6('867010022091696', 5) == '26958384')
    assert(encrypt_v2_6('867010022091697', 6) == '11406485')

    assert(encrypt_v2_7('867010022093344', 2) == '41232318')
    assert(encrypt_v2_7('234242342432305', 2) == '68014899')
    assert(encrypt_v2_7('221724677371250', 2) == '92023179')
    assert(encrypt_v2_7('867010022093350', 201) == '13122759')

    assert(proc_index('667010022091624', 201) == 2)
    assert(proc_index('867010022091624', 201) == 3)
    assert(proc_index('867010022091624', 2) == 0)

    assert(encrypt_v2_7('221724677371250', 2) == '92023179')

    # Try load extra test cases from file
    failed = False
    for test_type in [1, 2, 3]:
        try:
            test_file = os.path.join("tests", "test-{}.txt".format(test_type))
            for test_line in open(test_file, 'r'):
                imei, expected = test_line.strip().split(' ')
                calculated = unlock(imei, test_type)
                if calculated != expected:
                    print("Error: IMEI: %s  Calculated: %s Expected: %s" %
                          (imei, calculated, expected))
                    failed = True
        except OSError:
            print("Could not open test cases in '{}'.".format(test_file))

    if failed:
        print("Tests failed")
    else:
        print("All tests passed!")


def main():
    parser = argparse.ArgumentParser(
        description="Generate Huawei device unlock codes.")
    parser.add_argument("imei", type=str, help="The device IMEI number")
    parser.add_argument('--test', action="store_true",
                        help="Run the test cases")
    args = parser.parse_args()

    if args.test:
        return run_tests()

    if len(args.imei) != 15 or not args.imei.isdigit():
        print("Not a valid IMEI")

    else:
        # Looks like a valid IMEI, calculate codes.
        imei = args.imei
        print('IMEI: {}'.format(imei))
        print('Unlock (V1):     {}'.format(unlock(imei, 1)))
        print('Unlock (V2):     {}'.format(unlock(imei, 2)))
        print('Unlock (V3/201): {}'.format(unlock(imei, 3)))
        print('Flash:           {}'.format(unlock(imei, 'flash')))


if __name__ == '__main__':
    main()