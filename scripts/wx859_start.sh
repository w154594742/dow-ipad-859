#!/bin/bash

# 定义颜色
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# 定义端口
REDIS_PORT=6379
WX859_PORT=8059

echo -e "${BLUE}+------------------------------------------------+${NC}"
echo -e "${BLUE}|         WX859 Protocol Service Starter         |${NC}"
echo -e "${BLUE}+------------------------------------------------+${NC}"

# 强制释放端口函数
force_release_port() {
    local port=$1
    local service=$2
    echo -e "${YELLOW}正在检查并释放 $service 端口 $port...${NC}"
    
    # 查找占用端口的进程
    local pids=$(lsof -t -i :$port 2>/dev/null)
    
    if [ -n "$pids" ]; then
        echo -e "${YELLOW}发现端口 $port 被以下进程占用: $pids${NC}"
        for pid in $pids; do
            echo -e "${YELLOW}  正在终止进程 $pid...${NC}"
            kill -9 $pid 2>/dev/null
        done
        sleep 1
        
        # 再次检查
        local remaining_pids=$(lsof -t -i :$port 2>/dev/null)
        if [ -n "$remaining_pids" ]; then
            echo -e "${RED}警告: 端口 $port 仍被占用，可能需要手动处理${NC}"
        else
            echo -e "${GREEN}端口 $port 已成功释放${NC}"
        fi
    else
        echo -e "${GREEN}端口 $port 未被占用${NC}"
    fi
}

# 检查端口是否被占用
check_port() {
    local port=$1
    local service=$2
    if lsof -i :$port > /dev/null 2>&1; then
        echo -e "${RED}错误: $service 端口 $port 已被占用!${NC}"
        echo -e "${YELLOW}解决方案:${NC}"
        echo -e "1. 查看占用进程: ${BLUE}sudo lsof -i :$port${NC}"
        echo -e "2. 停止占用进程: ${BLUE}sudo kill -9 \$(sudo lsof -t -i :$port)${NC}"
        echo -e "3. 或者修改 $service 配置使用其他端口"
        return 1
    fi
    return 0
}

# 检查必要的命令是否存在
check_dependencies() {
    local missing_deps=()
    
    if ! command -v redis-server &> /dev/null; then
        missing_deps+=("redis-server")
    fi
    
    if ! command -v lsof &> /dev/null; then
        missing_deps+=("lsof")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        echo -e "${RED}错误: 缺少必要的依赖程序: ${missing_deps[*]}${NC}"
        echo -e "${YELLOW}请安装缺少的依赖:${NC}"
        echo -e "${BLUE}Ubuntu/Debian: sudo apt update && sudo apt install redis-server lsof${NC}"
        echo -e "${BLUE}CentOS/RHEL: sudo yum install redis lsof${NC}"
        return 1
    fi
    return 0
}

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${YELLOW}项目根目录: $PROJECT_ROOT${NC}"

# 检查依赖
echo -e "${YELLOW}[0/4] 检查系统依赖...${NC}"
if ! check_dependencies; then
    exit 1
fi
echo -e "${GREEN}系统依赖检查通过${NC}"

# 第一步：停止现有服务并释放端口
echo -e "${YELLOW}[1/4] 停止现有服务并释放相关端口...${NC}"

# 停止现有的WX859服务
echo -e "${YELLOW}正在停止现有的WX859服务...${NC}"
pkill -f wxapi_linux_v1_0_5 2>/dev/null || true

# 停止现有的Redis服务
echo -e "${YELLOW}正在停止现有的Redis服务...${NC}"
redis-cli -p $REDIS_PORT shutdown 2>/dev/null || true

# 等待服务完全停止
echo -e "${YELLOW}等待服务完全停止...${NC}"
sleep 3

# 强制释放端口（双重保险）
force_release_port $REDIS_PORT "Redis"
force_release_port $WX859_PORT "WX859"

# 第二步：启动Redis服务
echo -e "${YELLOW}[2/4] 正在启动Redis服务...${NC}"

# 检查Redis端口
if ! check_port $REDIS_PORT "Redis"; then
    echo -e "${RED}Redis端口检查失败，尝试强制释放...${NC}"
    force_release_port $REDIS_PORT "Redis"
    sleep 2
