-- MySQL dump 10.13  Distrib 8.0.44, for Win64 (x86_64)
--
-- Host: localhost    Database: metasejong
-- ------------------------------------------------------
-- Server version	8.0.44

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `buildings`
--

DROP TABLE IF EXISTS `buildings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `buildings` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(120) NOT NULL,
  `role` enum('restaurant','dropoff') NOT NULL DEFAULT 'dropoff',
  `note` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_building_name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `buildings`
--

LOCK TABLES `buildings` WRITE;
/*!40000 ALTER TABLE `buildings` DISABLE KEYS */;
INSERT INTO `buildings` VALUES (1,'Chungmu','restaurant','충무관/pickup'),(2,'Dasan','restaurant','다산관/pickup'),(3,'Yeongsil','dropoff','영실관/dropout'),(4,'ParkingGate','dropoff','파킹게이트/dropout'),(5,'SejongElementaryHall','dropoff','세종초등학교강당/dropout');
/*!40000 ALTER TABLE `buildings` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `edges`
--

DROP TABLE IF EXISTS `edges`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `edges` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `src_node_id` int unsigned NOT NULL,
  `dst_node_id` int unsigned NOT NULL,
  `length` double NOT NULL,
  `one_way` tinyint(1) NOT NULL DEFAULT '0',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_edges_directed` (`src_node_id`,`dst_node_id`),
  KEY `idx_edges_src` (`src_node_id`),
  KEY `idx_edges_dst` (`dst_node_id`),
  CONSTRAINT `fk_edges_dst` FOREIGN KEY (`dst_node_id`) REFERENCES `nodes` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `fk_edges_src` FOREIGN KEY (`src_node_id`) REFERENCES `nodes` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `edges`
--

LOCK TABLES `edges` WRITE;
/*!40000 ALTER TABLE `edges` DISABLE KEYS */;
INSERT INTO `edges` VALUES (1,4,3,81.789,0,'2025-11-03 09:16:22'),(2,3,4,81.789,0,'2025-11-03 09:16:22'),(4,3,2,26.854,0,'2025-11-03 09:16:22'),(5,2,3,26.854,0,'2025-11-03 09:16:22'),(7,3,5,57.969,0,'2025-11-03 09:16:22'),(8,5,3,57.969,0,'2025-11-03 09:16:22'),(10,5,6,38.242,0,'2025-11-03 09:16:22'),(11,6,5,38.242,0,'2025-11-03 09:16:22'),(13,5,4,92.6041325265779,0,'2025-11-06 06:03:20');
/*!40000 ALTER TABLE `edges` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Temporary view structure for view `edges_u`
--

DROP TABLE IF EXISTS `edges_u`;
/*!50001 DROP VIEW IF EXISTS `edges_u`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `edges_u` AS SELECT 
 1 AS `a`,
 1 AS `b`,
 1 AS `w`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `menu_full`
--

DROP TABLE IF EXISTS `menu_full`;
/*!50001 DROP VIEW IF EXISTS `menu_full`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `menu_full` AS SELECT 
 1 AS `menu_id`,
 1 AS `menu_name`,
 1 AS `menu_price`,
 1 AS `restaurant_id`,
 1 AS `restaurant_name`,
 1 AS `restaurant_category`,
 1 AS `building_id`,
 1 AS `building_name`*/;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `menus`
--

