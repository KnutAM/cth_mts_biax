""" Module for reading and compensating data from raw test files produced by the biaxial testing machine
"""

import numpy as np

    
def read(name, min_num_columns=9, num_rows=0):
    """Read the raw experiment data file into a numpy array and include additional information from the header.

    :param name: The path to the file to be read
    :type name: str

    :param min_num_columns: The minimum number of floating numbers that a line should be converted to in order to be
                            considered a data line
    :type min_num_columns: int

    :param num_rows: How many rows to read. If 0, read all
    :type num_rows: int

    :returns: A np.array with test data and an information dictionary containing the test date (key='date')
    :rtype: tuple( np.array, dict )

    If the file would have been formatted nicely, np.loadtxt() would be faster. The
    comments at the top makes this a bit more difficult. The function detects
    when the data starts by checking that the line converts into sufficient number
    of floating point numbers. Thereafter, all lines are assumed to be data lines.
    """

    with open(name, 'r') as fid:
        headers = []
        data = []
        num_rows = num_rows if num_rows != 0 else np.inf

        for line in fid:
            split_line = line.split()
            try:
                data_line = [float(item) for item in split_line]
            except ValueError:
                data_line = []  # Couldn't convert => not a data line
            if len(data_line) >= min_num_columns:
                data.append(data_line)
                break
            else:
                headers.append(line)

        row_nr = 1
        for line in fid:
            data.append([float(item) for item in line.split()])
            row_nr += 1
            if row_nr > num_rows:
                break

    info = {'date': 'not_found'}
    for hl in headers:
        date_split = hl.split('Date: ')
        if len(date_split) > 1:
            info['date'] = date_split[-1].strip()

    return np.array(data), info


def compensate(data, cols, od, tstr_sign=0):
    """ Compensate data wrt. scaling, stiffness and cross-talk
    
    :param data: The data matrix to be compensated (as returned from :py:func:`read`)
    
    :param cols: Dictionary giving the column number in data. Required keys are (with expected unit in parenthesis)

                 - ``forc``: Axial force [kN]
                 - ``torq``: Torque [Nm]

                 Optional keys are

                 - ``astr``: Axial strain [-]
                 - ``tstr``: Angular strain [rad] (Rotational strain measured by the extensometer, which is the rotation
                   over the gauge length calibrated for a 10 mm bar)
                 - ``disp``: Test bar elongation [mm]
                 - ``rota``: Test bar rotation [rad]
                 - ``acnt``: Axial cycle counter [cycle] (half cycles are counted as 0.5)
                 - ``tcnt``: Torsional cycle counter [cycle]

    :param od: The outer diameter of the test bar [mm]

    :param tstr_sign: The sign with which to scale the torsional strain in relation to the torque.
                      -1 if extensometer text upside down, -1 otherwise).
                      If 0 (default), try to automatically detect by correlation with the torque.

    :returns: The compensated data array, an information string about the compensations and the tstr_sign used
    :rtype: tuple( np.array, str, int)
    """

    # Compensation values from Meyer et al. (2018) [https://doi.org/10.1016/j.ijsolstr.2017.10.007]
    k_axial = 198.71e3          # N/mm      Machine axial stiffness, to compensate disp values
    k_torsional = 25920e3       # Nmm/rad   Machine torsional stiffness, to compensate rota values
    torque_per_force = 0.0901   # Nmm/N     Cross talk force to torque, note sign change due to reversed rotation axis.

    # Other parameters
    ext_cal_dia = 10.0          # mm        The diameter for which the extensometer was calibrated.

    # Automatically determine sign of shear strain scaling
    if tstr_sign == 0 and 'tstr' in cols:
        # Remove last 10 % when looking max min to avoid evaluating after failure.
        n = int(data.shape[0]*0.9)
        # Find max and min torque
        i_max = np.argmax(data[:n, cols['torq']])
        i_min = np.argmin(data[:n, cols['torq']])
        # Get sign of inclination for torque versus shear strain. If positive maintain sign versus torque.
        tsgn = np.sign((data[i_max, cols['torq']] - data[i_min, cols['torq']]) /
                       (data[i_max, cols['tstr']] - data[i_min, cols['tstr']]))
    else:
        tsgn = tstr_sign

    # Scale channels
    scale_factors = {'forc': 1000.0,    # Convert from kN to N
                     'torq': -1000.0,   # Convert from kNmm to Nmm and switch sign
                     'rota': -1.0,      # Reverse rotation direction
                     'tstr': -tsgn*ext_cal_dia/od,   # Reverse strain and compensate for different outer diameter.
                     'tcnt': 2,         # Counters in half step, double to make integers
                     'acnt': 2,
                     }
    for key in scale_factors:
        if key in cols:
            data[:, cols[key]] = scale_factors[key]*data[:, cols[key]]

    # Compensate for machine stiffness
    if 'disp' in cols:
        data[:, cols['disp']] -= data[:, cols['forc']]/k_axial
    if 'rota' in cols:
        data[:, cols['rota']] -= data[:, cols['torq']]/k_torsional
    stiffness_comp = ''
    if all([c in cols for c in ['disp', 'rota']]):
        stiffness_comp = ('Machine stiffness compensation:\n'
                          + ' disp = disp - forc * ({:0.6e} mm/N)\n'.format(1/k_axial)
                          + ' rota = rota - torq * ({:0.6e} rad/Nmm)\n'.format(1/k_torsional))

    # Compensate for cross talk
    data[:, cols['torq']] -= data[:, cols['forc']]*torque_per_force

    info = (''
            + 'Rotation (torq,rota) reversed from machine\n'
            + '' if (tstr_sign == 0 or 'tstr' not in cols) else ('tstr_sign = ' + str(tsgn) + '\n')
            + stiffness_comp  # Only add if disp and rota part of data
            + 'Cross talk compensation:\n'
            + ' torq = torq - forc * ({:0.4f} Nmm/N)\n'.format(torque_per_force)
            + 'Reference: https://doi.org/10.1016/j.ijsolstr.2017.10.007\n')

    return data, info, tsgn
