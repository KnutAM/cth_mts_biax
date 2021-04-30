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
    data, units = get_data(file)
    save_data(file, data, units)


def save_data(file, data, units):
    """Save data to hdf5 file for later use

    :param file: Path to hdf file to save data to, excluding .hdf suffix
    :type file: str

    :param data: Data dictionary where each item is a numpy array
    :type data: dict

    :param units: Dictionary with same keys as data, describing the units of the data
    :type units: dict

    """

    with h5py.File(file + '.hdf', 'w') as hdf:
        for name in data:
            ds = hdf.create_dataset(name, data=data[name])
            ds.attrs["unit"] = units[name]


def get_data(file, default_dtype=np.float32, special_dtypes={}):
    """ Get data from the biaxial machine's raw xml file.

    :param file: Path to xml file excluding .xml suffix
    :type file: str

    :param default_dtype: default datatype
    :type default_dtype: type

    :param special_dtypes: special data types to use for given keys (names in xml file)
    :type special_dtypes: dict

    :returns: Dictionary with key based on names in the xml file and content as numpy arrays
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
        dtypes = {name: special_dtypes[name] if name in special_dtypes else default_dtype for name in names}
        data = {name: [] for name in names}
        name_ind = 0    # Not actually needed
        row_count = 0
        for line in xml:
            if line.strip().startswith("<Value>"):
                name = names[name_ind]
                data[name].append(get_data_value(line, dtypes[name]))
                name_ind += 1
            elif line.strip() == "<Scan>":
                name_ind = 0
                row_count += 1
                if row_count % 100000 == 0:
                    print("{:0.1e}".format(row_count))

    for name in names:
        data[name] = np.array(data[name], dtype=dtypes[name])

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


if __name__ == '__main__':
    main(sys.argv)
