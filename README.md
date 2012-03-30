Dependency: PIL (http://www.pythonware.com/products/pil/).

TODO:

- ???

Screenshot:

rc="http://i.imgur.com/6u2lY.png" alt="termimage" title="termimage" />

Usage: termimage.py [options]

Takes an image URL and outputs it in the terminal using ANSI terminal colors.
Also contains                                     options for xterm colors and
IRC output.

Options:
  -h, --help            show this help message and exit
  --hires               Output image is twice the resolution, but only uses
                        half the colors.
  -c VALUE, --contrast=VALUE
                        Set the contrast level. Default is 1.0.
  -b VALUE, --black=VALUE
                        Set the black threshold. Default is 0.0.
  -w VALUE, --white=VALUE
                        Set the white threshold. Default is 0.0.
  -s STEP, --step=STEP  
  -i, --irc             Output image using IRC color codes.
  -x, --xterm           Uses xterm 256 colors.
  -l FILENAME, --local=FILENAME
                        Path to local file.
  --height=VALUE        Desired height of the output. Aspect ratio
                        is always preserved. Default is 100.
  --width=VALUE         Desired width of the output. Aspect ratio
                        is always preserved. Default is 100.
