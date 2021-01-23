################## Imports  ################################

import re
import os
import shutil
import sys

################## Constants ##################

supported_types = ['MPEG', 'PDF', 'BMP', 'GIF', 'JPG', 'JPG_FFDB', 'DOCX', 'AVI', 'PNG']
disk_image_name = 'Project2Updated.dd'

################## File headers and footers ##################

pdf_header_string = '25504446'
pdf_footer_string = '0A2525454F46'

gif_header_string = '474946383961'
gif_footer_string = '003B'

bmp_header_string = '424D'

docx_header_string = '504B030414000600'
docx_footer_string = '504B0506'

AVI_header_string = '52494646'

gif_header_string = '474946383961'
gif_footer_string = '003B000000000000'

png_header_string = '89504E470D0A1A0A'
png_footer_string = '49454E44AE426082'

jpg_header_string = 'FFD8FFE0'
jpg_header_string_ffdb = 'FFD8FFDB'
jpg_footer_string = 'FFD900000000'

bmp_header_string = '424D'

mpeg_header_string = '000001B3'
mpeg_footer_string = '000001B7'

"""
Variables for the program run:
Signature is a dictionary has different file types (key),
each element has the header and footer string in it

image_bytes contains the disk image bytes (type: bytes)

bytes_hex contains the disk image bytes (as a string) in hex (type: string)
note that bytes_hex is used to look for the headers, it is a string with no spaces
in between the bytes

recovered_files is an array to keep track of all the files that 
were recovered from the image

recovered_dir is a directory path to keep the recovered
files in
"""

signatures = {}
image_bytes = ""
bytes_hex = ""
recovered_files = []
recovered_dir = '/recovered'

################## Helper and utility functions ##################

"""
Helper function that takes a string and 
returns the string as a string of pairs of bytes
split by spaces. eg: AB32FF => AB 32 FF
"""


def hex_to_readable_line(hex_line):
    string = ""
    n = 2
    out = [(hex_line[i:i + n]) for i in range(0, len(hex_line), n)]
    for element in out:
        string += str(element) + " "
    return string


"""
Function that removes headers that don't 
start at sectors (512) and returns the 
valid header locations only
"""


def remove_illegal_headers(headers):
    valid_headers = []
    for occurrence in headers:
        o_location = get_offset_for_location(occurrence)
        if o_location % 512 == 0:
            valid_headers.append(occurrence)
    return valid_headers


"""
Function that removes footers that appear
before any header for a certain file type
"""


def remove_illegal_footers(footers, headers):
    valid_footers = []
    for occurrence in footers:
        if occurrence > headers[0]:
            valid_footers.append(occurrence)
    return valid_footers


"""
Function that takes a substring and a string
and returns all the locations (indexes) that 
the substring occurs in that string
eg: "ab", "ggtab" are substring and string
this would return 3
"""


def find_all_occurrences(substring, string):
    return [m.start() for m in re.finditer(substring, string)]


"""
Function that takes the byte location (in the string of hex)
and returns the byte offset for that location. This simply 
returns the index of the header divided by 2
this is because the hex string has no spaces,
and bytes are two chars each
"""


def get_offset_for_location(byte_location):
    return int(byte_location / 2)


"""
Initialization function for the signature dictionaries
"""


def init_signatures():
    for file_type in supported_types:
        signature = {}
        signature['header'] = ''
        signature['footer'] = ''
        signatures[file_type] = signature

    # PDF
    signatures['PDF']['header'] = pdf_header_string
    signatures['PDF']['footer'] = pdf_footer_string

    # DOCX
    signatures['DOCX']['header'] = docx_header_string
    signatures['DOCX']['footer'] = docx_footer_string

    # AVI
    signatures['AVI']['header'] = AVI_header_string
    signatures['AVI']['footer'] = ''

    # GIF
    signatures['GIF']['header'] = gif_header_string
    signatures['GIF']['footer'] = gif_footer_string

    # PNG
    signatures['PNG']['header'] = png_header_string
    signatures['PNG']['footer'] = png_footer_string

    # JPG
    signatures['JPG']['header'] = jpg_header_string
    signatures['JPG']['footer'] = jpg_footer_string

    signatures['JPG_FFDB']['header'] = jpg_header_string_ffdb
    signatures['JPG_FFDB']['footer'] = jpg_footer_string

    # BMP
    signatures['BMP']['header'] = bmp_header_string
    signatures['BMP']['footer'] = ''

    # MPEG
    signatures['MPEG']['header'] = mpeg_header_string
    signatures['MPEG']['footer'] = mpeg_footer_string


