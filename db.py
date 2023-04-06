from config import PASSWORD
import psycopg2


# бд пользователей
class User:
    def __init__(self, database='postgres', user='postgres', password=None):
        self.datebase = database
        self.user = user
        self.password = password
        self.conn = psycopg2.connect(database=self.datebase, user=self.user, password=self.password)
        self.conn.autocommit = True


    def create_db(self):
        with self.conn:
            with self.conn.cursor() as cur:
                cur.execute('''
                            CREATE TABLE IF NOT EXISTS user_vk (
                            id SERIAL PRIMARY KEY,
                            user_id TEXT NOT NULL UNIQUE,
                            offset_count INTEGER DEFAULT 0);
                            ''')


    def add_user(self, user_id):
        with self.conn:
            with self.conn.cursor() as cur:
                cur.execute('''
                            INSERT INTO user_vk (user_id)
                            VALUES(%s)
                            ''', (user_id,))


    def select_user(self, user_id):
        with self.conn:
            with self.conn.cursor() as cur:
                cur.execute('''
                            SELECT *
                            FROM user_vk
                            WHERE user_id=%s;
                            ''', (user_id,))
                user = cur.fetchall()
        return user


    def update_user(self, user_id, offset=None):
        with self.conn:
            with self.conn.cursor() as cur:
                cur.execute('''
                            UPDATE user_vk
                            SET offset_count=%s
                            WHERE user_id=%s;
                            ''', (offset, user_id))


# бд понравшиеся люди
class Contact:
    def __init__(self, database='postgres', user='postgres', password=None):
        self.datebase = database
        self.user = user
        self.password = password
        self.conn = psycopg2.connect(database=self.datebase, user=self.user, password=self.password)
        self.conn.autocommit = True


    def create_db(self):
        with self.conn:
            with self.conn.cursor() as cur:
                cur.execute('''
                            CREATE TABLE IF NOT EXISTS contact (
                            id SERIAL PRIMARY KEY,
                            contact_id TEXT NOT NULL UNIQUE,
                            user_id TEXT NOT NULL REFERENCES user_vk(user_id) ON DELETE CASCADE);
                            ''')


    def add_contact(self, contact, user_id):
        with self.conn:
            with self.conn.cursor() as cur:
                cur.execute('''
                               INSERT INTO contact (contact_id, user_id)
                               VALUES(%s, %s)
                               ''', (str(contact['user_id']), str(user_id)))


    def delete_contact(self, contact_id):
        with self.conn:
            with self.conn.cursor() as cur:
                cur.execute('''
                            DELETE
                            FROM contact
                            WHERE contact_id=%s;
                            ''', (str(contact_id),))


    def select_contact(self, user_id):
        with self.conn:
            with self.conn.cursor() as cur:
                cur.execute('''
                            SELECT contact_id
                            FROM contact
                            WHERE user_id=%s;
                            ''', (user_id,))
                contacts = cur.fetchall()
        return contacts


# бд просмотреные пользователи
class Viewed:
    def __init__(self, database='postgres', user='postgres', password=None):
        self.datebase = database
        self.user = user
        self.password = password
        self.conn = psycopg2.connect(database=self.datebase, user=self.user, password=self.password)
        self.conn.autocommit = True


    def create_db(self):
        with self.conn:
            with self.conn.cursor() as cur:
                cur.execute('''
                            CREATE TABLE IF NOT EXISTS viewed (
                            id SERIAL PRIMARY KEY,
                            contact_id TEXT NOT NULL UNIQUE,
                            user_id TEXT NOT NULL REFERENCES user_vk(user_id) ON DELETE CASCADE);
                            ''')


    def add_contact(self, contact_id, user_id):
        with self.conn:
            with self.conn.cursor() as cur:
                cur.execute('''
                               INSERT INTO viewed (contact_id, user_id)
                               VALUES(%s, %s)
                               ''', (str(contact_id), str(user_id)))


    def select_contact(self, contact_id, user_id):
        with self.conn:
            with self.conn.cursor() as cur:
                cur.execute('''
                            SELECT *
                            FROM viewed
                            WHERE contact_id=%s AND user_id=%s;
                            ''', (str(contact_id), str(user_id)))
                contacts = cur.fetchall()
        return contacts


# # создание нужных бд
# user_db = User(database='vkinder', password=PASSWORD)
# user_db.create_db()
#
# contact_db = Contact(database='vkinder', password=PASSWORD)
# contact_db.create_db()
#
# viewed_db = Viewed(database='vkinder', password=PASSWORD)
# viewed_db.create_db()




