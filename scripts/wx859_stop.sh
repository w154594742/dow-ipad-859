#!/bin/bash

# 定义颜色
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# 定义端口
REDIS_PORT=6378
WX859_PORT=8059

echo -e "${BLUE}+------------------------------------------------+${NC}"
echo -e "${BLUE}|         WX859 Protocol Service Stopper         |${NC}"
echo -e "${BLUE}+------------------------------------------------+${NC}"

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${YELLOW}项目根目录: $PROJECT_ROOT${NC}"

# 停止WX859服务
echo -e "${YELLOW}[1/3] 正在停止WX859协议服务...${NC}"

# 通过PID文件停止
if [ -f "/tmp/wx859_service.pid" ]; then
    WX859_PID=$(cat /tmp/wx859_service.pid)
    if [ -n "$WX859_PID" ] && ps -p $WX859_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}  正在终止WX859服务进程 (PID: $WX859_PID)...${NC}"
        kill -TERM $WX859_PID
        sleep 3
        
        # 如果进程仍然存在，强制终止
        if ps -p $WX859_PID > /dev/null 2>&1; then
            echo -e "${YELLOW}  强制终止WX859服务进程...${NC}"
            kill -9 $WX859_PID
        fi
        echo -e "${GREEN}WX859服务已停止 (PID: $WX859_PID)${NC}"
    else
        echo -e "${YELLOW}PID文件中的进程已不存在${NC}"
    fi
    rm -f /tmp/wx859_service.pid
fi

# 通过进程名停止
WX859_PROCESSES=$(ps aux | grep 'wxapi_linux_v1_0_5' | grep -v grep | awk '{print $2}')
if [ -n "$WX859_PROCESSES" ]; then
    for pid in $WX859_PROCESSES; do
        echo -e "${YELLOW}  正在终止WX859服务进程 (PID: $pid)...${NC}"
        kill -TERM $pid
        sleep 2
        
        # 检查进程是否还存在
        if ps -p $pid > /dev/null 2>&1; then
            echo -e "${YELLOW}  强制终止进程 $pid...${NC}"
            kill -9 $pid
        fi
    done
    echo -e "${GREEN}WX859服务进程已停止${NC}"
else
    echo -e "${YELLOW}未发现运行中的WX859服务进程${NC}"
fi

# 通过端口停止
WX859_PORT_PROCESSES=$(lsof -t -i :$WX859_PORT 2>/dev/null)
if [ -n "$WX859_PORT_PROCESSES" ]; then
    echo -e "${YELLOW}  发现占用端口 $WX859_PORT 的进程: $WX859_PORT_PROCESSES${NC}"
    for pid in $WX859_PORT_PROCESSES; do
        echo -e "${YELLOW}  正在终止占用端口的进程 (PID: $pid)...${NC}"
        kill -9 $pid
    done
    echo -e "${GREEN}端口 $WX859_PORT 已释放${NC}"
fi

# 停止Docker容器（如果存在）
echo -e "${YELLOW}[2/3] 检查并停止Docker容器...${NC}"
DOCKER_CONTAINERS=$(docker ps -q --filter "name=dp_wxapi" 2>/dev/null)
if [ -n "$DOCKER_CONTAINERS" ]; then
    echo -e "${YELLOW}  发现WX859相关Docker容器，正在停止...${NC}"
    docker stop $DOCKER_CONTAINERS
    echo -e "${GREEN}Docker容器已停止${NC}"
else
    echo -e "${YELLOW}未发现运行中的WX859 Docker容器${NC}"
fi

# 停止Redis服务
echo -e "${YELLOW}[3/3] 正在停止Redis服务...${NC}"

# 通过PID文件停止
if [ -f "/tmp/wx859_redis.pid" ]; then
    REDIS_PID=$(cat /tmp/wx859_redis.pid)
    if [ -n "$REDIS_PID" ] && ps -p $REDIS_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}  正在终止Redis服务进程 (PID: $REDIS_PID)...${NC}"
        kill -TERM $REDIS_PID
        sleep 2
        
        # 如果进程仍然存在，强制终止
        if ps -p $REDIS_PID > /dev/null 2>&1; then
            echo -e "${YELLOW}  强制终止Redis服务进程...${NC}"
            kill -9 $REDIS_PID
        fi
        echo -e "${GREEN}Redis服务已停止 (PID: $REDIS_PID)${NC}"
    else
        echo -e "${YELLOW}PID文件中的Redis进程已不存在${NC}"
    fi
    rm -f /tmp/wx859_redis.pid