DROP TABLE IF EXISTS `menus`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `menus` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `restaurant_id` int unsigned NOT NULL,
  `name` varchar(120) NOT NULL,
  `price` int unsigned NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_menu_unique` (`restaurant_id`,`name`),
  UNIQUE KEY `uk_menus_restaurant_name` (`restaurant_id`,`name`),
  KEY `idx_menu_rest` (`restaurant_id`),
  CONSTRAINT `fk_menu_rest` FOREIGN KEY (`restaurant_id`) REFERENCES `restaurants` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `fk_menus_restaurants` FOREIGN KEY (`restaurant_id`) REFERENCES `restaurants` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=229 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `menus`
--

LOCK TABLES `menus` WRITE;
/*!40000 ALTER TABLE `menus` DISABLE KEYS */;
INSERT INTO `menus` VALUES (1,3,'반미 클래식',5800,'2025-10-31 07:39:46'),(2,3,'반미 치킨',5800,'2025-10-31 07:39:46'),(3,3,'반미 에그치즈',4500,'2025-10-31 07:39:46'),(4,3,'반미 스파이시 포크',6000,'2025-10-31 07:39:46'),(5,3,'반미 토푸(비건)',5400,'2025-10-31 07:39:46'),(6,3,'미니 쌀국수',5200,'2025-10-31 07:39:46'),(7,3,'분짜 라이스볼',6500,'2025-10-31 07:39:46'),(8,3,'스프링롤 2P',3200,'2025-10-31 07:39:46'),(9,3,'짜조 3P',3500,'2025-10-31 07:39:46'),(10,4,'연어초밥 10P',7500,'2025-10-31 07:39:50'),(11,4,'모듬초밥 10P',8000,'2025-10-31 07:39:50'),(12,4,'참치마요 롤',6800,'2025-10-31 07:39:50'),(13,4,'새우초밥 8P',7000,'2025-10-31 07:39:50'),(14,4,'연어사시미',9000,'2025-10-31 07:39:50'),(15,4,'우동세트',8200,'2025-10-31 07:39:50'),(16,4,'미니유부초밥세트',4200,'2025-10-31 07:39:50'),(17,4,'연어덮밥',8500,'2025-10-31 07:39:50'),(18,4,'장어덮밥',9000,'2025-10-31 07:39:50'),(19,4,'사케동',8800,'2025-10-31 07:39:50'),(20,4,'연어샐러드',6500,'2025-10-31 07:39:50'),(21,1,'세종대왕돈까스',6000,'2025-10-31 08:18:44'),(22,1,'치킨까스',4500,'2025-10-31 08:18:44'),(23,1,'생선 까스',4000,'2025-10-31 08:18:44'),(24,1,'고구마돈까스',5000,'2025-10-31 08:18:44'),(25,1,'등심돈까스',5000,'2025-10-31 08:18:44'),(26,1,'가츠동',4300,'2025-10-31 08:18:44'),(27,1,'치즈 함박동',4700,'2025-10-31 08:18:44'),(28,1,'에비동',5000,'2025-10-31 08:18:44'),(29,1,'새우튀김 알밥',4500,'2025-10-31 08:18:44'),(30,1,'치킨 가라아게동',5000,'2025-10-31 08:18:44'),(31,1,'우삼겹 된장찌개',5000,'2025-10-31 08:18:44'),(32,1,'돼지고기 김치찌개',5000,'2025-10-31 08:18:44'),(33,1,'돈까스 김치찌개',5300,'2025-10-31 08:18:44'),(34,1,'참치 김치찌개',5000,'2025-10-31 08:18:44'),(35,1,'존슨치즈부대찌개',5500,'2025-10-31 08:18:44'),(36,1,'냉모밀',4000,'2025-10-31 08:18:44'),(37,1,'에비냉모밀',4500,'2025-10-31 08:18:44'),(38,1,'김치우동',2800,'2025-10-31 08:18:44'),(39,1,'어묵꼬치우동',3500,'2025-10-31 08:18:44'),(40,1,'왕새우튀김우동',5200,'2025-10-31 08:18:44'),(41,1,'왕새우튀김 냉모밀',5200,'2025-10-31 08:18:44'),(42,1,'새우튀김우동',4500,'2025-10-31 08:18:44'),(43,1,'야채핫바 우동',3700,'2025-10-31 08:18:44'),(44,1,'들기름소바',4300,'2025-10-31 08:18:44'),(45,1,'돈까스 우동정식',5000,'2025-10-31 08:18:44'),(46,1,'돈까스 냉모밀정식',5500,'2025-10-31 08:18:44'),(47,1,'들기름소바+떡갈비',6300,'2025-10-31 08:18:44'),(48,1,'돈까스 쟁반국수',5000,'2025-10-31 08:18:44'),(49,1,'돈까스 비빔모밀',4800,'2025-10-31 08:18:44'),(50,1,'치킨치즈까스 카레덮밥',5000,'2025-10-31 08:18:44'),(51,1,'치킨텐더 카레덮밥',4800,'2025-10-31 08:18:44'),(52,1,'새우튀김 카레덮밥',4800,'2025-10-31 08:18:44'),(53,1,'돈까스 카레덮밥',4800,'2025-10-31 08:18:44'),(54,1,'핫바 카레덮밥',4300,'2025-10-31 08:18:44'),(55,1,'함박 카레덮밥',4500,'2025-10-31 08:18:44'),(84,2,'오므라이스',3500,'2025-10-31 08:55:39'),(85,2,'닭강정 오므라이스',5000,'2025-10-31 08:55:39'),(86,2,'돈까스 오므라이스',5000,'2025-10-31 08:55:39'),(87,2,'함박오므라이스',5000,'2025-10-31 08:55:39'),(88,2,'롱소세지 오므라이스',5500,'2025-10-31 08:55:39'),(89,2,'피카츄 오므라이스',4500,'2025-10-31 08:55:39'),(90,2,'소떡소떡 오므라이스',5800,'2025-10-31 08:55:39'),(91,2,'해쉬브라운 오므라이스',5500,'2025-10-31 08:55:39'),(92,2,'치킨치즈까스 오므라이스',5500,'2025-10-31 08:55:39'),(93,2,'떡갈비 오므라이스',5800,'2025-10-31 08:55:39'),(94,2,'갈릭스팸볶음밥',5000,'2025-10-31 08:55:39'),(95,2,'스팸김치볶음밥',5000,'2025-10-31 08:55:39'),(96,2,'삼겹살김치볶음밥',5000,'2025-10-31 08:55:39'),(97,2,'소금구이덮밥',4500,'2025-10-31 08:55:39'),(98,2,'제육덮밥',5000,'2025-10-31 08:55:39'),(99,2,'간장돼지불고기덮밥',5000,'2025-10-31 08:55:39'),(100,2,'쫑쫑덮밥',5000,'2025-10-31 08:55:39'),(101,2,'마그마 볶네치킨덮밥',5000,'2025-10-31 08:55:39'),(102,2,'불닭덮밥',5000,'2025-10-31 08:55:39'),(103,2,'카오팟삼겹',5500,'2025-10-31 08:55:39'),(104,2,'그제덮밥',5000,'2025-10-31 08:55:39'),(105,2,'소금구이 비빔밥',5500,'2025-10-31 08:55:39'),(106,2,'제육 비빔밥',5800,'2025-10-31 08:55:39'),(107,2,'삼겹살강된장 비빔밥',5500,'2025-10-31 08:55:39'),(108,2,'삼겹살볶음고추장비빔밥',5500,'2025-10-31 08:55:39'),(109,2,'간장돼불마요 비빔밥',6000,'2025-10-31 08:55:39'),(110,2,'불닭비빔밥',5500,'2025-10-31 08:55:39'),(111,2,'수육정식',7500,'2025-10-31 08:55:39'),(112,2,'대패삼겹 비빔밥',5500,'2025-10-31 08:55:39'),(113,2,'돈까스 카레덮밥',4800,'2025-10-31 08:55:39'),(114,2,'왕새우튀김 카레덮밥',5800,'2025-10-31 08:55:39'),(115,2,'함박 카레덮밥',4500,'2025-10-31 08:55:39'),(116,2,'치킨텐더 카레덮밥',4800,'2025-10-31 08:55:39'),(117,2,'롱소세지 카레덮밥',5000,'2025-10-31 08:55:39'),(118,2,'해쉬브라운 카레덮밥',5000,'2025-10-31 08:55:39'),(119,2,'닭강정',3800,'2025-10-31 08:55:39'),(120,2,'소떡소떡',3000,'2025-10-31 08:55:39'),(121,2,'회오리감자',3300,'2025-10-31 08:55:39'),(122,2,'진라면(매운맛)',2500,'2025-10-31 08:55:39'),(123,2,'신라면',3000,'2025-10-31 08:55:39'),(124,2,'틈새라면',3300,'2025-10-31 08:55:39'),(125,2,'진라면(순한맛)',2500,'2025-10-31 08:55:39'),(126,2,'참치마요 비빔밥',3800,'2025-10-31 08:55:39'),(127,2,'참치 마그마요 비빔밥',4000,'2025-10-31 08:55:39'),(128,2,'국물라볶이',4500,'2025-10-31 08:55:39'),(129,2,'로제떡볶이',5500,'2025-10-31 08:55:39'),(130,2,'육회비빔밥',5500,'2025-10-31 08:55:39'),(131,2,'돈육 순두부찌개',4800,'2025-10-31 08:55:39'),(132,2,'스팸치즈 순두부찌개',5500,'2025-10-31 08:55:39'),(133,2,'떡만두국',4200,'2025-10-31 08:55:39'),(134,2,'물냉면',4000,'2025-10-31 08:55:39'),(135,2,'비빔냉면',4500,'2025-10-31 08:55:39'),(136,2,'잔치국수',3500,'2025-10-31 08:55:39'),(137,2,'떡갈비+물냉면',6000,'2025-10-31 08:55:39'),(138,2,'떡갈비+비빔냉면',6500,'2025-10-31 08:55:39'),(139,2,'칼만두',4300,'2025-10-31 08:55:39'),(140,2,'김치말이국수',4000,'2025-10-31 08:55:39'),(147,5,'제육볶음 정식',6200,'2025-11-03 10:22:26'),(148,5,'된장찌개 정식',5800,'2025-11-03 10:22:26'),(149,5,'김치찌개 정식',5800,'2025-11-03 10:22:26'),(150,5,'순두부찌개 정식',5800,'2025-11-03 10:22:26'),(151,5,'부대찌개 정식',6800,'2025-11-03 10:22:26'),(152,5,'고등어구이 정식',7000,'2025-11-03 10:22:26'),(153,5,'간장불고기 정식',6500,'2025-11-03 10:22:26'),(154,5,'닭갈비 정식',6800,'2025-11-03 10:22:26'),(155,5,'낙지볶음 정식',7800,'2025-11-03 10:22:26'),(156,5,'비빔밥',5500,'2025-11-03 10:22:26'),(157,5,'돌솥비빔밥',6500,'2025-11-03 10:22:26'),(158,5,'돼지목살구이 정식',7500,'2025-11-03 10:22:26'),(159,5,'치킨가라아게 정식',6500,'2025-11-03 10:22:26'),(160,5,'코다리조림 정식',7500,'2025-11-03 10:22:26'),(161,5,'제철나물 백반',5200,'2025-11-03 10:22:26'),(162,5,'도시락(제육)',5200,'2025-11-03 10:22:26'),(163,5,'도시락(불고기)',5200,'2025-11-03 10:22:26'),(164,5,'떡갈비 정식',7200,'2025-11-03 10:22:26'),(165,5,'삼치구이 정식',7300,'2025-11-03 10:22:26'),(166,5,'소불고기 전골',8900,'2025-11-03 10:22:26'),(167,5,'갈치구이 정식',7900,'2025-11-03 10:22:26'),(168,5,'계란말이 정식',5200,'2025-11-03 10:22:26'),(169,5,'김치제육 덮밥',5900,'2025-11-03 10:22:26'),(170,5,'청국장 정식',6800,'2025-11-03 10:22:26'),(171,5,'냄비우동 정식',5700,'2025-11-03 10:22:26'),(178,6,'돈코츠 라멘',7800,'2025-11-03 10:22:30'),(179,6,'쇼유 라멘',7200,'2025-11-03 10:22:30'),(180,6,'미소 라멘',7400,'2025-11-03 10:22:30'),(181,6,'시오 라멘',7200,'2025-11-03 10:22:30'),(182,6,'탄탄멘',8200,'2025-11-03 10:22:30'),(183,6,'카라미소 라멘',8200,'2025-11-03 10:22:30'),(184,6,'마제소바',8000,'2025-11-03 10:22:30'),(185,6,'츠케멘',8500,'2025-11-03 10:22:30'),(186,6,'치킨 가라아게 덮밥',6200,'2025-11-03 10:22:30'),(187,6,'차슈 덮밥',6500,'2025-11-03 10:22:30'),(188,6,'규동',6500,'2025-11-03 10:22:30'),(189,6,'교자(6P)',3800,'2025-11-03 10:22:30'),(190,6,'교자(10P)',6000,'2025-11-03 10:22:30'),(191,6,'차슈 추가',2000,'2025-11-03 10:22:30'),(192,6,'면 추가',1500,'2025-11-03 10:22:30'),(193,6,'반숙계란',1200,'2025-11-03 10:22:30'),(194,6,'김치 라멘',7600,'2025-11-03 10:22:30'),(195,6,'해물 라멘',8800,'2025-11-03 10:22:30'),(196,6,'매운 돈코츠',8400,'2025-11-03 10:22:30'),(197,6,'마늘 돈코츠',8200,'2025-11-03 10:22:30'),(198,6,'카레 라멘',7900,'2025-11-03 10:22:30'),(199,6,'냉라멘(여름한정)',8200,'2025-11-03 10:22:30'),(200,6,'라멘 + 교자 세트',9800,'2025-11-03 10:22:30'),(201,6,'라멘 + 차슈덮밥 세트',10500,'2025-11-03 10:22:30'),(202,6,'탄탄멘 + 교자 세트',10800,'2025-11-03 10:22:30'),(209,7,'닭가슴살 샐러드',6500,'2025-11-03 10:22:34'),(210,7,'연어 포케볼',8200,'2025-11-03 10:22:34'),(211,7,'불고기 샐러드볼',7600,'2025-11-03 10:22:34'),(212,7,'그릭요거트볼',6000,'2025-11-03 10:22:34'),(213,7,'베지테리언 샐러드',6200,'2025-11-03 10:22:34'),(214,7,'아보카도 샐러드',7800,'2025-11-03 10:22:34'),(215,7,'슈림프 샐러드',7900,'2025-11-03 10:22:34'),(216,7,'치킨 시저샐러드',6900,'2025-11-03 10:22:34'),(217,7,'퀴노아 파워볼',7800,'2025-11-03 10:22:34'),(218,7,'두부 곡물샐러드',6400,'2025-11-03 10:22:34'),(219,7,'프로틴 포케(참치)',8300,'2025-11-03 10:22:34'),(220,7,'프로틴 포케(치킨)',7800,'2025-11-03 10:22:34'),(221,7,'트리플 그린믹스',5600,'2025-11-03 10:22:34'),(222,7,'병아리콩 샐러드',6300,'2025-11-03 10:22:34'),(223,7,'케일 사과샐러드',6500,'2025-11-03 10:22:34'),(224,7,'훈제오리 샐러드',8900,'2025-11-03 10:22:34'),(225,7,'연어 크림치즈 샐러드',8800,'2025-11-03 10:22:34'),(226,7,'카프레제 샐러드',7000,'2025-11-03 10:22:34'),(227,7,'스테이크 샐러드',9800,'2025-11-03 10:22:34'),(228,7,'닭가슴살 라이스볼',7200,'2025-11-03 10:22:34');
/*!40000 ALTER TABLE `menus` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `mission_events`
--

DROP TABLE IF EXISTS `mission_events`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `mission_events` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `mission_id` int unsigned NOT NULL,
  `phase` enum('QUEUED','DISPATCHED','ARRIVED_PICKUP','LEAVE_PICKUP','ARRIVED_DROPOFF','DONE','FAILED') NOT NULL,
  `ts` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `note` varchar(500) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_evt_mission_ts` (`mission_id`,`ts`),
  CONSTRAINT `fk_evt_mission` FOREIGN KEY (`mission_id`) REFERENCES `missions` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `fk_mission_events_missions` FOREIGN KEY (`mission_id`) REFERENCES `missions` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `mission_events`