fi

# 检查Redis配置文件
REDIS_CONF="$PROJECT_ROOT/lib/wx859/859/redis/redis.linux.conf"
if [ ! -f "$REDIS_CONF" ]; then
    echo -e "${YELLOW}未找到Redis Linux配置文件，使用默认配置启动Redis...${NC}"
    redis-server --daemonize yes --port $REDIS_PORT &
    REDIS_PID=$!
else
    echo -e "${GREEN}使用项目Redis配置文件: $REDIS_CONF${NC}"
    cd "$PROJECT_ROOT/lib/wx859/859/redis"
    redis-server "$REDIS_CONF" &
    REDIS_PID=$!
fi

# 检查Redis是否启动成功
sleep 3
if ! redis-cli -p $REDIS_PORT ping > /dev/null 2>&1; then
    echo -e "${RED}Redis启动失败! 可能原因:${NC}"
    echo -e "1. 端口 $REDIS_PORT 被占用"
    echo -e "2. Redis配置文件有误"
    echo -e "3. 权限问题"
    echo -e "${YELLOW}请检查Redis日志获取更多信息${NC}"
    exit 1
fi

echo -e "${GREEN}Redis服务已启动，端口: $REDIS_PORT${NC}"

# 第三步：启动WX859协议服务
echo -e "${YELLOW}[3/4] 正在启动WX859协议服务...${NC}"

# 检查WX859端口
if ! check_port $WX859_PORT "WX859"; then
    echo -e "${RED}WX859端口检查失败，尝试强制释放...${NC}"
    force_release_port $WX859_PORT "WX859"
    sleep 2
fi

# 检查WX859 Linux服务文件
WX859_DIR="$PROJECT_ROOT/lib/wx859/859/linux"
WX859_BINARY="$WX859_DIR/wxapi_linux_v1_0_5"

if [ ! -d "$WX859_DIR" ]; then
    echo -e "${RED}WX859 Linux目录不存在: $WX859_DIR${NC}"
    echo -e "${RED}正在关闭Redis服务...${NC}"
    redis-cli -p $REDIS_PORT shutdown
    exit 1
fi

if [ ! -f "$WX859_BINARY" ]; then
    echo -e "${RED}WX859服务可执行文件不存在: $WX859_BINARY${NC}"
    echo -e "${RED}正在关闭Redis服务...${NC}"
    redis-cli -p $REDIS_PORT shutdown
    exit 1
fi

# 设置执行权限
chmod +x "$WX859_BINARY"

# 启动WX859服务
cd "$WX859_DIR"
echo -e "${GREEN}正在启动WX859服务...${NC}"

# 尝试多个可能的库路径
POSSIBLE_LIB_PATHS=(
    "/usr/lib64"
    "/lib64" 
    "$WX859_DIR/lib"
    "$WX859_DIR/lib_compat"
)

for lib_path in "${POSSIBLE_LIB_PATHS[@]}"; do
    if [ -d "$lib_path" ]; then
        export LD_LIBRARY_PATH="$lib_path:$LD_LIBRARY_PATH"
    fi
done

echo -e "${YELLOW}当前库路径: $LD_LIBRARY_PATH${NC}"

# 检查是否有启动脚本
if [ -f "$WX859_DIR/start.sh" ]; then
    chmod +x "$WX859_DIR/start.sh"
    echo -e "${BLUE}使用项目启动脚本...${NC}"
    cd "$WX859_DIR"
    ./start.sh &
    WX859_PID=$!
    cd "$PROJECT_ROOT"
else
    # 原有备用启动逻辑
    cd "$WX859_DIR"
    ./wxapi_linux_v1_0_5 &
    WX859_PID=$!
    cd "$PROJECT_ROOT"
fi

