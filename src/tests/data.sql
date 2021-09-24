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
