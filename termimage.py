#!/usr/bin/python
import Image, ImageOps, ImageEnhance
import urllib2
from cStringIO import StringIO
from math import sqrt
from optparse import OptionParser
import json

parser = OptionParser(description='''Takes an image URL and outputs it in the terminal using ANSI terminal colors. Also contains
                                    options for xterm colors and IRC output.''')
parser.add_option('--hires', action='store_true', dest='high_res', 
                    default=False, help='Output image is twice the resolution, but only uses half the colors.')
parser.add_option('-c', '--contrast', action='store', dest='contrast',
                    type=float, default=1, metavar='VALUE', help='Set the contrast level. Default is 1.0.')
parser.add_option('-b', '--black', action='store', dest='black_threshold',
                    type=float, default=0.0, metavar='VALUE', help='Set the black threshold. Default is 0.0.')
parser.add_option('-w', '--white', action='store', dest='white_threshold',
                    type=float, default=0.0, metavar='VALUE', help='Set the white threshold. Default is 0.0.')
parser.add_option('-s', '--step', action='store', dest='step',
                    type=int, default=2, metavar='STEP')
parser.add_option('-i', '--irc',  action='store_true', dest='irc',
                    default=False, help='Output image using IRC color codes.')
parser.add_option('-x', '--xterm', action='store_true', dest='xterm',
                    default=False, help='Uses xterm 256 colors.')
parser.add_option('-l', '--local', action='store', dest='filename',
                    help='Path to local file.')
parser.add_option('--height', action='store', dest='height',
                    type=float, default=100.0, metavar='VALUE', help='''Desired height of the output. Aspect ratio
                                                                    is always preserved. Default is 100.''')
parser.add_option('--width', action='store', dest='width',
                    type=float, default=100.0, metavar='VALUE', help='''Desired width of the output. Aspect ratio
                                                                    is always preserved. Default is 100.''')
parser.add_option('-m', '--mode', action='store', dest='mode', type='choice', default='antialias', metavar='MODE',
                    choices=['antialias', 'nearest', 'bicubic', 'bilinear'], help='Sets the resize mode. Default is antialias.')
parser.add_option('-g', '--google', action='store', dest='google', metavar='QUERY', 
                    help='Search Google for an image matching the search query.')
parser.add_option('-d', '--dither', action='store_true', dest='dither', default=False,
                    help='Enable dithering. Default is off.')
parser.add_option('--bw', action='store_true', dest='black_and_white', default=False,
                    help='Enable black and white')

(options, args) = parser.parse_args()


def rgb_to_xyz(R, G, B):
    '''From http://www.easyrgb.com/index.php?X=MATH'''
    var_R = (R / 255.)
    var_G = (G / 255.)
    var_B = (B / 255.)

    if var_R > 0.04045:
        var_R = ((var_R + 0.055) / 1.055) ** 2.4
    else:
        var_R /= 12.92

    if var_G > 0.04045:
        var_G = (( var_G + 0.055) / 1.055) ** 2.4
    else:
        var_G /= 12.92
    if var_B > 0.04045:
        var_B = ((var_B + 0.055) / 1.055) ** 2.4
    else:
        var_B /= 12.92

    var_R *= 100
    var_G *= 100
    var_B *= 100

    X = var_R * 0.4124 + var_G * 0.3576 + var_B * 0.1805
    Y = var_R * 0.2126 + var_G * 0.7152 + var_B * 0.0722
    Z = var_R * 0.0193 + var_G * 0.1192 + var_B * 0.9505

    return X,Y,Z

