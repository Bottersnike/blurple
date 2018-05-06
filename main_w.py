#!/usr/bin/env python3
from scipy import ndimage
import numpy as np
import argparse
import time
import sys
import os

from PIL import Image

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


def dynamic_filter(in_file, nh, out_file, rad_div, sigma=None, save_gaussian=False, gs=None):
    if gs is None:
        in_file.seek(0)
        img = pygame.image.load(in_file, nh)

        arr = pygame.surfarray.array3d(img)
        del img
        gs = np.mean(arr, axis=2)
        del arr

    if sigma is None:
        sigma = int((len(gs) * len(gs[0])) / RAD_DIV)
    gaussian = ndimage.filters.gaussian_filter(gs, sigma=sigma)

    new_img = 1 - (gs > gaussian) * 1
    new_img = new_img.astype(int)
    new_img = np.dstack((new_img, new_img, new_img)) * (141, 118, 37)
    new_img = 255 - new_img
    del gs
    
    im = Image.fromarray(np.uint8(new_img))
    im.save(out_file, format='PNG')
    out_file.seek(0)
    
    del new_img

    if save_gaussian:
        surf = pygame.surfarray.make_surface(gaussian)
        pygame.image.save(surf, out_file + '-gaussian.png')
        del surf
    del gaussian


def filter(in_file, nh, out_file, args, depth=0):
    in_file.seek(0)

    img = Image.open(in_file)
    if img.size[0] * img.size[1] > 1280 * 720:
        img.thumbnail((1280, 720), Image.ANTIALIAS)
    arr = np.asarray(img)
    gs = np.mean(arr, axis=2)

    if args.basic_filter:
        basic_filter(in_file, out_file, args.min_thresh, args.max_thresh, args.threshold, gs)
    else:
        dynamic_filter(in_file, nh, out_file, args.radius_div, args.sigma, args.save_gaussian, gs)

    if args.save_greyscale:
        repeated = np.repeat(gs, 3, axis=1)
        greyscale = np.reshape(repeated, (len(gs), len(gs[0]), 3))
        del repeated, gs

        surf = pygame.surfarray.make_surface(greyscale)
        del greyscale
        pygame.image.save(surf, out_file + '-greyscale.png')
        del surf
    else:
        del gs

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
