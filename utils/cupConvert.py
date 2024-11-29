import pandas as pd
import re

def convert_coord(coord_str):
    """
    Convert coordinates from DDMM.mmm"N" or DDDMM.mmm"E" format to decimal degrees.
    
    Args:
    coord_str (str): Coordinate in the format DDMM.mmmN or DDDMM.mmmE.
    
    Returns:
    float: Coordinate in decimal degrees.
    """
    match = re.match(r"(\d{2,3})(\d{2}\.\d+)([NSEW])", coord_str)
    if not match:
        raise ValueError(f"Coordinate format {coord_str} is not recognized.")
    
    degrees = int(match.group(1))
    minutes = float(match.group(2))
    direction = match.group(3)
    
    dd = degrees + minutes / 60
    
    # Adjust for south or west
    if direction in ["S", "W"]:
        dd = -dd
    
    return dd

# Load the CSV file
df = pd.read_csv('data/waypoints/guide_aires_securite.cup')  # Skip the header row

# Remove the version line if it's at the beginning (assuming it's the second row)
df = df[df['name'] != 'version=']

# Convert the coordinates
df['lat_dd'] = df['lat'].apply(convert_coord)
df['lon_dd'] = df['lon'].apply(convert_coord)

# Select only the fields you want to keep
df = df[['name', 'lon_dd', 'lat_dd']]

# Rename the new coordinate columns
df.rename(columns={'lat_dd': 'y', 'lon_dd': 'x'}, inplace=True)

# If you want to save this as a new CSV:
df.to_csv('data/waypoints/guide_aires_securite.csv', index=False)