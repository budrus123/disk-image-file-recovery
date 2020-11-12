##################   Imports  ##################

import binascii
import re


################## Constants ##################

pdf_header_string = "25504446" #hex
pdf_footer_string = "0A2525454F46" #hex

gif_header_string = '474946383961'
gif_footer_string = '003B'

bmp_header_string = '424D'

docx_header_string = '504B030414000600'
docx_footer_string = '504B0506'

AVI_header_string = '52494646'

gif_header_string = '474946383961'
gif_footer_string = '003B'


supported_types = ['MPG', 'PDF','BMP','GIF','ZIP','JPG','DOCX','AVI','PNG']
supported_types = ['PDF','DOCX', 'AVI']
supported_types = ['GIF']

signatures = {}
image_bytes = ""
bytes_hex = ""

def hex_to_readable_line(hex_line):
    string = ""
    n = 2
    out = [(hex_line[i:i + n]) for i in range(0, len(hex_line), n)]
    for element  in out:
        string += str(element) + " "
    return string

#removes headers that don't start at sectors (512) and cluster
def remove_illegal_headers(headers):
    valid_headers = headers
    for occurrence in headers:
        o_location = get_offset_for_location(occurrence)
        if o_location % 512 != 0:
            valid_headers.remove(occurrence)
    return valid_headers


def find_all_occurrences(substring, string):
    return [m.start() for m in re.finditer(substring, string)]


def get_offset_for_location(byte_location):
    return int(byte_location/2)


def init_signatures():
    for file_type in supported_types:
        signature = {}
        signature['header'] = ""
        signature['footer'] = ""
        signatures[file_type] = signature

    # #PDF
    # signatures['PDF']['header'] = pdf_header_string
    # signatures['PDF']['footer'] = pdf_footer_string
    #
    # #DOCX
    # signatures['DOCX']['header'] = docx_header_string
    # signatures['DOCX']['footer'] = docx_footer_string

    #AVI
    # signatures['AVI']['header'] = AVI_header_string
    # signatures['AVI']['footer'] = ''

    #GIF
    signatures['GIF']['header'] = gif_header_string
    signatures['GIF']['footer'] = gif_footer_string

def open_file(path):
    global image_bytes, bytes_hex
    with open(path, 'rb') as f:
        image_bytes = f.read()
        bytes_hex = image_bytes.hex().upper()



# pdf files have multiple footers per file
def handle_pdf(headers, footers):
    header_count = len(headers)
    footer_count = len(footers)

    file_start = -1
    file_end = -1
    footer_iterator = -1
    if header_count == 0 :
        return

    current_offset = headers[0]
    for index in range(header_count):
        file_start = get_offset_for_location(headers[index])
        #reached last header
        if index == (header_count - 1):
            # add 6 for file footer length
            file_end = get_offset_for_location(footers[footer_count - 1] + 6)
        else:
            footer_iterator = 0
            while footers[footer_iterator] < headers[index+1]:
                footer_iterator +=1
            file_end = get_offset_for_location(footers[footer_iterator - 1]) + 6

        file_bytes = image_bytes[file_start:file_end]
        f = open('pdf_'+str(index)+'.pdf', 'wb')
        f.write(file_bytes)
        f.close()




def handle_avi(headers):

    header_count = len(headers)
    print(headers)

    if header_count == 0 :
        return

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

def handle_gif(headers, footers):

    header_count = len(headers)
    footer_count = len(footers)
    print(headers)

    if header_count == 0:
        return

    for index, header in enumerate(headers):
        start = header
        footer_iterator = 0
        while footer_iterator < footer_count:
            if footers[footer_iterator] > header:
                break
            footer_iterator += 1

        end = footers[footer_iterator]
        print(end)
        file_start = get_offset_for_location(start)
        file_end = get_offset_for_location(end) + 2 #footer is 2 bytes
        file_bytes = image_bytes[file_start:file_end]
        f = open('gif_' + str(index) + '.gif', 'wb')
        f.write(file_bytes)
        f.close()


# docx files have multiple headers per file
def handle_docx(headers, footers):
    header_count = len(headers)
    footer_count = len(footers)

    print(headers)
    print(footers)

    # to find correct headers
    header_iterator = 0
    file_start = -1
    file_end = -1

    if header_count == 0:
        return

    file_start = get_offset_for_location(9502720)
    file_end = get_offset_for_location(17834478) + 22

    file_bytes = image_bytes[file_start:file_end]
    f = open('docx_' + 'ss' + '.docx', 'wb')
    f.write(file_bytes)
    f.close()

    # for index in range(footer_count):
    #     file_start = get_offset_for_location(headers[header_iterator])
    #     file_end = get_offset_for_location(footers[index]) + 22
    #
    #     file_bytes = image_bytes[file_start:file_end]
    #     f = open('docx_' + str(index) + '.docx', 'wb')
    #     f.write(file_bytes)
    #     f.close()

################## Main ##################


init_signatures()
open_file('Project2.dd')

# print(find_all_occurrences('474946383961', bytes_hex))
print(find_all_occurrences('003B', bytes_hex))

for sig in signatures:
    sig_header = signatures[sig]['header']
    sig_footer = signatures[sig]['footer']

    header_occ = find_all_occurrences(sig_header, bytes_hex)
    header_occ = remove_illegal_headers(header_occ)

    if sig_footer != '':
        footer_occ = find_all_occurrences(sig_footer, bytes_hex)

    if sig == 'PDF':
        handle_pdf(header_occ, footer_occ)
    elif sig == 'DOCX':
        handle_docx(header_occ, footer_occ)
    elif sig == 'AVI':
        handle_avi(header_occ)
    elif sig == 'GIF':
        handle_gif(header_occ, footer_occ)