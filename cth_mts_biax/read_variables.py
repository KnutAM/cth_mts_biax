""" The biaxial testing machine can use a command called "Save variables to file". This will save
the variables listed in an xml format. This module is used to read this file and save the variable
information in a dictionary format. Two output types are possible:

- Variable list: A list containing the variables written each time the "Save variables to file" command
  is called (:py:func:`get_variable_list`)
- Dictionary: Three dictionaries with keys according to the variable name (:py:func:`get_variable_dicts`)

  - The data for each variable as np.arrays
  - The unit for each variable
  - The indices (counter for output commands) for each variable


"""

#from xml.dom import minidom
from defusedxml import minidom
import numpy as np


def get_variable_dicts(file):
    """ Get the variable dictionary output from the xml-formatted file

    :param file: Path to the xml-formatted file
    :type file: str, pathlike

    :returns: Three dictionaries: data, unit, inds
    :rtype: tuple( dict )
    """
    var_list = get_variable_list(file)
    return var_list_to_dicts(var_list)


def var_list_to_dicts(var_list):
    """ Convert Variable list output to dictionary data output

    :param var_list: Output from :py:func:`get_variable_list`
    :type var_list: list[ dict ]

    :returns: Three dictionaries: data, unit, inds
    :rtype: tuple( dict )
    """

    data = {}
    unit = {}
    inds = {}
    for i, item in enumerate(var_list):
        for key in item:
            if key not in data:
                unit[key] = item[key][1]     # unit
                data[key] = []
                inds[key] = []
            if len(item[key][0]) == 1:
                data[key].append(item[key][0][0])
            else:
                data[key].append(item[key][0])
            inds[key].append(i)

    for key in data:
        inds[key] = np.array(inds[key])
        try:
            data[key] = np.array(data[key])
        except ValueError:
            pass

    return data, unit, inds


def get_variable_list(file):
    xml_doc = minidom.parse(file)
    # Get each instance where data has been written to the xml file
    write_instances = xml_doc.getElementsByTagName('ArrayOfVariableData')
    var_list = []
    for write_instance in write_instances:
        var_list.append(get_dict(write_instance))

    return var_list


def get_dict(write_instance):
    written_variables = write_instance.getElementsByTagName('VariableData')
    var_dict = {}
    for written_variable in written_variables:
        name = written_variable.getElementsByTagName('Name')[0].firstChild.data
        try:
            unit = written_variable.getElementsByTagName('Unit')[0].firstChild.data
        except IndexError:
            unit = ''
        values = get_values(written_variable.getElementsByTagName('Values')[0])
        var_dict[name] = (values, unit)

    return var_dict


def get_values(values_element):
    value_elements = values_element.getElementsByTagName('Value')
    values = []
    for value_element in value_elements:
        values.append(value_element.firstChild.data)

    convert_values(values)

    return values


def convert_values(values):

    try:
        tmp = [int(v) for v in values]
    except ValueError:
        try:
            tmp = [float(v) for v in values]
        except ValueError:
            tmp = values

    values[:] = tmp
