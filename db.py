from config import PASSWORD
import psycopg2


# бд пользователей
class User:
    def __init__(self, database='postgres', user='postgres', password=None):
        self.datebase = database
        self.user = user
        self.password = password


    def create_db(self):
        with psycopg2.connect(database=self.datebase, user=self.user, password=self.password) as conn:
            with conn.cursor() as cur:
                cur.execute('''
                            CREATE TABLE IF NOT EXISTS user_vk (
                            id SERIAL PRIMARY KEY,
                            user_id TEXT NOT NULL UNIQUE,
                            first_name VARCHAR(100),
                            last_name VARCHAR(100),
                            age INTEGER NOT NULL,
                            sex VARCHAR(1) NOT NULL,
                            city VARCHAR(100) NOT NULL,
                            relation INTEGER NOT NULL,
                            photo_id TEXT,
                            photo_link TEXT,
                            profile_link TEXT NOT NULL,
                            offset_count INTEGER DEFAULT 0);
                            ''')
                conn.commit()


    def add_user(self, user):
        with psycopg2.connect(database=self.datebase, user=self.user, password=self.password) as conn:
            with conn.cursor() as cur:
                cur.execute('''
                            INSERT INTO user_vk (
                                user_id, 
                                first_name, 
                                last_name, 
                                age,
                                sex,
                                city,
                                relation,
                                photo_id,
                                photo_link,
                                profile_link
                            )
                            VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ''', (user['user_id'],
                                  user['first_name'],
                                  user['last_name'],
                                  user['bdate'],
                                  user['sex'],
                                  user['city'],
                                  user['relation'],
                                  user['photo_id'],
                                  user['photo_50'],
                                  user['profile_link']))
                conn.commit()


    def select_user(self, user_id):
        with psycopg2.connect(database=self.datebase, user=self.user, password=self.password) as conn:
            with conn.cursor() as cur:
                cur.execute('''
                            SELECT *
                            FROM user_vk
                            WHERE user_id=%s;
                            ''', (user_id,))
                user = cur.fetchall()
                conn.commit()
        return user


    def update_user(self, user_id, age=None, city=None, relation=None, offset=None):
        keys = [
            ('age', age),
            ('city', city),
            ('relation', relation),
            ('offset_count', offset)
        ]
        template = 'UPDATE user_vk SET'

        for i, key in enumerate(keys):
            if key[1]:
                template += f' {key[0]}={key[1]}'
        template += f' WHERE user_id=%s;'

        with psycopg2.connect(database=self.datebase, user=self.user, password=self.password) as conn:
            with conn.cursor() as cur:
                cur.execute(template, (user_id,))
                conn.commit()


# бд понравшиеся люди
class Contact:
    def __init__(self, database='postgres', user='postgres', password=None):
        self.datebase = database
        self.user = user
        self.password = password


    def create_db(self):
        with psycopg2.connect(database=self.datebase, user=self.user, password=self.password) as conn:
            with conn.cursor() as cur:
                cur.execute('''
                            CREATE TABLE IF NOT EXISTS contact (
                            id SERIAL PRIMARY KEY,
                            contact_id TEXT NOT NULL UNIQUE,
                            first_name VARCHAR(100),
                            last_name VARCHAR(100),
                            city VARCHAR(100) NOT NULL,
                            profile_link TEXT NOT NULL,
                            user_id TEXT NOT NULL REFERENCES user_vk(user_id) ON DELETE CASCADE);
                            ''')
                conn.commit()


    def add_contact(self, contact, user_id):
        with psycopg2.connect(database=self.datebase, user=self.user, password=self.password) as conn:
            with conn.cursor() as cur:
                cur.execute('''
                               INSERT INTO contact (
                                   contact_id, 
                                   first_name, 
                                   last_name, 
                                   city,
                                   profile_link,
                                   user_id
                               )
                               VALUES(%s, %s, %s, %s, %s, %s)
                               ''', (contact['user_id'],
                                     contact['first_name'],
                                     contact['last_name'],
                                     contact['city'],
                                     contact['link'],
                                     user_id))
                conn.commit()


    def delete_contact(self, contact_id):
        with psycopg2.connect(database=self.datebase, user=self.user, password=self.password) as conn:
            with conn.cursor() as cur:
                cur.execute('''
                            DELETE
                            FROM contact
                            WHERE contact_id=%s;
                            ''', (contact_id,))
            conn.commit()


    def select_contact(self, user_id):
        with psycopg2.connect(database=self.datebase, user=self.user, password=self.password) as conn:
            with conn.cursor() as cur:
                cur.execute('''
                            SELECT *
                            FROM contact
                            WHERE user_id=%s;
                            ''', (user_id,))
                contacts = cur.fetchall()
                conn.commit()
        return contacts


