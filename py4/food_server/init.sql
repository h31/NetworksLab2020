DROP TABLE IF EXISTS USERS;
DROP TABLE IF EXISTS MARKET_TABLE;
DROP TABLE IF EXISTS HISTORY;

CREATE TABLE USERS
(
    user_name       varchar2(32) primary key,
    user_password   varchar2(64) not null,
    user_role       varchar2(32) not null
);

CREATE TABLE HISTORY
(
   buyer        varchar2(32) not null,
   items        text not null,
   price        real not null,
   seller       varchar2(32) not null
);
CREATE TABLE MARKET_TABLE
(
    store       varchar2(128),
    area_store  int not null,
    items       text,
    owner       varchar2(32) not null
);
