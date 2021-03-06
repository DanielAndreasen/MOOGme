#!/usr/bin/env python
# -*- coding: utf8 -*-

# My imports
from __future__ import division, print_function
import logging
import os
from shutil import copyfile
from glob import glob
import numpy as np
import decimal
import pandas as pd


def _run_ares():
    """Run ARES"""
    os.system('ARES > /dev/null')
    for tmp in ['tmp', 'tmp2', 'tmp3']:
        if os.path.isfile(tmp):
            os.remove(tmp)

def round_up0(i):
    """Round up to 2nd decimal because of stupid python"""

    rounded = decimal.Decimal(str(i)).quantize(decimal.Decimal('1.11'), rounding=decimal.ROUND_HALF_UP)
    return np.float(rounded)

def get_snr(fname='logARES.txt'):
    """Get the SNR from ARES

    Input
    -----
    fname : str
      Name of the logfile of ARES

    Output
    ------
    snr : int
      The SNR either provided by ARES or measured
    """

    with open(fname, 'r') as lines:
        for line in lines:
            if line.startswith('S/N'):
                break
    line = line.strip('\n').split(':')
    snr = int(float(line[1]))
    return snr

def make_linelist(line_file, ares, cut):
    """Merging linelist with ares file
    """

    linelist = pd.read_csv(line_file, skiprows=2,
                           names=['WL', 'num', 'EP', 'loggf', 'element', 'EWsun'],
                           delimiter=r'\s+', converters={'WL': round_up0})
    linelist = linelist.sort_values(['WL'])

    data = pd.read_csv(ares, usecols=(0, 4), names=['wave', 'EW'], delimiter=r'\s+')
    data = data.sort_values(['wave'])

    dout = pd.merge(left=linelist, right=data, left_on='WL', right_on='wave', how='inner')
    dout = dout.loc[:, ['WL', 'num', 'EP', 'loggf', 'EW']]
    dout = dout[dout.EW < float(cut)]
    dout.drop_duplicates('WL', keep='first', inplace=True)
    dout = dout.sort_values(['num', 'WL'])

    N2 = len(dout)
    N = len(linelist)
    try:
        snr = get_snr()
    except IndexError:
        snr = 0
    print('\tARES measured %i/%i lines.' % (N2, N))
    print('\tSNR used: %i' % snr)

    fout = '%s.moog' % ares.rpartition('.')[0]
    hdr = '%s - SNR: %s' % (fout, snr)
    np.savetxt(fout, dout.values, fmt=('%9.3f', '%10.1f', '%9.2f', '%9.3f', '%28.1f'), header=' %s' % hdr)
    os.remove(ares)

def _options(options=None):
    '''Reads the options inside the config file'''
    defaults = {'lambdai'   : '3900.0',
                'lambdaf'   : '6900.0',
                'smoothder' : '4',
                'space'     : '2.0',
                'rejt'      : False,
                'lineresol' : '0.07',
                'miniline'  : '2.0',
                'plots_flag': False,
                'EWcut'     : '200.0',
                'snr'       : False,
                'output'    : False,
                'rvmask'    : '"0,0"',
                'force'     : False,
                'extra'     : None
                }
    if not options:
        defaults['rejt'] = '3;5764,5766,6047,6053,6068,6076'
        return defaults
    else:
        options = options.split(',')
        for option in options:
            if ':' in option:
                option = option.split(':')
                defaults[option[0]] = option[1]
            else:
                defaults[option] = True
        defaults['lambdai']   = float(defaults['lambdai'])
        defaults['lambdaf']   = float(defaults['lambdaf'])
        defaults['smoothder'] = int(defaults['smoothder'])
        defaults['space']     = float(defaults['space'])
        defaults['lineresol'] = float(defaults['lineresol'])
        defaults['miniline']  = float(defaults['miniline'])
        defaults['rvmask']    = str(defaults['rvmask'])
        defaults['EWcut']     = float(defaults['EWcut'])
        if defaults['plots_flag']:
            defaults['plots_flag'] = '1'
        if not defaults['rejt']:
            defaults['rejt'] = '3;5764,5766,6047,6053,6068,6076'
        try:
            defaults['rejt'] = float(defaults['rejt'])
        except ValueError:
            defaults['rejt'] = str(defaults['rejt'])
        return defaults

