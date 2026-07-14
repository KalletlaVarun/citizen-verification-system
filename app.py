from flask import Flask, render_template, request
from db import connection, cursor
from verification import verify_application

app = Flask(__name__)

# ==========================================================
# HOME PAGE
# ==========================================================

@app.route("/")
def home():

    # Total Historical Records
    cursor.execute("SELECT COUNT(*) AS total FROM historical_record")
    historical = cursor.fetchone()["total"]

    # Total Applications
    cursor.execute("SELECT COUNT(*) AS total FROM new_application")
    applications = cursor.fetchone()["total"]

    # Verified
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM verification_result
        WHERE recommendation='Verified'
    """)
    verified = cursor.fetchone()["total"]

    # Manual Review
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM verification_result
        WHERE recommendation='Manual Review'
    """)
    manual = cursor.fetchone()["total"]

    # Rejected
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM verification_result
        WHERE recommendation='Rejected'
    """)
    rejected = cursor.fetchone()["total"]

    # Searches
    cursor.execute("SELECT COUNT(*) AS total FROM search_log")
    searches = cursor.fetchone()["total"]

    return render_template(
        "home.html",
        historical=historical,
        applications=applications,
        verified=verified,
        manual=manual,
        rejected=rejected,
        searches=searches
    )


# ==========================================================
# SEARCH PAGE
# ==========================================================

@app.route("/search_records")
def search_records():
    return render_template("search_records.html")


# ==========================================================
# SEARCH HISTORICAL RECORDS
# ==========================================================

@app.route("/search", methods=["POST"])
def search():

    first_name = request.form.get("first_name", "").strip()
    last_name = request.form.get("last_name", "").strip()
    father_name = request.form.get("father_name", "").strip()
    mother_name = request.form.get("mother_name", "").strip()
    dob = request.form.get("dob", "").strip()
    phone = request.form.get("phone", "").strip()
    district = request.form.get("district", "").strip()
    constituency = request.form.get("constituency", "").strip()

    # Empty Search
    if not any([
        first_name,
        last_name,
        father_name,
        mother_name,
        dob,
        phone,
        district,
        constituency
    ]):
        return render_template(
            "search_results.html",
            records=[],
            message="Please enter at least one search field."
        )

    query = """
    SELECT *
    FROM historical_record
    WHERE 1=1
    """

    values = []

    if first_name:
        query += " AND first_name LIKE %s"
        values.append(f"%{first_name}%")

    if last_name:
        query += " AND last_name LIKE %s"
        values.append(f"%{last_name}%")

    if father_name:
        query += " AND father_name LIKE %s"
        values.append(f"%{father_name}%")

    if mother_name:
        query += " AND mother_name LIKE %s"
        values.append(f"%{mother_name}%")

    if dob:
        query += " AND dob=%s"
        values.append(dob)

    if phone:
        query += " AND phone LIKE %s"
        values.append(f"%{phone}%")

    if district:
        query += " AND district LIKE %s"
        values.append(f"%{district}%")

    if constituency:
        query += " AND constituency LIKE %s"
        values.append(f"%{constituency}%")

    cursor.execute(query, tuple(values))
    records = cursor.fetchall()

    keyword = " | ".join(filter(None, [
        first_name,
        last_name,
        father_name,
        mother_name,
        dob,
        phone,
        district,
        constituency
    ]))

    cursor.execute("""
        INSERT INTO search_log
        (search_keyword, search_type, records_found)
        VALUES(%s,%s,%s)
    """,
    (
        keyword,
        "Search",
        len(records)
    ))

    connection.commit()

    if len(records) == 0:

        return render_template(
            "search_results.html",
            records=[],
            message="No Historical Record Found."
        )

    return render_template(
        "search_results.html",
        records=records,
        message=None
    )


# ==========================================================
# VIEW COMPLETE RECORD
# ==========================================================

@app.route("/record/<int:history_id>")
def record_details(history_id):

    cursor.execute(
        "SELECT * FROM historical_record WHERE history_id=%s",
        (history_id,)
    )

    record = cursor.fetchone()

    return render_template(
        "record_details.html",
        record=record
    )


# ==========================================================
# VIEW ALL HISTORICAL RECORDS
# ==========================================================

@app.route("/historical_records")
def historical_records():

    cursor.execute("""
        SELECT *
        FROM historical_record
        ORDER BY history_id
    """)

    records = cursor.fetchall()

    return render_template(
        "historical_records.html",
        records=records
    )


# ==========================================================
# NEW APPLICATION PAGE
# ==========================================================

@app.route("/new_application")
def new_application():
    return render_template("new_application.html")


# ==========================================================
# SAVE NEW APPLICATION
# ==========================================================

@app.route("/submit_application", methods=["POST"])
def submit_application():

    query = """
    INSERT INTO new_application
    (
        first_name,
        middle_name,
        last_name,
        father_name,
        mother_name,
        gender,
        dob,
        phone,
        email,
        address,
        city,
        district,
        state,
        pincode,
        constituency
    )

    VALUES
    (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    values = (

        request.form["first_name"],
        request.form["middle_name"],
        request.form["last_name"],
        request.form["father_name"],
        request.form["mother_name"],
        request.form["gender"],
        request.form["dob"] if request.form["dob"] else None,
        request.form["phone"],
        request.form["email"],
        request.form["address"],
        request.form["city"],
        request.form["district"],
        request.form["state"],
        request.form["pincode"],
        request.form["constituency"]

    )

    cursor.execute(query, values)
    connection.commit()

    application_id = cursor.lastrowid

    cursor.execute("""
    INSERT INTO audit_log
    (
    table_name,
    record_id,
    action_type,
    old_value,
    new_value
    )
    VALUES
    (%s,%s,%s,%s,%s)
    """,
    (
    "new_application",
    application_id,
    "INSERT",
    None,
    "Application Submitted"
    ))

    connection.commit()

    # ------------------------
    # Automatic Verification
    # ------------------------

    best_record, score, recommendation, score_details, reason = verify_application(application_id)

    return render_template(
    "verification_result.html",
    best_record=best_record,
    score=score,
    recommendation=recommendation,
    score_details=score_details,
    reason=reason
)


# ==========================================================
# VERIFICATION HISTORY
# ==========================================================

@app.route("/verification_results")
def verification_results():

    query = """
    SELECT
        vr.verification_id,
        vr.application_id,
        na.first_name,
        na.last_name,
        vr.overall_score,
        vr.recommendation,
        vr.verification_date
    FROM verification_result vr
    JOIN new_application na
        ON vr.application_id = na.application_id
    ORDER BY vr.verification_date DESC,
             vr.verification_id DESC
    """

    cursor.execute(query)
    results = cursor.fetchall()

    return render_template(
        "verification_history.html",
        results=results
    )

# ==========================================================
# SEARCH LOGS
# ==========================================================

@app.route("/search_logs")
def search_logs():

    cursor.execute("""
        SELECT *
        FROM search_log
        ORDER BY search_timestamp DESC
    """)

    logs = cursor.fetchall()

    return render_template(
        "search_logs.html",
        logs=logs
    )

@app.route("/audit_logs")
def audit_logs():

    cursor.execute("""
    SELECT *
    FROM audit_log
    ORDER BY action_date DESC
    """)

    logs = cursor.fetchall()

    return render_template(
        "audit_logs.html",
        logs=logs
    )

# ==========================================================
# RUN SERVER
# ==========================================================

if __name__ == "__main__":
    app.run(debug=True)