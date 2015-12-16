#!/usr/bin/env python
# -*- coding: utf8 -*-

from __future__ import print_function
from ewDriver import ewdriver
from synthDriver import synthdriver
from abundanceDriver import abundancedriver
from aresDriver import make_linelist, _run_ares
import argparse
from gooey import Gooey, GooeyParser


def ew(args):
    '''Driver for the EW method'''
    fout = ''
    linelist = args.linelist.rpartition('/')[-1]
    if args.spectralType:
        if not args.temperature and not args.surfacegravity:
            fout += '%s spt:%s,' % (linelist, args.spectralType)
        else:
            print('Temperature and/or surface gravity set. Will not use spectral type.')
    else:
        if not args.temperature:
            print('Warning: Temperature was set to 5777K')
            args.temperature = 5777
        if not args.surfacegravity:
            print('Warning: Surface gravity was set to 4.44')
            args.surfacegravity = 4.44
        if not args.FeH:
            args.FeH = 0.0
        if not args.microturbulence:
            print('Warning: Microturbulence was set to 1.00')
            args.microturbulence = 1.00
        fout += '%s %s %s %s %s ' % (linelist, args.temperature, args.surfacegravity, args.FeH, args.microturbulence)

    fout += 'model:%s,iterations:%s,weights:%s,RWslope:%s,EPslope:%s,abdiff:%s,MOOGv:%s' % (args.model, args.Iterations, args.weights, args.RWslope, args.EPslope, args.Fedifference, args.MOOGv)
    if args.Fixteff:
        fout += ',teff'
    if args.Fixgravity:
        fout += ',logg'
    if args.FixFeH:
        fout += ',feh'
    if args.Fixmicroturbulence:
        fout += ',vt'
    with open('StarMe.cfg', 'w') as f:
        f.writelines(fout)
    ewdriver()


def synth(args):
    """Driver for the synthesis method"""
    print(args)
    raise NotImplementedError('Patience you must have my young Padawan')


def abund(args):
    """Driver for abundances"""

    fout = ''
    linelist = args.linelist.rpartition('/')[-1]

    if not args.temperature:
        print('Warning: Temperature was set to 5777K')
        args.temperature = 5777
    if not args.surfacegravity:
        print('Warning: Surface gravity was set to 4.44')
        args.surfacegravity = 4.44
    if not args.FeH:
        args.FeH = 0.0
    if not args.microturbulence:
        print('Warning: Microturbulence was set to 1.00')
        args.microturbulence = 1.00
    fout += '%s %s %s %s %s ' % (linelist, args.temperature, args.surfacegravity, args.FeH, args.microturbulence)

    fout += 'model:%s,MOOGv:%s' % (args.model, args.MOOGv)

    with open('StarMe.cfg', 'w') as f:
        f.writelines(fout)

    abundancedriver()

def ares(args):
    """Driver for ARES"""
    def rejt_from_snr(snr):
        """Calculate rejt from SNR"""
        return 1-1/snr

    if args.SNR:
        rejt = rejt_from_snr(args.SNR)
    else:
        rejt = args.rejt
    rejt = 0.999 if rejt > 0.999 else rejt
    plot = 1 if args.plots else 0
    out = args.spectrum + '.ares' if not args.output else args.output

    fout = 'specfits=\'%s\'\n' % args.spectrum
    fout += 'readlinedat=\'%s\'\n' % args.linelist
    fout += 'fileout=\'linelist/%s\'\n' % out
    fout += 'lambdai=%s\n' % args.lambdai
    fout += 'lambdaf=%s\n' % args.lambdaf
    fout += 'smoothder= %s\n' % args.smoothder
    fout += 'space=%s\n' % args.space
    fout += 'rejt=%s\n' % rejt
    fout += 'lineresol=%s\n' % args.lineresol
    fout += 'miniline=%s\n' % args.miniline
    fout += 'plots_flag=%s\n' % plot

    with open('mine.opt', 'w') as f:
        f.writelines(fout)

    _run_ares()
    make_linelist(args.linelist, 'linelist/'+out, args.EWcut)
    print('Congratulations! The EWs are here:', 'linelist/'+out+'.moog')

@Gooey(program_name='MOOG Made Easy - deriving stellar parameters',
       default_size=(700, 1000),
       image_dir='./img')
