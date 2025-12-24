import datetime
import time
import re
import json

import dotenv
import polars as pl
import pytz
import modules.database as db
import yaml

from modules.database import get_conn_str, data_to_db

dotenv.load_dotenv()


def main():
    current_timestamp = datetime.datetime.now(tz=pytz.timezone("UTC")).timestamp()
    db_conn = get_conn_str()
    data_to_db("", db_conn, table_name="transactions")

    time.sleep(5)


# if __name__ == "__main__":
#     main()
