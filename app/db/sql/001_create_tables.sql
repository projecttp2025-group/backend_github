BEGIN;

CREATE SCHEMA IF NOT EXISTS main;
ALTER SCHEMA main OWNER TO admin_finance;

CREATE EXTENSION IF NOT EXISTS citext;
COMMIT;

BEGIN;
CREATE TABLE IF NOT EXISTS main.users (
  id             SERIAL PRIMARY KEY,
  email          CITEXT NOT NULL,
  password_hash  TEXT,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT email_len CHECK (length(email) <= 254),
  CONSTRAINT u_users_email UNIQUE (email)
);
COMMIT;

BEGIN;
CREATE TABLE IF NOT EXISTS main.accounts (
  id           SERIAL PRIMARY KEY,
  user_id      INT NOT NULL REFERENCES main.users(id) ON DELETE CASCADE,
  name         VARCHAR(120) NOT NULL,
  currency     CHAR(3)      NOT NULL DEFAULT 'BYN',
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMIT;

BEGIN;
CREATE TABLE IF NOT EXISTS main.categories (
  id          SERIAL PRIMARY KEY,
  user_id     INT NOT NULL REFERENCES main.users(id) ON DELETE CASCADE,
  name        VARCHAR(255) NOT NULL,                            
  type        VARCHAR(16)  NOT NULL,                            
  created_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),

  CONSTRAINT categories_type_chk
    CHECK (type IN ('expense', 'income')),

  CONSTRAINT u_categories_user_name_type
    UNIQUE (user_id, name, type)
);
COMMIT;

BEGIN;
CREATE TABLE IF NOT EXISTS main.transactions (
  id           SERIAL PRIMARY KEY,
  user_id      INT NOT NULL REFERENCES main.users(id)      ON DELETE CASCADE,
  account_id   INT NOT NULL REFERENCES main.accounts(id)   ON DELETE CASCADE,
  category_id  INT NOT NULL REFERENCES main.categories(id) ON DELETE CASCADE,
  amount       NUMERIC(15,2) NOT NULL,                     
  date         DATE NOT NULL,                               
  description  TEXT,                                        
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_tx_user_date
  ON main.transactions (user_id, date);

CREATE INDEX IF NOT EXISTS idx_tx_account_date
  ON main.transactions (account_id, date);

COMMIT;

BEGIN;
CREATE TABLE IF NOT EXISTS main.receipts (
  id               SERIAL PRIMARY KEY,
  user_id          INT NOT NULL REFERENCES main.users(id)        ON DELETE CASCADE, 
  transaction_id   INT NULL     REFERENCES main.transactions(id) ON DELETE SET NULL, 
  file_path        VARCHAR(1000) NOT NULL,                       
  merchant_name    VARCHAR(255),                                 
  total_amount     NUMERIC(15,2),                               
  transaction_date DATE,                                        
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_receipts_user
  ON main.receipts (user_id);

CREATE INDEX IF NOT EXISTS idx_receipts_tx
  ON main.receipts (transaction_id);

COMMIT;