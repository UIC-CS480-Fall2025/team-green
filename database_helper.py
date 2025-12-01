import psycopg2

conn = psycopg2.connect(database="postgres",
        host="localhost",
        user="postgres",
        password="postgres",
        port="5432")

# TODO: put all SQL implementation stuff with our database here
def authenticate_user(role, email, password):
    """
    Authenticate a user by role, email, and password.
    Returns the row if credentials are valid, None otherwise.
    """
    print(f"Authenticating {role} with email={email}...")
    cur = conn.cursor()

    # fetch a user with the defined email, password, and role
    users_select = """
        SELECT * FROM cs480_finalproject.users
        WHERE email = %s AND password = %s AND role = %s;
    """

    cur.execute(users_select, (email, password, role))
    result = cur.fetchone()
    print(result)
    cur.close()

    return result

def handle_signup(name, email, username, password):
    """
    Create a new EndUser by role, email, and password.
    Returns the full user row if successful, False otherwise.
    """
    print(f"Signing up a new EndUser with email={email}")
    try:
        with conn.cursor() as cur:
            # check email uniqueness
            cur.execute("SELECT 1 FROM cs480_finalproject.users WHERE email = %s;", (email,))
            if cur.fetchone() is not None:
                print("Error: Account with that email already exists.")
                return None

            # check username uniqueness
            cur.execute("SELECT 1 FROM cs480_finalproject.users WHERE username = %s;", (username,))
            if cur.fetchone() is not None:
                print("Error: Account with that username already exists.")
                return None

            # email and username are good, now actually insert it into the DB
            insert_query = """
                INSERT INTO cs480_finalproject.users (username, name, email, password, role)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING *;
            """
            cur.execute(insert_query, (username, name, email, password, 'EndUser')) # design choice, sign up can only add EndUser
            new_user_row = cur.fetchone()  # grab full row so main.py caller has all info

            conn.commit()
            return new_user_row
    except Exception as e:
        # this should really never happen
        print("Database error during signup:", e)
        conn.rollback()
        return None

# --- CREATE ---
def ADMIN_user_create(name, email, role, username, password):
    """
    Create a new user in the Users table.

    Only Admins can call this.
    """
    cur = conn.cursor()
    insert_query = """
        INSERT INTO cs480_finalproject.users (name, email, role, username, password)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING user_id;
    """
    cur.execute(insert_query, (name, email, role, username, password))
    user_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    print(f"User created with ID {user_id}")
    return user_id


# --- READ (Fetch all users) ---
def ADMIN_users_fetch():
    """
    Fetches all users from the Users table.
    """
    cur = conn.cursor()
    select_query = "SELECT * FROM cs480_finalproject.users;"
    cur.execute(select_query)
    users = cur.fetchall()
    cur.close()
    return users


# --- UPDATE ---
# we have all this optional fields because an Admin might not want to change everything, just some things
# DESIGN CHOICE: it is impossible for an admin to upgrade or degrade another user's permissions
# in other words, there is no way to change a user's role without deleting and remaking an account with that new role
def ADMIN_user_update(user_id, name=None, email=None, username=None, password=None):
    """
    Update fields for a given user_id.

    Only Admins are allowed to call this.
    """
    # print(f"User {user_id} updated successfully.")
    # all fields that we allow to be updated
    try:
        fields = {
            "username": username,
            "email": email,
            "name": name,
            "password": password,
        }
        print(fields)
        # which fields are actually getting updated
        updates = {key: val for key, val in fields.items() if val is not None and val != ""} # disallow None of an empty string
        print(updates)
        if not updates:
            return None

        set_clause = ", ".join(f"{key} = %s" for key in updates.keys())
        print(set_clause)
        query = f"""
            UPDATE cs480_finalproject.users
            SET {set_clause}
            WHERE user_id = %s
            RETURNING user_id;
        """
        print(f'query is {query}')
        params = list(updates.values()) + [user_id]
        print(f'params is {params}')


        with conn.cursor() as cur:
            cur.execute(query, params)
            updated_row = cur.fetchone()
            conn.commit()
        print(f"User {user_id} updated successfully.")
        return updated_row
    except Exception as e:
        # this could be reached if the user tries to update an email to one that already exists
        print("Database error during signup:", e)
        conn.rollback()
        return None

# --- DELETE ---
def ADMIN_user_delete(user_id):
    """
    Delete a user from the Users table.
    
    If User was an EndUser, delete all their QueryLogs and the logs of which documents were fetched too.
    This is handled by ON DELETE CASCADE, so we don't need additional implementation for it here.
    """
    with conn.cursor() as cur:
        # Check if the user exists and get their role
        cur.execute("SELECT 1 FROM cs480_finalproject.users WHERE user_id = %s;", (user_id,))
        result = cur.fetchone()

        if not result:
            return False  # No user with that ID

        # For EndUsers we need to get rid of all their QueryLogs, but this is handled by PostgreSQL because we have set up
        # ON DELETE CASCADE
        # if role == "EndUser":
        #     cur.execute("DELETE FROM QueryLog WHERE issuer_id = %s;", (user_id,))

        # Delete the user
        cur.execute("DELETE FROM cs480_finalproject.users WHERE user_id = %s RETURNING *;", (user_id,))
        deleted_row = cur.fetchone()
        print(f"User {user_id} delected successfully.")
        print(deleted_row)
        conn.commit()

        return deleted_row