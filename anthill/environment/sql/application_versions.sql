CREATE TABLE `application_versions` (
  `version_id` int(11) NOT NULL AUTO_INCREMENT,
  `application_id` int(11) NOT NULL,
  `version_name` varchar(45) NOT NULL,
  `version_environment` int(11) NOT NULL,
  PRIMARY KEY (`version_id`),
  KEY `app_key_idx` (`application_id`),
  KEY `app_env_idx` (`version_environment`),
  CONSTRAINT `application_versions_ibfk_1` FOREIGN KEY (`application_id`) REFERENCES `applications` (`application_id`) ON DELETE CASCADE,
  CONSTRAINT `application_versions_ibfk_2` FOREIGN KEY (`version_environment`) REFERENCES `environments` (`environment_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;