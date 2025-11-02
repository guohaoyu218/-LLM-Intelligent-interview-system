# 用户认证与数据库设计文档

## 1. 技术栈

### 1.1 核心依赖
- FastAPI: Web框架
- Uvicorn: ASGI服务器
- SQLAlchemy: ORM框架
- PyMySQL: MySQL驱动
- python-jose[cryptography]: JWT令牌处理
- passlib[bcrypt]: 密码加密
- python-multipart: 表单数据处理

### 1.2 数据库
- MySQL 8.0+

## 2. 数据库设计

### 2.1 用户表 (users)
```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    user_type ENUM('job_seeker', 'admin') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT TRUE
);
```

### 2.2 求职者信息表 (job_seeker_profiles)
```sql
CREATE TABLE job_seeker_profiles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNIQUE NOT NULL,
    resume_path VARCHAR(255),
    skills TEXT,
    experience_years INT,
    education_level VARCHAR(50),
    preferred_position VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### 2.3 面试记录表 (interviews)
```sql
CREATE TABLE interviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    session_id VARCHAR(36) NOT NULL,
    interview_type VARCHAR(50),
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    status VARCHAR(20),
    score DECIMAL(5,2),
    summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

## 3. API 设计

### 3.1 认证接口
```
POST /api/auth/register
- 注册新用户
- 请求体：username, email, password, user_type, full_name

POST /api/auth/login
- 用户登录
- 请求体：username/email, password
- 返回：JWT token

GET /api/auth/me
- 获取当前用户信息
- 需要认证

PUT /api/auth/password
- 修改密码
- 需要认证
```

### 3.2 用户管理接口
```
GET /api/users/{user_id}
- 获取用户详细信息
- 需要管理员权限

PUT /api/users/{user_id}
- 更新用户信息
- 需要认证或管理员权限

GET /api/users
- 获取用户列表（分页）
- 需要管理员权限
```

### 3.3 求职者接口
```
POST /api/jobseeker/profile
- 创建/更新求职者档案
- 需要求职者权限

GET /api/jobseeker/profile
- 获取求职者档案
- 需要认证

POST /api/jobseeker/resume
- 上传简历
- 需要求职者权限
```

## 4. 目录结构

```
backend/
├── api/
│   ├── __init__.py
│   ├── auth.py          # 认证相关路由
│   ├── users.py         # 用户管理路由
│   └── jobseeker.py     # 求职者相关路由
├── core/
│   ├── __init__.py
│   ├── config.py        # 配置管理
│   ├── security.py      # 安全相关（JWT、密码加密）
│   └── database.py      # 数据库连接管理
├── models/
│   ├── __init__.py
│   ├── user.py          # 用户模型
│   └── interview.py     # 面试相关模型
├── schemas/
│   ├── __init__.py
│   ├── user.py          # 用户相关Pydantic模型
│   └── interview.py     # 面试相关Pydantic模型
└── services/
    ├── __init__.py
    └── auth_service.py  # 认证相关服务
```

## 5. 安全考虑

### 5.1 密码安全
- 使用bcrypt进行密码加密存储
- 密码强度要求：最少8位，包含大小写字母和数字
- 密码重试限制：5次/小时

### 5.2 JWT配置
- Token有效期：访问令牌30分钟，刷新令牌7天
- 使用HS256算法
- Token轮换机制

### 5.3 API安全
- 使用HTTPS
- 实现请求速率限制
- CORS配置
- 输入验证和消毒

## 6. 开发计划

### 第一阶段：基础设施
1. 配置MySQL数据库
2. 实现数据库模型
3. 设置JWT认证系统

### 第二阶段：核心功能
1. 实现用户注册和登录
2. 实现用户档案管理
3. 集成面试系统

### 第三阶段：优化和测试
1. 添加单元测试
2. 性能优化
3. 安全性测试

## 7. 环境变量配置

创建.env文件，包含以下配置：
```
# 数据库配置
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/interview_db

# JWT配置
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# 应用配置
API_V1_PREFIX=/api
PROJECT_NAME=Interview System
BACKEND_CORS_ORIGINS=["http://localhost:3000"]

# 文件上传配置
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE=5242880  # 5MB
```

## 8. 注意事项

1. 所有API响应都应该使用统一的响应格式
2. 实现完整的错误处理机制
3. 记录关键操作日志
4. 定期备份数据库
5. 实现用户会话管理
6. 考虑未来的扩展性

## 9. 测试策略

1. 单元测试：使用pytest
2. 集成测试：测试API端点
3. 性能测试：使用locust
4. 安全测试：使用OWASP指南

## 10. 部署考虑

1. 使用Docker容器化
2. 实现健康检查端点
3. 配置监控系统
4. 设置CI/CD流程
