INSERT INTO user (username, password)
VALUES
  ('test', 'pbkdf2:sha256:50000$TCI4GzcX$0de171a4f4dac32e3364c7ddc7c14f3e2fa61f2d17574483f7ffbb431b4acb2f'),
  ('other', 'pbkdf2:sha256:50000$kJPKsz6N$d2d4784f1b030a9761f5ccaeeaca413f27f2ecb76d6168407af962ddce849f79');

INSERT INTO tourneys (name, note)
VALUES
  ('test_tourney_1', 'first test tourney'),
  ('test_tourney_2', 'second test tourney'),
  ('test_tourney_3', 'third test tourney'),
  ('test_tourney_4', 'fourth test tourney'),
  ('test_tourney_5', 'fifth test tourney');

INSERT INTO players (name, note)
VALUES
  ('Andy', 'test player 1'),
  ('Betty', 'test player 2'),
  ('Cal', 'test player 3');

INSERT INTO bouts (tourneyId, leftWins, leftPlayerId, rightPlayerId, rightWins, draws, note)
VALUES
  (1, 3, 1, 2, 5, 2, 'tourney 1 set 1'),
  (1, 2, 2, 1, 3, 1, 'tourney 1 set 2'),
  (1, 4, 3, 1, 2, 0, 'tourney 1 set 3'),
  (2, 3, 2, 3, 5, 1, 'tourney 2 set 1');

