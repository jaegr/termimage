#!/usr/bin/python
import rgb_values
import color_conversions
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
                    type=float, metavar='VALUE', help='Set the contrast level. Default is 1.0.')
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

if options.irc:
    rgb_values = rgb_values.irc_rgb_values
elif options.high_res and not options.xterm:
    rgb_values = rgb_values.default_rgb_values[:8]
elif options.xterm:
    if options.black_and_white:
        rgb_values = rgb_values.bw_xterm_rgb_values
    else:
        rgb_values = rgb_values.default_rgb_values + rgb_values.xterm_rgb_values
else:
    rgb_values = rgb_values.default_rgb_values

lab_values = [color_conversions.rgb_to_cielab(r,g,b) for (r,g,b) in rgb_values]

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
    '''
    Retrieves the image file from the given input method; local file, google search or url
    '''
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
    if options.mode.lower() == 'antialias':
        return Image.ANTIALIAS
    elif options.mode.lower() == 'bicubic':
        return Image.BICUBIC
    elif options.mode.lower() == 'bilinear':
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
    if options.contrast:
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
    '''
    Get the string template based on the options
    '''
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
    l1, a1, b1 = color_conversions.rgb_to_cielab(r1,g1,b1)
    for index, (l2, a2, b2) in enumerate(lab_values):
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
    '''
    Returns the first result from Google Images when searching for the user provided query string
    '''
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
    process_image()