# 检查WX859是否启动成功
sleep 5
if ! ps -p $WX859_PID > /dev/null 2>&1; then
    echo -e "${RED}WX859服务启动失败! 可能原因:${NC}"
    echo -e "1. 端口 $WX859_PORT 被占用"
    echo -e "2. 缺少依赖库文件"
    echo -e "3. 权限问题"
    echo -e "4. Redis服务未正常运行"
    echo -e "${YELLOW}请查看日志文件获取更多信息${NC}"
    echo -e "${YELLOW}可以尝试运行: ldd $WX859_BINARY 检查库依赖${NC}"
    echo -e "${RED}正在关闭Redis服务...${NC}"
    redis-cli -p $REDIS_PORT shutdown
    exit 1
fi

# 测试API连接
echo -e "${YELLOW}正在测试API连接...${NC}"
sleep 2
if curl -s "http://127.0.0.1:$WX859_PORT/api/Login/LoginGetQR" > /dev/null 2>&1; then
    echo -e "${GREEN}WX859 API服务正常响应${NC}"
else
    echo -e "${YELLOW}API暂时无响应，可能正在初始化中...${NC}"
fi

echo -e "${GREEN}WX859服务已启动，PID: $WX859_PID，端口: $WX859_PORT${NC}"

# 第四步：配置完成提示
echo -e "${YELLOW}[4/4] 服务启动完成!${NC}"
echo -e "${GREEN}WX859 协议服务已全部启动!${NC}"
echo
echo -e "${BLUE}服务状态:${NC}"
echo -e "${GREEN}  ✓ Redis服务: 127.0.0.1:$REDIS_PORT${NC}"
echo -e "${GREEN}  ✓ WX859服务: 127.0.0.1:$WX859_PORT${NC}"
echo
echo -e "${YELLOW}现在可以运行主程序，请确保在配置文件中设置:${NC}"
echo -e "${BLUE}  \"channel_type\": \"wx859\",${NC}"
echo -e "${BLUE}  \"wx859_protocol_version\": \"859\",${NC}"
echo -e "${BLUE}  \"wx859_api_host\": \"127.0.0.1\",${NC}"
echo -e "${BLUE}  \"wx859_api_port\": $WX859_PORT${NC}"
echo
echo -e "${YELLOW}启动主程序命令:${NC}"
echo -e "${BLUE}  cd $PROJECT_ROOT${NC}"
echo -e "${BLUE}  python3 app.py${NC}"
echo
echo -e "${YELLOW}Docker方式启动 (可选):${NC}"
echo -e "${BLUE}  cd $PROJECT_ROOT/lib/wx859/859/linux${NC}"
echo -e "${BLUE}  docker compose up -d${NC}"
echo
echo -e "${YELLOW}提示: 如需停止WX859服务，请按Ctrl+C或运行 wx859_stop.sh 脚本${NC}"
echo -e "${BLUE}+------------------------------------------------+${NC}"

# 创建PID文件用于停止脚本
echo "$REDIS_PID" > /tmp/wx859_redis.pid
echo "$WX859_PID" > /tmp/wx859_service.pid

# 设置信号处理
cleanup() {
    echo -e "\n${YELLOW}正在停止WX859服务...${NC}"
    if [ -n "$WX859_PID" ] && ps -p $WX859_PID > /dev/null 2>&1; then
        kill $WX859_PID
        echo -e "${GREEN}WX859服务已停止${NC}"
    fi
    
    echo -e "${YELLOW}正在停止Redis服务...${NC}"
    redis-cli -p $REDIS_PORT shutdown 2>/dev/null
    echo -e "${GREEN}Redis服务已停止${NC}"
    
    # 清理PID文件
    rm -f /tmp/wx859_redis.pid /tmp/wx859_service.pid
    
    echo -e "${GREEN}所有服务已关闭${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# 保持脚本运行，监控服务状态
echo -e "${BLUE}服务监控中... (按Ctrl+C停止)${NC}"
while true; do
    sleep 10
    
    # 检查Redis状态
    if ! redis-cli -p $REDIS_PORT ping > /dev/null 2>&1; then
        echo -e "${RED}Redis服务异常停止!${NC}"
        break
    fi
    
    # 检查WX859服务状态
    if ! ps -p $WX859_PID > /dev/null 2>&1; then
        echo -e "${RED}WX859服务异常停止!${NC}"
        break
    fi
done

# 如果循环退出，说明服务异常
echo -e "${RED}检测到服务异常，正在清理...${NC}"
cleanup 
