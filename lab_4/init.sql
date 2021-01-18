DROP TABLE IF EXISTS USERS;
DROP TABLE IF EXISTS MAIL_BOX;

CREATE TABLE USERS
(
    user_name        varchar2(32) primary key,
    user_password   varchar2(64) not null
);

CREATE TABLE MAIL_BOX
(
   sender_id        varchar2(32) not null,
   receiver_id      varchar2(32) not null,
   header_mail      text not null,
   content          text not null,
   unread           boolean
);