def main():
    '''Take care of all the argparse stuff.
    :returns: the args
    '''
    parser = GooeyParser(description='Set parameters')

    subparsers = parser.add_subparsers()

    # Common to all
    parent_parser = GooeyParser(add_help=False)
    parent_parser.add_argument('--temperature',     help='Input initial temperature',      default=5777,  type=int)
    parent_parser.add_argument('--surfacegravity',  help='Input initial gravity',          default=4.44,  type=float, metavar='logg')
    parent_parser.add_argument('--FeH',             help='Input initial metallicity',      default='0.00',type=float, metavar='[Fe/H]')
    parent_parser.add_argument('--microturbulence', help='Input initial microturbulence',  default=1.0,   type=float)
    parent_parser.add_argument('--MOOGv',           help='Version of MOOG', default='2013', choices=['2013', '2014'], type=str, metavar='MOOG version')
    # parent_parser.add_argument('--recal',           help='Recalibrate loggf for a given MOOG version and atm. model', metavar='Recalibrate loggf', action='store_true')
    parent_parser.add_argument('--model',           help='Model atmosphere',    default='kurucz95', choices=['kurucz95', 'kurucz08', 'marcs', 'PHOENIX'])


    # For the EW method
    ew_parser = subparsers.add_parser('ew', parents=[parent_parser], help='EW method')
    ew_parser.add_argument('linelist',             help='Input linelist file', widget='FileChooser')
    ew_parser.add_argument('--spectralType',       help='Input spectral type (optional)', default=False, metavar='Spectral type')
    ew_parser.add_argument('--Fixteff',            help='Fix temperature',     action='store_true', metavar='Fix temperature')
    ew_parser.add_argument('--Fixgravity',         help='Fix gravity',         action='store_true', metavar='Fix gravity')
    ew_parser.add_argument('--FixFeH',             help='Fix metallicity',     action='store_true', metavar='Fix [Fe/H]')
    ew_parser.add_argument('--Fixmicroturbulence', help='Fix microturbulence', action='store_true', metavar='Fix microturbulence')
    ew_parser.add_argument('--Iterations',         help='Maximum number of iterations', default=160, type=int)
    ew_parser.add_argument('--weights',            help='Calculate the slopes of EP and RW with weights', type=str, default='null', choices=['null', 'median', 'sigma', 'mad'])
    ew_parser.add_argument('--EPslope',            help='EP slope to converge', default=0.001, type=float, metavar='EP slope')
    ew_parser.add_argument('--RWslope',            help='RW slope to converge', default=0.003, type=float, metavar='RW slope')
    ew_parser.add_argument('--Fedifference',       help='Difference between FeI and FeII', default='0.000', type=float, metavar='|[Fel]-[Fell]|')
    ew_parser.set_defaults(driver=ew)

    # For the synhtesis method
    synth_parser = subparsers.add_parser('synth', parents=[parent_parser], help='Synthesis method')
    synth_parser.add_argument('--test', help='this is test')
    synth_parser.set_defaults(driver=synth)

    # For calculating the abundances
    abund_parser = subparsers.add_parser('abund', parents=[parent_parser], help='Abundances')
    abund_parser.add_argument('linelist', help='Input linelist file', widget='FileChooser')
    abund_parser.set_defaults(driver=abund)

    # Driver for ARES
    ares_parser = subparsers.add_parser('ares', help='ARES')
    ares_parser.add_argument('spectrum', help='1D spectrum', widget='FileChooser')
    ares_parser.add_argument('linelist', help='Input linelist file', widget='FileChooser')
    ares_parser.add_argument('--output', help='Output of final linelist')
    ares_parser.add_argument('--lambdai', help='Beginning of wavelength interval', default=3900, type=float)
    ares_parser.add_argument('--lambdaf', help='End of wavelength interval', default=25000, type=float)
    ares_parser.add_argument('--smoothder', help='Noise smoother', default=4, type=int)
    ares_parser.add_argument('--space', help='Interval for the line computation', default=2.0, type=float)
    ares_parser.add_argument('--rejt', help='Continuum position', default=0.995, type=float)
    ares_parser.add_argument('--lineresol', help='Line resolution', default=0.07, type=float)
    ares_parser.add_argument('--miniline', help='Weaker line to be printed out', default=2, type=int)
    ares_parser.add_argument('--plots', help='Flag for plots', default=False, action='store_true')
    ares_parser.add_argument('--SNR', help='If specified, the rejt is calculated')
    ares_parser.add_argument('--EWcut', help='Cut for the maximum EW value', default=200.0, type=float)
    ares_parser.set_defaults(driver=ares)

    args = parser.parse_args()
    return args.driver(args)


if __name__ == '__main__':
    main()
