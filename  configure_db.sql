CREATE DATABASE payments_system;

CREATE EXTENSION pgcrypto;

drop table if exists users;

create table if not exists users
(
    id              serial primary key,
    user_name       varchar not null unique,
    user_password   varchar not null,
    user_wallet_num char(16) not null,
    user_sum int not null
);

alter table users add constraint sum_constraint check ( user_sum > 0 ) ;