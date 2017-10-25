CREATE TABLE `application_versions` (
  `version_id` int(11) NOT NULL AUTO_INCREMENT,
  `application_id` int(11) NOT NULL,
  `version_name` varchar(45) NOT NULL,
  `version_environment` int(11) NOT NULL,
  `api_version` varchar(8) NOT NULL DEFAULT '1.0',
  PRIMARY KEY (`version_id`),
  KEY `app_key_idx` (`application_id`),
  KEY `app_env_idx` (`version_environment`),
  CONSTRAINT `app_env` FOREIGN KEY (`version_environment`) REFERENCES `environments` (`environment_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `app_key` FOREIGN KEY (`application_id`) REFERENCES `applications` (`application_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;