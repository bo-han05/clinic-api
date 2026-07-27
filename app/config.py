import os
from dotenv import load_dotenv


class Settings:
    def __init__(self):
        env = os.getenv("ENV", "dev")
        load_dotenv(f".env.{env}")

        self.env = os.getenv("ENV", env)
        self.testing = os.getenv("TESTING") == "1"

        self.sf_account = os.getenv("SNOWFLAKE_ACCOUNT")
        self.sf_user = os.getenv("SNOWFLAKE_USER")
        self.sf_password = os.getenv("SNOWFLAKE_PASSWORD")
        self.sf_role = os.getenv("SNOWFLAKE_ROLE")
        self.sf_warehouse = os.getenv("SNOWFLAKE_WAREHOUSE")
        self.sf_database = os.getenv("SNOWFLAKE_DATABASE")
        self.sf_schema = os.getenv("SNOWFLAKE_SCHEMA", f"HEALTHCARE_{self.env.upper()}")


settings = Settings()