--

LOCK TABLES `mission_events` WRITE;
/*!40000 ALTER TABLE `mission_events` DISABLE KEYS */;
/*!40000 ALTER TABLE `mission_events` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `missions`
--

DROP TABLE IF EXISTS `missions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `missions` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `user_msg` varchar(500) NOT NULL,
  `pickup_poi_id` int unsigned NOT NULL,
  `dropoff_poi_id` int unsigned NOT NULL,
  `restaurant_id` int unsigned DEFAULT NULL,
  `menu_id` int unsigned DEFAULT NULL,
  `attr_set_id` int unsigned DEFAULT NULL,
  `status` enum('queued','running','done','failed') NOT NULL DEFAULT 'queued',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_mis_pickup` (`pickup_poi_id`),
  KEY `fk_mis_dropoff` (`dropoff_poi_id`),
  KEY `fk_mis_rest` (`restaurant_id`),
  KEY `fk_mis_menu` (`menu_id`),
  KEY `idx_mis_status_time` (`status`,`created_at`),
  CONSTRAINT `fk_mis_dropoff` FOREIGN KEY (`dropoff_poi_id`) REFERENCES `pois` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `fk_mis_menu` FOREIGN KEY (`menu_id`) REFERENCES `menus` (`id`) ON DELETE SET NULL ON UPDATE RESTRICT,
  CONSTRAINT `fk_mis_pickup` FOREIGN KEY (`pickup_poi_id`) REFERENCES `pois` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `fk_mis_rest` FOREIGN KEY (`restaurant_id`) REFERENCES `restaurants` (`id`) ON DELETE SET NULL ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `missions`
--

LOCK TABLES `missions` WRITE;
/*!40000 ALTER TABLE `missions` DISABLE KEYS */;
/*!40000 ALTER TABLE `missions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Temporary view structure for view `node_summary`
--

DROP TABLE IF EXISTS `node_summary`;
/*!50001 DROP VIEW IF EXISTS `node_summary`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `node_summary` AS SELECT 
 1 AS `id`,
 1 AS `label`,
 1 AS `kind`,
 1 AS `building_id`,
 1 AS `x_rounded`,
 1 AS `y_rounded`,
 1 AS `x_raw`,
 1 AS `y_raw`,
 1 AS `created_at`*/;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `nodes`
