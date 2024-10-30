import psycopg2

from app.settings import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER


def create_db(organization_db):
    try:
        connection = psycopg2.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
        )

        cursor = connection.cursor()

        cursor.execute("COMMIT;")

        cursor.execute(f"CREATE DATABASE {organization_db};")

        connection.commit()

    except Exception as error:
        print(f"Error: {error}")
        # TODO raise validation error

    finally:
        cursor.close()
        connection.close()
