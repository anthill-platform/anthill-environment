CREATE TABLE `applications` (
  `application_id` int(11) NOT NULL AUTO_INCREMENT,
  `application_name` varchar(45) NOT NULL,
  `application_title` varchar(128) NOT NULL,
  `min_api` varchar(8) NOT NULL DEFAULT '0.1',
  PRIMARY KEY (`application_id`),
  UNIQUE KEY `application_name_UNIQUE` (`application_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;