def xyz_to_cielab(X, Y, Z):
    '''From http://www.easyrgb.com/index.php?X=MATH'''
    ref_X =  95.047
    ref_Y = 100.000
    ref_Z = 108.883

    var_X = X / ref_X
    var_Y = Y / ref_Y
    var_Z = Z / ref_Z

    if var_X > 0.008856:
        var_X **= (1./3.)
    else:
        var_X = (7.787 * var_X) + (16. / 116.)
    if var_Y > 0.008856:
        var_Y **= (1./3.)
    else:
        var_Y = (7.787 * var_Y) + (16. / 116.)
    if var_Z > 0.008856:
        var_Z **= ( 1./3. )
    else:
        var_Z = (7.787 * var_Z) + (16. / 116.)

    CIE_L = (116 * var_Y) - 16.
    CIE_a = 500. * (var_X - var_Y)
    CIE_b = 200. * (var_Y - var_Z)

    return CIE_L, CIE_a, CIE_b

def rgb_to_cielab(R, G, B):
    X, Y, Z = rgb_to_xyz(R, G ,B) 
    CIE_L, CIE_a, CIE_b = xyz_to_cielab(X, Y, Z)
    return CIE_L, CIE_a, CIE_b

irc_rgb_values = [
                (255,255,255),
                (0,0,0),
                (0, 0, 127),
                (0, 147, 0),
                (255, 0, 0),
                (127, 0, 0),
                (156, 0, 156),
                (252, 127, 0),
                (255, 255, 0),
                (0, 252, 0),
                (0, 147, 147),
                (0, 255, 255),
                (0, 0, 252),
                (255, 0, 255),
                (127, 127, 127),
                (210, 210, 210)
                ]

rgb_values = [
              (0,0,0),
              (128,0,0),
              (0,128,0),
              (128,128,0),
              (0,0,128),
              (128,0,128),
              (0,128,128),
              (192,192,192),
              (128,128,128),
              (255,0,0),
              (0,255,0),
              (255,255,0),
              (0,0,255),
              (255,0,255),
              (0,255,255),
              (255,255,255)
              ]

