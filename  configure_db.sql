/* payments */
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

/* food */
CREATE DATABASE food_service;

CREATE EXTENSION pgcrypto;

drop table if exists goods, shops, users;

create table if not exists users
(
    id              serial primary key,
    user_name       varchar not null unique,
    user_password   varchar not null,
    user_mode       bool not null
);

create table if not exists shops
(
    id              serial primary key,
    shop_name       varchar not null unique,
    shop_zone       int not null
);

create table if not exists goods
(
    id              serial primary key,
    shop_name       int not null,
    good_name       varchar not null,
    good_price      int not null,
    CONSTRAINT shop_good
        FOREIGN KEY (shop_name)
            REFERENCES shops (id)
);

create table if not exists history
(
    id              serial primary key,
    user_name       int not null,
    shop_name       int not null,
    order_goods     varchar not null,
    sum             int not null,
    CONSTRAINT shop_history
        FOREIGN KEY (shop_name)
            REFERENCES shops (id),
    CONSTRAINT user_history
        FOREIGN KEY (user_name)
            REFERENCES users (id)
);