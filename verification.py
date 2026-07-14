from db import cursor, connection


def verify_application(application_id):

    # -----------------------------
    # Get Application
    # -----------------------------
    cursor.execute("""
        SELECT *
        FROM new_application
        WHERE application_id=%s
    """, (application_id,))

    application = cursor.fetchone()

    # -----------------------------
    # Search by Parents
    # -----------------------------
    cursor.execute("""
        SELECT *
        FROM historical_record
        WHERE LOWER(father_name)=LOWER(%s)
           OR LOWER(mother_name)=LOWER(%s)
    """,
    (
        application["father_name"],
        application["mother_name"]
    ))

    historical_records = cursor.fetchall()

    # -----------------------------
    # No Family Found
    # -----------------------------
    if len(historical_records) == 0:

        cursor.execute("""
        INSERT INTO verification_result
        (
        application_id,
        history_id,
        name_score,
        father_name_score,
        mother_name_score,
        dob_score,
        address_score,
        phone_score,
        overall_score,
        recommendation,
        verification_date
        )

        VALUES
        (%s,NULL,0,0,0,0,0,0,0,'Manual Review',CURDATE())
        """,

        (application_id,))

        connection.commit()

        return None,0,"Manual Review",{
            "first_name":0,
            "last_name":0,
            "father_name":0,
            "mother_name":0,
            "dob":0,
            "phone":0,
            "district":0,
            "constituency":0
        }

    # -----------------------------
    # Compare only family members
    # -----------------------------

    best_record = None
    best_score = -1
    best_percentage = 0
    best_score_details = {}

    for record in historical_records:

        matched_score = 0
        max_score = 0
        details = {}

    # Father Name (30)
    max_score += 30
    if application["father_name"].lower() == record["father_name"].lower():
        matched_score += 30
        details["father_name"] = 30
    else:
        details["father_name"] = 0

    # Mother Name (20)
    max_score += 20
    if application["mother_name"].lower() == record["mother_name"].lower():
        matched_score += 20
        details["mother_name"] = 20
    else:
        details["mother_name"] = 0

    # First Name (15)
    if application["first_name"]:
        max_score += 15
        if application["first_name"].lower() == record["first_name"].lower():
            matched_score += 15
            details["first_name"] = 15
        else:
            details["first_name"] = 0
    else:
        details["first_name"] = "-"

    # Last Name (10)
    if application["last_name"]:
        max_score += 10
        if application["last_name"].lower() == record["last_name"].lower():
            matched_score += 10
            details["last_name"] = 10
        else:
            details["last_name"] = 0
    else:
        details["last_name"] = "-"

    # DOB (10)
    if application["dob"]:
        max_score += 10
        if application["dob"] == record["dob"]:
            matched_score += 10
            details["dob"] = 10
        else:
            details["dob"] = 0
    else:
        details["dob"] = "-"

    # Phone (5)
    if application["phone"]:
        max_score += 5
        if application["phone"] == record["phone"]:
            matched_score += 5
            details["phone"] = 5
        else:
            details["phone"] = 0
    else:
        details["phone"] = "-"

    # District (5)
    if application["district"]:
        max_score += 5
        if application["district"].lower() == record["district"].lower():
            matched_score += 5
            details["district"] = 5
        else:
            details["district"] = 0
    else:
        details["district"] = "-"

    # Constituency (5)
    if application["constituency"]:
        max_score += 5
        if application["constituency"].lower() == record["constituency"].lower():
            matched_score += 5
            details["constituency"] = 5
        else:
            details["constituency"] = 0
    else:
        details["constituency"] = "-"

    percentage = round((matched_score / max_score) * 100) if max_score else 0

    if percentage > best_percentage:
        best_percentage = percentage
        best_score = matched_score
        best_record = record
        best_score_details = details

    # -----------------------------
    # Recommendation
    # -----------------------------

    if best_percentage >= 90:
        recommendation = "Verified"
    elif best_percentage >= 50:
        recommendation = "Manual Review"
    else:
        recommendation = "Rejected"

    # -----------------------------
    # Insert Result
    # -----------------------------

    cursor.execute("""

    INSERT INTO verification_result
    (
    application_id,
    history_id,
    name_score,
    father_name_score,
    mother_name_score,
    dob_score,
    address_score,
    phone_score,
    overall_score,
    recommendation,
    verification_date
    )

    VALUES
    (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,CURDATE())

    """,

    (

    application_id,

    best_record["history_id"],

    25,

    30 if application["father_name"].lower()==best_record["father_name"].lower() else 0,

    20 if application["mother_name"].lower()==best_record["mother_name"].lower() else 0,

    10 if application["dob"] and application["dob"]==best_record["dob"] else 0,

    10 if application["district"].lower()==best_record["district"].lower() else 0,

    5 if application["phone"] and application["phone"]==best_record["phone"] else 0,

    best_percentage,

    recommendation

    ))

    connection.commit()

    score_details={

        "first_name":15 if application["first_name"].lower()==best_record["first_name"].lower() else 0,

        "last_name":10 if application["last_name"].lower()==best_record["last_name"].lower() else 0,

        "father_name":30 if application["father_name"].lower()==best_record["father_name"].lower() else 0,

        "mother_name":20 if application["mother_name"].lower()==best_record["mother_name"].lower() else 0,

        "dob":10 if application["dob"] and application["dob"]==best_record["dob"] else 0,

        "phone":5 if application["phone"] and application["phone"]==best_record["phone"] else 0,

        "district":5 if application["district"].lower()==best_record["district"].lower() else 0,

        "constituency":5 if application["constituency"].lower()==best_record["constituency"].lower() else 0

    }

    # -----------------------------
# Generate Reason
# -----------------------------

    if best_record is None:

        reason = "No matching family record was found in the historical database. The application requires manual verification by an officer."

    elif recommendation == "Verified":

        reason = (
            "Matching family record found in the historical database. "
            "The submitted information matches the historical record with a high confidence score."
        )

    elif recommendation == "Manual Review":

        reason = (
            "Matching family record found, but some submitted details differ from the historical record. "
            "Officer verification is recommended."
        )

    else:

        reason = (
            "Family record found, but significant differences exist between the submitted and historical information."
        )

    return (
            best_record,
            best_percentage,
            recommendation,
            best_score_details,
            reason
    )