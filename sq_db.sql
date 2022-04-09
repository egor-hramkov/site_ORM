CREATE TABLE IF NOT EXISTS users (
id integer PRIMARY KEY AUTOINCREMENT,
name text NOT NULL,
surname text NOT NULL,
email text NOT NULL,
age integer NOT NULL,
worked text NOT NULL,
post text NOT NULL,
password text NOT NULL,
photo string128 NOT NULL,
role text NOT NULL
);