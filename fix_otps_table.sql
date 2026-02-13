-- SQL commands to fix the otps table id column

-- First, check the current structure of the otps table
-- \d otps

-- Option 1: If the id column exists but is not auto-incrementing
-- Create a sequence and set it as default for the id column
CREATE SEQUENCE IF NOT EXISTS otps_id_seq;
ALTER TABLE otps ALTER COLUMN id SET DEFAULT nextval('otps_id_seq');
ALTER SEQUENCE otps_id_seq OWNED BY otps.id;

-- Update the sequence to start from the current max id + 1
SELECT setval('otps_id_seq', COALESCE((SELECT MAX(id) FROM otps), 0) + 1, false);

-- Make sure id is the primary key if it's not already
ALTER TABLE otps ADD PRIMARY KEY (id) IF NOT EXISTS;

-- Option 2: If you want to completely recreate the column as SERIAL
-- (Use this if Option 1 doesn't work)
-- ALTER TABLE otps DROP COLUMN id;
-- ALTER TABLE otps ADD COLUMN id SERIAL PRIMARY KEY;

-- Verify the changes
-- \d otps
