CREATE TABLE `scheme` (
  `key` int(11) NOT NULL DEFAULT '1',
  `data` json NOT NULL,
  PRIMARY KEY (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;