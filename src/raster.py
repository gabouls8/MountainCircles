import os
import numpy as np
from src.shortcuts import normJoin
from src.postprocess import postProcess
from src.logging import log_output


def read_asc(file_path):
    """Reads an .asc file into a numpy array with metadata."""
    with open(file_path, 'r') as file:
        ncols = int(next(file).split()[1])
        nrows = int(next(file).split()[1])
        xllcorner = float(next(file).split()[1])
        yllcorner = float(next(file).split()[1])
        cellsize = float(next(file).split()[1])
        nodata_value = float(next(file).split()[1])
        
        data = np.genfromtxt(file, dtype=float)
        
        return data, ncols, nrows, xllcorner, yllcorner, cellsize, nodata_value



def write_asc(data, filename, ncols, nrows, xllcorner, yllcorner, cellsize, nodata_value):
    """Writes a numpy array to an .asc file."""
    with open(filename, 'w') as file:
        file.write(f'ncols {ncols}\n')
        file.write(f'nrows {nrows}\n')
        file.write(f'xllcorner {xllcorner}\n')
        file.write(f'yllcorner {yllcorner}\n')
        file.write(f'cellsize {cellsize}\n')
        file.write(f'NODATA_value {nodata_value}\n')
        for row in data:
            row_str = ' '.join(str(val if not np.isnan(val) else nodata_value) for val in row)
            file.write(row_str + '\n')



def align_rasters(rasters, cellsize):
    """Aligns rasters into a common grid by updating only where data exists."""
    # Determine the extent of the entire area
    min_x = min(raster[3] for raster in rasters)
    max_x = max(raster[3] + raster[1] * cellsize for raster in rasters)
    min_y = min(raster[4] for raster in rasters)
    max_y = max(raster[4] + raster[2] * cellsize for raster in rasters)
    
    ncols = int((max_x - min_x) / cellsize)
    nrows = int((max_y - min_y) / cellsize)
    
    # Use nodata_value from the first raster for initialization
    nodata_value = rasters[0][6]  # Assuming nodata_value is the 7th element
    aligned = np.full((nrows, ncols), nodata_value)
    
    for data, ncols_sub, nrows_sub, xllcorner, yllcorner, _, _ in rasters:
        # Calculate positions
        start_row = nrows - int((yllcorner + nrows_sub * cellsize - min_y) / cellsize)
        end_row = start_row + nrows_sub
        start_col = int((xllcorner - min_x) / cellsize)
        end_col = start_col + ncols_sub
        
        # Slice of aligned where data should be updated
        aligned_slice = aligned[start_row:end_row, start_col:end_col]

        # Update aligned, taking the minimum where values aren't nodata
        aligned[start_row:end_row, start_col:end_col] = np.minimum(
            data, 
            aligned_slice
        )

    return aligned, min_x, min_y, nrows, ncols


def merge_output_rasters(config, output_filename, sectors_filename, output_queue=None):
    log_output("merging final raster", output_queue)
    nodata_value = float(config.max_altitude)
    # nodata_value = config.max_altitude

    """Merges all output_sub.asc files from airfield directories in chunks."""
    # First, read all headers to get the extent of all rasters
    all_headers = []
    for root, _, files in os.walk(config.calculation_folder_path):
        for file in files:
            if file == 'output_sub.asc':
                path = normJoin(root, file)
                with open(path, 'r') as file:
                    ncols = int(next(file).split()[1])
                    nrows = int(next(file).split()[1])
                    xllcorner = float(next(file).split()[1])
                    yllcorner = float(next(file).split()[1])
                    cellsize = float(next(file).split()[1])
                    # We don't need nodata_value from the file since we're using the one provided
                    all_headers.append((path, ncols, nrows, xllcorner, yllcorner, cellsize))

    if not all_headers:
        log_output("No output_sub.asc files found to merge.", output_queue)
        return

    cellsize=all_headers[0][5]

    # Determine the extent of the entire area
    min_x = min(header[3] for header in all_headers)
    max_x = max(header[3] + header[1] * cellsize for header in all_headers)
    min_y = min(header[4] for header in all_headers)
    max_y = max(header[4] + header[2] * cellsize for header in all_headers)

    ncols_total = int((max_x - min_x) / cellsize)
    nrows_total = int((max_y - min_y) / cellsize)
    
    # Initialize the aligned array with nodata_value
    aligned = np.full((nrows_total, ncols_total), nodata_value)
    sectors = np.full((nrows_total, ncols_total), nodata_value)
    # Process each raster file one by one
    sector=0
    for path, ncols_sub, nrows_sub, xllcorner, yllcorner, cellsize in all_headers:
        log_output(f"aligining {path}", output_queue)
        # Calculate positions in the aligned grid
        start_row = nrows_total - int((yllcorner + nrows_sub * cellsize - min_y) / cellsize)
        end_row = start_row + nrows_sub
        start_col = int((xllcorner - min_x) / cellsize)
        end_col = start_col + ncols_sub


        # Add bounds checking
        if start_row < 0 or end_row > nrows_total or start_col < 0 or end_col > ncols_total:
            log_output(f"airfield local matrix going out of bound of reconstructed matrix, skipping 1 line: {path}", output_queue)
            continue  # Skip this file if out of bounds

        # Read the data in chunks to avoid memory issues
        with open(path, 'r') as file:
            for _ in range(6):  # Skip header lines
                next(file)

            for i, line in enumerate(file):
                if i >= nrows_sub:
                    log_output("out of bounds", output_queue)
                    break  # Ensure we don't read beyond the specified number of rows

                row_data = np.fromstring(line, dtype=float, sep=' ')
                aligned_slice = aligned[start_row + i, start_col:end_col]
                sectors_slice = sectors[start_row + i, start_col:end_col]
                # Create a mask for where updates will occur
                update_mask = (row_data != nodata_value) & (row_data < aligned_slice)
                sectors_mask = (row_data != nodata_value) & (row_data < aligned_slice)
                sectors_reset = (row_data == 0) 
                # Update aligned array
                aligned_slice[update_mask] = row_data[update_mask]
                sectors_slice[sectors_mask] = sector
                sectors_slice[sectors_reset] = nodata_value
        sector += 1


    # Set merged data to nodata_value where data equals zero
    log_output("removing ground from merged raster", output_queue)
    aligned[aligned == 0] = nodata_value

    # Write the merged raster
    output_path = config.merged_output_raster_path
    sectors_path = config.sectors_filepath
    log_output(f"writing final raster to {output_path}", output_queue)
    log_output(f"writing sector raster to {sectors_path}", output_queue)
    log_output(f"Done, writing final raster...", output_queue)
    write_asc(aligned, output_path, ncols_total, nrows_total, min_x, min_y, all_headers[0][5], nodata_value)
    log_output(f"Done, writing sector raster...",output_queue)
    write_asc(sectors, sectors_path, ncols_total, nrows_total, min_x, min_y, all_headers[0][5], nodata_value)
    log_output(f"Post processing final raster...",output_queue)

    postProcess(config.calculation_folder_path, config.calculation_folder_path, config, output_path, config.merged_output_name)

