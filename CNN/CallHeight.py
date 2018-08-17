# 8/13/18
# chenyong
# call plant height

"""
call plant height from predicted images
"""
import os
import sys
import cv2
import numpy as np
import pandas as pd
import os.path as op
import scipy.misc as sm
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import rcParams
from PIL import Image
from math import hypot
from JamesLab.apps.natsort import natsorted
from JamesLab.apps.header import Slurm_header
from sklearn.linear_model import LinearRegression
from JamesLab.apps.base import ActionDispatcher, OptionParser, glob

def main():
    actions = (
        ('Polish', 'Polish the predicted images'),
        ('PolishBatch', 'generate all slurm jobs of polish'),
        ('CallHeight', 'call height from polished image'),
        ('CallHeightBatch', 'generate all slurm jobs of plant height calling'),
            )
    p = ActionDispatcher(actions)
    p.dispatch(globals())

def CallPart(rgb_arr, part='stem'):
    crp_shape2d = rgb_arr.shape[0:2]
    if part =='stem':
        r, g, b = 251, 129, 14
    elif part == 'panicle':
        r, g, b = 126, 94, 169
    elif part == 'leaf':
        r, g, b = 0, 147, 0
    else:
        sys.exit('only support stem, panicle, and leaf')
    p1 = np.full(crp_shape2d,r)
    p2 = np.full(crp_shape2d,g)
    p3 = np.full(crp_shape2d,b)
    p123 = np.stack([p1, p2, p3], axis=2)
    pRGB = np.where(rgb_arr==p123, rgb_arr, 255)
    return pRGB

def FilterPixels(arr3d, d=0):
    rgb_img = Image.fromarray(arr3d)
    gray_img = rgb_img.convert(mode='L')
    gray_blur_arr = cv2.GaussianBlur(np.array(gray_img), (3,3), 0)
    cutoff = pd.Series(gray_blur_arr.flatten()).value_counts().index.sort_values()[d]
    arr2d = np.where(gray_blur_arr<=cutoff, 0, 255) 
    return arr2d

def gray2rgb(arr2d, part="stem"):
    cond_k = arr2d==0
    if part =='stem':
        r, g, b = 251, 129, 14
    elif part == 'panicle':
        r, g, b = 126, 94, 169
    elif part == 'leaf':
        r, g, b = 0, 147, 0
    else:
        sys.exit('only support stem, panicle, and leaf')
    pr = np.where(cond_k, r, 255)
    pg = np.where(cond_k, g, 255)
    pb = np.where(cond_k, b, 255)
    pRGB = np.stack([pr, pg, pb], axis=2)
    return pRGB

def Polish(args):
    """
    %prog image_in image_out_prefix
    Using opencv blur function to filter noise pixles for each plant component
    """
    p = OptionParser(Polish.__doc__)
    p.add_option("--crop",
        help="if you want to crop image, please specify the crop size following coordinates of upper left conner and right bottom conner.")
    p.add_option("--blur_degree", default='4',
        help="specify the degree value in GaussinBlur function. [default: %default]")
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    imgIn, imgOut = args

    img = Image.open(imgIn)
    if opts.crop:
        crp_tuple = tuple([int(i) for i in opts.crop.split()]) # crop: left, upper, right, and lower pixel coordinate
        if len(crp_tuple) != 4:
            sys.exit("please specify 'left upper right bottom'")
        else:
            img = np.array(img.crop(crp_tuple))
    else:
        img = np.array(img)
    stemRGBraw = CallPart(img, 'stem')
    stem = FilterPixels(stemRGBraw)
    stemRGB = gray2rgb(stem, 'stem')
    panicleRGBraw = CallPart(img, 'panicle')
    panicle = FilterPixels(panicleRGBraw, d=int(opts.blur_degree))
    panicleRGB = gray2rgb(panicle, 'panicle')
    leafRGBraw = CallPart(img, 'leaf')
    leaf = FilterPixels(leafRGBraw, d=int(opts.blur_degree))
    leafRGB = gray2rgb(leaf, 'leaf')
    spRGB = np.where(stemRGB==255, panicleRGB, stemRGB)
    splRGB = np.where(spRGB==255, leafRGB, spRGB)
    sm.imsave('%s.polish.png'%imgOut, splRGB)