"""
Function to open the file (dd image)
and store the bytes and string of hex in a 
global variable.
"""


def open_file(path):
    global image_bytes, bytes_hex
    with open(path, 'rb') as f:
        image_bytes = f.read()  # bytes
        bytes_hex = image_bytes.hex().upper()  # string


'''
Function that takes array of bytes
and name and writes these bytes
to this file name
'''


def write_bytes(bytes, filename):
    path = os.getcwd() + recovered_dir + '/' + filename
    f = open(path, 'wb')
    f.write(bytes)
    f.close()


def get_empty_recovered_element():
    element = {}
    element['name'] = ''
    element['start'] = 0
    element['end'] = 0
    element['sha'] = ''
    return element


def make_recovery_directory():
    path = os.getcwd()
    path += recovered_dir
    if os.path.exists(path):
        shutil.rmtree(path)
    os.mkdir(path)


''' Outputs the sha256 value for a file
    Input: file name (string)
    Output: sha256 value (string) if valid input file
    Output: None if invalid input file
'''


def get_sha256(filename):
    import hashlib
    path = os.getcwd() + recovered_dir + '/' + filename
    file_bytes = None
    readable_hash = None
    try:
        with open(path, "rb") as f:
            file_bytes = f.read()  # read entire file as bytes
            readable_hash = hashlib.sha256(file_bytes).hexdigest()
    except Exception as e:
        print(e)
        return None
    return readable_hash


################## Handling functions ##################


############## START OF GENERIC HANDLING #####################
"""
Handling of Generic Files
"""


def handle_generic(headers, footers, file_name, file_extension, footer_length):
    header_count = len(headers)
    footer_count = len(footers)

    """
    if no headers found, return.
    """
    if header_count == 0:
        return

    """
    Loop the header locations
    """
    for index in range(header_count):

        """
        The start of the file, is always the current
        header in the sequence
        """
        file_start = get_offset_for_location(headers[index])

        """
        If last header, then for sure the footer for this file,
        is the last possible footer. End = last footer.

        If not last header, then the footer for this file,
        will be the last footer with an offset less than the 
        following header (header at index + 1).
        """
        if index == (header_count - 1):
            # the number of bytes in the footer are added to the file
            # to carve until the end of the footer
            file_end = get_offset_for_location(footers[footer_count - 1]) + footer_length
        else:
            footer_iterator = 0
            while footers[footer_iterator] < headers[index + 1]:
                footer_iterator += 1
            file_end = get_offset_for_location(footers[footer_iterator - 1]) + footer_length

        if file_extension == 'pdf':
            if index == 0:
                file_end += 2
            else:
                file_end += 1
        """
        Carve bytes out from the image bytes
        """
        output_name = file_name + '_' + str(index) + '.' + file_extension
        write_bytes(image_bytes[file_start:file_end], output_name)

        file_element = get_empty_recovered_element()
        file_element['name'] = output_name
        file_element['start'] = file_start
        file_element['end'] = file_end
        file_element['sha'] = get_sha256(output_name)
        recovered_files.append(file_element)


############## END OF GENERIC HANDLING #####################



############## START OF PNG HANDLING #####################
"""
Handling of PNG Files
"""


def handle_png(headers, footers, file_name, file_extension, footer_length):
    header_count = len(headers)
    footer_count = len(footers)

    """
    if no headers found, return.
    """
    if header_count == 0:
        return

    """
    Loop the header locations
    """
    for index in range(header_count):

        """
        The start of the file, is always the current
        header in the sequence
        """
        file_start = get_offset_for_location(headers[index])

        """
        If not last header, then the footer for this file,
        will be the Footer with an offset right after
        the current header, since PNG files have one
        footer per file
        """
        footer_iterator = 0
        while footers[footer_iterator] < headers[index]:
            footer_iterator += 1
        file_end = get_offset_for_location(footers[footer_iterator]) + footer_length

        """
        Carve bytes out from the image bytes
        """
        output_name = file_name + '_' + str(index) + '.' + file_extension
        write_bytes(image_bytes[file_start:file_end], output_name)

        file_element = get_empty_recovered_element()
        file_element['name'] = output_name
        file_element['start'] = file_start
        file_element['end'] = file_end
        file_element['sha'] = get_sha256(output_name)
        recovered_files.append(file_element)