fi

# 通过redis-cli优雅停止
if command -v redis-cli &> /dev/null; then
    if redis-cli -p $REDIS_PORT ping > /dev/null 2>&1; then
        echo -e "${YELLOW}  使用redis-cli优雅停止Redis服务...${NC}"
        redis-cli -p $REDIS_PORT shutdown
        sleep 2
        
        if redis-cli -p $REDIS_PORT ping > /dev/null 2>&1; then
            echo -e "${YELLOW}  Redis服务未响应shutdown命令，尝试强制停止...${NC}"
        else
            echo -e "${GREEN}Redis服务已优雅停止${NC}"
        fi
    fi
fi

# 通过进程名停止Redis
REDIS_PROCESSES=$(ps aux | grep 'redis-server' | grep -v grep | awk '{print $2}')
if [ -n "$REDIS_PROCESSES" ]; then
    for pid in $REDIS_PROCESSES; do
        # 检查是否是我们启动的Redis进程（端口匹配）
        if netstat -tlnp 2>/dev/null | grep ":$REDIS_PORT " | grep -q "$pid"; then
            echo -e "${YELLOW}  正在终止Redis服务进程 (PID: $pid)...${NC}"
            kill -TERM $pid
            sleep 2
            
            # 检查进程是否还存在
            if ps -p $pid > /dev/null 2>&1; then
                echo -e "${YELLOW}  强制终止Redis进程 $pid...${NC}"
                kill -9 $pid
            fi
        fi
    done
    echo -e "${GREEN}Redis服务进程已停止${NC}"
else
    echo -e "${YELLOW}未发现运行中的Redis服务进程${NC}"
fi

# 通过端口停止Redis
REDIS_PORT_PROCESSES=$(lsof -t -i :$REDIS_PORT 2>/dev/null)
if [ -n "$REDIS_PORT_PROCESSES" ]; then
    echo -e "${YELLOW}  发现占用端口 $REDIS_PORT 的进程: $REDIS_PORT_PROCESSES${NC}"
    for pid in $REDIS_PORT_PROCESSES; do
        echo -e "${YELLOW}  正在终止占用端口的进程 (PID: $pid)...${NC}"
        kill -9 $pid
    done
    echo -e "${GREEN}端口 $REDIS_PORT 已释放${NC}"
fi

# 最终检查
echo -e "${YELLOW}正在进行最终检查...${NC}"

# 检查端口是否已释放
if lsof -i :$WX859_PORT > /dev/null 2>&1; then
    echo -e "${RED}警告: 端口 $WX859_PORT 仍被占用${NC}"
    echo -e "${YELLOW}占用进程:${NC}"
    lsof -i :$WX859_PORT
else
    echo -e "${GREEN}端口 $WX859_PORT 已成功释放${NC}"
fi

if lsof -i :$REDIS_PORT > /dev/null 2>&1; then
    echo -e "${RED}警告: 端口 $REDIS_PORT 仍被占用${NC}"
    echo -e "${YELLOW}占用进程:${NC}"
    lsof -i :$REDIS_PORT
else
    echo -e "${GREEN}端口 $REDIS_PORT 已成功释放${NC}"
fi

# 清理临时文件
rm -f /tmp/wx859_*.pid

echo -e "${GREEN}所有WX859服务已停止!${NC}"
echo -e "${BLUE}+------------------------------------------------+${NC}"

# 提供重启建议
echo -e "${YELLOW}如需重新启动服务，请运行:${NC}"
echo -e "${BLUE}  ./wx859_start.sh${NC}"
echo
echo -e "${YELLOW}如需检查服务状态，请运行:${NC}"
echo -e "${BLUE}  sudo lsof -i :$WX859_PORT  # 检查WX859端口${NC}"
echo -e "${BLUE}  sudo lsof -i :$REDIS_PORT  # 检查Redis端口${NC}"
echo -e "${BLUE}  ps aux | grep wxapi_linux_v1_0_5  # 检查WX859进程${NC}"
echo -e "${BLUE}  ps aux | grep redis-server  # 检查Redis进程${NC}" 