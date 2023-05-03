CREATE TABLE `author` (
  `author_id` bigint PRIMARY KEY,
  `author_name` varchar(255)
);

CREATE TABLE `author_links` (
  `author_id` bigint,
  `site_id` bigint,
  `author_link` varchar(255)
);

CREATE TABLE `fandoms` (
  `fandom_id` bigint PRIMARY KEY,
  `fandom` varchar(255)
);

CREATE TABLE `fics` (
  `fic_id` bigint PRIMARY KEY,
  `title` varchar(255),
  `link` varchar(255),
  `author_id` bigint,
  `word_count` bigint,
  `fic_summary` text,
  `site_id` bigint
);

CREATE TABLE `fic_links` (
  `fic_id` bigint,
  `site_id` bigint,
  `fic_link` varchar(255)
);

CREATE TABLE `tags` (
  `tag_id` bigint PRIMARY KEY,
  `tag_name` varchar(255)
);

CREATE TABLE `relationships` (
  `ship_id` bigint PRIMARY KEY,
  `ship_name` varchar(255),
  `character_id` bigint
);

CREATE TABLE `sites` (
  `site_id` bigint PRIMARY KEY,
  `site_name` varchar(255)
);

CREATE TABLE `characters` (
  `character_id` bigint PRIMARY KEY,
  `character_name` varchar(255)
);

CREATE TABLE `categories` (
  `category_id` bigint PRIMARY KEY,
  `category` varchar(255)
);

CREATE TABLE `story_tags` (
  `story_id` bigint PRIMARY KEY,
  `fic_id` bigint,
  `tag_id` bigint,
  `relationship_id` bigint,
  `fandom_id` bigint,
  `character_id` bigint,
  `category_id` bigint
);

CREATE TABLE `author_fics` (
  `author_author_id` bigint,
  `fics_author_id` bigint,
  PRIMARY KEY (`author_author_id`, `fics_author_id`)
);

CREATE TABLE `sites_fics` (
  `sites_site_id` bigint,
  `fics_site_id` bigint,
  PRIMARY KEY (`sites_site_id`, `fics_site_id`)
);

CREATE TABLE `characters_relationships` (
  `characters_character_id` bigint,
  `relationships_character_id` bigint,
  PRIMARY KEY (`characters_character_id`, `relationships_character_id`)
);

CREATE TABLE `tags_story_tags` (
  `tags_tag_id` bigint,
  `story_tags_tag_id` bigint,
  PRIMARY KEY (`tags_tag_id`, `story_tags_tag_id`)
);

CREATE TABLE `relationships_story_tags` (
  `relationships_ship_id` bigint,
  `story_tags_relationship_id` bigint,
  PRIMARY KEY (`relationships_ship_id`, `story_tags_relationship_id`)
);

CREATE TABLE `fandoms_story_tags` (
  `fandoms_fandom_id` bigint,
  `story_tags_fandom_id` bigint,
  PRIMARY KEY (`fandoms_fandom_id`, `story_tags_fandom_id`)
);

CREATE TABLE `characters_story_tags` (
  `characters_character_id` bigint,
  `story_tags_character_id` bigint,
  PRIMARY KEY (`characters_character_id`, `story_tags_character_id`)
);

CREATE TABLE `categories_story_tags` (
  `categories_category_id` bigint,
  `story_tags_category_id` bigint,
  PRIMARY KEY (`categories_category_id`, `story_tags_category_id`)
);

ALTER TABLE `author_links` ADD FOREIGN KEY (`author_id`) REFERENCES `author` (`author_id`);

ALTER TABLE `author_links` ADD FOREIGN KEY (`site_id`) REFERENCES `sites` (`site_id`);

ALTER TABLE `author_fics` ADD FOREIGN KEY (`author_author_id`) REFERENCES `author` (`author_id`);

ALTER TABLE `author_fics` ADD FOREIGN KEY (`fics_author_id`) REFERENCES `fics` (`author_id`);

ALTER TABLE `sites_fics` ADD FOREIGN KEY (`sites_site_id`) REFERENCES `sites` (`site_id`);

ALTER TABLE `sites_fics` ADD FOREIGN KEY (`fics_site_id`) REFERENCES `fics` (`site_id`);

ALTER TABLE `fic_links` ADD FOREIGN KEY (`fic_id`) REFERENCES `fics` (`fic_id`);

ALTER TABLE `fic_links` ADD FOREIGN KEY (`site_id`) REFERENCES `sites` (`site_id`);

ALTER TABLE `characters_relationships` ADD FOREIGN KEY (`characters_character_id`) REFERENCES `characters` (`character_id`);

ALTER TABLE `characters_relationships` ADD FOREIGN KEY (`relationships_character_id`) REFERENCES `relationships` (`character_id`);

ALTER TABLE `story_tags` ADD FOREIGN KEY (`fic_id`) REFERENCES `fics` (`fic_id`);

ALTER TABLE `tags_story_tags` ADD FOREIGN KEY (`tags_tag_id`) REFERENCES `tags` (`tag_id`);

ALTER TABLE `tags_story_tags` ADD FOREIGN KEY (`story_tags_tag_id`) REFERENCES `story_tags` (`tag_id`);

ALTER TABLE `relationships_story_tags` ADD FOREIGN KEY (`relationships_ship_id`) REFERENCES `relationships` (`ship_id`);

ALTER TABLE `relationships_story_tags` ADD FOREIGN KEY (`story_tags_relationship_id`) REFERENCES `story_tags` (`relationship_id`);

ALTER TABLE `fandoms_story_tags` ADD FOREIGN KEY (`fandoms_fandom_id`) REFERENCES `fandoms` (`fandom_id`);

ALTER TABLE `fandoms_story_tags` ADD FOREIGN KEY (`story_tags_fandom_id`) REFERENCES `story_tags` (`fandom_id`);

ALTER TABLE `characters_story_tags` ADD FOREIGN KEY (`characters_character_id`) REFERENCES `characters` (`character_id`);

ALTER TABLE `characters_story_tags` ADD FOREIGN KEY (`story_tags_character_id`) REFERENCES `story_tags` (`character_id`);

ALTER TABLE `categories_story_tags` ADD FOREIGN KEY (`categories_category_id`) REFERENCES `categories` (`category_id`);

ALTER TABLE `categories_story_tags` ADD FOREIGN KEY (`story_tags_category_id`) REFERENCES `story_tags` (`category_id`);
