import tempfile
import pandas as pd
from app import db


def build_prescription_report(sf, fmt: str = "csv"):
    df = db.dataframe(
        sf,
        """
        select
            s.patient_id,
            u.name as patient_name,
            s.prescription_count,
            s.total_cost
        from prescription_summary s
        join patients pt on s.patient_id = pt.id
        join users u on pt.user_id = u.id
        order by s.patient_id
        """,
    )

    suffix = ".xlsx" if fmt == "xlsx" else ".csv"
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)

    if fmt == "xlsx":
        df.to_excel(temp.name, index=False)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        df.to_csv(temp.name, index=False)
        media_type = "text/csv"

    return temp.name, media_type