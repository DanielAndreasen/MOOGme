#!/usr/bin/env python
# -*- coding: utf8 -*-

from __future__ import print_function
from ewDriver import EWmethod
from abundanceDriver import AbundanceDriver
from aresDriver import aresdriver
from gooey import Gooey, GooeyParser


def ew(args):
    '''Driver for the EW method'''
    fout = ''
    linelist = args.linelist.rpartition('/')[-1]
    args.outlier = False if args.outlier == 'False' else args.outlier
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

    fout += 'model:%s,iterations:%s,weights:%s,RWcrit:%s,EPcrit:%s,ABdiffcrit:%s,MOOGv:%s,sigma:%s' % (args.model, args.Iterations, args.weights, args.RWslope, args.EPslope, args.Fedifference, args.MOOGv, args.sigma)
    if args.outlier:
        fout += ',outlier:%s' % args.outlier
    if args.refine:
        fout += ',refine'
    if args.Fixteff:
        fout += ',teff'
    if args.Fixgravity:
        fout += ',logg'
    if args.FixFeH:
        fout += ',feh'
    if args.Fixmicroturbulence:
        fout += ',vt'
    if args.teffrange:
        fout += ',teffrange'
    if args.autofixvt:
        fout += ',autofixvt'
    if args.tmcalc:
        fout += ',tmcalc'
    with open('StarMe_ew.cfg', 'w') as f:
        f.writelines(fout)
    EWmethod(overwrite=args.overwrite)
    driver = EWmethod(cfgfile='StarMe_ew.cfg', overwrite=None)
    parameters = driver.ewdriver()

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

    fout += 'model:%s,MOOGv:%s\n' % (args.model, args.MOOGv)

    with open('StarMe_abund.cfg', 'w') as f:
        f.writelines(fout)
    driver = AbundanceDriver(cfgfile='StarMe_abund.cfg')
    _ = driver.abundancedriver()
    driver.to_screen()

def ares(args):
    """Driver for ARES"""

    def rejt_from_snr(snr):
        """Calculate rejt from SNR"""
        return 1.0-(1.0/snr)

    #rvmask = False if args.RVmask == 0 else args.RVmask
    out = args.spectrum + '.ares' if not args.output else args.output

    # Make the StarMe_ares.cfg file from Gooey
    fout = args.linelist.rpartition('/')[2]
    fout += ' %s' % args.spectrum
    fout += ' lambdai:%s,lambdaf:%s,smoothder:%s' % (args.lambdai, args.lambdaf, args.smoothder)
    fout += ',space:%s,lineresol:%s' % (args.space, args.lineresol)
    fout += ',miniline:%s,EWcut:%s' % (args.miniline, args.EWcut)

    if args.rejt:
        rejt = args.rejt
        rejt = 0.999 if rejt > 0.999 else rejt
        fout += ',rejt:%s' % rejt
    if args.SNR:
        rejt = rejt_from_snr(args.SNR)
        rejt = 0.999 if rejt > 0.999 else rejt
        fout += ',rejt:%s' % rejt

    if args.output:
        fout += ',output:%s' % args.output
    if args.RVmask:
        fout += ',rvmask:%s' % args.RVmask
    if args.force:
        fout += ',force'

    with open('StarMe_ares.cfg', 'w') as f:
        f.writelines(fout)

    aresdriver()
    if args.output:
        print('Congratulations! The final line list are here: linelist/%s.moog' % args.output)
    else:
        linelist_out = 'linelist/%s.moog' % args.spectrum.rpartition('/')[2].rpartition('.')[0]
        print('Congratulations! The final line list are here: %s' % linelist_out)

@Gooey(program_name='FASMA - spectral analysis',
       default_size=(900, 1000),
       image_dir='./img')