xterm_rgb_values = [
                (0, 0, 0),
                (0, 0, 95),
                (0, 0, 135),
                (0, 0, 175),
                (0, 0, 215),
                (0, 0, 255),
                (0, 95, 0),
                (0, 95, 95),
                (0, 95, 135),
                (0, 95, 175),
                (0, 95, 215),
                (0, 95, 255),
                (0, 135, 0),
                (0, 135, 95),
                (0, 135, 135),
                (0, 135, 175),
                (0, 135, 215),
                (0, 135, 255),
                (0, 175, 0),
                (0, 175, 95),
                (0, 175, 135),
                (0, 175, 175),
                (0, 175, 215),
                (0, 175, 255),
                (0, 215, 0),
                (0, 215, 95),
                (0, 215, 135),
                (0, 215, 175),
                (0, 215, 215),
                (0, 215, 255),
                (0, 255, 0),
                (0, 255, 95),
                (0, 255, 135),
                (0, 255, 175),
                (0, 255, 215),
                (0, 255, 255),
                (95, 0, 0),
                (95, 0, 95),
                (95, 0, 135),
                (95, 0, 175),
                (95, 0, 215),
                (95, 0, 255),
                (95, 95, 0),
                (95, 95, 95),
                (95, 95, 135),
                (95, 95, 175),
                (95, 95, 215),
                (95, 95, 255),
                (95, 135, 0),
                (95, 135, 95),
                (95, 135, 135),
                (95, 135, 175),
                (95, 135, 215),
                (95, 135, 255),
                (95, 175, 0),
                (95, 175, 95),
                (95, 175, 135),
                (95, 175, 175),
                (95, 175, 215),
                (95, 175, 255),
                (95, 215, 0),
                (95, 215, 95),
                (95, 215, 135),
                (95, 215, 175),
                (95, 215, 215),
                (95, 215, 255),
                (95, 255, 0),
                (95, 255, 95),
                (95, 255, 135),
                (95, 255, 175),
                (95, 255, 215),
                (95, 255, 255),
                (135, 0, 0),
                (135, 0, 95),
                (135, 0, 135),
                (135, 0, 175),
                (135, 0, 215),
                (135, 0, 255),
                (135, 95, 0),
                (135, 95, 95),
                (135, 95, 135),
                (135, 95, 175),
                (135, 95, 215),
                (135, 95, 255),
                (135, 135, 0),
                (135, 135, 95),
                (135, 135, 135),
                (135, 135, 175),
                (135, 135, 215),
                (135, 135, 255),
                (135, 175, 0),
                (135, 175, 95),
                (135, 175, 135),
                (135, 175, 175),
                (135, 175, 215),
                (135, 175, 255),
                (135, 215, 0),
                (135, 215, 95),
                (135, 215, 135),
                (135, 215, 175),
                (135, 215, 215),
                (135, 215, 255),
                (135, 255, 0),
                (135, 255, 95),
                (135, 255, 135),
                (135, 255, 175),
                (135, 255, 215),
                (135, 255, 255),
                (175, 0, 0),
                (175, 0, 95),
                (175, 0, 135),
                (175, 0, 175),
                (175, 0, 215),
                (175, 0, 255),
                (175, 95, 0),
                (175, 95, 95),
                (175, 95, 135),
                (175, 95, 175),
                (175, 95, 215),
                (175, 95, 255),
                (175, 135, 0),
                (175, 135, 95),
                (175, 135, 135),
                (175, 135, 175),
                (175, 135, 215),
                (175, 135, 255),
                (175, 175, 0),
                (175, 175, 95),
                (175, 175, 135),
                (175, 175, 175),
                (175, 175, 215),
                (175, 175, 255),
                (175, 215, 0),
                (175, 215, 95),
                (175, 215, 135),
                (175, 215, 175),
                (175, 215, 215),
                (175, 215, 255),
                (175, 255, 0),
                (175, 255, 95),
                (175, 255, 135),
                (175, 255, 175),
                (175, 255, 215),
                (175, 255, 255),
                (215, 0, 0),
                (215, 0, 95),
                (215, 0, 135),
                (215, 0, 175),
                (215, 0, 215),
                (215, 0, 255),
                (215, 95, 0),
                (215, 95, 95),
                (215, 95, 135),
                (215, 95, 175),
                (215, 95, 215),
                (215, 95, 255),
                (215, 135, 0),
                (215, 135, 95),
                (215, 135, 135),
                (215, 135, 175),
                (215, 135, 215),
                (215, 135, 255),
                (215, 175, 0),
                (215, 175, 95),
                (215, 175, 135),
                (215, 175, 175),
                (215, 175, 215),
                (215, 175, 255),
                (215, 215, 0),
                (215, 215, 95),
                (215, 215, 135),
                (215, 215, 175),
                (215, 215, 215),
                (215, 215, 255),
                (215, 255, 0),
                (215, 255, 95),
                (215, 255, 135),
                (215, 255, 175),
                (215, 255, 215),
                (215, 255, 255),
                (255, 0, 0),
                (255, 0, 95),
                (255, 0, 135),
                (255, 0, 175),
                (255, 0, 215),
                (255, 0, 255),
                (255, 95, 0),
                (255, 95, 95),
                (255, 95, 135),
                (255, 95, 175),
                (255, 95, 215),
                (255, 95, 255),
                (255, 135, 0),
                (255, 135, 95),
                (255, 135, 135),
                (255, 135, 175),
                (255, 135, 215),
                (255, 135, 255),
                (255, 175, 0),
                (255, 175, 95),
                (255, 175, 135),
                (255, 175, 175),
                (255, 175, 215),
                (255, 175, 255),
                (255, 215, 0),
                (255, 215, 95),
                (255, 215, 135),
                (255, 215, 175),
                (255, 215, 215),
                (255, 215, 255),
                (255, 255, 0),
                (255, 255, 95),
                (255, 255, 135),
                (255, 255, 175),
                (255, 255, 215),
                (255, 255, 255),
                (8, 8, 8),
                (18, 18, 18),
                (28, 28, 28),
                (38, 38, 38),
                (48, 48, 48),
                (58, 58, 58),
                (68, 68, 68),
                (78, 78, 78),
                (88, 88, 88),
                (98, 98, 98),
                (108, 108, 108),
                (118, 118, 118),
                (128, 128, 128),
                (138, 138, 138),
                (148, 148, 148),
                (158, 158, 158),
                (168, 168, 168),
                (178, 178, 178),
                (188, 188, 188),
                (198, 198, 198),
                (208, 208, 208),
                (218, 218, 218),
                (228, 228, 228),
                (238, 238, 238)
                ]

