""" When very large experimental files are generated from the biaxial testing machine, it is unable to export as raw
data. To alleviate this issue, the present module can read the raw xml file that the biaxial testing machine uses
internally to store the testing data. That file can be found in the test folder: e.g.
<TestName>/test_runs/<TestRunName>/Data/daqTaskActivity1.xml
"""
import sys

import numpy as np
import h5py


def main(argv):
    if len(argv) < 1:
        print("A file name (excluding suffix) must be given)")
        return
    file = argv[1]
    rdata, runits = get_data(file)
    data, units, dtypes = reduce_data(rdata, runits)
    save_data(file, data, units, dtypes)


def save_data(file, data, units, dtypes=None):
    """Save data to hdf5 file for later use

    :param file: Path to hdf file to save data to, excluding .hdf suffix
    :type file: str

    :param data: Data dictionary where each item is a numpy array
    :type data: dict

    :param units: Dictionary with same keys as data, describing the units of the data
    :type units: dict

    :param dtypes: Dictionary with the data types with which the data should be saved
    :type dtypes: dict

    """
    dtypes_ = {} if dtypes is None else dtypes

    with h5py.File(file + '.hdf', 'w') as hdf:
        for name in data:
            if name in dtypes_:
                ds = hdf.create_dataset(name, data=data[name], dtype=dtypes_[name])
            else:
                ds = hdf.create_dataset(name, data=data[name])
            ds.attrs["unit"] = units[name]


def get_data(file):
    """ Get data from the biaxial machine's raw xml file.

    :param file: Path to xml file excluding .xml suffix
    :type file: str

    :returns: Dictionary with key based on names in the xml file and content as numpy arrays (float64)
              Dictionary with key based on names in the xml file and content strings with unit description
    :rtype: dict, dict
    """
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
                if row_count % 100000 == 0:
                    print("{:0.1e}".format(row_count))

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


if __name__ == '__main__':
    main(sys.argv)
