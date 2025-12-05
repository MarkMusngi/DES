-- init-dbs.sql
-- This script runs automatically on the first startup of the postgres container
-- to create the databases required by the various microservices.

-- Connect to the 'postgres' default database to execute CREATE DATABASE commands.
\c postgres

-- Create the database for the Course, Enrollment, and related services
-- We use conditional logic (SELECT ... \gexec) to ensure this script is idempotent 
-- and doesn't fail if the database somehow already exists.
SELECT 'CREATE DATABASE student_portal_courses'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'student_portal_courses')\gexec

-- Create the database for the Grades, and Faculty Grades services
SELECT 'CREATE DATABASE student_portal_grades'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'student_portal_grades')\gexec

-- Note: The 'student_portal_auth' database is created automatically 
-- by the POSTGRES_DB environment variable in the docker-compose.yml.