def update_ares(line_list, spectrum, out, options):
    """Driver for ARES"""

    default_options = options
    for key, value in default_options.items():
        if key not in options.keys():
            options[key] = value

    def rejt_from_snr(snr):
        """Calculate rejt from SNR"""
        return 1.0-(1.0/float(snr))

    if options['snr']:
        rejt = rejt_from_snr(options['snr'])
    else:
        rejt = options['rejt']
    plot = 1 if options['plots_flag'] else 0
    if isinstance(rejt, float):
        rejt = 0.999 if rejt > 0.999 else rejt

    if options['output']:
        out = options['output']
    else:
        out = '%s.ares' % spectrum.rpartition('.')[0]

    if options['fullpath']:
        fout = 'specfits=\'%s\'\n' % spectrum
    else:
        fout = 'specfits=\'spectra/%s\'\n' % spectrum
    fout += 'readlinedat=\'rawLinelist/%s\'\n' % line_list
    fout += 'fileout=\'linelist/%s\'\n' % out
    fout += 'lambdai=%s\n' % options['lambdai']
    fout += 'lambdaf=%s\n' % options['lambdaf']
    fout += 'smoothder=%s\n' % options['smoothder']
    fout += 'space=%s\n' % options['space']
    fout += 'rejt=%s\n' % rejt
    fout += 'lineresol=%s\n' % options['lineresol']
    fout += 'miniline=%s\n' % options['miniline']
    fout += 'plots_flag=%s\n' % plot
    fout += 'rvmask=\'0,%s\'\n' % options['rvmask']

    with open('mine.opt', 'w') as f:
        f.writelines(fout)

def findBadLine():
    """Read logARES.txt and return the last measured line (the bad one)"""
    linePresent = False
    with open('logARES.txt', 'r') as lines:
        for line in lines:
            if line.startswith('line result'):
                line = line.split(':')
                badLine = float(line[-1])
                linePresent = True
    if linePresent:
        return badLine
    else:
        return None

def cleanLineList(linelist, badline):
    badline = str(round(badline, 2))
    with open(linelist, 'r') as lines:
        fout = ''
        for line in lines:
            if line.startswith(badline):
                continue
            fout += line
    with open(linelist, 'w') as f:
        f.writelines(fout)

def aresRunner(linelist, spectrum, out, options):
    print('Using linelist: %s' % linelist)
    print('Using spectrum: %s' % spectrum)
    print('Your ARES output: linelist/%s' % out.replace('.ares', '.moog'))

    update_ares(linelist, spectrum, out, options)
    if options['force']:
        index = 1
        while True:
            _run_ares()
            if os.path.isfile('linelist/'+out):
                break
            else:
                atomicLine = findBadLine()
                if atomicLine:
                    print('\tRemoving line: %.2f' % atomicLine)
                    copyfile('rawLinelist/'+linelist, 'rawLinelist/tmp%i' % index)
                    tmplinelist = 'tmp%i' % index
                    cleanLineList('rawLinelist/'+tmplinelist, atomicLine)
                    update_ares(tmplinelist, spectrum, out, options)
                    index += 1
                else:
                    break
        for tmp in glob('rawLinelist/tmp*'):
            os.remove(tmp)
    else:
        _run_ares()
    try:
        make_linelist('rawLinelist/'+linelist, 'linelist/'+out, cut=options['EWcut'])
    except IOError:
        raise IOError('ARES did not run properly. Take a look at "logARES.txt" for more help.')
    print('\n')

def aresdriver(starLines='StarMe_ares.cfg'):
    """The function that glues everything together

    Input:
    starLines   -   Configuration file (default: StarMe_ares.cfg)

    Output:
    <linelist>.out          -   Output file
    """
    try:  # Cleaning from previous runs
        os.remove('captain.log')
    except OSError:
        pass
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler('captain.log')
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Check if there is a directory called linelist, if not create it and ask the user to put files there
    if not os.path.isdir('linelist'):
        os.mkdir('linelist')
        logger.info('linelist directory was created')

    if not os.path.isdir('rawLinelist'):
        os.mkdir('rawLinelist')
        logger.info('linelist directory was created')
        raise IOError('Please put linelists in rawLinelist folder')

    with open(starLines, 'r') as lines:
        for line in lines:
            if not line[0].isalpha():
                logger.debug('Skipping header: %s' % line.strip())
                continue
            logger.info('Processing: %s' % line.strip())
            line = line.strip()
            line = line.split(' ')

            if len(line) == 2:
                options = _options()
                line_list = line[0]
                spectrum = line[1]
            elif len(line) == 3:
                options = _options(line[-1])
                line_list = line[0]
                spectrum = line[1]
            else:
                logger.error('Could not process information for this line: %s' % line)
                continue

            if options['output']:
                out = options['output']
            else:
                out = '%s.ares' % spectrum.rpartition('/')[2].rpartition('.')[0]
                options['output'] = out
            if os.path.isfile('spectra/%s' % spectrum):
                options['fullpath'] = False
            elif os.path.isfile(spectrum):
                options['fullpath'] = True
            else:
                continue

            aresRunner(line_list, spectrum, out, options)
            if options['extra'] is not None:
                line_list = options['extra']
                out = out.replace('.ares', '_sec.ares')
                options['output'] = out
                aresRunner(line_list, spectrum, out, options)

    snr = get_snr()
    os.remove('logARES.txt')
    return snr

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        cfgfile = sys.argv[1]
    else:
        cfgfile = 'StarMe_ares.cfg'
    _ = aresdriver(starLines=cfgfile)