def main():
    '''Take care of all the argparse stuff.
    :returns: the args
    '''
    parser = GooeyParser(description='Set parameters')

    subparsers = parser.add_subparsers()

    # Common to all
    parent_parser = GooeyParser(add_help=False)
    parent_parser.add_argument('--temperature',     help='(in K)',    default=5777,   type=int,   metavar='Temperature')
    parent_parser.add_argument('--surfacegravity',  help='(in dex)',  default=4.44,   type=float, metavar='logg')
    parent_parser.add_argument('--FeH',             help='(in dex)',  default='0.00', type=float, metavar='[Fe/H]')
    parent_parser.add_argument('--microturbulence', help='(in km/s)', default=1.0,    type=float, metavar='Microturbulence')
    parent_parser.add_argument('--MOOGv',           default='2014', choices=['2013', '2014', '2016'], type=str, metavar='MOOG version')
    parent_parser.add_argument('--model',           help='Grid of models', default='kurucz95', choices=['kurucz95', 'apogee_kurucz', 'kurucz08', 'marcs', 'PHOENIX'], metavar='Model atmosphere')

    # For the EW method
    ew_parser = subparsers.add_parser('ew', parents=[parent_parser], help='EW method')
    ew_parser.add_argument('linelist',             help='Input linelist file', widget='FileChooser')
    ew_parser.add_argument('--spectralType',       help='(optional)', default=False, metavar='Spectral type')
    ew_parser.add_argument('--Fixteff',            help='Fix Teff',   action='store_true', metavar='Fix temperature')
    ew_parser.add_argument('--Fixgravity',         help='Fix logg',   action='store_true', metavar='Fix gravity')
    ew_parser.add_argument('--FixFeH',             help='Fix [Fe/H]', action='store_true', metavar='Fix metallicity')
    ew_parser.add_argument('--Fixmicroturbulence', help='Fix vt',     action='store_true', metavar='Fix microturbulence')
    ew_parser.add_argument('--tmcalc',             help='Better guess on initial conditions',     action='store_true', metavar='Set initial conditions')
    ew_parser.add_argument('--refine',             help='Refine parameters',   action='store_true', metavar='Refine parameters')
    ew_parser.add_argument('--Iterations',         help='Maximum number of iterations', default=160, type=int)
    ew_parser.add_argument('--outlier',            help='Remove outliers', default='False', choices=['False', '1Iter', '1Once', 'allIter', 'allOnce'])
    ew_parser.add_argument('--weights',            help='Calculate the slopes of EP and RW with weights', type=str, default='null', choices=['null', 'sigma', 'mad'])
    ew_parser.add_argument('--EPslope',            help='EP slope to converge', default=0.001, type=float, metavar='EP slope')
    ew_parser.add_argument('--RWslope',            help='RW slope to converge', default=0.003, type=float, metavar='RW slope')
    ew_parser.add_argument('--Fedifference',       help='Difference between FeI and FeII', default='0.000', type=float, metavar='|Fel-Fell|')
    ew_parser.add_argument('--overwrite',          help='Overwrite results.csv', action='store_true', default=False)
    ew_parser.add_argument('--teffrange',          help='Give warning at high Teff, and remove lines at low Teff', action='store_true', default=False, metavar='Teff range')
    ew_parser.add_argument('--autofixvt',          help='Auto fix vt if it goes too low or too high', action='store_true', default=False)
    ew_parser.add_argument('--sigma',              help='Number of sigma, for sigma clipping outliers (default: 3)', type=float, default=3)
    ew_parser.set_defaults(driver=ew)

    # For calculating the abundances
    abund_parser = subparsers.add_parser('abund', parents=[parent_parser], help='Abundances')
    abund_parser.add_argument('linelist',    help='Input linelist file', widget='FileChooser')
    abund_parser.add_argument('--overwrite', help='Overwrite abundances.csv', action='store_true', default=False)
    abund_parser.set_defaults(driver=abund)

    # Driver for ARES
    ares_parser = subparsers.add_parser('ares', help='ARES')
    ares_parser.add_argument('linelist',    help='Input linelist file', widget='FileChooser')
    ares_parser.add_argument('spectrum',    help='1D spectrum',         widget='FileChooser')
    ares_parser.add_argument('--output',    help='Name of the output file (optional)', metavar='Output')
    ares_parser.add_argument('--lambdai',   help='Start of wavelength interval',  default=3900,  type=int)
    ares_parser.add_argument('--lambdaf',   help='End of wavelength interval',        default=25000, type=int)
    ares_parser.add_argument('--smoothder', help='Noise smoother',                    default=4,     type=int)
    ares_parser.add_argument('--space',     help='Interval for the line computation', default=2.0,   type=float)
    ares_parser.add_argument('--rejt',      help='Continuum position',                default=False, type=float)
    ares_parser.add_argument('--lineresol', help='Line resolution',                   default=0.07,  type=float)
    ares_parser.add_argument('--miniline',  help='Weaker line to be printed out',     default=5.0,   type=float)
    ares_parser.add_argument('--SNR',       help='If specified, the rejt is calculated', type=float)
    ares_parser.add_argument('--EWcut',     help='Cut for the maximum EW value',      default=200.0, type=float)
    ares_parser.add_argument('--RVmask',    help='RV of spectrum (km/s)',             default=False, type=float)
    ares_parser.add_argument('--force',     help='Remove troublesome lines automatically', default=False, action='store_true', metavar='Force finish')
    ares_parser.set_defaults(driver=ares)

    args = parser.parse_args()
    return args.driver(args)


if __name__ == '__main__':
    main()
