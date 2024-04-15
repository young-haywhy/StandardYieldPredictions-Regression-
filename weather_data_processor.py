import re
import numpy as np
import pandas as pd
import logging
from data_ingestion import read_from_web_CSV

class WeatherDataProcessor:
    """
    A class representing weather data

    Attributes:
        config_params(str): A dictionary that contain useful class details
        loggin_level(str): level of log messages
    """
    
    def __init__(self, config_params, logging_level="INFO"): # Now we're passing in the confi_params dictionary already
        """
        Initialise a new weather data instance

        Atrributes:
            config_params(str): A dictionary that contain useful class details
            loggin_level(str): level of log messages
        """
        
        self.weather_station_data = config_params['weather_csv_path']
        self.patterns = config_params['regex_patterns']
        self.weather_df = None  # Initialize weather_df as None or as an empty DataFrame
        self.initialize_logging(logging_level)

    def initialize_logging(self, logging_level):
        """
        Sets up logging for this instance of FieldDataProcessor.
        """
        logger_name = __name__ + ".WeatherDataProcessor"
        self.logger = logging.getLogger(logger_name)
        self.logger.propagate = False  # Prevents log messages from being propagated to the root logger

        # Set logging level
        if logging_level.upper() == "DEBUG":
            log_level = logging.DEBUG
        elif logging_level.upper() == "INFO":
            log_level = logging.INFO
        elif logging_level.upper() == "NONE":  # Option to disable logging
            self.logger.disabled = True
            return
        else:
            log_level = logging.INFO  # Default to INFO

        self.logger.setLevel(log_level)

        # Only add handler if not already added to avoid duplicate messages
        if not self.logger.handlers:
            ch = logging.StreamHandler()  # Create console handler
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

    def weather_station_mapping(self):
        """
        Reads a CSV file into a Pandas DataFrame

        Returns:
            self.weather_df(df): A Pandas DataFraame
        """
        self.weather_df = read_from_web_CSV(self.weather_station_data)
        self.logger.info("Successfully loaded weather station data from the web.") 
        # Here, you can apply any initial transformations to self.weather_df if necessary.

    
    def extract_measurement(self, message):
        """ 
        Uses specified Regex pattern to extract measurement parameters from a series of String Datatype.

        Attributes:
            message(str): messages through which we search our Regex patterns
        Returns: None
            
        """
        for key, pattern in self.patterns.items():
            match = re.search(pattern, message)
            if match:
                self.logger.debug(f"Measurement extracted: {key}")
                return key, float(next((x for x in match.groups() if x is not None)))
        self.logger.debug("No measurement match found.")
        return None, None

    def process_messages(self):
        """
        Apply the extract_measurement() function to the weather_df dataframe to return a modified DataFrame

        Returns:
            A modified DataFrame with an additional column.
        """
        if self.weather_df is not None:
            result = self.weather_df['Message'].apply(self.extract_measurement)
            self.weather_df['Measurement'], self.weather_df['Value'] = zip(*result)
            self.logger.info("Messages processed and measurements extracted.")
        else:
            self.logger.warning("weather_df is not initialized, skipping message processing.")
        return self.weather_df

    def calculate_means(self):
        """
        Calculates the mean of the previously extracted numeric values grouped by the the 'Weather_station_ID' 
        and "Measurement' columns of the weather_df DataFrame
        """
        if self.weather_df is not None:
            means = self.weather_df.groupby(by=['Weather_station_ID', 'Measurement'])['Value'].mean()
            self.logger.info("Mean values calculated.")
            return means.unstack()
        else:
            self.logger.warning("weather_df is not initialized, cannot calculate means.")
            return None
    
    def process(self):
        """
        This process calls the correct methods and applies the changes, step by step. This is the method we will call, 
        and it will call the other methods in order.

        Returns: 
            self.weather_df(df): A completely processed DataFrame
        """
        self.weather_station_mapping()  # Load and assign data to weather_df
        self.process_messages()  # Process messages to extract measurements
        self.logger.info("Data processing completed.")