def PolishBatch(args):
    """
    %prog imagePattern("CM*.png")
    generate polish jobs for all image files
    """
    p = OptionParser(PolishBatch.__doc__)
    p.set_slurm_opts(array=False)
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    pattern, = args
    all_pngs = glob(pattern)
    for i in all_pngs:
        out_prefix = i.split('/')[-1].split('.png')[0]
        jobname = out_prefix + '.polish'
        cmd = 'python -m JamesLab.CNN.CallHeight Polish %s %s\n'%(i, out_prefix)
        header = Slurm_header%(opts.time, opts.memory, jobname, jobname, jobname)
        header += "ml anaconda\nsource activate %s\n"%opts.env
        header += cmd
        jobfile = open('%s.polish.slurm'%out_prefix, 'w')
        jobfile.write(header)
        jobfile.close()
        print('%s.slurm polish job file generated!'%jobname)

def CallHeight(args):
    """
    %prog image_in output_prefix
    call height from polished image
    """
    p = OptionParser(CallHeight.__doc__)
    p.add_option("--crop",
        help="if you want to crop image, please specify the crop size following coordinates of upper left conner and right bottom conner.")
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    imageIn, outPrefix = args

    img = Image.open(imageIn)
    if opts.crop:
        crp_tuple = tuple([int(i) for i in opts.crop.split()]) # crop: left, upper, right, and lower pixel coordinate
        if len(crp_tuple) != 4:
            sys.exit("please specify 'left upper right bottom'")
        else:
            img = np.array(img.crop(crp_tuple))
    else:
        img = np.array(img)

    # get stem and panicle pixels
    sRGB = CallPart(img, 'stem')
    sRGB_img = Image.fromarray(sRGB)
    sgray = np.array(sRGB_img.convert(mode='L'))
    pRGB = CallPart(img, 'panicle')
    pRGB_img = Image.fromarray(pRGB)
    pgray = np.array(pRGB_img.convert(mode='L'))
    spgray = np.where(sgray==255, pgray, sgray)
    xlim, ylim = spgray.shape 
    # fit model
    X, Y = np.where(spgray< 255)
    X = X*-1+xlim
    model = LinearRegression()
    model.fit(X.reshape(-1,1), Y)
    # regression line
    
    #a = X.max()
    a = 131
    b = np.abs(model.predict(0)-model.predict(a))
    c = hypot(a, b)
    f1 = open('%s.Height.csv'%outPrefix, 'w')
    f1.write('%s'%c)
    f1.close()
    # plot
    plt.switch_backend('agg')
    rcParams['figure.figsize'] = xlim*0.015, ylim*0.015
    fig, ax = plt.subplots()
    ax.scatter(X, Y, s=0.1, color='k', alpha=0.7)
    ax.plot([0, a], [model.predict(0), model.predict(a)], c='r', linewidth=1)
    ax.text(100, 50, "%.2f"%c, fontsize=12)
    ax.set_xlim([0,xlim])
    ax.set_ylim([0,ylim])
    plt.tight_layout()
    plt.savefig('%s.Height.png'%outPrefix)

def CallHeightBatch(args):
    """
    %prog imagePattern("CM*.polish.png")
    generate height call jobs for all polished image files
    """
    p = OptionParser(CallHeightBatch.__doc__)
    p.set_slurm_opts(array=False)
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    pattern, = args
    all_pngs = glob(pattern)
    for i in all_pngs:
        out_prefix = i.split('/')[-1].split('.polish.png')[0]
        jobname = out_prefix + '.Height'
        cmd = 'python -m JamesLab.CNN.CallHeight CallHeight %s %s\n'%(i, out_prefix)
        header = Slurm_header%(opts.time, opts.memory, jobname, jobname, jobname)
        header += "ml anaconda\nsource activate %s\n"%opts.env
        header += cmd
        jobfile = open('%s.CallHeight.slurm'%out_prefix, 'w')
        jobfile.write(header)
        jobfile.close()
        print('%s.CallHeight.slurm call height job file generated!'%jobname)

if __name__ == "__main__":
    main()
















