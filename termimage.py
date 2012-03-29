#!/usr/bin/python
import Image, ImageOps, ImageEnhance
import urllib2
from cStringIO import StringIO
from math import sqrt
from optparse import OptionParser

parser = OptionParser(description='Takes an image URL and outputs it in the terminal using ANSI terminal colors')
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

if options.irc:
    rgb_values = irc_rgb_values
if options.high_res and not options.xterm:
    rgb_values = rgb_values[:8]
if options.xterm:
    rgb_values = rgb_values + xterm_rgb_values

lab_values = [rgb_to_cielab(r,g,b) for (r,g,b) in rgb_values]

index_to_irc = ['0',
                '1',
                '2',
                '3',
                '4',
                '5',
                '6',
                '7',
                '8',
                '9',
                '10',
                '11',
                '12',
                '13',
                '14',
                '15'
                ]

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
        fs = open(options.filename)
    else:
        headers = {'User-Agent' : 'pjaeBot'}
        request = urllib2.Request(args[0], None, headers)
        fs = StringIO(urllib2.urlopen(request).read())
    return Image.open(fs)
       

def process_image():
    im = get_image()
    im = im.convert('RGB')
    im.thumbnail((120,100), Image.ANTIALIAS)
    im = ImageEnhance.Contrast(im).enhance(options.contrast)
    final_image = []
    template = get_template()
    for x in range(0, im.size[1], options.step):
        if options.high_res:
            line = u'\u2580'.join(template.format(k,j) for k, j in [(get_nearest_rgb(im, i, x), get_nearest_rgb(im, i, x+1, back=True)) for i in range(im.size[0])])
        else:
            line = u' '.join(template.format(k) for k in [(get_nearest_rgb(im, i, x, back=True)) for i in range(im.size[0])])
        if not options.irc:
            line += '\033[0m'
        final_image.append(line)
    return final_image

def get_template():
    if options.irc:
        if options.high_res:
            return '\x03{0},{1}'
        else:
            return '\x03{0},{0}'
    elif options.xterm:
        if options.high_res:
            return '\033[38;5;{0}m\033[48;5;{1}m'
        else:   
            return '\033[48;5;{0}m'
    else:
        if options.high_res:
            return '\033[{0};{1}m'
        else:
            return '\033[{0}m'



def get_nearest_rgb(im, x, y, back=False): #deprecated
    nearest = None
#    current = 1000
    color_index = -1
    try:
        r1, g1, b1 = im.getpixel((x, y))
    except IndexError:
        r1 = g1 = b1 = 0
    l1, a1, b1 = rgb_to_cielab(r1,g1,b1)
    for i, (l2, a2, b2) in enumerate(lab_values):
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
        if dE < nearest or not nearest:
            if (i == 0 or i == 15) and dE < options.black_threshold or (i == 7 or i == 15) and dE < options.white_threshold:
                pass
            else:
                nearest = dE 
                color_index = i
    if options.irc:
        return index_to_irc[color_index]
    elif options.xterm:
        return color_index
    else:
        if back:
            return index_to_ansi_back[color_index]
        else:
            return index_to_ansi_front[color_index]

if __name__ == '__main__':
    import sys
    for i in process_image():
        print i.encode('utf8')
