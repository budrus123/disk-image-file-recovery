##################   Imports  ################################

import re


################## File headers and footers ##################

disk_image_name = 'Project2Updated.dd'

pdf_header_string = '25504446'
pdf_footer_string = '0A2525454F46'

gif_header_string = '474946383961'
gif_footer_string = '003B'

bmp_header_string = '424D'

docx_header_string = '504B030414000600'
docx_footer_string = '504B0506'
''
AVI_header_string = '52494646'

gif_header_string = '474946383961'
gif_footer_string = '003B000000000000'

png_header_string = '89504E470D0A1A0A'   ##-- 2 HITS - DECK 6/SLIDE 27 HAS INFO; 0X0488E29 (DOES NOT START FROM THE LEFT) AND 0X04AA000(STARTS FROM THE LEFT)
png_footer_string = '49454E44AE426082'   ##-- 2 HITS - DECK 6/SLIDE 27 HAS INFO; 0X04A7284 AND 0X04E1A73

jpg_header_string = 'FFD8FFE0'
jpg_footer_string = 'FFD900000000'
jpg_header_string_ffdb = 'FFD8FFDB'


supported_types = ['MPG', 'PDF','BMP','GIF','JPG','DOCX','AVI','PNG']
supported_types = ['PDF','AVI','DOCX','GIF']
supported_types = ['GIF']
# supported_types = ['PNG']
# supported_types = ['JPG','JPG_FFDB']

# GIF, DOCX -> Mahmoud
# JPG, PNG -> Janet
# BMP, ZIP -> WARREN

"""
Variables for the program run:
Signature is a dictionary has different file types (key),
each element has the header and footer string in it

image_bytes contains the disk image bytes (type: bytes)

bytes_hex contains the disk image bytes (as a string) in hex (type: string)
note that bytes_hex is used to look for the headers, it is a string with no spaces
in between the bytes
"""

signatures = {}
image_bytes = ""
bytes_hex = ""

"""
Helper function that takes a string and 
returns the string as a string of pairs of bytes
split by spaces. eg: AB32FF => AB 32 FF
"""
def hex_to_readable_line(hex_line):
    string = ""
    n = 2
    out = [(hex_line[i:i + n]) for i in range(0, len(hex_line), n)]
    for element  in out:
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
before any header
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
    return int(byte_location/2)


"""
Initialization function for the signature dictionaries
"""
def init_signatures():
    for file_type in supported_types:
        signature = {}
        signature['header'] = ''
        signature['footer'] = ''
        signatures[file_type] = signature

    # #PDF
    # signatures['PDF']['header'] = pdf_header_string
    # signatures['PDF']['footer'] = pdf_footer_string
    #
    # # DOCX
    # signatures['DOCX']['header'] = docx_header_string
    # signatures['DOCX']['footer'] = docx_footer_string
    #
    # #AVI
    # signatures['AVI']['header'] = AVI_header_string
    # signatures['AVI']['footer'] = ''

    #GIF
    signatures['GIF']['header'] = gif_header_string
    signatures['GIF']['footer'] = gif_footer_string

    #PNG
    # signatures['PNG']['header'] = png_header_string
    # signatures['PNG']['footer'] = png_footer_string

    # JPG
    # signatures['JPG']['header'] = jpg_header_string
    # signatures['JPG']['footer'] = jpg_footer_string
    #
    # signatures['JPG_FFDB']['header'] = jpg_header_string_ffdb
    # signatures['JPG_FFDB']['footer'] = jpg_footer_string



"""
Function to open the file (dd image)
and store the bytes and string of hex in a 
global variable.
"""
def open_file(path):
    global image_bytes, bytes_hex
    with open(path, 'rb') as f:
        image_bytes = f.read() #bytes
        bytes_hex = image_bytes.hex().upper() #string



