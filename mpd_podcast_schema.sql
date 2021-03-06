-- Liste des Flux RSS
create table flux (
       id    integer primary key autoincrement not null,
       url   text,
       titre text,
       --Resumer facultatif
       last_update date
);

create table item (
       id    integer primary key autoincrement not null,
       titre text,
       --resummer facultatif
       url text,
       status integer ,
       item_date date,
       -- Definition des status dans l'application
       flux integer not null references flux(id),
       nom text
);

create table setup (
       user primary key,
       podcast_path text,
       mpd_host text,
       mpd_port integer	,
       password text
);