############## END OF PNG HANDLING #####################

############## START OF AVI HANDLING #####################
"""
Handling function for AVI files. 
Note that AVI files have
the size of the file 
in the header
"""


def handle_avi(headers):
    header_count = len(headers)
    """
    if no headers found, return.
    """
    if header_count == 0:
        return

    """
    for each header, get size from the start of the header + 4
    the end of the size will be at the size start +3
    then convert that size to little indian 
    and carve file out
    """
    for index, header in enumerate(headers):
        byte_offset = get_offset_for_location(header)
        size_start = byte_offset + 4
        size_end = size_start + 4

        size_bytes = image_bytes[size_start:size_end]
        size_int = int.from_bytes(size_bytes, "little")
        # Adding 8 bytes to account for
        # the 4 header and 4 size bytes
        file_end = byte_offset + size_int + 8
        file_name = 'avi_' + str(index) + '.avi'
        write_bytes(image_bytes[byte_offset:file_end], file_name)

        file_element = get_empty_recovered_element()
        file_element['name'] = file_name
        file_element['start'] = byte_offset
        file_element['end'] = file_end
        file_element['sha'] = get_sha256(file_name)
        recovered_files.append(file_element)


############## END OF AVI HANDLING #####################



############## START OF JPG HANDLE #####################

def handle_jpg(headers, footers, file_name, file_extension, footer_length):
    header_count = len(headers)

    """
    if no headers found, return.
    """
    if header_count == 0:
        return

    """
    Loop the header locations
    """
    for index in range(header_count):

        """
        The start of the file, is always the current
        header in the sequence
        """
        file_start = get_offset_for_location(headers[index])

        """
        Find the footer that is directly 
        after the current header for both types
        pf JPG files
        """
        footer_iterator = 0
        while footers[footer_iterator] < headers[index]:
            footer_iterator += 1
        file_end = get_offset_for_location(footers[footer_iterator]) + footer_length

        """
        Carve bytes out from the image bytes
        """
        output_name = file_name + '_' + str(index) + '.' + file_extension
        write_bytes(image_bytes[file_start:file_end], output_name)

        file_element = get_empty_recovered_element()
        file_element['name'] = output_name
        file_element['start'] = file_start
        file_element['end'] = file_end
        file_element['sha'] = get_sha256(output_name)
        recovered_files.append(file_element)


############## END OF JPG HANDLE #####################



############## START OF BMP HANDLE #####################

"""
Function to handle BMP headers

We look for 0x424D (BMP header) to find a possible BMP file.
Each 0x424D found should have their offset checked to see if it is divisible by 512.
If they are not divisible by 512, then the signature is not aligned to a sector,
and there is either no file or the file is embedded in another file (Will not be detected)

We get the BMP file size from the header.
We look at the reserved sections to filter out false positives again.

input 'headers' is a list with the offset of every 0x424D found.
"""


def handle_bmp(headers):
    header_count = len(headers)

    # if no headers found, return.
    if header_count == 0:
        return

    """
    BMP Header format:
    Offset 0    Size 2      0x424D or 'BM' Signature
    Offset 2    Size 4      BMP file size (little endian)
    Offset 6    Size 2      Reserved. Should be 0s
    Offset 8    Size 2      Reserved. Should be 0s
    """
    matches_found = 0
    for index, header in enumerate(headers):
        byte_offset = get_offset_for_location(header)
        # Reading BMP file size field in the header
        size_start = byte_offset + 2
        size_end = size_start + 4
        size_bytes = image_bytes[size_start:size_end]
        size_int = int.from_bytes(size_bytes, "little")

        # Reading BMP reserved section fields in the header
        reserved_section_start = byte_offset + 6
        reserved_section_end = reserved_section_start + 4
        reserved_section = int.from_bytes(image_bytes[reserved_section_start:reserved_section_end], "little")
        if (reserved_section != 0):
            # Note: Reserved section not all 0s. Ignoring this false positive
            continue

        # Creating the file
        file_end = byte_offset + size_int
        file_bytes = image_bytes[byte_offset:file_end]
        name_to_use = "bmp_" + str(matches_found) + ".bmp"
        write_bytes(image_bytes[byte_offset:file_end], name_to_use)
        matches_found += 1

        file_element = get_empty_recovered_element()
        file_element['name'] = name_to_use
        file_element['start'] = byte_offset
        file_element['end'] = file_end
        file_element['sha'] = get_sha256(name_to_use)
        recovered_files.append(file_element)


