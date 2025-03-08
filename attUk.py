import cx_Oracle
import os
import datetime

# Read credentials from environment variables
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_DSN = os.getenv("DB_DSN")

# Ensure the environment variables are set
if not DB_USER or not DB_PASSWORD or not DB_DSN:
    raise ValueError("Database credentials are not set in the environment variables.")

# Get the current date
today = datetime.datetime.now()

# Format the month and day in two digits
month = today.strftime("%m")  # Current month as a two-digit string
day = today.strftime("%d")    # Current day as a two-digit string

# Construct the filename
INPUT_FILE = f"REC{month}{day}.txt"

# Print the filename to verify
print("Input file name:", INPUT_FILE)

# Maximum allowed EID length from database schema
MAX_EID_LENGTH = 10

# Function to process the text file
def process_attendance_file(file_path):
    with open(file_path, "r") as file:
        lines = file.readlines()

    attendance_data = []
    for line in lines:
        parts = line.strip().split(":")
        if len(parts) == 5:
            machine_id, eid, card_date, card_time, blank_c = parts
            # Truncate EID if it exceeds the maximum length
            if len(eid) > MAX_EID_LENGTH:
                print(f"Truncating oversized EID: {eid}")
                eid = eid[:MAX_EID_LENGTH]

            card_datetime = datetime.datetime.strptime(card_date + card_time, "%y%m%d%H%M%S")
            attendance_data.append((machine_id, eid, card_datetime))
    return attendance_data

# Function to push data into Oracle database
def push_to_database(attendance_data, file_name):
    try:
        # Connect to the database
        connection = cx_Oracle.connect(DB_USER, DB_PASSWORD, DB_DSN)
        cursor = connection.cursor()

        # Get sequence for TXN_ID
        cursor.execute("SELECT HRAI_ATENDANCE.NEXTVAL FROM dual")
        txn_id = cursor.fetchone()[0]

        txn_src = os.path.basename(file_name).upper()

        # Insert into HRAI_ATTENDANCE
        cursor.execute(
            """
            INSERT INTO HRAI_ATTENDANCE (TXN_ID, TXN_DATE, TXN_SRC, TXN_IN4, TXN_STATUS, TXN_LEVEL)
            VALUES (:1, SYSDATE, :2, 'Started Updating Database', 'true', '1')
            """,
            (txn_id, txn_src)
        )

        # Insert into HR_ATTENDANCE
        for i, (machine_id, eid, card_datetime) in enumerate(attendance_data):
            try:
                # Get sequence for AID
                cursor.execute("SELECT 'AL' || lpad(SEQ_AID.NEXTVAL, 8, '0') FROM dual")
                aid = cursor.fetchone()[0]

                # Insert into HR_ATTENDANCE
                cursor.execute(
                    """
                    INSERT INTO HR_ATTENDANCE (AID, EID, REG_DATE, CARD_TIME, STATUS, MACHINE_ID, TXN_BRK)
                    VALUES (:1, :2, SYSDATE, :3, :4, :5, :6)
                    """,
                    (aid, eid, card_datetime, '0', machine_id, txn_id)
                )
            except cx_Oracle.DatabaseError as e:
                # Handle specific database errors
                error_code = e.args[0].code
                if error_code == 12899:  # ORA-12899: Value too large for column
                    print(f"Skipping record with oversized EID: {eid}")
                elif error_code == 1:  # ORA-00001: Unique constraint violation
                    print(f"Skipping duplicate entry for EID {eid}, Machine ID {machine_id}, Card Time {card_datetime}.")
                else:
                    raise  # Re-raise other exceptions

        # Commit the transactions
        connection.commit()
        print("Data successfully inserted into the database.")

    except cx_Oracle.DatabaseError as e:
        print(f"Database error: {e}")
        if connection:
            connection.rollback()
    finally:
        # Close the connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()

if __name__ == "__main__":
    # Step 1: Process the file
    try:
        data = process_attendance_file(INPUT_FILE)

        # Step 2: Push to Oracle database
        push_to_database(data, INPUT_FILE)
    except FileNotFoundError:
        print(f"Error: Input file {INPUT_FILE} not found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
