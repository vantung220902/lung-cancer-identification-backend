from flask_bcrypt import Bcrypt
from psycopg2._psycopg import connection

def create_user(username, password, full_name, conn: connection, bcrypt: Bcrypt):
    try:
        cur = conn.cursor()
        hashed_password = bcrypt.generate_password_hash(
            password).decode('utf-8')

        cur.execute(
            'INSERT INTO users (username, password, full_name) VALUES (%s, %s, %s)',
            (username, hashed_password, full_name)
        )
        conn.commit()
        cur.close()
        print("Created user successfully")
    except Exception as e:
        print("Failed to create user")
        print(e)


def find_user_by_id(id, conn: connection):
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE id = %s', (id,))
        user = cur.fetchone()
        cur.close()
        return {'username': user[0], 'full_name': user[2], "id": user[3]}
    except Exception as e:
        print("Cannot find the user")
        print(e)
        return None


def find_user(username, password, conn: connection, bcrypt: Bcrypt):
    try:
        cur = conn.cursor()

        # Correct tuple syntax for WHERE clause
        cur.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cur.fetchone()
        hashed_password = user[1]
        print("hashed_password", hashed_password)
        print("user", user)
        is_valid = bcrypt.check_password_hash(hashed_password, password)
        cur.close()
        if is_valid == True:
            print('Password correct')
            return {'username': user[0], 'full_name': user[2], "id": user[3]}
        else:
            print('Username or password is incorrectly')
            return None
    except Exception as e:
        print("Cannot find the user")
        print(e)
        return None
