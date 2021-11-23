import cth_mts_biax.read_variables as rv
import os

# This script reads variables saved by the user (save variables) from a mts test program. This can be useful to save intermediate test results measured by the machine
# Especially useful for keeping track of counters for specific events (e.g. when a measurement is taking place). Also for debugging the setup (e.g. to check if stiffness measurements are reasonable)
# It is just for demo purposes, and doesn't save anything: it just shows how to read the variables which can be used somehow depending on your context

def main():
    # Specify input xml_file and output hdf_file        
    xml_file = 'data/variables.xml'
    
    variables, units, inds = rv.get_variable_dicts("data/variables.xml")
    # variables: Dictionary with numpy array of the values
    # units: Dictionary with the unit of each variable (same keys as ``variables``)
    # inds: Dictionary with the indices when each variable was saved (same keys as ``variables``). 
    # If we have multiple times in the test when something is saved, but not everything is saved each time. 
    # So if "Emod" is only saved every other time, inds["Emod"] = [0, 2, 4, ...]
    
    print("{:30s} {:6s}   {:30s}".format("variable", "length", "unit"))
    for key in variables:
        print("{:30s} {:6.0f}   {:30s}".format(key, len(variables[key]), units[key]))
    

if __name__ == '__main__':
    main()
