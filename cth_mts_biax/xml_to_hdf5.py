""" When very large experimental files are generated from the biaxial testing machine, it is unable to export as raw
data. To alleviate this issue, the present module can read the raw xml file that the biaxial testing machine uses
internally to store the testing data. That file can be found in the test folder: e.g.
<TestName>/test_runs/<TestRunName>/Data/daqTaskActivity1.xml
"""
import sys
import os

import numpy as np
import h5py


def main(argv):
    if len(argv) < 2:
        print("1) A file name (excluding suffix) must be given)")
        print("2) The outer diameter (in mm) must be given")
        return
    file = argv[1]
    outer_diameter = float(argv[2])
    rdata, runits = get_data(file)
    data, units, dtypes = reduce_data(rdata, runits)
    comp_data, comp_units, comp_attributes = compensate(data, units, outer_diameter)
    save_data(file, comp_data, comp_units, dtypes, global_attributes=comp_attributes)


def save_data(file, data, units, dtypes=None, global_attributes=None):
    """Save data to hdf5 file for later use

    :param file: Path to hdf file to save data to, excluding .hdf suffix
    :type file: str

    :param data: Data dictionary where each item is a numpy array
    :type data: dict

    :param units: Dictionary with same keys as data, describing the units of the data
    :type units: dict

    :param dtypes: Dictionary with the data types with which the data should be saved
    :type dtypes: dict

    :param global_attributes: Attributes to add the the top level
    :type global_attributes: dict

    """
    dtypes_ = {} if dtypes is None else dtypes

    with h5py.File(file + '.hdf', 'w') as hdf:
        for name in data:
            if name in dtypes_:
                ds = hdf.create_dataset(name, data=data[name], dtype=dtypes_[name])
            else:
                ds = hdf.create_dataset(name, data=data[name])
            ds.attrs["unit"] = units[name]
        if global_attributes is not None:
            for key in global_attributes:
                hdf.attrs[key] = global_attributes[key]


def get_data(file, max_lines=None):
    """ Get data from the biaxial machine's raw xml file.

    :param file: Path to xml file excluding .xml suffix
    :type file: str

    :param max_lines: Maximum number of lines to read from xml file.
                      Defaults to None, meaning read all lines
    :type max_lines: int

    :returns: Dictionary with key based on names in the xml file and content as numpy arrays (float64)
              Dictionary with key based on names in the xml file and content strings with unit description
    :rtype: dict, dict
    """
    if max_lines is None:
        size_per_line = 341.57                       # Bytes/line
        file_size = os.path.getsize(file + '.xml')   # Bytes
        estimated_lines = file_size / size_per_line  # line
        max_lines = np.inf
    else:
        estimated_lines = max_lines

    with open(file + '.xml', 'r') as xml:
        # Read until signal description list starts
        for line in xml:
            if line.strip() == "<Signals>":
                break
        # Acquire signal names and units
        names = []
        units = {}
        for line in xml:
            if line.strip() == "</Signals>":
                break
            name, unit = get_name_and_unit(line)
            names.append(name)
            units[name] = unit
        data = {name: [] for name in names}
        name_ind = 0    # Not actually needed
        row_count = 0
        for line in xml:
            if line.strip().startswith("<Value>"):
                name = names[name_ind]
                data[name].append(get_data_value(line, np.float64))
                name_ind += 1
            elif line.strip() == "<Scan>":
                name_ind = 0
                row_count += 1
                if row_count >= max_lines:
                    break
                if row_count % 100000 == 0:
                    progress = 100 * row_count / estimated_lines
                    sys.stdout.write("\rEstimated progress: {:5.1f} %".format(progress))
                    sys.stdout.flush()
    print('\n')
    print("Total number of lines: ", row_count)
    for name in names:
        data[name] = np.array(data[name])

    return data, units


def get_name_and_unit(line):
    """ Get the name and unit of the given signal description. An example line is
    "    <Signal Name="Running Time" InternalName="Running Time" Dimension="time" Unit="sec" />\n"

    :param line: The line in the xml file
    :type line: str

    :returns: name, unit
    :rtype: str, str
    """
    name = line.split("Name=")[-1].split('"')[1]
    unit = line.split("Unit=")[-1].split('"')[1]

    return name, unit


def get_data_value(line, dtype):
    """ Get the data value from the line, an example line is
    "    <Value>8.14404296875</Value>\n"

    :param line: The line in the xml file
    :type line: str

    :param dtype: The data type to convert to
    :type dtype: type

    :returns: The value in the requested data type
    :rtype: dtype
    """
    value = line.split("<Value>")[-1].split("</Value>")[0]
    return dtype(value)