"""
Handling function for PDF files. 
Note that PDF files have multiple 
footers (might) for a single file
"""
def handle_pdf(headers, footers):
    header_count = len(headers)
    footer_count = len(footers)

    file_start = -1
    file_end = -1
    footer_iterator = -1

    """
    if no headers found, return.
    """
    if header_count == 0 :
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
        will be the last footer with an offset before the current header.
        """
        if index == (header_count - 1):
            # add 6 for file footer length
            file_end = get_offset_for_location(footers[footer_count - 1] + 6)
        else:
            footer_iterator = 0
            while footers[footer_iterator] < headers[index+1]:
                footer_iterator +=1
            file_end = get_offset_for_location(footers[footer_iterator - 1]) + 6

        """
        Carve bytes out from the image bytes
        """
        file_bytes = image_bytes[file_start:file_end]
        f = open('pdf_'+str(index)+'.pdf', 'wb')
        f.write(file_bytes)
        f.close()


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
    if header_count == 0 :
        return

    """
    for each header, get size from the start of the header + 4
    the end of the size will be at the size start +3
    then convert that size to little indian 
    and carve file out
    """
    for index,header in enumerate(headers):
        byte_offset = get_offset_for_location(header)
        size_start = byte_offset + 4
        size_end = size_start + 3
        size_bytes = image_bytes[size_start:size_end]
        size_int = int.from_bytes(size_bytes, "little")
        file_end = byte_offset + size_int
        file_bytes = image_bytes[byte_offset:file_end]
        f = open('avi_' + str(index) + '.avi', 'wb')
        f.write(file_bytes)
        f.close()



def handle_docx(headers, footers):
    header_count = len(headers)
    footer_count = len(footers)

    file_start = -1
    file_end = -1
    footer_iterator = -1

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
        will be the last footer with an offset before the current header.
        """
        if index == (header_count - 1):
            # add 22 for file footer length
            file_end = get_offset_for_location(footers[footer_count - 1]) + 22
        else:
            footer_iterator = 0
            while footers[footer_iterator] < headers[index + 1]:
                footer_iterator += 1
            file_end = get_offset_for_location(footers[footer_iterator - 1]) + 22

        """
        Carve bytes out from the image bytes
        """
        file_bytes = image_bytes[file_start:file_end]
        f = open('docx_' + str(index) + '.docx', 'wb')
        f.write(file_bytes)
        f.close()


##############START OF PNG HANDLE #####################

def handle_png(headers, footers):
    header_count = len(headers)
    footer_count = len(footers)

    file_start = -1
    file_end = -1
    footer_iterator = -1

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
        will be the last footer with an offset before the current header.
        """
        if index == (header_count):
            file_end = get_offset_for_location(footers[footer_count])+ 8
        else:
            footer_iterator = 0
            while footers[footer_iterator] < headers[index]:
                footer_iterator += 1
            file_end = get_offset_for_location(footers[footer_iterator]) + 8
            #TODO: add the bytes for the footer

        """
        Carve bytes out from the image bytes
        """
        file_bytes = image_bytes[file_start:file_end]
        f = open('png_' + str(index) + '.png', 'wb')
        f.write(file_bytes)
        f.close()


##############END OF PNG#####################

def handle_gif(headers, footers):
    header_count = len(headers)
    footer_count = len(footers)

    file_start = -1
    file_end = -1
    footer_iterator = -1

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
        will be the last footer with an offset before the current header.
        """
        footer_iterator = 0
        while footers[footer_iterator] < headers[index]:
            footer_iterator += 1
        file_end = get_offset_for_location(footers[footer_iterator]) + 2


        """
        Carve bytes out from the image bytes
        """

        file_bytes = image_bytes[file_start:file_end]
        f = open("gif_new_" + str(index) + '.gif', 'wb')
        f.write(file_bytes)
        f.close()

##############START OF JPG HANDLE #####################

def handle_jpg(headers, footers, file_type):
    header_count = len(headers)
    footer_count = len(footers)

    file_start = -1
    file_end = -1
    footer_iterator = -1

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
        will be the last footer with an offset before the current header.
        """
        footer_iterator = 0
        while footers[footer_iterator] < headers[index]:
            footer_iterator += 1
        file_end = get_offset_for_location(footers[footer_iterator]) + 2


        """
        Carve bytes out from the image bytes
        """

        file_bytes = image_bytes[file_start:file_end]
        f = open(file_type +"_" + str(index) + '.jpg', 'wb')
        f.write(file_bytes)
        f.close()



        #############END OF JPG#####################


################## Main ######################################

"""
Initialization signatures and open the file
"""
init_signatures()
open_file(disk_image_name)


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
        handle_pdf(header_occ, footer_occ)
    elif sig == 'AVI':
        handle_avi(header_occ)
    elif sig == 'DOCX':
        handle_docx(header_occ,footer_occ)
    elif sig == 'GIF':
        handle_gif(header_occ,footer_occ)
    elif sig == 'PNG':
        handle_png(header_occ,footer_occ)
    elif sig == 'JPG':
        handle_jpg(header_occ, footer_occ, 'jpg')
    elif sig == 'JPG_FFDB':
        handle_jpg(header_occ, footer_occ, 'jpg_ffdb')
