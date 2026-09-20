FROM postgres:alpine
COPY init.sql /docker-entrypoint-initdb.d/
COPY pg_hba.conf /usr/local/share/postgresql/pg_hba.conf.sample