# бд просмотреные пользователи
class Viewed:
    def __init__(self, database='postgres', user='postgres', password=None):
        self.datebase = database
        self.user = user
        self.password = password


    def create_db(self):
        with psycopg2.connect(database=self.datebase, user=self.user, password=self.password) as conn:
            with conn.cursor() as cur:
                cur.execute('''
                            CREATE TABLE IF NOT EXISTS viewed (
                            id SERIAL PRIMARY KEY,
                            contact_id TEXT NOT NULL UNIQUE);
                            ''')
                conn.commit()


    def add_contact(self, contact_id):
        with psycopg2.connect(database=self.datebase, user=self.user, password=self.password) as conn:
            with conn.cursor() as cur:
                cur.execute('''
                               INSERT INTO viewed (contact_id)
                               VALUES(%s)
                               ''', (contact_id,))
                conn.commit()


    def select_contact(self, contact_id):
        with psycopg2.connect(database=self.datebase, user=self.user, password=self.password) as conn:
            with conn.cursor() as cur:
                cur.execute('''
                            SELECT *
                            FROM viewed
                            WHERE contact_id=%s;
                            ''', (str(contact_id),))
                contacts = cur.fetchall()
                conn.commit()
        return contacts

# бд фотографии понравшиеся человека
class Photos:
    def __init__(self, database='postgres', user='postgres', password=None):
        self.datebase = database
        self.user = user
        self.password = password


    def create_db(self):
        with psycopg2.connect(database=self.datebase, user=self.user, password=self.password) as conn:
            with conn.cursor() as cur:
                cur.execute('''
                            CREATE TABLE IF NOT EXISTS photos (
                            id SERIAL PRIMARY KEY,
                            photo_id TEXT NOT NULL UNIQUE,
                            count_likes INTEGER NOT NULL,
                            photo_link TEXT NOT NULL,
                            contact_id TEXT NOT NULL REFERENCES contact(contact_id) ON DELETE CASCADE);
                            ''')
                conn.commit()


    def add_photos(self, photos, contact_id):
        with psycopg2.connect(database=self.datebase, user=self.user, password=self.password) as conn:
            with conn.cursor() as cur:
                for photo in photos:
                    cur.execute('''
                                INSERT INTO photos (photo_id, count_likes, photo_link, contact_id)
                                VALUES(%s, %s, %s, %s)
                                ''', (photo[1], photo[0], photo[2], contact_id))
                    conn.commit()


    def select_photos(self, contact_id):
        with psycopg2.connect(database=self.datebase, user=self.user, password=self.password) as conn:
            with conn.cursor() as cur:
                cur.execute('''
                            SELECT photo_id
                            FROM photos
                            WHERE contact_id=%s;
                            ''', (contact_id,))
                photos = cur.fetchall()
                conn.commit()
        return photos



# создание нужных бд
user_db = User(database='vkinder', password=PASSWORD)
user_db.create_db()

contact_db = Contact(database='vkinder', password=PASSWORD)
contact_db.create_db()

viewed_db = Viewed(database='vkinder', password=PASSWORD)
viewed_db.create_db()

photos_db = Photos(database='vkinder', password=PASSWORD)
photos_db.create_db()


