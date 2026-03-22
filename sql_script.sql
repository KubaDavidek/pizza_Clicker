CREATE TABLE public.leaderboard (
  id integer NOT NULL DEFAULT nextval('leaderboard_id_seq'::regclass),
  user_id integer NOT NULL UNIQUE,
  name character varying NOT NULL,
  pps double precision NOT NULL,
  total double precision NOT NULL,
  CONSTRAINT leaderboard_pkey PRIMARY KEY (id),
  CONSTRAINT leaderboard_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id)
);
CREATE TABLE public.saves (
  id integer NOT NULL DEFAULT nextval('saves_id_seq'::regclass),
  user_id integer NOT NULL UNIQUE,
  pizzeria_name character varying NOT NULL,
  money double precision NOT NULL,
  total_earned double precision NOT NULL,
  click_value double precision NOT NULL,
  upgrades text NOT NULL,
  last_save bigint NOT NULL,
  extra_data text DEFAULT '{}'::text,
  CONSTRAINT saves_pkey PRIMARY KEY (id),
  CONSTRAINT saves_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id)
);
CREATE TABLE public.users (
  id integer NOT NULL DEFAULT nextval('users_id_seq'::regclass),
  nickname character varying NOT NULL UNIQUE,
  password_hash character varying NOT NULL,
  created_at timestamp without time zone DEFAULT now(),
  CONSTRAINT users_pkey PRIMARY KEY (id)
);