import cth_mts_biax.xml_to_hdf5 as x2h
import os

# This script reads in the test data saved in the MTS test machines native xml format and saves it to a hdf5 file format (which is more efficient)
# Using this approach is necessary for very large test data files, but has advantages (such as automatic recognizing the unit) even for smaller data files


def main():
    # Create output folder if it doesn't already exist
    if not os.path.exists("output"):
        os.mkdir("output")
    # Specify input xml_file and output hdf_file        
    xml_file = 'data/data'
    hdf_file = 'output/data'
    # Outer diameter required to get the correct surface strain as the extensometer is calibrated for 10.00 mm diameter
    outer_diameter = 19.95
    
    # Read the data "as-is" from the xml file
    raw_data, raw_units = x2h.get_data(xml_file)
    
    # Reduce the data size by using float32 for sensor data and possibly for time.
    # Also, only save one count (axial). In this case, save displacements and rotations (can be removed by setting save_disp=False)
    # Please see documentation for keyword options
    data, units, dtypes = x2h.reduce_data(raw_data, raw_units, save_disp=True)
    # raw_data is not needed later, so delete to reduce memory usage
    del raw_data    
    # Compensate data based on machine stiffness and outer diameter (surface strain). 
    # Also, switch sign on rotation for consistent coordinate system
    comp_data, comp_units, comp_attributes = x2h.compensate(data, units, outer_diameter)
    # Delete the uncompensated data to save memory
    del data
    # Save the compensated data to hdf, adding the compensation values to the top level attributes
    x2h.save_data(hdf_file, comp_data, comp_units, dtypes, global_attributes=comp_attributes)


if __name__ == '__main__':
    main()
