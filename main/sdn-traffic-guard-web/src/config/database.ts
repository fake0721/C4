// 数据库连接配置
export interface DatabaseConfig {
  host: string
  port: number
  database: string
  user: string
  password: string
}

// 从环境变量获取数据库配置
export const dbConfig: DatabaseConfig = {
  host: import.meta.env.VITE_DB_HOST || 'localhost',
  port: Number(import.meta.env.VITE_DB_PORT) || 3306,
  database: import.meta.env.VITE_DB_NAME || 'network_management',
  user: import.meta.env.VITE_DB_USER || 'root',
  password: import.meta.env.VITE_DB_PASSWORD || ''
}

// MySQL连接池配置
export const poolConfig = {
  connectionLimit: 10,
  host: dbConfig.host,
  port: dbConfig.port,
  user: dbConfig.user,
  password: dbConfig.password,
  database: dbConfig.database,
  charset: 'utf8mb4'
}