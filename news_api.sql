
CREATE TABLE IF NOT EXISTS `news_api_newsvector` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
  `news_id` INT NOT NULL UNIQUE COMMENT '新闻ID',
  `vector_data` LONGTEXT COMMENT '向量数据(JSON格式)',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  INDEX `idx_news_id` (`news_id`),
  FOREIGN KEY (`news_id`) REFERENCES `news_api_newsdetail`(`news_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='新闻向量存储表';


CREATE TABLE IF NOT EXISTS `news_api_qahistory` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
  `userid` INT NOT NULL COMMENT '用户ID',
  `newsid` INT NOT NULL COMMENT '新闻ID',
  `question` TEXT COMMENT '用户问题',
  `answer` TEXT COMMENT '系统回答',
  `time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '问答时间',
  INDEX `idx_userid` (`userid`),
  INDEX `idx_newsid` (`newsid`),
  INDEX `idx_time` (`time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='新闻问答历史表';
