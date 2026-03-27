-- PostgreSQL Setup Script for JobMate
-- Run this in psql as superuser: psql -U postgres -f setup_postgresql.sql

-- Create database
CREATE DATABASE jobmate;

-- Create user
CREATE USER jobmate_user WITH PASSWORD 'jobmate_pass';

-- Grant privileges
ALTER ROLE jobmate_user SET client_encoding TO 'utf8';
ALTER ROLE jobmate_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE jobmate_user SET timezone TO 'Asia/Kolkata';
GRANT ALL PRIVILEGES ON DATABASE jobmate TO jobmate_user;

-- Connect to the new database and grant schema privileges
\c jobmate
GRANT ALL ON SCHEMA public TO jobmate_user;

\echo 'PostgreSQL setup complete!'
\echo 'Now run: python manage.py migrate'