bw_xterm_rgb_values = [
                (8, 8, 8),
                (18, 18, 18),
                (28, 28, 28),
                (38, 38, 38),
                (48, 48, 48),
                (58, 58, 58),
                (68, 68, 68),
                (78, 78, 78),
                (88, 88, 88),
                (98, 98, 98),
                (108, 108, 108),
                (118, 118, 118),
                (128, 128, 128),
                (138, 138, 138),
                (148, 148, 148),
                (158, 158, 158),
                (168, 168, 168),
                (178, 178, 178),
                (188, 188, 188),
                (198, 198, 198),
                (208, 208, 208),
                (218, 218, 218),
                (228, 228, 228),
                (238, 238, 238)
            ]

if options.irc:
    rgb_values = irc_rgb_values
if options.high_res and not options.xterm:
    rgb_values = rgb_values[:8]
if options.xterm:
    if options.black_and_white:
        rgb_values = bw_xterm_rgb_values
    else:
        rgb_values = rgb_values + xterm_rgb_values

lab_values = [rgb_to_cielab(r,g,b) for (r,g,b) in rgb_values]

index_to_ansi_front = ['30',
                 '31',
                 '32',
                 '33',
                 '34',
                 '35',
                 '36',
                 '37',
                 '30;1',
                 '31;1',
                 '32;1',
                 '33;1',
                 '34;1',
                 '35;1',
                 '36;1',
                 '37;1'
                 ]

index_to_ansi_back = [
                 '40',
                 '41',
                 '42',
                 '43',
                 '44',
                 '45',
                 '46',
                 '47',
                 '40;1',
                 '41;1',
                 '42;1',
                 '43;1',
                 '44;1',
                 '45;1',
                 '46;1',
                 '47;1'
                 ]

def get_image():
    if options.filename:
        try:
            fs = open(options.filename)
        except IOError as e:
            sys.exit(e)
    else:
        if options.google:
            url = google()
        else:
            url = args[0]
        headers = {'User-Agent' : 'pjaeBot'}
        request = urllib2.Request(url, None, headers)
        fs = StringIO(urllib2.urlopen(request).read())
    return Image.open(fs)

def get_mode():
    if options.mode == 'antialias':
        return Image.ANTIALIAS
    elif options.mode == 'bicubic':
        return Image.BICUBIC
    elif options.mode == 'bilinear':
        return Image.BILINEAR
    else:
        return Image.NEAREST
       
def quantize(im):
    pal_im = im.convert('P')
    vals = []
    for val in rgb_values:
        for n in val:
            vals.append(n)
    pal_im.putpalette(vals)
#    im = im.convert('RGB')
    im = im.quantize(palette=pal_im)
    im = im.convert('RGB')
    return im
    

def process_image():
    im = get_image()
    im = im.convert('RGB')
