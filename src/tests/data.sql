INSERT INTO user (id, username, email, password_hash, admin, confirmed, remember_me)
VALUES
  (1, 'test', 'foo@bar.baz', 'pbkdf2:sha256:50000$TCI4GzcX$0de171a4f4dac32e3364c7ddc7c14f3e2fa61f2d17574483f7ffbb431b4acb2f', False, True, True),
  (2, 'other', 'blrfl@bar.baz', 'pbkdf2:sha256:50000$kJPKsz6N$d2d4784f1b030a9761f5ccaeeaca413f27f2ecb76d6168407af962ddce849f79', False, True, False),
  (3, 'admin', 'admin@foo.bar', 'pbkdf2:sha256:260000$d5HvAo7r21kTmXSQ$2c0fefa87879115fbb1721838ab26b270f120291c49c113106372bc4e6f603f9', True, True, False);

INSERT INTO "group" (id, name)
VALUES
  (1, 'groupone'),
  (2, 'grouptwo'),
  (3, 'test'),
  (4, 'other'),
  (5, 'everyone');

INSERT INTO user_group_pair (id, user_id, group_id)
VALUES
  (1, 1, 3),
  (2, 1, 5),
  (3, 2, 4),
  (4, 2, 5);

INSERT INTO tourneys (name, note, owner, 'group',
owner_read, owner_write, owner_delete,
group_read, group_write, group_delete,
other_read, other_write, other_delete
)
VALUES
  ('test_tourney_1', 'first test tourney', 1, 3,
  True, True, True, True, False, False, False, False, False),
  ('test_tourney_2', 'second test tourney', 1, 5,
  True, True, True, True, False, False, False, False, False),
  ('test_tourney_3', 'third test tourney', 2, 4,
  True, True, True, True, False, False, False, False, False),
  ('test_tourney_4', 'fourth test tourney', 2, 5,
  True, True, True, True, False, False, False, False, False),
  ('test_tourney_5', 'fifth test tourney', 2, 4,
  True, True, True, True, False, False, False, False, False),
  ('test_tourney_6', 'sixth test tourney', 2, 4,
  True, True, True, True, False, False, True, True, True),
  ('test_tourney_7', 'seventh test tourney', 2, 5,
  True, True, True, True, True, True, False, False, False);

INSERT INTO players (name, note)
VALUES
  ('Andy', 'test player 1'),
  ('Betty', 'test player 2'),
  ('Cal', 'test player 3'),
  ('Donna', 'test player 4'),
  ('Eli', 'test player 5');

INSERT INTO bouts (tourneyId, leftWins, leftPlayerId, rightPlayerId, rightWins, draws, note)
VALUES
  (1, 3, 1, 2, 5, 2, 'tourney 1 set 1'),
  (1, 2, 2, 1, 3, 1, 'tourney 1 set 2'),
  (1, 4, 3, 1, 2, 0, 'tourney 1 set 3'),
  (2, 3, 2, 3, 5, 1, 'tourney 2 set 1');

-- The following block construct player_tourney_pair entries appropriate for these bouts --
CREATE TEMPORARY TABLE t1 AS SELECT tourneyId AS tourney_id, leftPlayerId AS player_id FROM bouts;
CREATE TEMPORARY TABLE t2 AS SELECT tourneyId AS tourney_id, rightPlayerId AS player_id FROM bouts;
CREATE TEMPORARY TABLE t3 AS SELECT * FROM t1 UNION SELECT * FROM t2;
INSERT INTO 'player_tourney_pair' (tourney_id, player_id) SELECT DISTINCT tourney_id, player_id FROM t3;
DROP TABLE t3;
DROP TABLE t2;
DROP TABLE t1;

