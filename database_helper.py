import pgvector
import psycopg2
import psycopg2.extras

# TODO: put all SQL implementation stuff with our database here
def authenticate_user(role, email, password):
    """
    Stub for authentication logic.
    Replace with actual backend check.
    Return True if credentials are valid, False otherwise.
    """
    print(f"Authenticating {role} with email={email} (stub).")
    assert(False)
    # TODO: implement actual authentication
    return False   # always fail for now, so user bounces back

def create_enduser(conn, username, name, email, password):
    query = """
        INSERT INTO Users (username, name, email, password, role)
        VALUES (%s, %s, %s, %s, 3)
        RETURNING id;
        """
    try:
        with conn.cursor() as cur:
            cur.execute(query,(username,name,email, password))
            new_id = cur.fetchone()[0]
            conn.commit()
            return new_id
    except Exception as e:
        print("Error:",e)
        return False

def fetch_users(conn):
    query = """
        SELCET id, name, email, username, role
        FROM Users;
        """
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute(query)
        rows = cur.fetchall()

    return [dict(row) for row in rows]

def update_user(conn, user_id, username=None, name=None, email=None, password=None, role=None)
    fields = {
        "username": username,
        "email": email,
        "name": name,
        "password": password,
        "role": role
    }

    updates = {key: val for key, val in fields.items() if val is not None}

    if not updates:
        return False

    set_clause = ", ".join(f"{key} = %s" for key in updates.keys())

    query = f"""
        UPDATE Users
        SET {set_clause}
        WHERE id = %s
        RETURNING id;
    """

    params = list(updates.values()) + [user_id]

    with conn.cursor() as cur:
        cur.execute(query, params)
        updated = cur.fetchone()
        conn.commit()

    return updated is not None

def delete_user(conn, user_id):
    with conn.cursor() as cur:
        # Check if the user exists and get their role
        cur.execute("SELECT role FROM Users WHERE id = %s;", (user_id,))
        result = cur.fetchone()

        if not result:
            return False  # No user with that ID

        role = result[0]

        # If role == 3, delete QueryLog entries
        if role == 3:
            cur.execute("DELETE FROM QueryLog WHERE user_id = %s;", (user_id,))

        # Delete the user
        cur.execute("DELETE FROM Users WHERE id = %s;", (user_id,))

        conn.commit()

        return True