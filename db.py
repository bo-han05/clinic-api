from app.models import MODELS, table_name, columns_for


def create_snowpark_session(settings):
    from snowflake.snowpark import Session

    return Session.builder.configs(
        {
            "account": settings.sf_account,
            "user": settings.sf_user,
            "password": settings.sf_password,
            "role": settings.sf_role,
            "warehouse": settings.sf_warehouse,
            "database": settings.sf_database,
            "schema": settings.sf_schema,
        }
    ).create()

def q(value):
    if value is None:
        return "null"
    if isinstance(value, str):
        return "'" + value.replace("'", "''") + "'"
    return str(value)

def execute(sf, sql: str):
    return sf.sql(sql).collect()

def rows(sf, sql: str):
    return [_lower(r.as_dict()) for r in sf.sql(sql).collect()]

def row(sf, sql: str):
    result = rows(sf, sql)
    return result[0] if result else None

def dataframe(sf, sql: str):
    return sf.sql(sql).to_pandas()

def _lower(d: dict):
    return {k.lower(): v for k, v in d.items()}

def init_snowflake(sf, settings):
    execute(sf, f"create schema if not exists {settings.sf_schema}")
    execute(sf, f"use schema {settings.sf_schema}")

    for model in MODELS:
        cols = ", ".join(columns_for(model, settings.env))
        execute(sf, f"create or replace temporary table {table_name(model)} ({cols})")

    if settings.env == "prod":
        execute(
            sf,
            """
            create or replace temporary view prescription_summary as
            select patient_id, count(*) as prescription_count, sum(cost) as total_cost
            from prescriptions
            group by patient_id
            """,
        )
    else:
        execute(
            sf,
            """
            create or replace temporary view prescription_summary as
            select patient_id, count(*) as prescription_count, 0 as total_cost
            from prescriptions
            group by patient_id
            """,
        )

def seed_data(sf, env: str):
    execute(
        sf,
        """
        insert into users (id, name, role) values
        (1, 'Alice Robinson', 'patient'),
        (2, 'Bob Parker', 'patient'),
        (3, 'Dr. Smith', 'provider'),
        (4, 'Admin User', 'admin')
        """,
    )

    execute(
        sf,
        """
        insert into patients (id, user_id, insurance_policy_number) values
        (1, 1, 'POL-A111'),
        (2, 2, 'POL-B222')
        """,
    )

    execute(
        sf,
        """
        insert into appointments (id, patient_id, provider_id, status) values
        (1, 1, 3, 'confirmed')
        """,
    )

    if env == "prod":
        execute(
            sf,
            """
            insert into prescriptions
            (id, patient_id, medication, dosage, status, cost) values
            (1, 1, 'Atorvastatin', '10mg', 'active', 12.50),
            (2, 2, 'Metformin', '500mg', 'active', 8.75)
            """,
        )
    else:
        execute(
            sf,
            """
            insert into prescriptions
            (id, patient_id, medication, dosage, status) values
            (1, 1, 'Atorvastatin', '10mg', 'active'),
            (2, 2, 'Metformin', '500mg', 'active')
            """,
        )