############## END OF BMP HANDLE #####################



"""
Function for handling MPEG-1 Headers.

Assumes MPG-1 Header 0x00 00 01 B3
Assumes MPG-1 Footer 0x00 00 01 B7

MPEG-1 Files are carved from header to footer.
"""


############## START OF MPEG HANDLE #####################

def handle_mpeg(headers, footers):
    header_count = len(headers)
    footer_count = len(footers)

    # if no headers or footers found, return.
    if header_count == 0 or footer_count == 0:
        return

    # Debugging warning message to warn if there is not the same amount of headers as footers
    if header_count != footer_count:
        pass

    """
    MPG Header format:
    Offset 0    Size 4      0x00 00 01 Bx signature
                            We look for 0x00 00 01 B3 here.

    MPG Footer format:
    Offset x    Size 4      0x00 00 01 B7 Signature
    """
    i = 0
    j = 0
    last_used_footer_index = 0
    matches_found = 0
    while i < len(headers):
        byte_offset = get_offset_for_location(headers[i])

        j = last_used_footer_index
        if j == len(footers):
            return

        while j < len(footers):
            try:
                footer_offset = get_offset_for_location(footers[i])
            except Exception:  # This might not actually be reachable -- while loop may filter out out-of-bounds results
                #               print("No more MPG footers available. Ending function.")
                return
            if footer_offset < byte_offset:
                #              print("MPG footer at %d starts before a header" % footer_offset)
                j += 1
                continue
            last_used_footer_index += 1
            break

        file_end = footer_offset + 4

        # Creating the file
        file_bytes = image_bytes[byte_offset:file_end]
        name_to_use = "mpg_" + str(matches_found) + ".mpg"
        write_bytes(image_bytes[byte_offset:file_end], name_to_use)
        matches_found += 1
        i += 1

        file_element = get_empty_recovered_element()
        file_element['name'] = name_to_use
        file_element['start'] = byte_offset
        file_element['end'] = file_end
        file_element['sha'] = get_sha256(name_to_use)
        recovered_files.append(file_element)


############## END OF MPEG HANDLE #####################



################## Main ######################################

"""
Initialization signatures and open the file
"""
disk_image_name = sys.argv[1]
open_file(disk_image_name)
init_signatures()
make_recovery_directory()

"""
Loop all the signatures in the signatures dictionary and one by one do:
    1. get the header and footer for the file type
    2. get the locations of the header
    3. remove the illegal header locations
    4. if file has footers, find the location of the footers
    5. send header locations, footer locations to appropriate handling function
"""

for sig in signatures:
    sig_header = signatures[sig]['header']
    sig_footer = signatures[sig]['footer']

    header_occ = find_all_occurrences(sig_header, bytes_hex)
    header_occ = remove_illegal_headers(header_occ)

    if sig_footer != '':
        footer_occ = find_all_occurrences(sig_footer, bytes_hex)
        footer_occ = remove_illegal_footers(footer_occ, header_occ)

    if sig == 'PDF':
        handle_generic(header_occ, footer_occ, 'pdf_file', 'pdf', 6)
    elif sig == 'AVI':
        handle_avi(header_occ)
    elif sig == 'DOCX':
        handle_generic(header_occ, footer_occ, 'document', 'docx', 22)
    elif sig == 'GIF':
        handle_generic(header_occ, footer_occ, 'gif_file', 'gif', 2)
    elif sig == 'PNG':
        handle_png(header_occ, footer_occ, 'png_file', 'png', 8)
    elif sig == 'JPG':
        handle_jpg(header_occ, footer_occ, 'jpg_file', 'jpg', 2)
    elif sig == 'JPG_FFDB':
        handle_jpg(header_occ, footer_occ, 'jpg_ffdb', 'jpg', 2)
    elif sig == 'BMP':
        handle_bmp(header_occ)
    elif sig == 'MPEG':
        handle_mpeg(header_occ, footer_occ)

'''
Printing the found files and their info
'''

number_of_recovered_files = len(recovered_files)
print("The disk image contains " + str(number_of_recovered_files) + " files")

for file in recovered_files:
    print(file['name'] + ', Start offset: ' + hex(file['start']) + ', End Offset: ' + hex(file['end']))
    print('SHA-256: ' + file['sha'])
    print()