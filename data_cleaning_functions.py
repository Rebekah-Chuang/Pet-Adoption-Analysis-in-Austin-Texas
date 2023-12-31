"""
This data_cleaning_functions.py file includes all functions I used for data cleaning
"""
import requests
import pandas as pd


def get_data(urls: dict):
    """
    Fetches the latest data from API endpoints provided by Austin Animal Center.

    :param urls: a dictionary of data file where key is the file_name and value is the url for that dataset
    :return: intake_data and outcome_data
    """
    # Store data in dictionaries
    data_dict = {}

    # Make a GET request to fetch the data
    for file_name, url in urls.items():
        response = requests.get(url)
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Read the response content (CSV data) into a pandas DataFrame
            data = pd.read_csv(url)
            # Store the DataFrame in the dictionary
            data_dict[file_name] = data
            # Display the first few rows of the data
            print(f"Successfully get {file_name.upper()} data({len(data_dict[file_name])} rows)...")
        else:
            print(f"Failed to retrieve {file_name.upper()} data. Status code:", response.status_code)

    # Access the DataFrames by their labels
    intake_data = data_dict["intake"]
    outcome_data = data_dict["outcome"]

    return intake_data, outcome_data


def date_format(df: pd.DataFrame, col: str, datetime_format: str) -> pd.DataFrame:
    """
    Modify the datetime format of a specified column in the dataframe.

    :param df: dataframe you want to modify
    :param col: column in the dataframe you would like to change the date format
    :param datetime_format: the data or time format you want
    :return: the updated dataframe

    >>> test = {"date":["2014-04-02 15:55:00"]}
    >>> test_df = pd.DataFrame(test)
    >>> date_format(test_df, "date", "%Y-%m-%d")["date"]
    0   2014-04-02
    Name: date, dtype: datetime64[ns]

    >>> test2 = {"date":["2013-10-11T11:29:35.000"]}
    >>> test_df2 = pd.DataFrame(test2)
    >>> date_format(test_df2, "date", "%Y-%m-%d %H:%M")["date"]
    0   2013-10-11 11:29:00
    Name: date, dtype: datetime64[ns]
    """
    df[col] = pd.to_datetime(df[col])
    df[col] = pd.to_datetime(df[col].dt.strftime(datetime_format))
    return df


def merge_intake_n_outcome(intake_data: pd.DataFrame, outcome_data: pd.DataFrame) -> pd.DataFrame:
    """
    Merges intake and outcome datasets based on animal_id, intake_datetime, and outcome_datetime.

    :param intake_data: DataFrame containing intake information
    :param outcome_data: DataFrame containing outcome information
    :return: Merged DataFrame containing intake and outcome information

    >>> test_intake = pd.read_csv("test_data/test_intake.csv")
    >>> test_intake_data = pd.DataFrame(test_intake)
    >>> test_intake_data['datetime'] = pd.to_datetime(test_intake_data['datetime'])
    >>> test_outcome = pd.read_csv("test_Data/test_outcome.csv")
    >>> test_outcome_data = pd.DataFrame(test_outcome)
    >>> test_outcome_data['datetime'] = pd.to_datetime(test_outcome_data['datetime'])
    >>> merge_intake_n_outcome(test_intake_data, test_outcome_data)
      animal_id     datetime_intake    datetime_outcome    datetime_outcome
    0         a 2019-05-08 18:20:00 2019-05-13 18:20:00 2019-05-13 18:20:00
    1         a 2020-08-12 09:35:00                 NaT                 NaT
    2         b 2013-04-21 07:24:00 2013-04-21 07:24:00 2013-04-21 07:24:00
    3         c 2021-11-25 15:50:00 2021-11-25 15:50:00 2021-11-25 15:50:00
    4         d 2022-03-07 21:05:00 2022-09-18 08:30:00 2022-09-18 08:30:00
    5         e 2023-07-18 12:15:00                 NaT                 NaT
    """
    # Create a dictionary to store each outcome datetime for an animal, where key:animal_id, value:[outcome_datetime]
    outcome_dict = {}
    for index, row in outcome_data.iterrows():
        if row.animal_id not in outcome_dict.keys():
            outcome_dict[row.animal_id] = []
            outcome_dict[row.animal_id].append(row.datetime)
        else:
            outcome_dict[row.animal_id].append(row.datetime)

    # Iterate over each row in intake data to store outcome_datetime for each animal
    intake_data['datetime_outcome'] = pd.NaT
    for index, row in intake_data.iterrows():
        if row.animal_id in outcome_dict.keys():
            if len(outcome_dict[row.animal_id]) > 0:
                intake_data.at[index, "datetime_outcome"] = outcome_dict[row.animal_id][0]
                outcome_dict[row.animal_id].pop(0)

    # Merge the intake and outcome dataframes based on animal_id, outcome datetime
    merged_data = pd.merge(intake_data,
                           outcome_data,
                           how="left",
                           left_on=["animal_id", "datetime_outcome"],
                           right_on=["animal_id", "datetime"],
                           suffixes=("_intake", "_outcome"))
    merged_data.reset_index(drop=True, inplace=True)
    return merged_data


def calculate_time_delta(df: pd.DataFrame, start: str, end: str, unit: str = "days", col_suffix: str = "") -> pd.DataFrame:
    """
    Calculate the age difference or duration between two dates in a DataFrame.

    :param df: DataFrame containing the date columns
    :param start: Column representing the starting date
    :param end: Column representing the ending date
    :param col_suffix: Suffix for the new column name (default: "")
    :param unit: Unit for calculating time difference ("days" or "years") (default: "days")
    :return: DataFrame with a new column representing the time difference

    Examples:
    Calculate the duration from the date of birth to leaving in years
    >>> test = {"date_of_birth":["2014-04-02 15:55:00"], "date_leave":["2015-04-27 14:45:00"]}
    >>> test["date_of_birth"] = pd.to_datetime(test["date_of_birth"])
    >>> test["date_leave"] = pd.to_datetime(test["date_leave"])
    >>> test_df = pd.DataFrame(test)
    >>> calculate_time_delta(test_df, "date_of_birth", "date_leave", unit="years", col_suffix="leaving")
    0    1.1
    Name: age_upon_leaving(years), dtype: float64

    Calculate the duration from the start date to the end date in days
    >>> test2 = {"date_start":["2014-04-02 15:55:00"], "date_end":["2015-04-27 14:45:00"]}
    >>> test2["date_start"] = pd.to_datetime(test2["date_start"])
    >>> test2["date_end"] = pd.to_datetime(test2["date_end"])
    >>> test_df2 = pd.DataFrame(test2)
    >>> calculate_time_delta(test_df2, "date_start", "date_end", unit="days")
    0    389
    Name: duration(days), dtype: int64
    """
    time_delta = df[end] - df[start]
    time_in_days = time_delta.dt.days
    if start == "date_of_birth":
        column_name = f"age_upon_{col_suffix}({unit})"
        if unit == "years":
            time_in_years = round(time_in_days / 365.25, 1)
            df[column_name] = time_in_years
        else:
            df[column_name] = time_in_days

    else:
        column_name = f"duration({unit})"
        df[column_name] = time_in_days

    return df[column_name]