--

DROP TABLE IF EXISTS `nodes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `nodes` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `x` double NOT NULL,
  `y` double NOT NULL,
  `kind` enum('junction','entrance','other') NOT NULL DEFAULT 'junction',
  `label` varchar(120) DEFAULT NULL,
  `building_id` int unsigned DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_nodes_label` (`label`),
  KEY `idx_nodes_kind` (`kind`),
  KEY `idx_nodes_building` (`building_id`),
  CONSTRAINT `fk_nodes_building` FOREIGN KEY (`building_id`) REFERENCES `buildings` (`id`) ON DELETE SET NULL ON UPDATE RESTRICT,
  CONSTRAINT `fk_nodes_buildings` FOREIGN KEY (`building_id`) REFERENCES `buildings` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `nodes`
--

LOCK TABLES `nodes` WRITE;
/*!40000 ALTER TABLE `nodes` DISABLE KEYS */;
INSERT INTO `nodes` VALUES (1,-0.233,-0.003,'other','Start',NULL,'2025-11-03 00:56:13'),(2,31.528,-2.318,'entrance','Chungmu',1,'2025-11-03 00:56:13'),(3,6.461,7.314,'entrance','Yeongsil',3,'2025-11-03 00:56:13'),(4,-73.519,24.422,'entrance','ParkingGate',4,'2025-11-03 00:56:13'),(5,9.625,65.197,'entrance','SejongElementaryHall',5,'2025-11-03 00:56:13'),(6,42.636,45.891,'entrance','Dasan',2,'2025-11-03 00:56:14');
/*!40000 ALTER TABLE `nodes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pois`
--

DROP TABLE IF EXISTS `pois`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pois` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `building_id` int unsigned NOT NULL,
  `x` double NOT NULL,
  `y` double NOT NULL,
  `node_id` int unsigned DEFAULT NULL,
  `label` varchar(120) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_pois_building_role` (`building_id`),
  KEY `fk_pois_nodes` (`node_id`),
  CONSTRAINT `fk_pois_building` FOREIGN KEY (`building_id`) REFERENCES `buildings` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `fk_pois_buildings` FOREIGN KEY (`building_id`) REFERENCES `buildings` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_pois_node` FOREIGN KEY (`node_id`) REFERENCES `nodes` (`id`) ON DELETE SET NULL ON UPDATE RESTRICT,
  CONSTRAINT `fk_pois_nodes` FOREIGN KEY (`node_id`) REFERENCES `nodes` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pois`
--

LOCK TABLES `pois` WRITE;
/*!40000 ALTER TABLE `pois` DISABLE KEYS */;
INSERT INTO `pois` VALUES (1,1,31.528,-2.318,2,'Chungmu entrance','2025-11-03 00:56:26'),(2,3,6.461,7.314,3,'Yeongsil entrance','2025-11-03 00:56:26'),(3,4,-73.519,24.422,4,'ParkingGate entrance','2025-11-03 00:56:26'),(4,5,9.625,65.197,5,'SejongElementaryHall entrance','2025-11-03 00:56:26'),(5,2,42.636,45.891,6,'Dasan entrance','2025-11-03 00:56:26');
/*!40000 ALTER TABLE `pois` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `restaurants`
--

DROP TABLE IF EXISTS `restaurants`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `restaurants` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(120) NOT NULL,
  `category` varchar(60) NOT NULL,
  `building_id` int unsigned NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_rest_name_building` (`name`,`building_id`),
  UNIQUE KEY `uk_restaurants_name_building` (`name`,`building_id`),
  KEY `idx_rest_building` (`building_id`),
  CONSTRAINT `fk_rest_building` FOREIGN KEY (`building_id`) REFERENCES `buildings` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `restaurants`
--

LOCK TABLES `restaurants` WRITE;
/*!40000 ALTER TABLE `restaurants` DISABLE KEYS */;
INSERT INTO `restaurants` VALUES (1,'나루또','돈가스·우동',1,'2025-10-31 07:39:38'),(2,'아지오','덮밥·분식',1,'2025-10-31 07:39:38'),(3,'반미하우스','반미·쌀국수',1,'2025-10-31 07:39:38'),(4,'스시고','초밥·회',1,'2025-10-31 07:39:38'),(5,'청춘백반','한식·정식',2,'2025-11-03 10:07:54'),(6,'라멘당','라멘·일식',2,'2025-11-03 10:07:54'),(7,'샐러디움','샐러드·헬시푸드',2,'2025-11-03 10:07:54');
/*!40000 ALTER TABLE `restaurants` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Final view structure for view `edges_u`
--

/*!50001 DROP VIEW IF EXISTS `edges_u`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `edges_u` AS select `edges`.`src_node_id` AS `a`,`edges`.`dst_node_id` AS `b`,`edges`.`length` AS `w` from `edges` union all select `edges`.`dst_node_id` AS `a`,`edges`.`src_node_id` AS `b`,`edges`.`length` AS `w` from `edges` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `menu_full`
--

/*!50001 DROP VIEW IF EXISTS `menu_full`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `menu_full` AS select `m`.`id` AS `menu_id`,`m`.`name` AS `menu_name`,`m`.`price` AS `menu_price`,`r`.`id` AS `restaurant_id`,`r`.`name` AS `restaurant_name`,`r`.`category` AS `restaurant_category`,`b`.`id` AS `building_id`,`b`.`name` AS `building_name` from ((`menus` `m` join `restaurants` `r` on((`r`.`id` = `m`.`restaurant_id`))) join `buildings` `b` on((`b`.`id` = `r`.`building_id`))) */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `node_summary`
--

/*!50001 DROP VIEW IF EXISTS `node_summary`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `node_summary` AS select `nodes`.`id` AS `id`,`nodes`.`label` AS `label`,`nodes`.`kind` AS `kind`,`nodes`.`building_id` AS `building_id`,round(`nodes`.`x`,1) AS `x_rounded`,round(`nodes`.`y`,1) AS `y_rounded`,`nodes`.`x` AS `x_raw`,`nodes`.`y` AS `y_raw`,`nodes`.`created_at` AS `created_at` from `nodes` order by `nodes`.`label` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-11-24 10:31:02
