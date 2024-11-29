import os
import shutil
import yaml


def load_config(filename):
    with open(filename, 'r') as file:
        return yaml.safe_load(file)

class Config:
    def __init__(self, config_file):
        config = load_config(config_file)

        self.name = config['name']

        self.airfield_file_path = config['input_files']['airfield_file']
        self.topography_file_path = config['input_files']['topography_file']
        self.result_folder_path = config['input_files']['result_folder']
        self.compute = config['input_files']['compute']
        self.mapcssTemplate = config['input_files']['mapcssTemplate']
        
        self.conda_path = config['conda_path']
        self.conda_gdal_env = config['conda_gdal_env']

        self.CRS = config['CRS']['definition']
        self.CRS_name = config['CRS']['name']

        self.glide_ratio = config['glide_parameters']['glide_ratio']
        self.ground_clearance = config['glide_parameters']['ground_clearance']
        self.circuit_height = config['glide_parameters']['circuit_height']

        self.max_altitude = config['calculation_parameters']['max_altitude']

        self.contour_height = config['rendering']['contour_height']

        self.gurumaps = config["gurumaps"]
        self.exportPasses = config["exportPasses"]
        self.reset_results = self.clean(config["reset_results"])

        self.merged_output_name = config["merged_output_name"]
        
        self.calculation_folder = self.create_calculation_folder()

    def create_calculation_folder(self):
        dir_path = os.path.join(self.result_folder_path,f'{self.glide_ratio}-{self.ground_clearance}-{self.circuit_height}-{self.max_altitude}')
        # dir_path = f"{result_folder_path}/{glide_ratio}-{ground_clearance}-{circuit_height}-{max_altitude}"
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        return dir_path

    def clean(self, reset):
        if reset:
            try:
                # Check if the directory exists before attempting to remove it
                if os.path.exists(self.result_folder_path):
                    # Remove the directory and all its contents
                    shutil.rmtree(self.result_folder_path)
                    print(f"deleted {self.result_folder_path}")
            except Exception as e:
                print(f"An error occurred while trying to delete the directory {self.result_folder_path}: {e}")
        return reset
    
    def print(self):
        print(f"airfields: {self.airfield_file_path}")
        print(f"topography: {self.topography_file_path} - {self.CRS_name}")
        print(f"results folder: {self.result_folder_path}")
        print(f"calculating {self.name} with glide {self.glide_ratio}, ground clearance {self.ground_clearance}, circuit height {self.circuit_height}, up to {self.max_altitude}m")