def reduce_data(raw_data, raw_units, save_disp=False, join_cnt=True,
                sensor_dtype=np.float32, time_accuracy=1.e-4, cnt_tol=0.1):
    """ Reduce the amount of data stored by

    1) Choose appropriate datatypes for sensor values
    2) Automatically determine datatype for time column
    3) Not saving displacement/rotation values unless requested
    4) Save only the indices when the counter changes
    5) Join counters unless requested not to

    :param raw_data: The raw data read from the xml file
    :type raw_data: dict

    :param raw_units: The units corresponding to raw_data
    :type raw_units: dict

    :param save_disp: Should displacements and rotations be saved? Defaults to False
    :type save_disp: bool

    :param join_cnt: Should counters be joined/merged? Defaults to True
    :type join_cnt: bool

    :param sensor_dtype: Datatype for sensor values (load,strain and disp/rota)
    :type sensor_dtype: type

    :param time_accuracy: The minimum time difference that should be stored accurately
    :type time_accuracy: float

    :param cnt_tol: The minimum counter change required to detect new count
    :type cnt_tol: float

    :returns: (data, units, dtype)
              data: New dictionary with keys "forc", "torq", "astr", "tstr",
              "disp", "rota", "time", ["cnt" or ("acnt", "tcnt")] whichever is available. Note that only the data in
              the counters are modified, otherwise no conversion from the machine data is performed.
              units: Unit strings (converted to ascii characters to avoid strange unicode issues)
              dtype: The datatype with which the data should be stored.
    :rtype: (dict, dict, dict)
    """
    data = {}
    units = {}
    dtypes = {}
    # Save sensor values (load and strains)
    sensor_keys = {"forc": "Axial Force",
                   "torq": "Torsional Torque",
                   "astr": "Axial Strain",
                   "tstr": "Torsional Strain (ang)"}
    for skey in sensor_keys:
        if sensor_keys[skey] in raw_data:
            data[skey] = raw_data[sensor_keys[skey]]
            dtypes[skey] = sensor_dtype
            units[skey] = str2ascii(raw_units[sensor_keys[skey]])

    # Save displacements (if requested)
    disp_keys = {"disp": "Axial Displacement",
                 "rota": "Torsional Rotation"}
    if save_disp:
        for dkey in disp_keys:
            if disp_keys[dkey] in raw_data:
                data[dkey] = raw_data[disp_keys[dkey]]
                dtypes[dkey] = sensor_dtype
                units[dkey] = str2ascii(raw_units[disp_keys[dkey]])

    # Save counter information
    cnt_keys = {"acnt": "Axial Segment Count",
                "tcnt": "Torsional Segment Count"}

    cnt = 0
    for ckey in cnt_keys:
        if cnt_keys[ckey] in raw_data:
            if join_cnt:
                cnt += raw_data[cnt_keys[ckey]][:]
            else:
                data[ckey] = np.where(raw_data[cnt_keys[ckey]][1:] > (raw_data[cnt_keys[ckey]][:-1] + cnt_tol))[0]
                dtypes[ckey] = data[ckey].dtype
                units[ckey] = "-"

    if join_cnt:
        data["cnt"] = np.where(cnt[1:] > (cnt[:-1] + cnt_tol))[0]
        dtypes["cnt"] = data["cnt"].dtype
        units["cnt"] = "-"

    # Save time
    trkey = "Running Time"
    tkey = "time"
    if trkey in raw_data:
        data[tkey] = raw_data[trkey]
        units[tkey] = raw_units[trkey]
        if (data[tkey][-1]/time_accuracy) > 1.e7:
            dtypes[tkey] = np.float64
        else:
            dtypes[tkey] = np.float32

    return data, units, dtypes


def str2ascii(raw_str):
    # Convert a string to ascii by removing non-ascii characters
    return raw_str.encode("ascii", "ignore").decode()