#    im = quantize(im)
    width = im.size[0]
    height = im.size[1]
    ratio = get_ratio(width, height)
    resize_width = int(width * ratio + 0.5)
    resize_height = int(height * ratio + 0.5)
    mode = get_mode()
    im = im.resize((resize_width,resize_height), mode)
    if options.dither:
        pim = im.convert('P')
        im = pim.convert('RGB')
    im = ImageEnhance.Contrast(im).enhance(options.contrast)
    template = get_template()
    line = ''
    prev_fore = None
    prev_back = None
    fore = None
    back = None
    for y in range(0, resize_height, options.step):
        for x in range(resize_width):
            if options.high_res:
                fore, back = (get_nearest_rgb(im, x, y), get_nearest_rgb(im, x, y+1, back=True))
                if prev_fore == fore and prev_back == back and x != 0:
                    line += u'\u2580'
                elif prev_fore == fore and x != 0:
                    line += template['back'].format(fore, back) + u'\u2580' 
                elif prev_back == back and x != 0:
                    line += template['fore'].format(fore, back) + u'\u2580' 
                else:
                    line += template['both'].format(fore, back) + u'\u2580' 
            else:
                back = get_nearest_rgb(im, x, y, back=True)
                if prev_back == back and x != 0:
                    line += u' '
                else:
                    line += template.format(back) + u' '
            prev_fore, prev_back = fore, back
        if not options.irc:
            line += '\033[0m'
        print line.encode('utf8')
        line = ''

def get_ratio(width, height):
    max_width = options.width
    max_height = options.height
    return min(max_width/width, max_height/height)

def get_template():
    if options.irc:
        if options.high_res:
            return {'both': '\x03{0},{1}', 'fore': '\x03{0}', 'back': '\x03,{1}'}
        else:
            return '\x03{0},{0}'
    elif options.xterm:
        if options.high_res:
            return {'both': '\033[38;5;{0}m\033[48;5;{1}m', 'fore': '\033[38;5;{0}m', 'back': '\033[48;5;{1}m'}
        else:   
            return '\033[48;5;{0}m'
    else:
        if options.high_res:
            return {'both': '\033[{0};{1}m', 'fore': '\033[{0}m', 'back': '\033[{1}m'}
        else:
            return '\033[{0}m'


def get_nearest_rgb(im, x, y, back=False): #deprecated
    nearest = None
    try:
        r1, g1, b1 = im.getpixel((x, y))
    except IndexError:
        r1 = g1 = b1 = 0
    l1, a1, b1 = rgb_to_cielab(r1,g1,b1)
    for index, (l2, a2, b2) in enumerate(lab_values):
#        current = sqrt(((r2-r1)*0.3)**2 + ((g2-g1)*0.59)**2 + ((b2-b1)*0.11)**2)
#        current = sqrt((r2-r1)**2 + (g2-g1)**2 + (b2-b1)**2)
        dL = l1 - l2
        c1 = sqrt(a1**2 + b1**2)
        c2 = sqrt(a2**2 + b2**2)
        dC = c1 - c2
        dA = a1 - a2
        dB = b1 - b2
        dH = dA**2 + dB ** 2 - dC **2
        dE = sqrt((dL/1) ** 2 + (dC/(1 + 0.045 * c1)) ** 2 + (dH/(1+0.015*c2)**2) )
        if dE < nearest or nearest is None:
#            if (i == 0 or i == 15) and dE < options.black_threshold or (i == 7 or i == 15) and dE < options.white_threshold:
#                pass
#            else:
            nearest = dE 
            color_index = index
    if options.irc or options.xterm:
        if options.xterm and options.black_and_white:
            color_index += 232
        return color_index
    else:
        if back:
            return index_to_ansi_back[color_index]
        else:
            return index_to_ansi_front[color_index]

def google():
    uri = 'http://ajax.googleapis.com/ajax/services/search/images'
    query = options.google.decode('utf8')
    args = '?v=1.0&safe=off&q=' + urllib2.quote(query.encode('utf-8'))
    raw = urllib2.urlopen(uri + args)
    json_object = json.load(raw)
    try:
        url = json_object['responseData']['results'][0]['unescapedUrl']
        return url
    except IndexError:
        sys.exit('Something went wrong with the google search!')

if __name__ == '__main__':
    import sys
    process_image()
