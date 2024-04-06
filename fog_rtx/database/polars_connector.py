import logging
from typing import List
import polars as pl
from fog_rtx.database.utils import _datasets_dtype_to_pld

logger = logging.getLogger(__name__)

class PolarsConnector:
    def __init__(self, path: str):
        # In Polars, data is directly read into DataFrames from files, not through a database engine
        self.path = path
        self.tables = {}  # This will store table names as keys and DataFrames as values

    def close(self):
        # No connection to close in Polars, but we could clear the tables dictionary
        pass

    def list_tables(self):
        # Listing available DataFrame tables
        return list(self.tables.keys())

    def create_table(self, table_name: str):
        # Create a new DataFrame with specified columns
        # schema = {column_name: _datasets_dtype_to_arrow(column_type) for column_name, column_type in columns.items()}
        self.tables[table_name] = pl.DataFrame()
        logger.info(f"Table {table_name} created with Polars.")

    def add_column(self, table_name: str, column_name: str, column_type):
        if column_name in self.tables[table_name].columns:
            logger.warning(f"Column {column_name} already exists in table {table_name}.")
            return
        # Add a new column to an existing DataFrame
        if table_name in self.tables:
            arrow_type = _datasets_dtype_to_pld(column_type)
            # self.tables[table_name] = self.tables[table_name].with_column(pl.lit(None).alias(column_name).cast(column_type))
            self.tables[table_name] = self.tables[table_name].with_columns(pl.lit(None).alias(column_name).cast(arrow_type))
            logger.info(f"Column {column_name} added to table {table_name}.")
        else:
            logger.error(f"Table {table_name} does not exist.")

    def insert_data(self, table_name: str, data: dict):
        # Inserting a new row into the DataFrame and return the index of the new row
        if table_name in self.tables:
            ordered_data = {col: data.get(col, None) for col in self.tables[table_name].columns}
            logger.info(f"Inserting data into {self.tables[table_name]} with data {ordered_data}")
            new_row = pl.DataFrame([ordered_data])
            index_of_new_row = len(self.tables[table_name])
            self.tables[table_name] = pl.concat([self.tables[table_name], new_row])
            logger.info(f"Data inserted into {table_name}: {ordered_data}")
            return index_of_new_row  # Return the index of the inserted row
        else:
            logger.error(f"Table {table_name} does not exist.")
            return None  # Or raise an exception depending on your error handling strategy

    def update_data(self, table_name: str, index: int, data: dict):
        # update data
        for column_name, value in data.items():
            logger.info(self.tables[table_name])
            self.tables[table_name][column_name][index] = value

    def merge_tables_with_timestamp(self, tables: List[str], output_table: str):
        # Merging tables using timestamps
        if len(tables) > 1:
            merged_df = self.tables[tables[0]].join(self.tables[tables[1]], on="Timestamp", how="outer")
            for table_name in tables[2:]:
                merged_df = merged_df.join(self.tables[table_name], on="Timestamp", how="outer")
            self.tables[output_table] = merged_df.sort("Timestamp")
            logger.info("Tables merged on Timestamp.")
        else:
            logger.error("Need at least two tables to merge.")

    def select_table(self, table_name: str):
        # Return the DataFrame
        if table_name in self.tables:
            return self.tables[table_name]
        else:
            logger.error(f"Table {table_name} does not exist.")
            return None