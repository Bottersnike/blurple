#!/usr/bin/env python3
from scipy import ndimage
import numpy as np
import argparse
import time
import sys
import os

from PIL import Image, ImageSequence, ImageEnhance, ImageOps

MIN_T = 130
MAX_T = 240
RAD_DIV = 4000
DESCRIPTION = 'Convert an image to black and white'
VERSION = '0.0.1a'
IMAGE_EXTENTIONS = ['png', 'jpg', 'jpeg', 'bmp']


class Parser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_usage()
        sys.exit(2)


def basic_filter(in_file, out_file, min_t, max_t, thresh=None, gs=None):
    if gs is not None:
        img = pygame.image.load(in_file)

        arr = pygame.surfarray.array3d(img)
        del img
        gs = np.mean(arr, axis=2)
        del arr

    if thresh is None:
        avg = np.sum(gs) / (len(gs) * len(gs[0])) / 3
        thresh = min(max_t, max(min_t, avg))
        del avg
    new_img = (gs > thresh) * 255
    new_img = new_img.astype(int)
    del gs, thresh

    surf = pygame.surfarray.make_surface(new_img)
    pygame.image.save(surf, out_file)
    del new_img, surf


def dynamic_filter(gs, full=False, sigma=None): #, out_file, rad_div, sigma=None, save_gaussian=False, gs=None):
    sigma = sigma or int((len(gs) * len(gs[0])) / RAD_DIV)
    gaussian = ndimage.filters.gaussian_filter(gs, sigma=sigma)

    new_img = (gs - gaussian)
    new_img = new_img / (np.amax(new_img) + 1)
    ni = new_img.astype(int)
    ni = np.dstack((ni, ni, ni))

    palette = [(255, 255, 255), (114, 137, 218), (78, 93, 148)]
    if full:
        palette = [(255, 255, 255), (235, 238, 250), (208, 216, 243), (181, 193, 236), (154, 171, 229), (127, 148, 222), (114, 137, 218), (78, 93, 148)]
    step = 1.5 / len(palette)

    for n, c in enumerate(palette):
        ni[new_img < (len(palette) - n) * step - 0.5] = c#(255 - c[0], 255 - c[1], 255 - c[2])
    #ni = 255 - ni

    #ni[new_img > 0.3] = (255, 255, 255)
    #ni[new_img <= 0.3] = (114, 137, 218)
    #ni[-0.3 > new_img] = (78, 93, 148)

    return Image.fromarray(np.uint8(ni))


def normalized_filter(im, full=False):
    na = im.convert('RGB')
    fc = np.asarray(im)
    na = ImageOps.autocontrast(na)
    gs = np.mean(np.asarray(na), axis=2)

    ni = gs.astype(int)
    ni = np.dstack((ni, ni, ni, ni))

    palette = [(255, 255, 255), (114, 137, 218), (114, 137, 218), (78, 93, 148), (78, 93, 148)]
    if full:
        palette = [(255, 255, 255), (235, 238, 250), (208, 216, 243), (181, 193, 236), (154, 171, 229), (127, 148, 222), (114, 137, 218), (78, 93, 148)]
    step = 255 / len(palette)

    for n, c in enumerate(palette[::-1]):
        ni[gs >= (n) * step] = (c[0], c[1], c[2], 255)
    #print(fc)
    #print(np.max(fc * (0, 0, 0, 1), axis=2))
    ni[np.max(fc * (0, 0, 0, 1), axis=2) < 254] = (255, 0, 255, 0) 

    return Image.fromarray(np.uint8(ni))


def filter(in_file, nh, out_file, args, full=False, depth=0):
    in_file.seek(0)

    img = Image.open(in_file)

    if img.size[0] * img.size[1] > 1280 * 720:
        img.thumbnail((1280, 720), Image.ANTIALIAS)

    if args.basic_filter:
        gs = np.mean(np.asarray(img), axis=2)
        basic_filter(in_file, out_file, args.min_thresh, args.max_thresh, args.threshold, gs)
    else:
        try:
            img.info['version']
            is_gif = True
            gif_loop = int(img.info.get('loop', 0))
            gif_duration = img.info.get('duration')
        except Exception:
            is_gif = False
            gif_loop = gif_duration = None

        frames = []
        for frame in ImageSequence.Iterator(img):
            frames.append(frame.copy())

        for n, frame in enumerate(frames):
            #frame = frame.convert('RBG')
            #frame = ImageEnhance.Sharpness(frame.convert('RGB')).enhance(1)
            #frame = ImageEnhance.Contrast(frame).enhance(2)

            #gs = np.mean(np.asarray(frame), axis=2)
            #frames[n] = dynamic_filter(gs, full, args.sigma)
            frame = frame.convert('RGBA')
            frames[n] = normalized_filter(frame, full)

        for n, frame in enumerate(frames):
            frames[n] = frame.quantize()

        if is_gif:
            frames[0].save(out_file, format='gif', duration=gif_duration, save_all=True, append_images=frames[1:], loop=gif_loop)
        else:
            frames[0].save(out_file, format='png')
        #else:
        #    img = img.convert('RGBA')
            #img = ImageEnhance.Sharpness(img.convert('RGB')).enhance(1)
            #img = ImageEnhance.Contrast(img).enhance(2)

            #gs = np.mean(np.asarray(img), axis=2)
        #    normalized_filter(img, full).save(out_file, format='png')
            #dynamic_filter(gs, full, args.sigma).save(out_file, format='png')

        out_file.seek(0)

    sys.stdout.write(' [Done]\n')
    sys.stdout.flush()

    return 0


def main():
    parser = Parser(description=DESCRIPTION)
    parser.add_argument('-v', '--version', action='version', version=VERSION)
    parser.add_argument('-r', '--radius_div', action='store', type=int, default=None)
    parser.add_argument('-s', '--sigma', action='store', type=int, default=None)
    parser.add_argument('-m', '--max_thresh', action='store', type=int, default=MAX_T)
    parser.add_argument('-n', '--min_thresh', action='store', type=int, default=MIN_T)
    parser.add_argument('-g', '--save_gaussian', action='store_true')
    parser.add_argument('-y', '--save_greyscale', action='store_true')
    parser.add_argument('-b', '--basic_filter', action='store_true')
    parser.add_argument('-t', '--threshold', action='store', type=int, default=None)
    parser.add_argument('-i', '--input', action='store', dest='input', required=True)
    parser.add_argument('-o', '--output', action='store', dest='output', required=True)

    if len(sys.argv) < 2:
        parser.print_usage()
        sys.exit(2)

    args = parser.parse_args()

    if args.input == args.output:
        print('Input and output destination cannot be the same!')
        sys.exit(1)
    if not os.path.exists(args.input):
        print('No such file or directory ' + args.input)
        sys.exit(1)
    if args.radius_div is not None and args.sigma is not None:
        print('radius_div and sigma cannot both be defined.')
        sys.exit(1)
    if args.radius_div is None:
        args.radius_div = RAD_DIV

    sys.exit(filter(args.input, args.output, args))


if __name__ == '__main__':
    main()
