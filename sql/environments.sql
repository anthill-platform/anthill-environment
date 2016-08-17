CREATE TABLE `environments` (
  `environment_id` int(11) NOT NULL AUTO_INCREMENT,
  `environment_name` varchar(45) NOT NULL,
  `environment_discovery` varchar(45) NOT NULL,
  `environment_data` json NOT NULL,
  PRIMARY KEY (`environment_id`),
  UNIQUE KEY `environment_name_UNIQUE` (`environment_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;