#!/bin/bash
# Script này chạy tự động khi PostgreSQL khởi động lần đầu tiên
# Tạo tất cả databases cần thiết cho các Microservices

set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    SELECT 'CREATE DATABASE "AuthService"'    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'AuthService')\gexec
    SELECT 'CREATE DATABASE "CompanyService"' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'CompanyService')\gexec
    SELECT 'CREATE DATABASE "JobService"'     WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'JobService')\gexec
    SELECT 'CREATE DATABASE "ProfileService"' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'ProfileService')\gexec
    SELECT 'CREATE DATABASE "ResumeService"'  WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'ResumeService')\gexec
    SELECT 'CREATE DATABASE "NotificationService"' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'NotificationService')\gexec
EOSQL

echo "✅ Tất cả databases đã được tạo thành công!"