def compensate(data, units, outer_diameter, tstr_sign=0):
    """ Compensate data wrt. units, stiffness and cross-talk.

    :param data: The data dictionary to be compensated (as returned from :py:func:`reduce_data`)

    :param units: Dictionary of units (as returned from :py:func:`reduce_data`)

    :param outer_diameter: The outer diameter of the test bar [mm]

    :param tstr_sign: The sign with which to scale the torsional strain in relation to the torque.
                      -1 if extensometer text upside down, 1 otherwise).
                      If 0 (default), try to automatically detect by correlation with the torque.

    :returns: The compensated data dictionary, adjusted units, attributes describing compensation
    :rtype: (dict, dict, dict)
    """
    # The units with which the data will be output
    fixed_units = {'forc': 'N', 'torq': 'Nmm', 'disp': 'mm', 'rota': 'rad', 'astr': '-', 'tstr': 'rad', 'time': 's'}

    # Compensation values from Meyer et al. (2018) [https://doi.org/10.1016/j.ijsolstr.2017.10.007]
    k_axial = 198.71e3          # N/mm      Machine axial stiffness, to compensate disp values
    k_torsional = 25920e3       # Nmm/rad   Machine torsional stiffness, to compensate rota values
    torque_per_force = 0.0901   # Nmm/N     Cross talk force to torque, note sign change due to reversed rotation axis.

    # Other parameters
    ext_cal_dia = 10.0          # mm        The diameter for which the extensometer was calibrated.

    # Automatically determine sign of shear strain scaling
    if tstr_sign == 0 and 'tstr' in data:
        # Remove last 10 % when looking max min to avoid evaluating after failure.
        n = int(data['tstr'].shape[0]*0.9)
        # Find max and min torque
        i_max = np.argmax(data['torq'][:n])
        i_min = np.argmin(data['torq'][:n])
        # Get sign of inclination for torque versus shear strain. If positive maintain sign versus torque.
        tsgn = np.sign((data['torq'][i_max] - data['torq'][i_min]) /
                       (data['tstr'][i_max] - data['tstr'][i_min]))
    else:
        tsgn = tstr_sign

    # Scale channels
    # If KeyError is thrown below, it is suitable to add more units in the following dictionary
    scale_factors = {'forc': {'N': 1.0, 'kN': 1000.0},
                     'torq': {'Nm': -1000.0, 'Nmm': -1.0, 'kNm': -1.0e6, 'kNmm': -1.0e3},  # "-" due to machine
                     'disp': {'m': 1000.0, 'mm': 1.0},
                     'rota': {'rad': -1.0},                                                # "-" due to machine
                     'astr': {length_measure + '/' + length_measure: 1.0
                              for length_measure in ['mm', 'm', 'inch']},    # e.g. m/m
                     'tstr': {'rad': -tsgn * ext_cal_dia / outer_diameter},                # "-" due to machine
                     'time': {'sec': 1.0, 's': 1.0},
                     }
    for key in scale_factors:
        if key in data:
            try:
                sfac = scale_factors[key][units[key]]
            except KeyError as ke:
                if not units[key] in scale_factors[key]:
                    print("Unknown unit {:s} for variable {:s}".format(units[key], key))
                    print("Available units are: {:s}".format(",".join(['"' + u + '"' for u in scale_factors[key]])))
                    print("Consider adding additional unit conversions to 'scale_factors' (see above in the code)")
                raise ke
            data[key] = sfac * data[key]

    # Compensate for machine stiffness
    if 'disp' in data:
        data['disp'] -= data['forc']/k_axial
    if 'rota' in data:
        data['rota'] -= data['torq']/k_torsional
    stiffness_comp = ''
    if any([c in data for c in ['disp', 'rota']]):
        stiffness_comp = 'Machine stiffness compensation:\n'
        stiffness_comp += ' disp = disp - forc * ({:0.6e} mm/N)\n'.format(1/k_axial) if 'disp' in data else ''
        stiffness_comp += ' rota = rota - torq * ({:0.6e} rad/Nmm)\n'.format(1/k_torsional) if 'rota' in data else ''

    # Compensate for cross talk
    data['torq'] -= data['forc']*torque_per_force

    # Write modified units
    new_units = {key: (fixed_units[key] if key in fixed_units else units[key]) for key in data}

    info = (''
            + 'Rotation (torq,rota) reversed from machine\n'
            + '' if (tstr_sign == 0 or 'tstr' not in data) else ('tstr_sign = ' + str(tsgn) + '\n')
            + stiffness_comp  # Only add if disp and rota part of data
            + 'Cross talk compensation:\n'
            + ' torq = torq - forc * ({:0.4f} Nmm/N)\n'.format(torque_per_force)
            + 'Reference: https://doi.org/10.1016/j.ijsolstr.2017.10.007\n')

    attributes = {'info': info,
                  'cross_talk_torque_per_force': torque_per_force,
                  'axial_stiffness': k_axial,
                  'torsional_stiffness': k_torsional,
                  'tstr_sign': tsgn,
                  }

    return data, new_units, attributes


if __name__ == '__main__':
    main(sys.argv)
