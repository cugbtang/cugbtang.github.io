---
title: "Go-micro advance, how to play?"
date: 2023-09-15T15:44:23+08:00
lastmod: 2023-09-15T16:44:23+08:00
draft: false
tags: [ "go", "micro","go-micro"]
categories: ["go", "micro","go-micro"]
author: "yesplease"
---
# Go Micro 高级特性深度解析：从理论到实践

## 🌐 服务发现：客户端如何感知服务注册变化

### 原理深度解析

Go Micro 的服务发现机制基于注册中心的**订阅-通知模式**，客户端通过 Watcher 机制实时感知服务实例的变化。这种机制确保了服务发现的动态性和实时性。

### 核心实现机制

#### 1. **Watcher 接口设计**
```go
type Watcher interface {
    // 下一个服务变更事件
    Next() (*Result, error)
    // 停止监听
    Stop()
}

type Result struct {
    // 服务实例
    Service *Service
    // 操作类型：register, deregister, update
    Action string
    // 时间戳
    Timestamp time.Time
}
```

#### 2. **服务订阅完整实现**
```go
package main

import (
    "context"
    "fmt"
    "log"
    "sync"
    "time"

    "github.com/go-micro/go-micro/v4"
    "github.com/go-micro/go-micro/v4/registry"
    "github.com/go-micro/go-micro/plugins/v4/registry/consul"
)

type ServiceWatcher struct {
    registry registry.Registry
    services map[string][]*registry.Service
    mu       sync.RWMutex
}

func NewServiceWatcher(reg registry.Registry) *ServiceWatcher {
    return &ServiceWatcher{
        registry: reg,
        services: make(map[string][]*registry.Service),
    }
}

// 监听服务变化
func (sw *ServiceWatcher) WatchService(ctx context.Context, serviceName string) error {
    // 创建 watcher
    watcher, err := sw.registry.Watch(
        registry.WatchService(serviceName),
    )
    if err != nil {
        return fmt.Errorf("failed to create watcher: %w", err)
    }
    defer watcher.Stop()

    log.Printf("开始监听服务 %s 的变化...", serviceName)

    for {
        select {
        case <-ctx.Done():
            log.Println("停止监听服务变化")
            return nil
        default:
            // 获取下一个事件
            result, err := watcher.Next()
            if err != nil {
                log.Printf("获取服务变化事件失败: %v", err)
                time.Sleep(2 * time.Second)
                continue
            }

            // 处理服务变化
            sw.handleServiceChange(result)
        }
    }
}

// 处理服务变化
func (sw *ServiceWatcher) handleServiceChange(result *registry.Result) {
    sw.mu.Lock()
    defer sw.mu.Unlock()

    serviceName := result.Service.Name
    action := result.Action

    switch action {
    case "register", "update":
        log.Printf("服务 %s 注册/更新: %+v", serviceName, result.Service.Nodes)
        sw.services[serviceName] = []*registry.Service{result.Service}

    case "deregister":
        log.Printf("服务 %s 注销: %+v", serviceName, result.Service.Nodes)
        delete(sw.services, serviceName)

    default:
        log.Printf("未知的服务变化动作: %s", action)
    }
}

// 获取可用服务实例
func (sw *ServiceWatcher) GetServiceInstances(serviceName string) []*registry.Node {
    sw.mu.RLock()
    defer sw.mu.RUnlock()

    services, exists := sw.services[serviceName]
    if !exists || len(services) == 0 {
        return nil
    }

    var nodes []*registry.Node
    for _, service := range services {
        nodes = append(nodes, service.Nodes...)
    }

    return nodes
}

func main() {
    // 创建 Consul 注册中心
    reg := consul.NewRegistry(
        registry.Addrs("127.0.0.1:8500"),
    )

    watcher := NewServiceWatcher(reg)

    // 创建上下文
    ctx, cancel := context.WithCancel(context.Background())
    defer cancel()

    // 启动多个服务的监听
    services := []string{"user-service", "order-service", "payment-service"}

    for _, serviceName := range services {
        go func(name string) {
            if err := watcher.WatchService(ctx, name); err != nil {
                log.Printf("监听服务 %s 失败: %v", name, err)
            }
        }(serviceName)
    }

    // 模拟客户端获取服务实例
    go func() {
        for {
            time.Sleep(5 * time.Second)

            for _, serviceName := range services {
                instances := watcher.GetServiceInstances(serviceName)
                log.Printf("服务 %s 的可用实例: %d", serviceName, len(instances))

                for i, instance := range instances {
                    log.Printf("  实例 %d: %s:%d", i+1, instance.Address, instance.Port)
                }
            }
        }
    }()

    // 等待程序退出
    select {}
}
```

#### 3. **事件驱动缓存机制**
```go
type ServiceCache struct {
    cache    map[string][]*registry.Service
    watchers map[string]registry.Watcher
    mu       sync.RWMutex
    registry registry.Registry
}

func (sc *ServiceCache) GetService(name string) ([]*registry.Service, error) {
    sc.mu.RLock()
    services, exists := sc.cache[name]
    sc.mu.RUnlock()

    if exists && len(services) > 0 {
        return services, nil
    }

    // 缓存中没有，从注册中心获取
    services, err := sc.registry.GetService(name)
    if err != nil {
        return nil, err
    }

    sc.mu.Lock()
    sc.cache[name] = services
    sc.mu.Unlock()

    // 启动监听
    sc.startWatching(name)

    return services, nil
}

func (sc *ServiceCache) startWatching(name string) {
    sc.mu.Lock()
    defer sc.mu.Unlock()

    if _, exists := sc.watchers[name]; exists {
        return
    }

    watcher, err := sc.registry.Watch(registry.WatchService(name))
    if err != nil {
        log.Printf("创建 watcher 失败: %v", err)
        return
    }

    sc.watchers[name] = watcher

    go func() {
        defer watcher.Stop()

        for {
            result, err := watcher.Next()
            if err != nil {
                log.Printf("获取服务变化事件失败: %v", err)
                break
            }

            sc.updateCache(name, result)
        }
    }()
}

func (sc *ServiceCache) updateCache(name string, result *registry.Result) {
    sc.mu.Lock()
    defer sc.mu.Unlock()

    switch result.Action {
    case "register", "update":
        sc.cache[name] = []*registry.Service{result.Service}
    case "deregister":
        delete(sc.cache, name)
    }
}
```

### 高级特性

#### **多级缓存策略**
```go
type MultiLevelCache struct {
    l1Cache *LocalCache    // 本地内存缓存
    l2Cache *RedisCache    // 分布式Redis缓存
    l3Cache *RegistryCache  // 注册中心缓存
    stats   *CacheStats
    mu      sync.RWMutex
}

type LocalCache struct {
    items map[string]*CacheItem
    ttl   time.Duration
    mu    sync.RWMutex
}

type CacheItem struct {
    Value      interface{}
    Expiration time.Time
    Hits       int64
    Misses     int64
}

func (mlc *MultiLevelCache) GetService(ctx context.Context, serviceName string) ([]*registry.Service, error) {
    // L1: 本地内存缓存
    if services, err := mlc.l1Cache.Get(serviceName); err == nil {
        mlc.stats.IncL1Hit()
        log.Printf("L1 Cache hit for service: %s", serviceName)
        return services, nil
    }
    mlc.stats.IncL1Miss()

    // L2: Redis缓存
    if services, err := mlc.l2Cache.Get(ctx, serviceName); err == nil {
        // 回填L1缓存
        mlc.l1Cache.Set(serviceName, services, time.Minute*5)
        mlc.stats.IncL2Hit()
        log.Printf("L2 Cache hit for service: %s", serviceName)
        return services, nil
    }
    mlc.stats.IncL2Miss()

    // L3: 注册中心缓存
    if services, err := mlc.l3Cache.GetService(serviceName); err == nil {
        // 回填L1和L2缓存
        mlc.l1Cache.Set(serviceName, services, time.Minute*5)
        mlc.l2Cache.Set(ctx, serviceName, services, time.Minute*30)
        mlc.stats.IncL3Hit()
        log.Printf("L3 Cache hit for service: %s", serviceName)
        return services, nil
    }
    mlc.stats.IncL3Miss()

    return nil, registry.ErrNotFound
}

func (mlc *MultiLevelCache) UpdateService(serviceName string, services []*registry.Service) {
    mlc.mu.Lock()
    defer mlc.mu.Unlock()

    // 同步更新所有缓存级别
    mlc.l1Cache.Set(serviceName, services, time.Minute*5)
    mlc.l2Cache.Set(context.Background(), serviceName, services, time.Minute*30)
    mlc.l3Cache.UpdateService(serviceName, services)

    log.Printf("Service cache updated: %s", serviceName)
}

// 缓存预热机制
func (mlc *MultiLevelCache) WarmUp(ctx context.Context, serviceNames []string) error {
    var wg sync.WaitGroup
    errChan := make(chan error, len(serviceNames))
    sem := make(chan struct{}, 10) // 限制并发数

    for _, name := range serviceNames {
        wg.Add(1)
        go func(serviceName string) {
            defer wg.Done()
            sem <- struct{}{}
            defer func() { <-sem }()

            services, err := mlc.l3Cache.GetService(serviceName)
            if err != nil {
                errChan <- fmt.Errorf("预热服务 %s 失败: %w", serviceName, err)
                return
            }

            mlc.l1Cache.Set(serviceName, services, time.Minute*5)
            mlc.l2Cache.Set(ctx, serviceName, services, time.Minute*30)
            log.Printf("服务 %s 预热完成", serviceName)
        }(name)
    }

    wg.Wait()
    close(errChan)

    for err := range errChan {
        if err != nil {
            return err
        }
    }

    return nil
}
```

#### **智能服务路由**
```go
type SmartRouter struct {
    registry       registry.Registry
    loadBalancer   LoadBalancer
    healthChecker HealthChecker
    router        *RouterEngine
    metrics       *RouterMetrics
}

type RouteRule struct {
    ServiceName   string            `json:"service_name"`
    Weight       int               `json:"weight"`
    Conditions   []RouteCondition  `json:"conditions"`
    Priority     int               `json:"priority"`
    Metadata     map[string]string `json:"metadata"`
}

type RouteCondition struct {
    Field    string      `json:"field"`
    Operator string      `json:"operator"`
    Value    interface{} `json:"value"`
}

func (sr *SmartRouter) SelectService(ctx context.Context, serviceName string, request interface{}) (*registry.Service, error) {
    // 获取路由规则
    rules, err := sr.router.GetRules(serviceName)
    if err != nil {
        return nil, fmt.Errorf("获取路由规则失败: %w", err)
    }

    // 评估路由条件
    matchedRules := sr.evaluateRules(rules, request)
    if len(matchedRules) == 0 {
        // 没有匹配规则，使用默认负载均衡
        return sr.defaultSelect(serviceName)
    }

    // 根据权重选择规则
    selectedRule := sr.selectRuleByWeight(matchedRules)
    if selectedRule == nil {
        return sr.defaultSelect(serviceName)
    }

    // 应用路由策略
    return sr.applyRouteStrategy(ctx, selectedRule, serviceName)
}

func (sr *SmartRouter) evaluateRules(rules []RouteRule, request interface{}) []RouteRule {
    var matched []RouteRule

    for _, rule := range rules {
        if sr.matchConditions(rule.Conditions, request) {
            matched = append(matched, rule)
        }
    }

    // 按优先级排序
    sort.Slice(matched, func(i, j int) bool {
        return matched[i].Priority > matched[j].Priority
    })

    return matched
}

func (sr *SmartRouter) matchConditions(conditions []RouteCondition, request interface{}) bool {
    requestMap, ok := request.(map[string]interface{})
    if !ok {
        return false
    }

    for _, condition := range conditions {
        value, exists := requestMap[condition.Field]
        if !exists {
            return false
        }

        if !sr.compareValues(value, condition.Operator, condition.Value) {
            return false
        }
    }

    return true
}

func (sr *SmartRouter) compareValues(actual, operator string, expected interface{}) bool {
    switch operator {
    case "equals":
        return fmt.Sprintf("%v", actual) == fmt.Sprintf("%v", expected)
    case "not_equals":
        return fmt.Sprintf("%v", actual) != fmt.Sprintf("%v", expected)
    case "contains":
        return strings.Contains(fmt.Sprintf("%v", actual), fmt.Sprintf("%v", expected))
    case "in":
        expectedList, ok := expected.([]interface{})
        if !ok {
            return false
        }
        for _, item := range expectedList {
            if fmt.Sprintf("%v", actual) == fmt.Sprintf("%v", item) {
                return true
            }
        }
        return false
    default:
        return false
    }
}

// 灰度发布路由
func (sr *SmartRouter) CanaryRouting(ctx context.Context, serviceName string, userID string) (*registry.Service, error) {
    // 基于用户ID的灰度路由
    hash := fnv.New32a()
    hash.Write([]byte(userID))
    userHash := hash.Sum32()

    // 获取灰度配置
    canaryConfig, err := sr.router.GetCanaryConfig(serviceName)
    if err != nil {
        return sr.defaultSelect(serviceName)
    }

    // 计算灰度比例
    threshold := uint32(canaryConfig.Percentage * 100)
    if userHash%100 < threshold {
        // 走灰度服务
        return sr.selectServiceByVersion(serviceName, canaryConfig.CanaryVersion)
    }

    // 走稳定服务
    return sr.selectServiceByVersion(serviceName, canaryConfig.StableVersion)
}
```

#### **服务健康状态过滤**
```go
func (sw *ServiceWatcher) GetHealthyInstances(serviceName string) []*registry.Node {
    sw.mu.RLock()
    defer sw.mu.RUnlock()

    services, exists := sw.services[serviceName]
    if !exists {
        return nil
    }

    var healthyNodes []*registry.Node
    for _, service := range services {
        for _, node := range service.Nodes {
            if sw.isNodeHealthy(node) {
                healthyNodes = append(healthyNodes, node)
            }
        }
    }

    return healthyNodes
}

func (sw *ServiceWatcher) isNodeHealthy(node *registry.Node) bool {
    // 检查节点元数据中的健康状态
    if health, exists := node.Metadata["health"]; exists {
        return health == "healthy"
    }

    // 检查最近的心跳时间
    if lastHeartbeat, exists := node.Metadata["last_heartbeat"]; exists {
        if heartbeatTime, err := time.Parse(time.RFC3339, lastHeartbeat); err == nil {
            if time.Since(heartbeatTime) > 30*time.Second {
                return false
            }
        }
    }

    // 默认认为节点健康
    return true
}

// 动态健康检查调度器
type HealthScheduler struct {
    watcher      *ServiceWatcher
    interval     time.Duration
    stopChan     chan struct{}
    healthChecks map[string]HealthCheckFunc
    mu          sync.RWMutex
}

type HealthCheckFunc func(ctx context.Context, node *registry.Node) (bool, string)

func NewHealthScheduler(watcher *ServiceWatcher, interval time.Duration) *HealthScheduler {
    return &HealthScheduler{
        watcher:      watcher,
        interval:     interval,
        stopChan:     make(chan struct{}),
        healthChecks: make(map[string]HealthCheckFunc),
    }
}

func (hs *HealthScheduler) RegisterHealthCheck(serviceName string, checkFunc HealthCheckFunc) {
    hs.mu.Lock()
    defer hs.mu.Unlock()
    hs.healthChecks[serviceName] = checkFunc
}

func (hs *HealthScheduler) Start() {
    go func() {
        ticker := time.NewTicker(hs.interval)
        defer ticker.Stop()

        for {
            select {
            case <-ticker.C:
                hs.performHealthChecks()
            case <-hs.stopChan:
                return
            }
        }
    }()
}

func (hs *HealthScheduler) performHealthChecks() {
    hs.mu.RLock()
    defer hs.mu.RUnlock()

    for serviceName, checkFunc := range hs.healthChecks {
        go func(name string, check HealthCheckFunc) {
            ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
            defer cancel()

            instances := hs.watcher.GetServiceInstances(name)
            for _, instance := range instances {
                healthy, reason := checkFunc(ctx, instance)
                hs.watcher.UpdateHealthStatus(name, instance.Id, healthy, reason)
            }
        }(serviceName, checkFunc)
    }
}

func (hs *HealthScheduler) Stop() {
    close(hs.stopChan)
}

// 故障节点自动恢复机制
type FailureRecovery struct {
    watcher          *ServiceWatcher
    recoveryTimeout  time.Duration
    maxRetries      int
    recoveryAttempts map[string]int
    mu              sync.RWMutex
}

func NewFailureRecovery(watcher *ServiceWatcher, timeout time.Duration, maxRetries int) *FailureRecovery {
    return &FailureRecovery{
        watcher:          watcher,
        recoveryTimeout:  timeout,
        maxRetries:      maxRetries,
        recoveryAttempts: make(map[string]int),
    }
}

func (fr *FailureRecovery) MonitorRecovery(serviceName, nodeID string) {
    fr.mu.Lock()
    attempts := fr.recoveryAttempts[serviceName+nodeID]
    fr.mu.Unlock()

    if attempts >= fr.maxRetries {
        log.Printf("节点 %s-%s 已达到最大重试次数，停止恢复尝试", serviceName, nodeID)
        return
    }

    go func() {
        // 等待恢复超时
        time.Sleep(fr.recoveryTimeout)

        // 检查节点是否恢复
        if fr.watcher.CheckNodeRecovery(serviceName, nodeID) {
            fr.mu.Lock()
            delete(fr.recoveryAttempts, serviceName+nodeID)
            fr.mu.Unlock()

            log.Printf("节点 %s-%s 已自动恢复", serviceName, nodeID)
            return
        }

        // 记录恢复失败
        fr.mu.Lock()
        fr.recoveryAttempts[serviceName+nodeID]++
        fr.mu.Unlock()

        // 继续下一次恢复尝试
        fr.MonitorRecovery(serviceName, nodeID)
    }()
}
```

### 性能优化策略

#### **连接池管理**
```go
type ConnectionPool struct {
    pools  map[string]*connPool
    mu     sync.RWMutex
    maxConns int
}

type connPool struct {
    conns    chan *grpc.ClientConn
    createFn func() (*grpc.ClientConn, error)
}

func (cp *ConnectionPool) GetConnection(address string) (*grpc.ClientConn, error) {
    cp.mu.RLock()
    pool, exists := cp.pools[address]
    cp.mu.RUnlock()

    if !exists {
        cp.mu.Lock()
        pool = &connPool{
            conns:    make(chan *grpc.ClientConn, cp.maxConns),
            createFn: func() (*grpc.ClientConn, error) {
                return grpc.Dial(address, grpc.WithInsecure())
            },
        }
        cp.pools[address] = pool
        cp.mu.Unlock()
    }

    select {
    case conn := <-pool.conns:
        return conn, nil
    default:
        return pool.createFn()
    }
}
```

## 🔍 注册中心健康检查机制深度解析

### Consul 健康检查架构

Consul 的健康检查机制是其服务发现系统的核心组件，通过主动和被动相结合的方式，确保服务实例的可用性能够被及时发现。

### 默认健康检查机制详解

#### **HTTP 健康检查配置**
```go
package main

import (
    "log"
    "time"

    "github.com/go-micro/go-micro/v4"
    "github.com/go-micro/go-micro/v4/registry"
    "github.com/go-micro/plugins/v4/registry/consul"
)

type HealthCheckConfig struct {
    HTTP     string        `json:"http"`      // HTTP 检查地址
    Interval time.Duration `json:"interval"` // 检查间隔
    Timeout  time.Duration `json:"timeout"`  // 超时时间
    DeregisterCriticalServiceAfter time.Duration `json:"deregister_critical_service_after"`
}

func main() {
    // 创建 Consul 注册中心
    reg := consul.NewRegistry(
        registry.Addrs("127.0.0.1:8500"),
    )

    // 创建服务配置
    service := micro.NewService(
        micro.Name("user-service"),
        micro.Registry(reg),
        micro.RegisterTTL(time.Second*30), // 服务注册TTL
        micro.RegisterInterval(time.Second*15), // 重新注册间隔
    )

    // 获取服务节点信息
    node := ®istry.Node{
        Id:      "user-service-1",
        Address: "192.168.1.100",
        Port:    8080,
        Metadata: map[string]string{
            "health_check_url": "http://192.168.1.100:8080/health",
            "health_check_method": "GET",
            "health_check_interval": "10s",
            "health_check_timeout": "1s",
        },
    }

    // 注册健康检查
    if err := registerHealthCheck(reg, node); err != nil {
        log.Fatalf("注册健康检查失败: %v", err)
    }

    log.Println("服务已启动，健康检查已注册")
}

// 注册健康检查
func registerHealthCheck(reg registry.Registry, node *registry.Node) error {
    // 健康检查配置
    healthCheck := ®istry.HealthCheck{
        ID:                            node.Id + "-health",
        Name:                          node.Id + "-health",
        Interval:                       time.Second * 10,
        Timeout:                        time.Second * 1,
        DeregisterCriticalServiceAfter:    time.Minute * 5,
        HTTP:                          node.Metadata["health_check_url"],
        Method:                         node.Metadata["health_check_method"],
    }

    // 注册服务时包含健康检查
    service := ®istry.Service{
        Name:  "user-service",
        Nodes: []*registry.Node{node},
    }

    return reg.Register(service, registry.RegisterHealthCheck(healthCheck))
}
```

#### **健康检查端点实现**
```go
package main

import (
    "encoding/json"
    "net/http"
    "runtime"
    "time"

    "github.com/gorilla/mux"
)

type HealthStatus struct {
    Status    string    `json:"status"`
    Timestamp time.Time `json:"timestamp"`
    Version   string    `json:"version"`
    Uptime    int64     `json:"uptime"`
    Memory    Memory    `json:"memory"`
    Database  Database  `json:"database"`
    Cache     Cache     `json:"cache"`
}

type Memory struct {
    Alloc      uint64 `json:"alloc"`
    TotalAlloc uint64 `json:"total_alloc"`
    Sys        uint64 `json:"sys"`
    NumGC      uint32 `json:"num_gc"`
}

type Database struct {
    Status   string `json:"status"`
    Latency  int64  `json:"latency_ms"`
}

type Cache struct {
    Status   string `json:"status"`
    HitRate  float64 `json:"hit_rate"`
}

var startTime = time.Now()

func main() {
    r := mux.NewRouter()

    // 健康检查端点
    r.HandleFunc("/health", healthCheckHandler).Methods("GET")
    r.HandleFunc("/health/ready", readinessCheckHandler).Methods("GET")
    r.HandleFunc("/health/live", livenessCheckHandler).Methods("GET")

    srv := &http.Server{
        Addr:    ":8080",
        Handler: r,
    }

    log.Println("服务启动，监听端口 8080")
    log.Fatal(srv.ListenAndServe())
}

// 基础健康检查
func healthCheckHandler(w http.ResponseWriter, r *http.Request) {
    var m runtime.MemStats
    runtime.ReadMemStats(&m)

    status := HealthStatus{
        Status:    "healthy",
        Timestamp: time.Now(),
        Version:   "1.0.0",
        Uptime:    int64(time.Since(startTime).Seconds()),
        Memory: Memory{
            Alloc:      m.Alloc,
            TotalAlloc: m.TotalAlloc,
            Sys:        m.Sys,
            NumGC:      m.NumGC,
        },
        Database: checkDatabase(),
        Cache:    checkCache(),
    }

    // 根据组件状态判断整体健康状态
    if status.Database.Status != "healthy" || status.Cache.Status != "healthy" {
        status.Status = "unhealthy"
        w.WriteHeader(http.StatusServiceUnavailable)
    } else {
        w.WriteHeader(http.StatusOK)
    }

    json.NewEncoder(w).Encode(status)
}

// 就绪检查
func readinessCheckHandler(w http.ResponseWriter, r *http.Request) {
    // 检查依赖服务是否就绪
    if !isDatabaseReady() || !isCacheReady() {
        w.WriteHeader(http.StatusServiceUnavailable)
        json.NewEncoder(w).Encode(map[string]string{
            "status":  "not_ready",
            "message": "依赖服务未就绪",
        })
        return
    }

    w.WriteHeader(http.StatusOK)
    json.NewEncoder(w).Encode(map[string]string{
        "status": "ready",
    })
}

// 存活检查
func livenessCheckHandler(w http.ResponseWriter, r *http.Request) {
    // 简单的存活检查，返回200表示服务存活
    w.WriteHeader(http.StatusOK)
    json.NewEncoder(w).Encode(map[string]string{
        "status": "alive",
    })
}

func checkDatabase() Database {
    start := time.Now()
    // 模拟数据库连接检查
    // err := db.Ping()
    // if err != nil {
    //     return Database{Status: "unhealthy"}
    // }

    latency := time.Since(start).Milliseconds()
    return Database{
        Status:  "healthy",
        Latency: latency,
    }
}

func checkCache() Cache {
    // 模拟缓存连接检查
    return Cache{
        Status:  "healthy",
        HitRate: 0.95,
    }
}

func isDatabaseReady() bool {
    // 检查数据库是否就绪
    return true
}

func isCacheReady() bool {
    // 检查缓存是否就绪
    return true
}
```

### 高级健康检查策略

#### **多级健康检查**
```go
type HealthChecker struct {
    checks map[string]CheckFunc
    status map[string]string
    mu     sync.RWMutex
}

type CheckFunc func() (bool, string)

func NewHealthChecker() *HealthChecker {
    return &HealthChecker{
        checks: make(map[string]CheckFunc),
        status: make(map[string]string),
    }
}

// 注册检查项
func (hc *HealthChecker) RegisterCheck(name string, check CheckFunc) {
    hc.mu.Lock()
    defer hc.mu.Unlock()
    hc.checks[name] = check
}

// 执行所有检查
func (hc *HealthChecker) RunChecks() map[string]string {
    hc.mu.Lock()
    defer hc.mu.Unlock()

    for name, check := range hc.checks {
        if healthy, reason := check(); healthy {
            hc.status[name] = "healthy"
        } else {
            hc.status[name] = "unhealthy: " + reason
        }
    }

    return hc.status
}

// 获取整体状态
func (hc *HealthChecker) GetOverallStatus() string {
    hc.mu.RLock()
    defer hc.mu.RUnlock()

    for _, status := range hc.status {
        if status != "healthy" {
            return "unhealthy"
        }
    }
    return "healthy"
}

// 使用示例
func main() {
    healthChecker := NewHealthChecker()

    // 注册各种检查项
    healthChecker.RegisterCheck("database", checkDatabaseConnection)
    healthChecker.RegisterCheck("cache", checkCacheConnection)
    healthChecker.RegisterCheck("external_api", checkExternalAPI)
    healthChecker.RegisterCheck("disk_space", checkDiskSpace)
    healthChecker.RegisterCheck("memory_usage", checkMemoryUsage)

    // 定期执行健康检查
    go func() {
        ticker := time.NewTicker(30 * time.Second)
        defer ticker.Stop()

        for range ticker.C {
            results := healthChecker.RunChecks()
            overallStatus := healthChecker.GetOverallStatus()

            log.Printf("健康检查结果: %+v", results)
            log.Printf("整体状态: %s", overallStatus)

            // 如果状态不健康，可以触发告警
            if overallStatus == "unhealthy" {
                triggerAlert(results)
            }
        }
    }()
}

func checkDatabaseConnection() (bool, string) {
    // 实现数据库连接检查
    return true, ""
}

func checkCacheConnection() (bool, string) {
    // 实现缓存连接检查
    return true, ""
}

func checkExternalAPI() (bool, string) {
    // 实现外部API检查
    return true, ""
}

func checkDiskSpace() (bool, string) {
    // 实现磁盘空间检查
    return true, ""
}

func checkMemoryUsage() (bool, string) {
    // 实现内存使用检查
    return true, ""
}

func triggerAlert(results map[string]string) {
    // 触发告警逻辑
    log.Printf("系统告警: %+v", results)
}
```

#### **健康检查与负载均衡集成**
```go
type HealthAwareBalancer struct {
    registry    registry.Registry
    selector    selector.Selector
    healthCache *HealthCache
}

type HealthCache struct {
    services map[string]map[string]bool
    mu       sync.RWMutex
}

func NewHealthAwareBalancer(reg registry.Registry) *HealthAwareBalancer {
    return &HealthAwareBalancer{
        registry:    reg,
        selector:    selector.NewSelector(),
        healthCache: NewHealthCache(),
    }
}

func (hab *HealthAwareBalancer) Select(service string, opts ...selector.SelectOption) (next selector.Next, error) {
    // 获取服务节点
    services, err := hab.registry.GetService(service)
    if err != nil {
        return nil, err
    }

    // 过滤健康节点
    var healthyNodes []*registry.Node
    for _, svc := range services {
        for _, node := range svc.Nodes {
            if hab.healthCache.IsHealthy(service, node.Id) {
                healthyNodes = append(healthyNodes, node)
            }
        }
    }

    if len(healthyNodes) == 0 {
        return nil, fmt.Errorf("no healthy nodes available for service %s", service)
    }

    // 使用选择器选择节点
    return hab.selector.Select(service, opts...)
}

func (hab *HealthAwareBalancer) UpdateHealth(service, nodeID string, healthy bool) {
    hab.healthCache.Update(service, nodeID, healthy)
}

func NewHealthCache() *HealthCache {
    return &HealthCache{
        services: make(map[string]map[string]bool),
    }
}

func (hc *HealthCache) IsHealthy(service, nodeID string) bool {
    hc.mu.RLock()
    defer hc.mu.RUnlock()

    if nodes, exists := hc.services[service]; exists {
        if healthy, nodeExists := nodes[nodeID]; nodeExists {
            return healthy
        }
    }

    // 默认返回true，认为是健康的
    return true
}

func (hc *HealthCache) Update(service, nodeID string, healthy bool) {
    hc.mu.Lock()
    defer hc.mu.Unlock()

    if _, exists := hc.services[service]; !exists {
        hc.services[service] = make(map[string]bool)
    }

    hc.services[service][nodeID] = healthy
}
```

### 健康检查最佳实践

#### **智能健康检查策略**
```go
type AdaptiveHealthChecker struct {
    checkers        map[string]HealthChecker
    thresholds      map[string]HealthThreshold
    metrics         *HealthMetrics
    adaptivePolicy  *AdaptivePolicy
    mu              sync.RWMutex
}

type HealthThreshold struct {
    SuccessRate    float64 `json:"success_rate"`
    Latency        int64   `json:"latency_ms"`
    ErrorRate      float64 `json:"error_rate"`
    ConsecutiveFail int     `json:"consecutive_failures"`
}

type AdaptivePolicy struct {
    SampleSize       int           `json:"sample_size"`
    WindowSize       time.Duration `json:"window_size"`
    GracePeriod      time.Duration `json:"grace_period"`
    RampUpPeriod    time.Duration `json:"ramp_up_period"`
}

func (ahc *AdaptiveHealthChecker) EvaluateServiceHealth(serviceName string) HealthStatus {
    ahc.mu.RLock()
    checker, exists := ahc.checkers[serviceName]
    threshold := ahc.thresholds[serviceName]
    ahc.mu.RUnlock()

    if !exists {
        return HealthStatus{Status: "unknown"}
    }

    metrics := ahc.metrics.GetServiceMetrics(serviceName)

    // 基于多维度指标评估健康状态
    status := ahc.calculateHealthScore(metrics, threshold)

    // 应用自适应策略
    adjustedStatus := ahc.applyAdaptivePolicy(serviceName, status, metrics)

    return adjustedStatus
}

func (ahc *AdaptiveHealthChecker) calculateHealthScore(metrics *ServiceMetrics, threshold HealthThreshold) HealthStatus {
    score := 100.0

    // 成功率评分
    if metrics.SuccessRate < threshold.SuccessRate {
        score -= (threshold.SuccessRate - metrics.SuccessRate) * 100
    }

    // 延迟评分
    if metrics.AvgLatency > time.Duration(threshold.Latency)*time.Millisecond {
        latencyRatio := float64(metrics.AvgLatency) / float64(threshold.Latency*1000000)
        score -= math.Min(latencyRatio*10, 30)
    }

    // 错误率评分
    if metrics.ErrorRate > threshold.ErrorRate {
        score -= (metrics.ErrorRate - threshold.ErrorRate) * 50
    }

    // 连续失败惩罚
    if metrics.ConsecutiveFailures > threshold.ConsecutiveFail {
        score -= float64(metrics.ConsecutiveFailures - threshold.ConsecutiveFail) * 15
    }

    // 确定健康状态
    switch {
    case score >= 90:
        return HealthStatus{Status: "healthy", Score: score}
    case score >= 70:
        return HealthStatus{Status: "degraded", Score: score}
    case score >= 50:
        return HealthStatus{Status: "warning", Score: score}
    default:
        return HealthStatus{Status: "critical", Score: score}
    }
}

func (ahc *AdaptiveHealthChecker) applyAdaptivePolicy(serviceName string, status HealthStatus, metrics *ServiceMetrics) HealthStatus {
    policy := ahc.adaptivePolicy

    // 采样期判断
    if metrics.TotalRequests < policy.SampleSize {
        return HealthStatus{Status: "sampling", Score: status.Score}
    }

    // 缓存期策略
    if status.Status == "healthy" && metrics.Uptime < policy.GracePeriod {
        return HealthStatus{Status: "warming", Score: status.Score}
    }

    // 流量突增处理
    if metrics.RequestGrowth > 2.0 && status.Status != "critical" {
        return HealthStatus{Status: "scaling", Score: status.Score}
    }

    return status
}
```

#### **多层次健康检查架构**
```go
type MultiLevelHealthChecker struct {
    networkChecker   *NetworkHealthChecker
    applicationChecker *ApplicationHealthChecker
    dependencyChecker *DependencyHealthChecker
    resourceChecker  *ResourceHealthChecker
    coordinator     *HealthCoordinator
}

type HealthCoordinator struct {
    levels          map[string]HealthLevel
    weights         map[string]float64
    combinationRule  string // "weighted", "strict", "majority"
    cascadePolicy   CascadePolicy
}

type CascadePolicy struct {
    CriticalLevel  string   `json:"critical_level"`
    Affects        []string `json:"affects"`
    TriggerTimeout time.Duration `json:"trigger_timeout"`
}

func (mlhc *MultiLevelHealthChecker) GetCompositeHealth(serviceName string) (*CompositeHealthResult, error) {
    ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
    defer cancel()

    var wg sync.WaitGroup
    results := make(chan *LevelHealthResult, 4)

    // 并行执行各层级健康检查
    wg.Add(4)
    go mlhc.checkNetworkLevel(ctx, serviceName, &wg, results)
    go mlhc.checkApplicationLevel(ctx, serviceName, &wg, results)
    go mlhc.checkDependencyLevel(ctx, serviceName, &wg, results)
    go mlhc.checkResourceLevel(ctx, serviceName, &wg, results)

    go func() {
        wg.Wait()
        close(results)
    }()

    // 收集结果
    levelResults := make(map[string]*LevelHealthResult)
    for result := range results {
        levelResults[result.Level] = result
    }

    // 协调各层级结果
    return mlhc.coordinator.CoordinateResults(serviceName, levelResults)
}

// 网络层健康检查
func (mlhc *MultiLevelHealthChecker) checkNetworkLevel(ctx context.Context, serviceName string, wg *sync.WaitGroup, results chan<- *LevelHealthResult) {
    defer wg.Done()

    result := &LevelHealthResult{
        Level:     "network",
        Timestamp: time.Now(),
    }

    // TCP连接检查
    if err := mlhc.networkChecker.TCPConnectivity(ctx, serviceName); err != nil {
        result.Status = "unhealthy"
        result.Details = append(result.Details, fmt.Sprintf("TCP连接失败: %v", err))
        results <- result
        return
    }

    // DNS解析检查
    if err := mlhc.networkChecker.DNSResolution(ctx, serviceName); err != nil {
        result.Status = "degraded"
        result.Details = append(result.Details, fmt.Sprintf("DNS解析失败: %v", err))
    } else {
        result.Status = "healthy"
    }

    // 带宽测试
    bandwidth, err := mlhc.networkChecker.BandwidthTest(ctx, serviceName)
    if err == nil {
        result.Metrics = map[string]interface{}{
            "bandwidth_mbps": bandwidth,
        }
    }

    results <- result
}

// 应用层健康检查
func (mlhc *MultiLevelHealthChecker) checkApplicationLevel(ctx context.Context, serviceName string, wg *sync.WaitGroup, results chan<- *LevelHealthResult) {
    defer wg.Done()

    result := &LevelHealthResult{
        Level:     "application",
        Timestamp: time.Now(),
    }

    // HTTP健康检查
    httpStatus, latency, err := mlhc.applicationChecker.HTTPHealthCheck(ctx, serviceName)
    if err != nil {
        result.Status = "unhealthy"
        result.Details = append(result.Details, fmt.Sprintf("HTTP健康检查失败: %v", err))
        results <- result
        return
    }

    // 应用指标收集
    metrics, err := mlhc.applicationChecker.GetApplicationMetrics(ctx, serviceName)
    if err != nil {
        result.Status = "degraded"
        result.Details = append(result.Details, fmt.Sprintf("应用指标收集失败: %v", err))
    } else {
        result.Status = mlhc.evaluateApplicationHealth(httpStatus, metrics)
        result.Metrics = metrics
    }

    result.Metrics["http_status"] = httpStatus
    result.Metrics["latency_ms"] = latency.Milliseconds()

    results <- result
}

// 依赖层健康检查
func (mlhc *MultiLevelHealthChecker) checkDependencyLevel(ctx context.Context, serviceName string, wg *sync.WaitGroup, results chan<- *LevelHealthResult) {
    defer wg.Done()

    result := &LevelHealthResult{
        Level:     "dependency",
        Timestamp: time.Now(),
    }

    dependencies, err := mlhc.dependencyChecker.GetDependencies(serviceName)
    if err != nil {
        result.Status = "unknown"
        result.Details = append(result.Details, fmt.Sprintf("获取依赖列表失败: %v", err))
        results <- result
        return
    }

    var healthyCount, totalCount int
    dependencyStatus := make(map[string]interface{})

    for _, dep := range dependencies {
        depHealth, err := mlhc.dependencyChecker.CheckDependencyHealth(ctx, dep)
        if err != nil {
            dependencyStatus[dep.Name] = map[string]interface{}{
                "status": "unhealthy",
                "error":  err.Error(),
            }
        } else {
            dependencyStatus[dep.Name] = depHealth
            if depHealth.Status == "healthy" {
                healthyCount++
            }
        }
        totalCount++
    }

    if totalCount == 0 {
        result.Status = "healthy"
    } else {
        healthRatio := float64(healthyCount) / float64(totalCount)
        switch {
        case healthRatio >= 0.9:
            result.Status = "healthy"
        case healthRatio >= 0.7:
            result.Status = "degraded"
        case healthRatio >= 0.5:
            result.Status = "warning"
        default:
            result.Status = "unhealthy"
        }
    }

    result.Metrics = map[string]interface{}{
        "dependencies": dependencyStatus,
        "healthy_ratio":  float64(healthyCount) / float64(totalCount),
    }

    results <- result
}

// 资源层健康检查
func (mlhc *MultiLevelHealthChecker) checkResourceLevel(ctx context.Context, serviceName string, wg *sync.WaitGroup, results chan<- *LevelHealthResult) {
    defer wg.Done()

    result := &LevelHealthResult{
        Level:     "resource",
        Timestamp: time.Now(),
    }

    // CPU使用率
    cpuUsage, err := mlhc.resourceChecker.GetCPUUsage(ctx, serviceName)
    if err != nil {
        result.Status = "unknown"
        result.Details = append(result.Details, fmt.Sprintf("CPU使用率获取失败: %v", err))
    }

    // 内存使用率
    memUsage, err := mlhc.resourceChecker.GetMemoryUsage(ctx, serviceName)
    if err != nil {
        result.Status = "unknown"
        result.Details = append(result.Details, fmt.Sprintf("内存使用率获取失败: %v", err))
    }

    // 磁盘使用率
    diskUsage, err := mlhc.resourceChecker.GetDiskUsage(ctx, serviceName)
    if err != nil {
        result.Status = "unknown"
        result.Details = append(result.Details, fmt.Sprintf("磁盘使用率获取失败: %v", err))
    }

    if result.Status == "unknown" && len(result.Details) == 0 {
        result.Status = mlhc.evaluateResourceHealth(cpuUsage, memUsage, diskUsage)
    }

    result.Metrics = map[string]interface{}{
        "cpu_usage_percent":    cpuUsage,
        "memory_usage_percent": memUsage,
        "disk_usage_percent":   diskUsage,
    }

    results <- result
}
```

#### **优雅降级策略**
```go
type GracefulDegradation struct {
    service         *micro.Service
    healthChecker   *HealthChecker
    degradedMode    bool
    mu             sync.RWMutex
    degradationRules []DegradationRule
    rollbackPlan    *RollbackPlan
    metrics        *DegradationMetrics
}

type DegradationRule struct {
    Name           string
    CheckFunc      func() bool
    DegradationFunc func()
    Priority       int
    Timeout        time.Duration
    RollbackFunc   func()
}

type RollbackPlan struct {
    Steps         []RollbackStep
    CheckInterval  time.Duration
    MaxRetries    int
}

type RollbackStep struct {
    Name          string
    ExecuteFunc   func() error
    ValidateFunc  func() bool
    Timeout       time.Duration
}

func (gd *GracefulDegradation) Start() {
    go func() {
        ticker := time.NewTicker(10 * time.Second)
        defer ticker.Stop()

        for range ticker.C {
            gd.checkAndDegrade()
        }
    }()
}

func (gd *GracefulDegradation) checkAndDegrade() {
    results := gd.healthChecker.RunChecks()
    overallStatus := gd.healthChecker.GetOverallStatus()

    gd.mu.Lock()
    defer gd.mu.Unlock()

    if overallStatus == "healthy" && gd.degradedMode {
        // 恢复正常模式
        gd.recoverFromDegradation()
    } else if overallStatus == "unhealthy" && !gd.degradedMode {
        // 进入降级模式
        gd.enterDegradationMode(results)
    } else if overallStatus == "degraded" && !gd.degradedMode {
        // 部分降级
        gd.enterPartialDegradation(results)
    }
}

func (gd *GracefulDegradation) enterDegradationMode(results map[string]string) {
    log.Println("进入降级模式")
    gd.degradedMode = true

    // 按优先级执行降级规则
    sort.Slice(gd.degradationRules, func(i, j int) bool {
        return gd.degradationRules[i].Priority > gd.degradationRules[j].Priority
    })

    for _, rule := range gd.degradationRules {
        if !rule.CheckFunc() {
            log.Printf("执行降级规则: %s", rule.Name)

            // 超时控制
            timeoutCtx, cancel := context.WithTimeout(context.Background(), rule.Timeout)
            defer cancel()

            done := make(chan struct{})
            go func() {
                rule.DegradationFunc()
                close(done)
            }()

            select {
            case <-done:
                log.Printf("降级规则 %s 执行完成", rule.Name)
                gd.metrics.RecordDegradation(rule.Name, "success")
            case <-timeoutCtx.Done():
                log.Printf("降级规则 %s 执行超时", rule.Name)
                gd.metrics.RecordDegradation(rule.Name, "timeout")

                // 执行回滚
                if rule.RollbackFunc != nil {
                    go rule.RollbackFunc()
                }
            }
        }
    }

    // 发送告警
    gd.sendAlert(results)
}

func (gd *GracefulDegradation) enterPartialDegradation(results map[string]string) {
    log.Println("进入部分降级模式")

    // 仅执行关键降级规则
    for _, rule := range gd.degradationRules {
        if rule.Priority >= 10 && !rule.CheckFunc() {
            log.Printf("执行关键降级规则: %s", rule.Name)
            rule.DegradationFunc()
            gd.metrics.RecordDegradation(rule.Name, "partial")
        }
    }
}

func (gd *GracefulDegradation) recoverFromDegradation() {
    log.Println("从降级模式恢复")
    gd.degradedMode = false

    // 执行回滚计划
    if gd.rollbackPlan != nil {
        success := gd.executeRollbackPlan()
        if !success {
            log.Println("回滚计划执行失败，保持降级模式")
            gd.degradedMode = true
            return
        }
    }

    // 恢复服务
    gd.recoverServices()
    gd.sendRecoveryNotification()
    gd.metrics.RecordRecovery()
}

func (gd *GracefulDegradation) executeRollbackPlan() bool {
    for _, step := range gd.rollbackPlan.Steps {
        for attempt := 0; attempt < gd.rollbackPlan.MaxRetries; attempt++ {
            timeoutCtx, cancel := context.WithTimeout(context.Background(), step.Timeout)
            defer cancel()

            done := make(chan struct{})
            errChan := make(chan error, 1)

            go func() {
                if err := step.ExecuteFunc(); err != nil {
                    errChan <- err
                } else {
                    close(done)
                }
            }()

            select {
            case <-done:
                // 验证回滚结果
                if step.ValidateFunc() {
                    log.Printf("回滚步骤 %s 执行成功", step.Name)
                    break
                }
                log.Printf("回滚步骤 %s 验证失败，重试中...", step.Name)

            case <-timeoutCtx.Done():
                log.Printf("回滚步骤 %s 执行超时", step.Name)
                return false

            case err := <-errChan:
                log.Printf("回滚步骤 %s 执行失败: %v", step.Name, err)
                if attempt == gd.rollbackPlan.MaxRetries-1 {
                    return false
                }
            }

            time.Sleep(gd.rollbackPlan.CheckInterval)
        }
    }

    return true
}
```

这些健康检查机制确保了 Go Micro 服务的可用性和稳定性，通过多层次、多角度的健康监控，及时发现和处理服务异常，为生产环境提供了强大的保障。

## ⚖️ 客户端负载均衡策略深度解析

### 负载均衡架构概述

Go Micro 的客户端负载均衡采用**选择器模式**（Selector Pattern），它位于客户端和服务发现层之间，负责从多个可用服务实例中选择最优的一个进行请求分发。

### 核心负载均衡策略

#### **1. Round-Robin 轮询策略**
```go
package balancer

import (
    "github.com/go-micro/go-micro/v4/selector"
    "github.com/go-micro/go-micro/v4/registry"
)

type RoundRobinBalancer struct {
    index map[string]int
    mu    sync.RWMutex
}

func NewRoundRobinBalancer() selector.Balancer {
    return &RoundRobinBalancer{
        index: make(map[string]int),
    }
}

func (r *RoundRobinBalancer) Select(service string, nodes []*registry.Node) (*registry.Node, error) {
    if len(nodes) == 0 {
        return nil, selector.ErrNoneAvailable
    }

    r.mu.Lock()
    defer r.mu.Unlock()

    // 获取当前服务的索引
    currentIndex := r.index[service]
    selectedIndex := currentIndex % len(nodes)

    // 更新索引
    r.index[service] = currentIndex + 1

    return nodes[selectedIndex], nil
}

func (r *RoundRobinBalancer) String() string {
    return "roundrobin"
}

// 使用示例
func main() {
    // 创建选择器并设置轮询均衡器
    selector := selector.NewSelector(
        selector.SetBalancer(NewRoundRobinBalancer()),
    )

    service := micro.NewService(
        micro.Name("client-service"),
        micro.Selector(selector),
    )

    // 进行服务调用
    client := service.Client()
    response := proto.UserResponse{}
    err := client.Call(context.Background(),
        "user-service",
        "GetUser",
        &proto.UserRequest{UserId: "123"},
        &response)
}
```

#### **2. Random 随机策略**
```go
type RandomBalancer struct{}

func NewRandomBalancer() selector.Balancer {
    return &RandomBalancer{}
}

func (r *RandomBalancer) Select(service string, nodes []*registry.Node) (*registry.Node, error) {
    if len(nodes) == 0 {
        return nil, selector.ErrNoneAvailable
    }

    // 随机选择节点
    randomIndex := rand.Intn(len(nodes))
    return nodes[randomIndex], nil
}

func (r *RandomBalancer) String() string {
    return "random"
}
```

#### **3. Least Connection 最少连接策略**
```go
type ConnectionTracker struct {
    connections map[string]int // service -> nodeID -> connectionCount
    mu           sync.RWMutex
}

type LeastConnectionBalancer struct {
    tracker *ConnectionTracker
}

func NewLeastConnectionBalancer() *LeastConnectionBalancer {
    return &LeastConnectionBalancer{
        tracker: NewConnectionTracker(),
    }
}

func (l *LeastConnectionBalancer) Select(service string, nodes []*registry.Node) (*registry.Node, error) {
    if len(nodes) == 0 {
        return nil, selector.ErrNoneAvailable
    }

    // 获取每个节点的连接数
    var nodeStats []*NodeStats
    for _, node := range nodes {
        connections := l.tracker.GetConnectionCount(service, node.Id)
        nodeStats = append(nodeStats, &NodeStats{
            Node:        node,
            Connections: connections,
        })
    }

    // 按连接数排序
    sort.Slice(nodeStats, func(i, j int) bool {
        return nodeStats[i].Connections < nodeStats[j].Connections
    })

    return nodeStats[0].Node, nil
}

func (l *LeastConnectionBalancer) String() string {
    return "least-connection"
}

type NodeStats struct {
    Node        *registry.Node
    Connections int
}

type ConnectionTracker struct {
    connections map[string]map[string]int // service -> nodeID -> connectionCount
    mu           sync.RWMutex
}

func NewConnectionTracker() *ConnectionTracker {
    return &ConnectionTracker{
        connections: make(map[string]map[string]int),
    }
}

func (ct *ConnectionTracker) Increment(service, nodeID string) {
    ct.mu.Lock()
    defer ct.mu.Unlock()

    if _, exists := ct.connections[service]; !exists {
        ct.connections[service] = make(map[string]int)
    }

    ct.connections[service][nodeID]++
}

func (ct *ConnectionTracker) Decrement(service, nodeID string) {
    ct.mu.Lock()
    defer ct.mu.Unlock()

    if _, exists := ct.connections[service]; exists {
        if count, nodeExists := ct.connections[service][nodeID]; nodeExists && count > 0 {
            ct.connections[service][nodeID]--
        }
    }
}

func (ct *ConnectionTracker) GetConnectionCount(service, nodeID string) int {
    ct.mu.RLock()
    defer ct.mu.RUnlock()

    if _, exists := ct.connections[service]; exists {
        return ct.connections[service][nodeID]
    }

    return 0
}
```

#### **4. Weighted 加权策略**
```go
type WeightedBalancer struct {
    weightCalculator WeightCalculator
}

type WeightCalculator interface {
    CalculateWeight(node *registry.Node) int
}

type NodeWeightCalculator struct{}

func (n *NodeWeightCalculator) CalculateWeight(node *registry.Node) int {
    // 从节点元数据中获取权重
    if weightStr, exists := node.Metadata["weight"]; exists {
        if weight, err := strconv.Atoi(weightStr); err == nil {
            return weight
        }
    }

    // 默认权重
    return 1
}

func NewWeightedBalancer(calculator WeightCalculator) *WeightedBalancer {
    if calculator == nil {
        calculator = &NodeWeightCalculator{}
    }
    return &WeightedBalancer{
        weightCalculator: calculator,
    }
}

func (w *WeightedBalancer) Select(service string, nodes []*registry.Node) (*registry.Node, error) {
    if len(nodes) == 0 {
        return nil, selector.ErrNoneAvailable
    }

    // 计算总权重
    var totalWeight int
    var weightedNodes []*WeightedNode
    for _, node := range nodes {
        weight := w.weightCalculator.CalculateWeight(node)
        totalWeight += weight
        weightedNodes = append(weightedNodes, &WeightedNode{
            Node:   node,
            Weight: weight,
        })
    }

    if totalWeight == 0 {
        return nil, selector.ErrNoneAvailable
    }

    // 生成随机数选择节点
    randomWeight := rand.Intn(totalWeight)
    currentWeight := 0

    for _, weightedNode := range weightedNodes {
        currentWeight += weightedNode.Weight
        if randomWeight < currentWeight {
            return weightedNode.Node, nil
        }
    }

    return weightedNodes[len(weightedNodes)-1].Node, nil
}

func (w *WeightedBalancer) String() string {
    return "weighted"
}

type WeightedNode struct {
    Node   *registry.Node
    Weight int
}
```

### 高级负载均衡特性

#### **自适应延迟感知负载均衡**
```go
type AdaptiveLatencyBalancer struct {
    latencyTracker    *AdaptiveLatencyTracker
    regionAwareness  *RegionAwareness
    congestionControl *CongestionControl
    trendAnalyzer    *TrendAnalyzer
    metrics         *BalancerMetrics
}

type AdaptiveLatencyTracker struct {
    latencies       map[string]map[string]*LatencyWindow // service -> nodeID -> latency window
    weights         map[string]map[string]float64        // service -> nodeID -> dynamic weight
    regionLatencies map[string]map[string]time.Duration // region -> service -> avg latency
    mu              sync.RWMutex
    windowSize      int
    sampleInterval time.Duration
}

type LatencyWindow struct {
    samples []time.Duration
    mean     time.Duration
    stdDev   time.Duration
    trend    string // "improving", "stable", "degrading"
    updated  time.Time
}

type CongestionControl struct {
    thresholds      map[string]int64 // nodeID -> current threshold
    backpressure    map[string]bool // nodeID -> under backpressure
    recoveryTime    map[string]time.Time
    adaptiveWindow  bool
    minThreshold   int64
    maxThreshold   int64
}

func NewAdaptiveLatencyBalancer() *AdaptiveLatencyBalancer {
    return &AdaptiveLatencyBalancer{
        latencyTracker:    NewAdaptiveLatencyTracker(20, time.Second*30),
        regionAwareness:  NewRegionAwareness(),
        congestionControl: NewCongestionControl(true),
        trendAnalyzer:    NewTrendAnalyzer(),
        metrics:         NewBalancerMetrics(),
    }
}

func (alb *AdaptiveLatencyBalancer) Select(service string, nodes []*registry.Node) (*registry.Node, error) {
    if len(nodes) == 0 {
        return nil, selector.ErrNoneAvailable
    }

    // 获取节点性能指标
    nodeScores := make([]*NodeScore, 0, len(nodes))
    for _, node := range nodes {
        score := alb.calculateNodeScore(service, node)
        nodeScores = append(nodeScores, score)
    }

    // 按综合评分排序
    sort.Slice(nodeScores, func(i, j int) bool {
        return nodeScores[i].TotalScore > nodeScores[j].TotalScore
    })

    // 应用拥塞控制
    selected := alb.applyCongestionControl(service, nodeScores)
    if selected == nil {
        return nil, selector.ErrNoneAvailable
    }

    log.Printf("选择最优节点: %s (评分: %.2f, 延迟: %v, 拥塞度: %.2f)",
        selected.Node.Id, selected.TotalScore, selected.Latency, selected.CongestionScore)

    return selected.Node, nil
}

func (alb *AdaptiveLatencyBalancer) calculateNodeScore(service string, node *registry.Node) *NodeScore {
    score := &NodeScore{
        Node:     node,
        Latency:  alb.latencyTracker.GetAverageLatency(service, node.Id),
    }

    // 延迟评分 (权重 40%)
    latencyScore := alb.calculateLatencyScore(service, node)

    // 拥塞控制评分 (权重 30%)
    congestionScore := alb.calculateCongestionScore(node)

    // 区域感知评分 (权重 20%)
    regionScore := alb.regionAwareness.CalculateRegionScore(node)

    // 趋势评分 (权重 10%)
    trendScore := alb.trendAnalyzer.CalculateTrendScore(service, node.Id)

    // 综合评分计算
    score.TotalScore = latencyScore*0.4 + congestionScore*0.3 + regionScore*0.2 + trendScore*0.1
    score.LatencyScore = latencyScore
    score.CongestionScore = congestionScore
    score.RegionScore = regionScore
    score.TrendScore = trendScore

    return score
}

func (alb *AdaptiveLatencyBalancer) calculateLatencyScore(service string, node *registry.Node) float64 {
    latency := alb.latencyTracker.GetAverageLatency(service, node.Id)
    if latency == 0 {
        return 1.0
    }

    // 使用对数函数将延迟映射到0-1分，延迟越低分数越高
    maxLatency := 5 * time.Second
    if latency >= maxLatency {
        return 0.1
    }

    return math.Log(float64(maxLatency/latency)) / math.Log(float64(maxLatency/time.Millisecond))
}

func (alb *AdaptiveLatencyBalancer) calculateCongestionScore(node *registry.Node) float64 {
    congestionLevel := alb.congestionControl.GetCongestionLevel(node.Id)

    // 拥塞程度越高，分数越低
    switch congestionLevel {
    case "low":
        return 1.0
    case "medium":
        return 0.6
    case "high":
        return 0.3
    case "critical":
        return 0.1
    default:
        return 0.8
    }
}

func (alb *AdaptiveLatencyBalancer) applyCongestionControl(service string, nodes []*NodeScore) *NodeScore {
    alb.congestionControl.UpdateThresholds(nodes)

    // 过滤掉处于严重拥塞状态的节点
    var availableNodes []*NodeScore
    for _, node := range nodes {
        if !alb.congestionControl.IsUnderBackpressure(node.Node.Id) {
            availableNodes = append(availableNodes, node)
        }
    }

    if len(availableNodes) == 0 {
        // 如果所有节点都拥塞，选择拥塞程度最轻的
        return nodes[0]
    }

    return availableNodes[0]
}

func NewAdaptiveLatencyTracker(windowSize int, sampleInterval time.Duration) *AdaptiveLatencyTracker {
    return &AdaptiveLatencyTracker{
        latencies:       make(map[string]map[string]*LatencyWindow),
        weights:         make(map[string]map[string]float64),
        regionLatencies: make(map[string]map[string]time.Duration),
        windowSize:      windowSize,
        sampleInterval:  sampleInterval,
    }
}

func (alt *AdaptiveLatencyTracker) Record(service, nodeID string, latency time.Duration) {
    alt.mu.Lock()
    defer alt.mu.Unlock()

    key := service + ":" + nodeID
    if _, exists := alt.latencies[service]; !exists {
        alt.latencies[service] = make(map[string]*LatencyWindow)
    }

    window, exists := alt.latencies[service][nodeID]
    if !exists {
        window = &LatencyWindow{
            samples: make([]time.Duration, 0, alt.windowSize),
            updated: time.Now(),
        }
        alt.latencies[service][nodeID] = window
    }

    // 添加新样本
    window.samples = append(window.samples, latency)

    // 保持窗口大小
    if len(window.samples) > alt.windowSize {
        window.samples = window.samples[1:]
    }

    // 计算统计指标
    alt.updateWindowStatistics(window)

    // 更新区域延迟
    if region := alt.getNodeRegion(nodeID); region != "" {
        alt.updateRegionLatency(region, service, latency)
    }
}

func (alt *AdaptiveLatencyTracker) updateWindowStatistics(window *LatencyWindow) {
    if len(window.samples) == 0 {
        return
    }

    // 计算平均值
    var total time.Duration
    for _, sample := range window.samples {
        total += sample
    }
    window.mean = total / time.Duration(len(window.samples))

    // 计算标准差
    if len(window.samples) > 1 {
        var variance float64
        for _, sample := range window.samples {
            diff := float64(sample - window.mean)
            variance += diff * diff
        }
        variance /= float64(len(window.samples))
        window.stdDev = time.Duration(math.Sqrt(variance))
    }

    // 分析趋势
    window.trend = alt.analyzeTrend(window.samples)
    window.updated = time.Now()
}

func (alt *AdaptiveLatencyTracker) analyzeTrend(samples []time.Duration) string {
    if len(samples) < 3 {
        return "stable"
    }

    // 简单的线性回归分析趋势
    n := len(samples)
    sumX := float64(n * (n - 1) / 2)
    sumY := 0.0
    sumXY := 0.0
    sumXX := 0.0

    for i, sample := range samples {
        x := float64(i)
        y := float64(sample)
        sumY += y
        sumXY += x * y
        sumXX += x * x
    }

    slope := (float64(n)*sumXY - sumX*sumY) / (float64(n)*sumXX - sumX*sumX)

    // 根据斜率判断趋势
    if slope > -1000000 { // 下降趋势
        return "improving"
    } else if slope < 1000000 { // 上升趋势
        return "degrading"
    }
    return "stable"
}

type NodeScore struct {
    Node            *registry.Node
    TotalScore      float64
    LatencyScore    float64
    CongestionScore float64
    RegionScore     float64
    TrendScore      float64
    Latency         time.Duration
}

// 动态权重调整算法
type DynamicWeightAdjuster struct {
    balancer        *AdaptiveLatencyBalancer
    adjustmentRules []WeightAdjustmentRule
    metrics        *WeightMetrics
    adjustmentLock sync.RWMutex
}

type WeightAdjustmentRule struct {
    Condition     func(*NodeScore) bool
    Adjustment    func(*NodeScore) float64
    Priority      int
    Description   string
}

func (dwa *DynamicWeightAdjuster) AdjustWeights(service string, nodes []*registry.Node) {
    dwa.adjustmentLock.Lock()
    defer dwa.adjustmentLock.Unlock()

    // 计算当前节点评分
    nodeScores := make([]*NodeScore, len(nodes))
    for i, node := range nodes {
        nodeScores[i] = dwa.balancer.calculateNodeScore(service, node)
    }

    // 应用权重调整规则
    for _, score := range nodeScores {
        for _, rule := range dwa.adjustmentRules {
            if rule.Condition(score) {
                newWeight := rule.Adjustment(score)
                dwa.balancer.latencyTracker.UpdateWeight(service, score.Node.Id, newWeight)
                log.Printf("权重调整: %s -> %.2f (规则: %s)", score.Node.Id, newWeight, rule.Description)
                break
            }
        }
    }
}

func (dwa *DynamicWeightAdjuster) AddRule(rule WeightAdjustmentRule) {
    dwa.adjustmentRules = append(dwa.adjustmentRules, rule)
    // 按优先级排序
    sort.Slice(dwa.adjustmentRules, func(i, j int) bool {
        return dwa.adjustmentRules[i].Priority > dwa.adjustmentRules[j].Priority
    })
}
```

#### **智能熔断器集成**
```go
type SmartCircuitBreakerBalancer struct {
    breaker      *AdaptiveCircuitBreaker
    childBalancer selector.Balancer
    metrics      *CircuitBreakerMetrics
    policy       *CircuitBreakerPolicy
}

type AdaptiveCircuitBreaker struct {
    states           map[string]*BreakerState      // service -> state
    healthMetrics    map[string]*HealthMetrics    // service -> metrics
    recoveryStrategies map[string]RecoveryStrategy // service -> recovery strategy
    mu               sync.RWMutex
    config           *CircuitBreakerConfig
}

type BreakerState struct {
    State           string    // "open", "closed", "half-open"
    Failures        int
    LastFailure     time.Time
    RecoveryCount   int
    SuccessRate     float64
    LatencyPercentile time.Duration
}

type CircuitBreakerConfig struct {
    MaxFailures          int           `json:"max_failures"`
    Timeout              time.Duration `json:"timeout"`
    HalfOpenRequests    int           `json:"half_open_requests"`
    SuccessThreshold    float64       `json:"success_threshold"`
    RecoveryDelay       time.Duration `json:"recovery_delay"`
    LatencyThreshold    time.Duration `json:"latency_threshold"`
}

type HealthMetrics struct {
    TotalRequests     int64
    SuccessRequests   int64
    FailedRequests    int64
    LatencySamples    []time.Duration
    ErrorRate        float64
    LastUpdated      time.Time
}

func NewSmartCircuitBreakerBalancer(balancer selector.Balancer) *SmartCircuitBreakerBalancer {
    return &SmartCircuitBreakerBalancer{
        childBalancer: balancer,
        breaker:      NewAdaptiveCircuitBreaker(&CircuitBreakerConfig{
            MaxFailures:       5,
            Timeout:           time.Minute,
            HalfOpenRequests: 3,
            SuccessThreshold: 0.6,
            RecoveryDelay:    time.Second * 30,
            LatencyThreshold: time.Second * 2,
        }),
        metrics: NewCircuitBreakerMetrics(),
        policy:  NewCircuitBreakerPolicy(),
    }
}

func (scb *SmartCircuitBreakerBalancer) Select(service string, nodes []*registry.Node) (*registry.Node, error) {
    // 检查熔断器状态
    state := scb.breaker.GetState(service)
    switch state.State {
    case "open":
        return nil, fmt.Errorf("circuit breaker open for service %s", service)
    case "half-open":
        // 半开状态下只允许少量请求
        if !scb.shouldAllowHalfOpenRequest(service) {
            return nil, fmt.Errorf("circuit breaker half-open, rejecting request for service %s", service)
        }
    }

    // 使用子均衡器选择节点
    node, err := scb.childBalancer.Select(service, nodes)
    if err != nil {
        scb.breaker.RecordFailure(service, err)
        return nil, err
    }

    return node, nil
}

func (scb *SmartCircuitBreakerBalancer) RecordSuccess(service string, latency time.Duration) {
    scb.breaker.RecordSuccess(service, latency)
}

func (scb *SmartCircuitBreakerBalancer) RecordFailure(service string, err error) {
    scb.breaker.RecordFailure(service, err)
}

func (scb *SmartCircuitBreakerBalancer) shouldAllowHalfOpenRequest(service string) bool {
    scb.breaker.mu.RLock()
    defer scb.breaker.mu.RUnlock()

    state := scb.breaker.states[service]
    if state == nil || state.State != "half-open" {
        return false
    }

    // 检查是否超过半开状态的最大请求数
    if state.RecoveryCount >= scb.breaker.config.HalfOpenRequests {
        return false
    }

    return true
}

func NewAdaptiveCircuitBreaker(config *CircuitBreakerConfig) *AdaptiveCircuitBreaker {
    return &AdaptiveCircuitBreaker{
        states:           make(map[string]*BreakerState),
        healthMetrics:    make(map[string]*HealthMetrics),
        recoveryStrategies: make(map[string]RecoveryStrategy),
        config:           config,
    }
}

func (acb *AdaptiveCircuitBreaker) RecordSuccess(service string, latency time.Duration) {
    acb.mu.Lock()
    defer acb.mu.Unlock()

    state := acb.getOrCreateState(service)
    metrics := acb.getOrCreateMetrics(service)

    // 更新指标
    metrics.TotalRequests++
    metrics.SuccessRequests++
    metrics.LatencySamples = append(metrics.LatencySamples, latency)
    metrics.LastUpdated = time.Now()

    // 更新状态
    if state.State == "half-open" {
        state.RecoveryCount++
        // 计算成功率
        successRate := float64(state.RecoveryCount) / float64(acb.config.HalfOpenRequests)
        state.SuccessRate = successRate

        if successRate >= acb.config.SuccessThreshold {
            // 恢复到关闭状态
            state.State = "closed"
            state.RecoveryCount = 0
            log.Printf("熔断器恢复到关闭状态 for service %s", service)
        }
    } else {
        state.Failures = 0
        state.State = "closed"
    }

    // 更新延迟百分位
    acb.updateLatencyPercentile(service)
}

func (acb *AdaptiveCircuitBreaker) RecordFailure(service string, err error) {
    acb.mu.Lock()
    defer acb.mu.Unlock()

    state := acb.getOrCreateState(service)
    metrics := acb.getOrCreateMetrics(service)

    // 更新指标
    metrics.TotalRequests++
    metrics.FailedRequests++
    metrics.LastUpdated = time.Now()
    metrics.ErrorRate = float64(metrics.FailedRequests) / float64(metrics.TotalRequests)

    // 更新状态
    state.Failures++
    state.LastFailure = time.Now()

    if state.Failures >= acb.config.MaxFailures {
        // 检查是否需要自适应调整阈值
        if acb.shouldAdaptThreshold(service, metrics) {
            acb.adaptThreshold(service, metrics)
        }

        state.State = "open"
        state.RecoveryCount = 0
        log.Printf("熔断器开启 for service %s (失败次数: %d)", service, state.Failures)
    }
}

func (acb *AdaptiveCircuitBreaker) shouldAdaptThreshold(service string, metrics *HealthMetrics) bool {
    // 基于错误率和延迟趋势判断是否需要调整阈值
    if metrics.TotalRequests < 100 {
        return false // 样本不足，不调整
    }

    errorRate := metrics.ErrorRate
    if errorRate > 0.8 {
        return true // 错误率过高，需要调整
    }

    avgLatency := acb.calculateAverageLatency(metrics.LatencySamples)
    if avgLatency > acb.config.LatencyThreshold*2 {
        return true // 延迟过高，需要调整
    }

    return false
}

func (acb *AdaptiveCircuitBreaker) adaptThreshold(service string, metrics *HealthMetrics) {
    state := acb.states[service]
    if state == nil {
        return
    }

    // 降低最大失败次数阈值，避免频繁熔断
    newMaxFailures := max(acb.config.MaxFailures/2, 2)
    log.Printf("自适应调整熔断器阈值: %s -> %d", service, newMaxFailures)

    // 更新配置
    acb.config.MaxFailures = newMaxFailures
    state.Failures = 0 // 重置失败次数
}

func (acb *AdaptiveCircuitBreaker) GetState(service string) *BreakerState {
    acb.mu.RLock()
    defer acb.mu.RUnlock()

    if state, exists := acb.states[service]; exists {
        // 检查是否需要从开启状态转为半开
        if state.State == "open" {
            recoveryStrategy := acb.recoveryStrategies[service]
            if recoveryStrategy == nil {
                recoveryStrategy = ExponentialBackoffRecovery{}
            }

            if recoveryStrategy.ShouldRecover(state, acb.config.Timeout) {
                acb.mu.RUnlock()
                acb.mu.Lock()
                state.State = "half-open"
                state.RecoveryCount = 0
                log.Printf("熔断器进入半开状态 for service %s", service)
                acb.mu.Unlock()
                acb.mu.RLock()
            }
        }
        return state
    }

    return acb.getOrCreateState(service)
}

func (acb *AdaptiveCircuitBreaker) updateLatencyPercentile(service string) {
    metrics := acb.healthMetrics[service]
    if metrics == nil || len(metrics.LatencySamples) == 0 {
        return
    }

    state := acb.states[service]
    if state == nil {
        return
    }

    // 计算P95延迟
    sortedLatencies := make([]time.Duration, len(metrics.LatencySamples))
    copy(sortedLatencies, metrics.LatencySamples)
    sort.Slice(sortedLatencies, func(i, j int) bool {
        return sortedLatencies[i] < sortedLatencies[j]
    })

    index := int(float64(len(sortedLatencies)) * 0.95)
    if index >= len(sortedLatencies) {
        index = len(sortedLatencies) - 1
    }

    state.LatencyPercentile = sortedLatencies[index]
}

func (acb *AdaptiveCircuitBreaker) calculateAverageLatency(samples []time.Duration) time.Duration {
    if len(samples) == 0 {
        return 0
    }

    var total time.Duration
    for _, sample := range samples {
        total += sample
    }

    return total / time.Duration(len(samples))
}

func (acb *AdaptiveCircuitBreaker) getOrCreateState(service string) *BreakerState {
    if state, exists := acb.states[service]; exists {
        return state
    }

    state := &BreakerState{
        State:    "closed",
        Failures: 0,
    }
    acb.states[service] = state
    return state
}

func (acb *AdaptiveCircuitBreaker) getOrCreateMetrics(service string) *HealthMetrics {
    if metrics, exists := acb.healthMetrics[service]; exists {
        return metrics
    }

    metrics := &HealthMetrics{
        LastUpdated: time.Now(),
    }
    acb.healthMetrics[service] = metrics
    return metrics
}

// 恢复策略接口
type RecoveryStrategy interface {
    ShouldRecover(state *BreakerState, timeout time.Duration) bool
    GetDelay() time.Duration
}

// 指数退避恢复策略
type ExponentialBackoffRecovery struct{}

func (ebr ExponentialBackoffRecovery) ShouldRecover(state *BreakerState, timeout time.Duration) bool {
    elapsed := time.Since(state.LastFailure)
    delay := ebr.GetDelay(state)

    return elapsed >= delay
}

func (ebr ExponentialBackoffRecovery) GetDelay() time.Duration {
    return time.Minute * 2 // 固定延迟
}

func (ebr ExponentialBackoffRecovery) GetDelay(state *BreakerState) time.Duration {
    baseDelay := time.Second * 30
    multiplier := math.Pow(2, float64(state.Failures))
    return baseDelay * time.Duration(multiplier)
}

// 线性退避恢复策略
type LinearBackoffRecovery struct{}

func (lbr LinearBackoffRecovery) ShouldRecover(state *BreakerState, timeout time.Duration) bool {
    elapsed := time.Since(state.LastFailure)
    delay := lbr.GetDelay(state)

    return elapsed >= delay
}

func (lbr LinearBackoffRecovery) GetDelay(state *BreakerState) time.Duration {
    baseDelay := time.Second * 30
    increment := time.Second * 10
    return baseDelay + time.Duration(state.Failures)*increment
}
```

### 客户端集成示例

#### **智能客户端实现**
```go
type SmartClient struct {
    service   micro.Service
    selector  selector.Selector
    latencyTracker *LatencyTracker
    circuitBreaker *CircuitBreaker
    connectionTracker *ConnectionTracker
}

func NewSmartClient(service micro.Service) *SmartClient {
    // 创建复合负载均衡器
    primaryBalancer := NewLatencyBasedBalancer()
    secondaryBalancer := NewRoundRobinBalancer()

    // 创建选择器
    selector := selector.NewSelector(
        selector.SetBalancer(primaryBalancer),
        selector.SetFallback(secondaryBalancer),
    )

    return &SmartClient{
        service:          service,
        selector:         selector,
        latencyTracker:    NewLatencyTracker(10),
        circuitBreaker:   NewCircuitBreaker(5, time.Minute),
        connectionTracker: NewConnectionTracker(),
    }
}

func (sc *SmartClient) Call(ctx context.Context, service, method string, req, rsp interface{}) error {
    startTime := time.Now()

    // 获取服务节点
    next, err := sc.selector.Select(service)
    if err != nil {
        return fmt.Errorf("failed to select service node: %w", err)
    }

    node, err := next()
    if err != nil {
        return fmt.Errorf("failed to get service node: %w", err)
    }

    // 记录连接
    sc.connectionTracker.Increment(service, node.Id)
    defer sc.connectionTracker.Decrement(service, node.Id)

    // 检查熔断器状态
    state := sc.circuitBreaker.GetState(service)
    if state.State == "open" {
        return fmt.Errorf("service %s circuit breaker is open", service)
    }

    // 执行调用
    client := sc.service.Client()
    err = client.Call(ctx, service, method, req, rsp)

    // 记录延迟和成功率
    latency := time.Since(startTime)
    sc.latencyTracker.Record(service, node.Id, latency)

    if err != nil {
        sc.circuitBreaker.RecordFailure(service)
    } else {
        sc.circuitBreaker.RecordSuccess(service)
    }

    return err
}
```

这些负载均衡策略提供了灵活的服务调用分发机制，可以根据不同的业务场景和性能需求选择合适的策略，确保系统的高可用性和性能优化。

## 🎯 直接连接模式：绕过服务发现的IP+Port直连

### 场景说明

在某些特殊场景下，我们可能希望绕过服务发现机制，直接通过 IP:Port 方式连接到服务实例。这种模式适用于：

- **开发调试**：快速连接到特定服务实例进行调试
- **测试环境**：在测试环境中需要精确控制服务连接
- **小型应用**：不需要复杂的服务发现机制
- **混合部署**：部分服务使用服务发现，部分服务直接连接

### 实现方案

#### **1. 直接使用 RPC 客户端**
```go
package main

import (
    "context"
    "log"

    "google.golang.org/grpc"
    "google.golang.org/grpc/credentials/insecure"

    pb "github.com/yourproject/user/proto"
)

func main() {
    // 直接创建 gRPC 连接
    conn, err := grpc.Dial("192.168.1.100:8080", grpc.WithInsecure())
    if err != nil {
        log.Fatalf("无法连接到服务: %v", err)
    }
    defer conn.Close()

    // 创建客户端
    client := pb.NewUserServiceClient(conn)

    // 直接调用服务
    ctx := context.Background()
    response, err := client.GetUser(ctx, &pb.GetUserRequest{
        UserId: "12345",
    })

    if err != nil {
        log.Printf("调用服务失败: %v", err)
        return
    }

    log.Printf("用户信息: %+v", response.User)
}
```

#### **2. 自定义服务注册器**
```go
package main

import (
    "context"
    "log"
    "sync"

    "github.com/go-micro/go-micro/v4"
    "github.com/go-micro/go-micro/v4/client"
    "github.com/go-micro/go-micro/v4/registry"
    "github.com/go-micro/go-micro/v4/selector"
)

type DirectRegistry struct {
    services map[string][]*registry.Service
    mu       sync.RWMutex
}

func NewDirectRegistry() *DirectRegistry {
    return &DirectRegistry{
        services: make(map[string][]*registry.Service),
    }
}

// 添加静态服务
func (dr *DirectRegistry) AddService(name, address string, port int) {
    dr.mu.Lock()
    defer dr.mu.Unlock()

    node := &registry.Node{
        Id:      name + "-static",
        Address: address,
        Port:    port,
    }

    service := &registry.Service{
        Name:  name,
        Nodes: []*registry.Node{node},
    }

    dr.services[name] = append(dr.services[name], service)
    log.Printf("添加静态服务: %s -> %s:%d", name, address, port)
}

// 实现注册中心接口
func (dr *DirectRegistry) GetService(name string) ([]*registry.Service, error) {
    dr.mu.RLock()
    defer dr.mu.RUnlock()

    services, exists := dr.services[name]
    if !exists {
        return nil, registry.ErrNotFound
    }

    return services, nil
}

func (dr *DirectRegistry) Register(service *registry.Service, opts ...registry.RegisterOption) error {
    dr.mu.Lock()
    defer dr.mu.Unlock()

    name := service.Name
    dr.services[name] = append(dr.services[name], service)
    log.Printf("注册服务: %s", name)
    return nil
}

func (dr *DirectRegistry) Deregister(service *registry.Service, opts ...registry.DeregisterOption) error {
    dr.mu.Lock()
    defer dr.mu.Unlock()

    name := service.Name
    if _, exists := dr.services[name]; exists {
        delete(dr.services, name)
        log.Printf("注销服务: %s", name)
    }
    return nil
}

func (dr *DirectRegistry) ListServices(opts ...registry.ListOption) ([]*registry.Service, error) {
    dr.mu.RLock()
    defer dr.mu.RUnlock()

    var allServices []*registry.Service
    for _, services := range dr.services {
        allServices = append(allServices, services...)
    }

    return allServices, nil
}

func (dr *DirectRegistry) Watch(opts ...registry.WatchOption) (registry.Watcher, error) {
    // 返回空的 watcher，不支持监听
    return &EmptyWatcher{}, nil
}

func (dr *DirectRegistry) String() string {
    return "direct-registry"
}

type EmptyWatcher struct{}

func (ew *EmptyWatcher) Next() (*registry.Result, error) {
    return nil, registry.ErrWatcherStopped
}

func (ew *EmptyWatcher) Stop() {
    // 空实现
}

// 使用示例
func main() {
    // 创建直接连接的注册器
    directReg := NewDirectRegistry()

    // 添加静态服务配置
    services := map[string]string{
        "user-service":     "192.168.1.100:8080",
        "order-service":    "192.168.1.101:8081",
        "payment-service": "192.168.1.102:8082",
    }

    for name, addr := range services {
        address, port := parseAddress(addr)
        directReg.AddService(name, address, port)
    }

    // 创建服务，使用直接注册器
    service := micro.NewService(
        micro.Name("client-service"),
        micro.Registry(directReg),
        micro.Selector(selector.NewSelector()),
    )

    service.Init()

    // 进行服务调用
    client := service.Client()

    // 调用用户服务
    userResponse := struct {
        Name  string `json:"name"`
        Email string `json:"email"`
    }{}

    err := client.Call(context.Background(),
        "user-service",
        "GetUser",
        map[string]interface{}{"user_id": "123"},
        &userResponse,
    )

    if err != nil {
        log.Printf("调用用户服务失败: %v", err)
        return
    }

    log.Printf("用户信息: %+v", userResponse)
}

func parseAddress(addr string) (string, int) {
    // 简单的地址解析
    var host string
    var port int

    n, err := fmt.Sscanf(addr, "%s:%d", &host, &port)
    if err != nil || n != 2 {
        return "localhost", 8080
    }

    return host, port
}
```

#### **3. 自定义客户端包装器**
```go
package main

import (
    "context"
    "log"
    "strings"

    "github.com/go-micro/go-micro/v4"
    "github.com/go-micro/go-micro/v4/client"
    "github.com/go-micro/go-micro/v4/selector"
)

type DirectClientWrapper struct {
    client.Client
    endpoints map[string]string // service name -> address
}

func NewDirectClientWrapper(endpoints map[string]string) *DirectClientWrapper {
    return &DirectClientWrapper{
        endpoints: endpoints,
    }
}

func (dcw *DirectClientWrapper) Call(ctx context.Context, req client.Request, opts ...client.CallOption) error {
    // 检查是否有直接配置的端点
    if address, exists := dcw.endpoints[req.Service()]; exists {
        log.Printf("使用直接连接调用服务 %s -> %s", req.Service(), address)

        // 替换服务名称为具体地址
        originalService := req.Service()
        modifiedReq := &DirectRequest{
            Request: req,
            service: address,
        }

        return dcw.Client.Call(ctx, modifiedReq, opts...)
    }

    // 否则使用原有的客户端逻辑
    return dcw.Client.Call(ctx, req, opts...)
}

type DirectRequest struct {
    client.Request
    service string
}

func (dr *DirectRequest) Service() string {
    return dr.service
}

// 使用示例
func main() {
    // 配置直接连接的端点
    endpoints := map[string]string{
        "user-service":     "192.168.1.100:8080",
        "order-service":    "192.168.1.101:8081",
        "payment-service": "192.168.1.102:8082",
    }

    // 创建服务
    service := micro.NewService(
        micro.Name("client-service"),
    )

    // 包装客户端
    wrappedClient := NewDirectClientWrapper(endpoints)
    service.Client().Init(client.WithWrapper(wrappedClient))

    service.Init()

    // 测试调用
    client := service.Client()

    // 调用用户服务（将使用直接连接）
    userResponse := struct {
        Name  string `json:"name"`
        Email string `json:"email"`
    }{}

    err := client.Call(context.Background(),
        "user-service",
        "GetUser",
        map[string]interface{}{"user_id": "123"},
        &userResponse,
    )

    if err != nil {
        log.Printf("调用用户服务失败: %v", err)
        return
    }

    log.Printf("用户信息: %+v", userResponse)

    // 调用其他服务（将使用服务发现）
    orderResponse := struct {
        OrderId string `json:"order_id"`
        Amount  int64  `json:"amount"`
    }{}

    err = client.Call(context.Background(),
        "inventory-service", // 没有在endpoints中配置
        "GetInventory",
        map[string]interface{}{"product_id": "456"},
        &orderResponse,
    )

    if err != nil {
        log.Printf("调用库存服务失败: %v", err)
        return
    }

    log.Printf("库存信息: %+v", orderResponse)
}
```

#### **4. 配置驱动的连接方式**
```go
package main

import (
    "context"
    "encoding/json"
    "log"
    "os"

    "github.com/go-micro/go-micro/v4"
)

type ServiceConfig struct {
    DirectMode  bool              `json:"direct_mode"`
    Services   map[string]string `json:"services"`
    Registry   struct {
        Type    string   `json:"type"`
        Address string   `json:"address"`
    } `json:"registry"`
}

func loadConfig(configPath string) (*ServiceConfig, error) {
    data, err := os.ReadFile(configPath)
    if err != nil {
        return nil, err
    }

    var config ServiceConfig
    if err := json.Unmarshal(data, &config); err != nil {
        return nil, err
    }

    return &config, nil
}

func createService(config *ServiceConfig) micro.Service {
    if config.DirectMode {
        return createDirectService(config)
    }
    return createRegistryService(config)
}

func createDirectService(config *ServiceConfig) micro.Service {
    log.Println("使用直接连接模式")

    // 创建直接注册器
    directReg := NewDirectRegistry()

    for name, address := range config.Services {
        host, port := parseAddress(address)
        directReg.AddService(name, host, port)
    }

    return micro.NewService(
        micro.Name("client-service"),
        micro.Registry(directReg),
    )
}

func createRegistryService(config *ServiceConfig) micro.Service {
    log.Println("使用服务发现模式")

    var opts []micro.Option
    switch config.Registry.Type {
    case "consul":
        opts = append(opts, micro.Registry(consul.NewRegistry(
            registry.Addrs(config.Registry.Address),
        )))
    case "etcd":
        opts = append(opts, micro.Registry(etcd.NewRegistry(
            registry.Addrs(config.Registry.Address),
        )))
    default:
        log.Printf("未知的注册中心类型: %s, 使用默认", config.Registry.Type)
    }

    return micro.NewService(
        micro.Name("client-service"),
        opts...,
    )
}

func main() {
    // 加载配置
    config, err := loadConfig("service-config.json")
    if err != nil {
        log.Fatalf("加载配置失败: %v", err)
    }

    // 根据配置创建服务
    service := createService(config)
    service.Init()

    // 服务调用逻辑
    client := service.Client()

    // 调用用户服务
    userResponse := struct {
        Name  string `json:"name"`
        Email string `json:"email"`
    }{}

    err = client.Call(context.Background(),
        "user-service",
        "GetUser",
        map[string]interface{}{"user_id": "123"},
        &userResponse,
    )

    if err != nil {
        log.Printf("调用服务失败: %v", err)
        return
    }

    log.Printf("用户信息: %+v", userResponse)
}

// 配置文件示例 (service-config.json)
/*
{
    "direct_mode": true,
    "services": {
        "user-service": "192.168.1.100:8080",
        "order-service": "192.168.1.101:8081",
        "payment-service": "192.168.1.102:8082"
    },
    "registry": {
        "type": "consul",
        "address": "127.0.0.1:8500"
    }
}
*/
```

### 高级应用场景

#### **生产级混合连接管理器**
```go
type ProductionHybridConnectionManager struct {
    directEndpoints      map[string]*DirectEndpoint
    registryClient     client.Client
    selector          selector.Selector
    healthMonitor      *EndpointHealthMonitor
    failoverManager   *FailoverManager
    metrics           *ConnectionMetrics
    config            *HybridConnectionConfig
    mu                sync.RWMutex
}

type DirectEndpoint struct {
    Address           string            `json:"address"`
    Client            client.Client     `json:"-"`
    Health            *EndpointHealth  `json:"health"`
    ActiveConnections  int              `json:"active_connections"`
    TotalConnections   int64            `json:"total_connections"`
    Latency           time.Duration    `json:"latency"`
    ErrorRate         float64          `json:"error_rate"`
    Metadata          map[string]string `json:"metadata"`
}

type EndpointHealth struct {
    Status           string    `json:"status"` // "healthy", "degraded", "unhealthy"
    LastCheck        time.Time `json:"last_check"`
    ConsecutiveFail   int       `json:"consecutive_fail"`
    RecoveryCount     int       `json:"recovery_count"`
    Uptime           time.Duration `json:"uptime"`
}

type HybridConnectionConfig struct {
    DirectMode           bool              `json:"direct_mode"`
    RegistryFallback    bool              `json:"registry_fallback"`
    HealthCheckInterval time.Duration     `json:"health_check_interval"`
    FailoverTimeout    time.Duration     `json:"failover_timeout"`
    MaxRetries          int               `json:"max_retries"`
    ConnectionPoolSize  int               `json:"connection_pool_size"`
    CircuitBreaker      bool              `json:"circuit_breaker"`
}

type FailoverManager struct {
    strategies        map[string]FailoverStrategy
    currentStrategy   string
    failoverHistory   []FailoverEvent
    mu                sync.RWMutex
}

type FailoverStrategy struct {
    Name              string                 `json:"name"`
    Priority          int                    `json:"priority"`
    Condition         func(*EndpointHealth) bool `json:"-"`
    Action           func(string) error     `json:"-"`
    Rollback         func(string) error     `json:"-"`
}

type FailoverEvent struct {
    Timestamp       time.Time `json:"timestamp"`
    ServiceName    string    `json:"service_name"`
    FromMode       string    `json:"from_mode"`  // "direct", "registry"
    ToMode         string    `json:"to_mode"`
    Reason         string    `json:"reason"`
    Success        bool      `json:"success"`
}

func NewProductionHybridConnectionManager(service micro.Service, config *HybridConnectionConfig) *ProductionHybridConnectionManager {
    return &ProductionHybridConnectionManager{
        directEndpoints:     make(map[string]*DirectEndpoint),
        registryClient:    service.Client(),
        selector:          service.Options().Selector,
        healthMonitor:      NewEndpointHealthMonitor(config.HealthCheckInterval),
        failoverManager:   NewFailoverManager(),
        metrics:           NewConnectionMetrics(),
        config:            config,
    }
}

func (phcm *ProductionHybridConnectionManager) AddDirectEndpoint(serviceName, address string, metadata map[string]string) error {
    phcm.mu.Lock()
    defer phcm.mu.Unlock()

    // 创建连接池
    connectionPool := NewConnectionPool(phcm.config.ConnectionPoolSize)

    // 创建专用客户端
    directClient := client.NewClient(
        client.Selector(selector.NewSelector(
            selector.SetBalancer(&SmartDirectBalancer{
                Address:       address,
                ConnectionPool: connectionPool,
                HealthMonitor:  phcm.healthMonitor,
            }),
        )),
    )

    endpoint := &DirectEndpoint{
        Address:    address,
        Client:     directClient,
        Metadata:   metadata,
        Health: &EndpointHealth{
            Status:     "healthy",
            LastCheck:  time.Now(),
        },
    }

    phcm.directEndpoints[serviceName] = endpoint
    phcm.metrics.RegisterEndpoint(serviceName, "direct")

    // 启动健康监控
    phcm.healthMonitor.RegisterEndpoint(serviceName, address)

    log.Printf("添加直接端点: %s -> %s (元数据: %+v)", serviceName, address, metadata)
    return nil
}

func (phcm *ProductionHybridConnectionManager) Call(ctx context.Context, req client.Request, opts ...client.CallOption) error {
    serviceName := req.Service()
    startTime := time.Now()

    // 选择连接策略
    strategy := phcm.selectConnectionStrategy(serviceName)

    var err error
    var mode string

    switch strategy {
    case "direct":
        mode = "direct"
        err = phcm.callDirectEndpoint(ctx, serviceName, req, opts...)
    case "registry":
        mode = "registry"
        err = phcm.callRegistryEndpoint(ctx, serviceName, req, opts...)
    case "failover":
        mode = "failover"
        err = phcm.callWithFailover(ctx, serviceName, req, opts...)
    default:
        err = fmt.Errorf("未知的连接策略: %s", strategy)
    }

    // 记录调用指标
    latency := time.Since(startTime)
    phcm.metrics.RecordCall(serviceName, mode, err == nil, latency)

    return err
}

func (phcm *ProductionHybridConnectionManager) selectConnectionStrategy(serviceName string) string {
    phcm.mu.RLock()
    defer phcm.mu.RUnlock()

    // 检查直接端点是否可用
    if endpoint, exists := phcm.directEndpoints[serviceName]; exists {
        health := phcm.healthMonitor.GetEndpointHealth(serviceName, endpoint.Address)

        if health.Status == "healthy" {
            if phcm.config.DirectMode {
                return "direct"
            }
        } else if health.Status == "degraded" && phcm.config.RegistryFallback {
            return "registry" // 降级到注册中心
        }
    }

    // 检查是否需要故障转移
    if phcm.failoverManager.ShouldFailover(serviceName) {
        return "failover"
    }

    // 默认使用注册中心
    return "registry"
}

func (phcm *ProductionHybridConnectionManager) callDirectEndpoint(ctx context.Context, serviceName string, req client.Request, opts ...client.CallOption) error {
    phcm.mu.RLock()
    endpoint, exists := phcm.directEndpoints[serviceName]
    phcm.mu.RUnlock()

    if !exists {
        return fmt.Errorf("直接端点不存在: %s", serviceName)
    }

    // 检查端点健康状态
    health := phcm.healthMonitor.GetEndpointHealth(serviceName, endpoint.Address)
    if health.Status != "healthy" {
        return fmt.Errorf("直接端点不健康: %s (状态: %s)", serviceName, health.Status)
    }

    // 执行调用
    endpoint.ActiveConnections++
    endpoint.TotalConnections++

    err := endpoint.Client.Call(ctx, req, opts...)

    endpoint.ActiveConnections--

    // 更新健康状态
    if err != nil {
        phcm.healthMonitor.RecordFailure(serviceName, endpoint.Address, err)
        endpoint.ErrorRate = (endpoint.ErrorRate*float64(endpoint.TotalConnections-1) + 1.0) / float64(endpoint.TotalConnections)
    } else {
        phcm.healthMonitor.RecordSuccess(serviceName, endpoint.Address)
        endpoint.ErrorRate = endpoint.ErrorRate * float64(endpoint.TotalConnections-1) / float64(endpoint.TotalConnections)
    }

    return err
}

func (phcm *ProductionHybridConnectionManager) callRegistryEndpoint(ctx context.Context, serviceName string, req client.Request, opts ...client.CallOption) error {
    log.Printf("通过注册中心调用服务: %s", serviceName)
    err := phcm.registryClient.Call(ctx, req, opts...)

    if err != nil {
        // 记录注册中心调用失败
        phcm.metrics.RecordRegistryFailure(serviceName, err)

        // 如果配置了故障转移，尝试直接端点
        if phcm.config.RegistryFallback {
            if endpoint, exists := phcm.directEndpoints[serviceName]; exists {
                log.Printf("注册中心调用失败，尝试直接端点: %s", serviceName)
                return phcm.callDirectEndpoint(ctx, serviceName, req, opts...)
            }
        }
    }

    return err
}

func (phcm *ProductionHybridConnectionManager) callWithFailover(ctx context.Context, serviceName string, req client.Request, opts ...client.CallOption) error {
    // 获取故障转移策略
    strategy := phcm.failoverManager.GetCurrentStrategy(serviceName)
    if strategy == nil {
        return fmt.Errorf("无可用的故障转移策略: %s", serviceName)
    }

    log.Printf("执行故障转移策略: %s for service %s", strategy.Name, serviceName)

    // 执行故障转移操作
    err := strategy.Action(serviceName)
    event := FailoverEvent{
        Timestamp:    time.Now(),
        ServiceName: serviceName,
        FromMode:     "unknown",
        ToMode:       "failover",
        Reason:       "故障转移激活",
        Success:      err == nil,
    }

    phcm.failoverManager.RecordEvent(event)

    if err != nil {
        return fmt.Errorf("故障转移失败: %w", err)
    }

    // 重试调用
    return phcm.Call(ctx, req, opts...)
}

type SmartDirectBalancer struct {
    Address         string
    ConnectionPool *ConnectionPool
    HealthMonitor  *EndpointHealthMonitor
}

func (sdb *SmartDirectBalancer) Select(service string, nodes []*registry.Node) (selector.Next, error) {
    // 从连接池获取连接
    conn, err := sdb.ConnectionPool.GetConnection(sdb.Address)
    if err != nil {
        return nil, fmt.Errorf("获取连接失败: %w", err)
    }

    host, port := parseAddress(sdb.Address)
    return func() (*registry.Node, error) {
        return &registry.Node{
            Id:      fmt.Sprintf("%s-%d", service, rand.Intn(10000)),
            Address: host,
            Port:    port,
            Metadata: map[string]string{
                "connection_id": conn.ID(),
                "created_at":    time.Now().Format(time.RFC3339),
            },
        }, nil
    }, nil
}

func (sdb *SmartDirectBalancer) String() string {
    return "smart-direct-balancer"
}

type ConnectionPool struct {
    connections chan *PooledConnection
    maxSize     int
    currentSize  int
    mu          sync.Mutex
}

type PooledConnection struct {
    ID         string
    Connection interface{}
    Created    time.Time
    LastUsed   time.Time
    Healthy    bool
}

func NewConnectionPool(maxSize int) *ConnectionPool {
    return &ConnectionPool{
        connections: make(chan *PooledConnection, maxSize),
        maxSize:     maxSize,
    }
}

func (cp *ConnectionPool) GetConnection(address string) (*PooledConnection, error) {
    select {
    case conn := <-cp.connections:
        cp.mu.Lock()
        conn.LastUsed = time.Now()
        cp.currentSize--
        cp.mu.Unlock()
        return conn, nil
    default:
        // 连接池为空，创建新连接
        return cp.createNewConnection(address)
    }
}

func (cp *ConnectionPool) ReturnConnection(conn *PooledConnection) {
    if !conn.Healthy {
        return // 不健康的连接不返回到池中
    }

    cp.mu.Lock()
    defer cp.mu.Unlock()

    if cp.currentSize < cp.maxSize {
        conn.LastUsed = time.Now()
        cp.connections <- conn
        cp.currentSize++
    }
}

func (cp *ConnectionPool) createNewConnection(address string) (*PooledConnection, error) {
    connID := fmt.Sprintf("conn-%d-%d", time.Now().UnixNano(), rand.Intn(10000))

    return &PooledConnection{
        ID:        connID,
        Connection: nil, // 实际连接根据协议类型创建
        Created:   time.Now(),
        LastUsed:  time.Now(),
        Healthy:   true,
    }, nil
}

func NewFailoverManager() *FailoverManager {
    strategies := map[string]FailoverStrategy{
        "retry": {
            Name:     "重试策略",
            Priority: 1,
            Condition: func(health *EndpointHealth) bool {
                return health.ConsecutiveFail < 3
            },
            Action: func(serviceName string) error {
                log.Printf("执行重试策略 for service %s", serviceName)
                return nil // 重试逻辑由调用者处理
            },
            Rollback: func(serviceName string) error {
                return nil
            },
        },
        "direct_only": {
            Name:     "仅直接模式",
            Priority: 2,
            Condition: func(health *EndpointHealth) bool {
                return health.Status == "healthy"
            },
            Action: func(serviceName string) error {
                log.Printf("切换到仅直接模式 for service %s", serviceName)
                return nil
            },
            Rollback: func(serviceName string) error {
                return nil
            },
        },
        "cache_fallback": {
            Name:     "缓存回退",
            Priority: 3,
            Condition: func(health *EndpointHealth) bool {
                return health.ConsecutiveFail >= 3
            },
            Action: func(serviceName string) error {
                log.Printf("切换到缓存回退模式 for service %s", serviceName)
                return nil
            },
            Rollback: func(serviceName string) error {
                return nil
            },
        },
    }

    return &FailoverManager{
        strategies:      strategies,
        currentStrategy: "retry",
        failoverHistory: make([]FailoverEvent, 0),
    }
}
```

这种直接连接模式提供了灵活的部署选项，让开发者可以根据实际需求选择最适合的服务连接方式。 the command line interface for developing Go Micro projects.

## ⚠️ 自定义错误返回机制

### 错误处理的重要性

在分布式系统中，错误处理不仅关系到系统的稳定性，还直接影响用户体验和问题排查效率。Go Micro 提供了强大的自定义错误返回机制，让开发者能够根据业务需求设计和实现统一的错误处理规范。

### 自定义错误类型

#### **1. 定义业务错误码**
```go
package errors

import (
    "fmt"
    "google.golang.org/grpc/codes"
    "google.golang.org/grpc/status"
)

// 定义错误码常量
const (
    ErrorCodeUserNotFound     = 10001
    ErrorCodeInvalidPassword   = 10002
    ErrorCodeUserAlreadyExists = 10003
    ErrorCodeInsufficientBalance = 10004
    ErrorCodeOrderNotFound     = 20001
    ErrorCodePaymentFailed     = 20002
    ErrorCodeInvalidOrderStatus = 20003
)

// 错误码映射
var errorCodeToGRPC = map[int32]codes.Code{
    ErrorCodeUserNotFound:      codes.NotFound,
    ErrorCodeInvalidPassword:   codes.InvalidArgument,
    ErrorCodeUserAlreadyExists: codes.AlreadyExists,
    ErrorCodeInsufficientBalance: codes.ResourceExhausted,
    ErrorCodeOrderNotFound:      codes.NotFound,
    ErrorCodePaymentFailed:      codes.Internal,
    ErrorCodeInvalidOrderStatus: codes.FailedPrecondition,
}

var errorCodeToMessage = map[int32]string{
    ErrorCodeUserNotFound:      "用户不存在",
    ErrorCodeInvalidPassword:   "密码无效",
    ErrorCodeUserAlreadyExists: "用户已存在",
    ErrorCodeInsufficientBalance: "余额不足",
    ErrorCodeOrderNotFound:      "订单不存在",
    ErrorCodePaymentFailed:      "支付失败",
    ErrorCodeInvalidOrderStatus: "订单状态无效",
}

// 业务错误类型
type BusinessError struct {
    Code        int32                  `json:"code"`
    Message     string                 `json:"message"`
    Details     string                 `json:"details,omitempty"`
    StackTrace  string                 `json:"stack_trace,omitempty"`
    Context     map[string]interface{} `json:"context,omitempty"`
    Timestamp   time.Time              `json:"timestamp"`
    RequestID   string                 `json:"request_id,omitempty"`
}

func (be *BusinessError) Error() string {
    return fmt.Sprintf("业务错误 [%d]: %s", be.Code, be.Message)
}

func (be *BusinessError) GRPCStatus() *status.Status {
    grpcCode, exists := errorCodeToGRPC[be.Code]
    if !exists {
        grpcCode = codes.Unknown
    }

    return status.New(grpcCode, be.Message)
}

// 错误上下文管理器
type ErrorContext struct {
    RequestID   string
    UserID      string
    ServiceName string
    Method      string
    TraceID     string
    SpanID      string
    Metadata     map[string]interface{}
    Timestamp   time.Time
}

type ErrorContextManager struct {
    contextMap map[string]*ErrorContext
    mu         sync.RWMutex
}

func NewErrorContextManager() *ErrorContextManager {
    return &ErrorContextManager{
        contextMap: make(map[string]*ErrorContext),
    }
}

func (ecm *ErrorContextManager) SetContext(key string, ctx *ErrorContext) {
    ecm.mu.Lock()
    defer ecm.mu.Unlock()
    ecm.contextMap[key] = ctx
}

func (ecm *ErrorContextManager) GetContext(key string) *ErrorContext {
    ecm.mu.RLock()
    defer ecm.mu.RUnlock()
    return ecm.contextMap[key]
}

// 创建增强的业务错误
func NewBusinessErrorWithContext(code int32, message string, ctx *ErrorContext, details ...string) *BusinessError {
    err := &BusinessError{
        Code:      code,
        Message:   message,
        Timestamp: time.Now(),
        Context:   make(map[string]interface{}),
    }

    if ctx != nil {
        err.RequestID = ctx.RequestID
        err.Context["user_id"] = ctx.UserID
        err.Context["service_name"] = ctx.ServiceName
        err.Context["method"] = ctx.Method
        err.Context["trace_id"] = ctx.TraceID
        err.Context["span_id"] = ctx.SpanID
        if ctx.Metadata != nil {
            for k, v := range ctx.Metadata {
                err.Context[k] = v
            }
        }
    }

    if len(details) > 0 {
        err.Details = details[0]
    }

    // 添加堆栈信息
    err.StackTrace = captureStackTrace(3)

    return err
}

// 创建业务错误
func NewBusinessError(code int32, message string, details ...string) *BusinessError {
    return NewBusinessErrorWithContext(code, message, nil, details...)
}

// 预定义错误创建函数
var (
    ErrUserNotFound = func(details ...string) error {
        ctx := getCurrentErrorContext()
        return NewBusinessErrorWithContext(ErrorCodeUserNotFound, errorCodeToMessage[ErrorCodeUserNotFound], ctx, details...)
    }

    ErrInvalidPassword = func(details ...string) error {
        ctx := getCurrentErrorContext()
        return NewBusinessErrorWithContext(ErrorCodeInvalidPassword, errorCodeToMessage[ErrorCodeInvalidPassword], ctx, details...)
    }

    ErrUserAlreadyExists = func(details ...string) error {
        ctx := getCurrentErrorContext()
        return NewBusinessErrorWithContext(ErrorCodeUserAlreadyExists, errorCodeToMessage[ErrorCodeUserAlreadyExists], ctx, details...)
    }

    ErrInsufficientBalance = func(details ...string) error {
        ctx := getCurrentErrorContext()
        return NewBusinessErrorWithContext(ErrorCodeInsufficientBalance, errorCodeToMessage[ErrorCodeInsufficientBalance], ctx, details...)
    }

    ErrOrderNotFound = func(details ...string) error {
        ctx := getCurrentErrorContext()
        return NewBusinessErrorWithContext(ErrorCodeOrderNotFound, errorCodeToMessage[ErrorCodeOrderNotFound], ctx, details...)
    }

    ErrPaymentFailed = func(details ...string) error {
        ctx := getCurrentErrorContext()
        return NewBusinessErrorWithContext(ErrorCodePaymentFailed, errorCodeToMessage[ErrorCodePaymentFailed], ctx, details...)
    }
)

// 全局错误上下文管理
var globalErrorContextManager = NewErrorContextManager()
var currentErrorContext atomic.Value // stores *ErrorContext

func WithErrorContext(ctx context.Context) context.Context {
    if requestID := ctx.Value("request_id"); requestID != nil {
        errorCtx := &ErrorContext{
            RequestID:   requestID.(string),
            ServiceName: ctx.Value("service_name").(string),
            Method:      ctx.Value("method").(string),
            TraceID:     ctx.Value("trace_id").(string),
            SpanID:      ctx.Value("span_id").(string),
            Timestamp:   time.Now(),
        }

        if userID := ctx.Value("user_id"); userID != nil {
            errorCtx.UserID = userID.(string)
        }

        currentErrorContext.Store(errorCtx)
    }
    return ctx
}

func getCurrentErrorContext() *ErrorContext {
    if ctx := currentErrorContext.Load(); ctx != nil {
        return ctx.(*ErrorContext)
    }
    return nil
}

func captureStackTrace(skip int) string {
    pc := make([]uintptr, 32)
    n := runtime.Callers(skip+2, pc)
    if n == 0 {
        return ""
    }

    pc = pc[:n]
    frames := runtime.CallersFrames(pc)
    var builder strings.Builder

    for {
        frame, more := frames.Next()
        if !more {
            break
        }

        funcInfo := runtime.FuncForPC(frame.PC)
        if funcInfo != nil {
            file, line := funcInfo.FileLine(frame.PC)
            builder.WriteString(fmt.Sprintf("%s:%d - %s\n", file, line, funcInfo.Name()))
        }
    }

    return builder.String()
}
```

#### **2. 错误包装器**
```go
package errors

import (
    "context"
    "errors"
    "log"
    "runtime/debug"
    "time"

    "github.com/go-micro/go-micro/v4/errors"
)

// 错误包装器
type ErrorWrapper struct {
    service string
    method  string
}

func NewErrorWrapper(service, method string) *ErrorWrapper {
    return &ErrorWrapper{
        service: service,
        method:  method,
    }
}

// 包装业务错误
func (ew *ErrorWrapper) WrapBusinessError(ctx context.Context, err *BusinessError) error {
    // 记录错误日志
    ew.logError(ctx, err, "business")

    // 转换为 gRPC 错误
    return err.GRPCStatus().Err()
}

// 包装系统错误
func (ew *ErrorWrapper) WrapSystemError(ctx context.Context, err error) error {
    // 记录错误日志
    ew.logError(ctx, err, "system")

    // 返回原始错误或包装为内部错误
    if errors.Is(err, context.Canceled) {
        return err
    }

    return errors.InternalServer("internal server error", err)
}

// 包装数据库错误
func (ew *ErrorWrapper) WrapDatabaseError(ctx context.Context, err error) error {
    ew.logError(ctx, err, "database")
    return errors.InternalServer("database operation failed", err)
}

// 包装验证错误
func (ew *ErrorWrapper) WrapValidationError(ctx context.Context, err error) error {
    ew.logError(ctx, err, "validation")
    return errors.InvalidArgument("validation failed", err)
}

// 包装外部服务错误
func (ew *ErrorWrapper) WrapExternalServiceError(ctx context.Context, serviceName, method string, err error) error {
    ew.logError(ctx, err, "external_service")
    return errors.ServiceUnavailable(
        fmt.Sprintf("external service %s method %s failed", serviceName, method),
        err,
    )
}

// 错误日志记录
func (ew *ErrorWrapper) logError(ctx context.Context, err error, errorType string) {
    now := time.Now()

    // 获取调用栈信息
    stack := debug.Stack()

    log.Printf("[%s] [%s] %s - %s\n%s",
        now.Format("2006-01-02 15:04:05"),
        errorType,
        ew.service,
        ew.method,
        err.Error(),
        stack,
    )
}

// 使用示例
func ExampleUsage() {
    wrapper := NewErrorWrapper("user-service", "CreateUser")

    ctx := context.Background()

    // 模拟业务错误
    businessErr := ErrUserNotFound("user_id: 12345")
    grpcErr := wrapper.WrapBusinessError(ctx, businessErr)
    log.Printf("业务错误: %v", grpcErr)

    // 模拟系统错误
    systemErr := errors.New("database connection timeout")
    grpcErr = wrapper.WrapSystemError(ctx, systemErr)
    log.Printf("系统错误: %v", grpcErr)

    // 模拟验证错误
    validationErr := errors.New("email format invalid")
    grpcErr = wrapper.WrapValidationError(ctx, validationErr)
    log.Printf("验证错误: %v", grpcErr)
}
```

#### **3. 错误处理器中间件**
```go
package middleware

import (
    "context"
    "net/http"

    "github.com/go-micro/go-micro/v4/client"
    "github.com/go-micro/go-micro/v4/selector"
    "github.com/yourproject/errors"
)

// 错误处理器
type ErrorHandler struct {
    errorWrapper *errors.ErrorWrapper
}

func NewErrorHandler(serviceName string) *ErrorHandler {
    return &ErrorHandler{
        errorWrapper: errors.NewErrorWrapper(serviceName, "*"),
    }
}

// gRPC 调用错误处理包装器
func (eh *ErrorHandler) WrapCall(fn func(ctx context.Context, req interface{}, rsp interface{}) error) func(ctx context.Context, req interface{}, rsp interface{}) error {
    return func(ctx context.Context, req interface{}, rsp interface{}) error {
        err := fn(ctx, req, rsp)
        if err != nil {
            return eh.errorWrapper.WrapSystemError(ctx, err)
        }
        return nil
    }
}

// HTTP 错误处理器
func (eh *ErrorHandler) HandleHTTPError(w http.ResponseWriter, r *http.Request, err error) {
    // 记录错误
    eh.errorWrapper.WrapSystemError(r.Context(), err)

    // 根据 error 类型返回相应的 HTTP 状态码
    var statusCode int
    var message string

    switch {
    case errors.Is(err, errors.NotFound):
        statusCode = http.StatusNotFound
        message = "Resource not found"
    case errors.Is(err, errors.InvalidArgument):
        statusCode = http.StatusBadRequest
        message = "Invalid request"
    case errors.Is(err, errors.AlreadyExists):
        statusCode = http.StatusConflict
        message = "Resource already exists"
    case errors.Is(err, errors.ResourceExhausted):
        statusCode = http.StatusTooManyRequests
        message = "Rate limit exceeded"
    case errors.Is(err, errors.InternalServer):
        statusCode = http.StatusInternalServerError
        message = "Internal server error"
    case errors.Is(err, errors.ServiceUnavailable):
        statusCode = http.StatusServiceUnavailable
        message = "Service unavailable"
    default:
        statusCode = http.StatusInternalServerError
        message = "Unknown error"
    }

    // 返回错误响应
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(statusCode)

    json.NewEncoder(w).Encode(map[string]interface{}{
        "error": map[string]interface{}{
            "code":    statusCode,
            "message": message,
            "details":  err.Error(),
        },
        "timestamp": time.Now(),
    })
}

// 使用示例
func ExampleUsage() {
    errorHandler := NewErrorHandler("user-service")

    // gRPC 服务中使用
    type UserService struct{}

    func (s *UserService) CreateUser(ctx context.Context, req *CreateUserRequest, rsp *CreateUserResponse) error {
        // 业务逻辑
        if req.Email == "" {
            return errors.InvalidArgument("email is required")
        }

        // 调用仓储层，并包装错误
        err := userRepository.Create(ctx, req)
        if err != nil {
            return errorHandler.WrapCall(func(ctx context.Context, req interface{}, rsp interface{}) error {
                return userRepository.Create(ctx, req)
            })(ctx, req, rsp)
        }

        return nil
    }

    // HTTP 服务中使用
    http.HandleFunc("/users", func(w http.ResponseWriter, r *http.Request) {
        var req CreateUserRequest
        if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
            errorHandler.HandleHTTPError(w, r, errors.InvalidArgument("invalid request body"))
            return
        }

        rsp := CreateUserResponse{}
        // 模拟业务错误
        if req.Email == "existing@example.com" {
            err := errors.ErrUserAlreadyExists("email already exists")
            errorHandler.HandleHTTPError(w, r, err)
            return
        }

        // 正常处理
        json.NewEncoder(w).Encode(rsp)
    })
}
```

### 高级错误处理特性

#### **错误恢复机制**
```go
package errors

import (
    "context"
    "fmt"
    "time"

    "github.com/go-micro/go-micro/v4/errors"
)

// 错误恢复器
type ErrorRecoverer struct {
    retryCount    int
    maxRetries    int
    retryableErrors map[error]bool
}

func NewErrorRecoverer(maxRetries int) *ErrorRecoverer {
    return &ErrorRecoverer{
        maxRetries: maxRetries,
        retryableErrors: map[error]bool{
            errors.ServiceUnavailable: true,
            errors.ResourceExhausted: true,
            errors.InternalServer:     true,
        },
    }
}

// 带重试的调用
func (er *ErrorRecoverer) CallWithRetry(
    ctx context.Context,
    fn func(context.Context) error,
    serviceName string,
    methodName string,
) error {
    var lastErr error
    var retryDelay time.Duration

    for er.retryCount = 0; er.retryCount < er.maxRetries; er.retryCount++ {
        lastErr = fn(ctx)

        if lastErr == nil {
            return nil
        }

        // 检查是否是可重试的错误
        if !er.isRetryableError(lastErr) {
            return lastErr
        }

        // 如果不是最后一次尝试，则等待一段时间后重试
        if er.retryCount < er.maxRetries {
            // 指数退避策略计算延迟
            retryDelay = er.calculateRetryDelay(er.retryCount)

            select {
            case <-time.After(retryDelay):
                log.Printf("重试调用 %s.%s (第%d次, 等待 %v)", serviceName, methodName, er.retryCount+1, retryDelay)
            case <-ctx.Done():
                return ctx.Err()
            }
        }
    }

    return lastErr
}

// 计算重试延迟
func (er *ErrorRecoverer) calculateRetryDelay(attempt int) time.Duration {
    baseDelay := time.Second
    maxDelay := time.Second * 30

    // 指数退避：delay = baseDelay * 2^(attempt-1)
    delay := baseDelay * time.Duration(math.Pow(2, float64(attempt-1)))

    if delay > maxDelay {
        return maxDelay
    }

    return delay
}

// 带熔断的调用
func (er *ErrorRecoverer) CallWithCircuitBreaker(
    ctx context.Context,
    fn func(context.Context) error,
    serviceName string,
    methodName string,
    maxFailures int,
) error {
    lastErr := fn(ctx)

    if lastErr == nil {
        return nil
    }

    // 检查是否是网络错误或服务不可用错误
    if er.isRetryableError(lastErr) {
        // 熔断器逻辑，这里简化处理
        return fmt.Errorf("service %s method %s failed after circuit breaker: %w", serviceName, methodName, lastErr)
    }

    return lastErr
}

// 带断路器的高级调用
func (er *ErrorRecoverer) CallWithAdvancedRetry(
    ctx context.Context,
    fn func(context.Context) error,
    config *RetryConfig,
) error {
    var lastErr error
    var consecutiveFailures int
    var backoffDelay time.Duration

    for er.retryCount = 0; er.retryCount < config.MaxRetries; er.retryCount++ {
        lastErr = fn(ctx)

        if lastErr == nil {
            return nil
        }

        // 检查是否是可重试的错误
        if !er.isRetryableError(lastErr) {
            return lastErr
        }

        consecutiveFailures++
        backoffDelay = config.Strategy.CalculateDelay(consecutiveFailures)

        // 检查是否超过最大重试时间
        if config.MaxRetryTime > 0 && time.Since(ctx.Value("retry_start_time").(time.Time)) > config.MaxRetryTime {
            return fmt.Errorf("超过最大重试时间限制: %v", config.MaxRetryTime)
        }

        if er.retryCount < config.MaxRetries-1 {
            select {
            case <-time.After(backoffDelay):
                log.Printf("重试调用 (第%d次, 延迟: %v, 策略: %s)",
                    er.retryCount+1, backoffDelay, config.Strategy.Name())
            case <-ctx.Done():
                return ctx.Err()
            }
        }
    }

    return lastErr
}

// 重试策略接口
type RetryStrategy interface {
    Name() string
    CalculateDelay(attempt int) time.Duration
}

// 指数退避策略
type ExponentialBackoffStrategy struct {
    BaseDelay time.Duration
    MaxDelay  time.Duration
    Multiplier float64
}

func (e *ExponentialBackoffStrategy) Name() string {
    return "exponential_backoff"
}

func (e *ExponentialBackoffStrategy) CalculateDelay(attempt int) time.Duration {
    delay := e.BaseDelay * time.Duration(math.Pow(e.Multiplier, float64(attempt-1)))
    if delay > e.MaxDelay {
        return e.MaxDelay
    }
    return delay
}

// 线性退避策略
type LinearBackoffStrategy struct {
    BaseDelay time.Duration
    MaxDelay  time.Duration
    Increment time.Duration
}

func (l *LinearBackoffStrategy) Name() string {
    return "linear_backoff"
}

func (l *LinearBackoffStrategy) CalculateDelay(attempt int) time.Duration {
    delay := l.BaseDelay + time.Duration(attempt-1)*l.Increment
    if delay > l.MaxDelay {
        return l.MaxDelay
    }
    return delay
}

// 固定间隔策略
type FixedIntervalStrategy struct {
    Interval time.Duration
}

func (f *FixedIntervalStrategy) Name() string {
    return "fixed_interval"
}

func (f *FixedIntervalStrategy) CalculateDelay(attempt int) time.Duration {
    return f.Interval
}

// 重试配置
type RetryConfig struct {
    MaxRetries   int           `json:"max_retries"`
    MaxRetryTime time.Duration `json:"max_retry_time"`
    Strategy     RetryStrategy `json:"strategy"`
    Jitter       bool          `json:"jitter"`
}

// 使用示例
func ExampleUsage() {
    // 配置不同的重试策略
    exponentialStrategy := &ExponentialBackoffStrategy{
        BaseDelay: time.Second,
        MaxDelay:  time.Second * 30,
        Multiplier: 2.0,
    }

    linearStrategy := &LinearBackoffStrategy{
        BaseDelay: time.Second,
        MaxDelay:  time.Second * 20,
        Increment: time.Second * 2,
    }

    fixedStrategy := &FixedIntervalStrategy{
        Interval: time.Second * 5,
    }

    configs := map[string]*RetryConfig{
        "exponential": {
            MaxRetries:   5,
            MaxRetryTime: time.Minute * 10,
            Strategy:     exponentialStrategy,
            Jitter:       true,
        },
        "linear": {
            MaxRetries:   6,
            MaxRetryTime: time.Minute * 5,
            Strategy:     linearStrategy,
            Jitter:       false,
        },
        "fixed": {
            MaxRetries:   8,
            MaxRetryTime: 0,
            Strategy:     fixedStrategy,
            Jitter:       false,
        },
    }

    ctx, cancel := context.WithTimeout(context.Background(), time.Minute*2)
    defer cancel()

    // 模拟一个可能失败的服务调用
    attemptCount := 0
    for strategyName, config := range configs {
        ctx = context.WithValue(ctx, "retry_start_time", time.Now())

        err := NewErrorRecoverer(config.MaxRetries).CallWithAdvancedRetry(
            ctx,
            func(ctx context.Context) error {
                attemptCount++
                log.Printf("执行服务调用 (策略: %s, 尝试: %d)", strategyName, attemptCount)

                // 模拟前几次失败，最后一次成功
                if attemptCount < 4 {
                    return errors.ServiceUnavailable(fmt.Sprintf("service temporarily unavailable (attempt %d)", attemptCount))
                }
                return nil
            },
            config,
        )

        if err != nil {
            log.Printf("策略 %s 最终调用失败: %v", strategyName, err)
        } else {
            log.Printf("策略 %s 调用成功", strategyName)
        }

        // 重置计数器
        attemptCount = 0
    }
}
```
```

#### **错误监控和告警**
```go
package monitoring

import (
    "context"
    "log"
    "sync"
    "time"

    "github.com/go-micro/go-micro/v4/errors"
)

// 错误监控器
type ErrorMonitor struct {
    errorCounts map[string]int64 // error type -> count
    alerts      map[string]*AlertConfig
    mu           sync.RWMutex
}

type AlertConfig struct {
    Threshold   int           `json:"threshold"`
    Interval    time.Duration `json:"interval"`
    WebhookURL string         `json:"webhook_url"`
}

func NewErrorMonitor() *ErrorMonitor {
    return &ErrorMonitor{
        errorCounts: make(map[string]int64),
        alerts:      make(map[string]*AlertConfig),
    }
}

// 记录错误
func (em *ErrorMonitor) RecordError(err error, service, method string) {
    em.mu.Lock()
    defer em.mu.Unlock()

    errorType := em.classifyError(err)
    em.errorCounts[errorType]++

    log.Printf("错误监控: %s.%s - %s (%s)", service, method, errorType, err.Error())

    // 检查是否需要触发告警
    if alert, exists := em.alerts[errorType]; exists {
        if em.errorCounts[errorType] >= int64(alert.Threshold) {
            em.triggerAlert(errorType, alert, service, method)
        }
    }
}

// 分类错误类型
func (em *ErrorMonitor) classifyError(err error) string {
    switch {
    case errors.Is(err, errors.NotFound):
        return "not_found"
    case errors.Is(err, errors.InvalidArgument):
        return "invalid_argument"
    case errors.Is(err, errors.AlreadyExists):
        return "already_exists"
    case errors.Is(err, errors.ResourceExhausted):
        return "resource_exhausted"
    case errors.Is(err, errors.ServiceUnavailable):
        return "service_unavailable"
    case errors.Is(err, errors.InternalServer):
        return "internal_server"
    default:
        return "unknown"
    }
}

// 触发告警
func (em *ErrorMonitor) triggerAlert(errorType string, alert *AlertConfig, service, method string) {
    alertData := map[string]interface{}{
        "timestamp":    time.Now(),
        "error_type":   errorType,
        "service":      service,
        "method":       method,
        "count":        em.errorCounts[errorType],
        "threshold":    alert.Threshold,
        "message":      fmt.Sprintf("%s errors exceeded threshold", errorType),
    }

    log.Printf("触发告警: %+v", alertData)

    // 这里可以发送到外部监控系统
    // em.sendToWebhook(alert.WebhookURL, alertData)
    // em.sendToSlack(alertData)
    // em.sendToEmail(alertData)
}

// 添加告警配置
func (em *ErrorMonitor) AddAlert(errorType string, threshold int, interval time.Duration, webhookURL string) {
    em.mu.Lock()
    defer em.mu.Unlock()

    em.alerts[errorType] = &AlertConfig{
        Threshold:   threshold,
        Interval:    interval,
        WebhookURL: webhookURL,
    }

    log.Printf("添加告警配置: %s -> threshold: %d", errorType, threshold)
}

// 定期重置计数器
func (em *ErrorMonitor) StartPeriodicReset(interval time.Duration) {
    go func() {
        ticker := time.NewTicker(interval)
        defer ticker.Stop()

        for range ticker.C {
            em.resetCounts()
            log.Println("错误计数器已重置")
        }
    }()
}

func (em *ErrorMonitor) resetCounts() {
    em.mu.Lock()
    defer em.mu.Unlock()

    for key := range em.errorCounts {
        em.errorCounts[key] = 0
    }
}

// 高级错误聚合器
type ErrorAggregator struct {
    windowSize     time.Duration
    errorBuffer    []ErrorEvent
    patternMatcher *ErrorPatternMatcher
    mu             sync.RWMutex
}

type ErrorEvent struct {
    Timestamp   time.Time              `json:"timestamp"`
    ServiceName string                 `json:"service_name"`
    Method      string                 `json:"method"`
    ErrorType   string                 `json:"error_type"`
    Message     string                 `json:"message"`
    TraceID     string                 `json:"trace_id"`
    UserID      string                 `json:"user_id,omitempty"`
    Metadata    map[string]interface{} `json:"metadata"`
}

type ErrorPattern struct {
    Pattern    string   `json:"pattern"`
    Type       string   `json:"type"`
    Priority   int      `json:"priority"`
    Action      string   `json:"action"` // "alert", "log", "ignore"
}

func NewErrorAggregator(windowSize time.Duration) *ErrorAggregator {
    return &ErrorAggregator{
        windowSize:     windowSize,
        errorBuffer:    make([]ErrorEvent, 0),
        patternMatcher: NewErrorPatternMatcher(),
    }
}

func (ea *ErrorAggregator) RecordError(event ErrorEvent) {
    ea.mu.Lock()
    defer ea.mu.Unlock()

    // 添加到缓冲区
    ea.errorBuffer = append(ea.errorBuffer, event)

    // 保持窗口大小
    cutoff := time.Now().Add(-ea.windowSize)
    for i := 0; i < len(ea.errorBuffer); i++ {
        if ea.errorBuffer[i].Timestamp.Before(cutoff) {
            ea.errorBuffer = ea.errorBuffer[i:]
            break
        }
    }

    // 检查错误模式
    patterns := ea.patternMatcher.MatchPatterns(event)
    for _, pattern := range patterns {
        ea.handlePatternMatch(event, pattern)
    }
}

func (ea *ErrorAggregator) handlePatternMatch(event ErrorEvent, pattern ErrorPattern) {
    switch pattern.Action {
    case "alert":
        log.Printf("错误模式匹配告警: %s - %s (模式: %s)", event.ErrorType, event.Message, pattern.Pattern)
    case "log":
        log.Printf("错误模式记录: %s - %s (模式: %s)", event.ErrorType, event.Message, pattern.Pattern)
    case "ignore":
        // 忽略此错误
    }
}

func (ea *ErrorAggregator) GetErrorReport(startTime, endTime time.Time) *ErrorReport {
    ea.mu.RLock()
    defer ea.mu.RUnlock()

    var events []ErrorEvent
    errorStats := make(map[string]int)
    serviceStats := make(map[string]int)

    for _, event := range ea.errorBuffer {
        if event.Timestamp.After(startTime) && event.Timestamp.Before(endTime) {
            events = append(events, event)
            errorStats[event.ErrorType]++
            serviceStats[event.ServiceName]++
        }
    }

    return &ErrorReport{
        StartTime:    startTime,
        EndTime:      endTime,
        TotalEvents:   len(events),
        Events:       events,
        ErrorStats:   errorStats,
        ServiceStats:  serviceStats,
    }
}

type ErrorReport struct {
    StartTime    time.Time              `json:"start_time"`
    EndTime      time.Time              `json:"end_time"`
    TotalEvents  int                   `json:"total_events"`
    Events       []ErrorEvent          `json:"events"`
    ErrorStats   map[string]int         `json:"error_stats"`
    ServiceStats  map[string]int         `json:"service_stats"`
}

type ErrorPatternMatcher struct {
    patterns []ErrorPattern
    mu       sync.RWMutex
}

func NewErrorPatternMatcher() *ErrorPatternMatcher {
    return &ErrorPatternMatcher{
        patterns: []ErrorPattern{
            {
                Pattern:  "timeout|deadline",
                Type:     "timeout_error",
                Priority: 1,
                Action:   "alert",
            },
            {
                Pattern:  "connection.*fail",
                Type:     "connection_error",
                Priority: 2,
                Action:   "alert",
            },
            {
                Pattern:  "permission.*denied",
                Type:     "authorization_error",
                Priority: 3,
                Action:   "log",
            },
        },
    }
}

func (epm *ErrorPatternMatcher) AddPattern(pattern ErrorPattern) {
    epm.mu.Lock()
    defer epm.mu.Unlock()

    epm.patterns = append(epm.patterns, pattern)
    // 按优先级排序
    sort.Slice(epm.patterns, func(i, j int) bool {
        return epm.patterns[i].Priority < epm.patterns[j].Priority
    })
}

func (epm *ErrorPatternMatcher) MatchPatterns(event ErrorEvent) []ErrorPattern {
    epm.mu.RLock()
    defer epm.mu.RUnlock()

    var matchedPatterns []ErrorPattern

    for _, pattern := range epm.patterns {
        matched, _ := regexp.MatchString(pattern.Pattern, event.Message)
        if matched {
            matchedPatterns = append(matchedPatterns, pattern)
        }
    }

    return matchedPatterns
}

// 使用示例
func ExampleUsage() {
    monitor := NewErrorMonitor()
    aggregator := NewErrorAggregator(time.Hour)

    // 配置告警规则
    monitor.AddAlert("service_unavailable", 10, time.Minute, "https://hooks.slack.com/services/xxx")
    monitor.AddAlert("internal_server", 5, time.Minute*5, "https://hooks.slack.com/services/xxx")

    // 启动定期重置
    monitor.StartPeriodicReset(time.Hour)

    // 配置自定义错误模式
    aggregator.patternMatcher.AddPattern(ErrorPattern{
        Pattern:  "payment.*failed",
        Type:     "payment_error",
        Priority: 1,
        Action:   "alert",
    })

    // 模拟错误记录
    err := errors.ServiceUnavailable("service down")
    monitor.RecordError(err, "user-service", "GetUser")
    aggregator.RecordError(ErrorEvent{
        Timestamp:   time.Now(),
        ServiceName: "user-service",
        Method:      "GetUser",
        ErrorType:   "service_unavailable",
        Message:     "service down",
        TraceID:     "trace-123",
    })

    err = errors.InternalServer("database connection failed")
    monitor.RecordError(err, "order-service", "CreateOrder")
    aggregator.RecordError(ErrorEvent{
        Timestamp:   time.Now(),
        ServiceName: "order-service",
        Method:      "CreateOrder",
        ErrorType:   "internal_server",
        Message:     "database connection failed",
        TraceID:     "trace-456",
    })

    // 生成错误报告
    report := aggregator.GetErrorReport(time.Now().Add(-time.Hour), time.Now())
    log.Printf("错误报告: 总事件=%d, 错误统计=%+v", report.TotalEvents, report.ErrorStats)
}
```

### 最佳实践建议

#### **错误处理策略**
1. **分层错误处理**
   - **数据层错误**：数据库操作错误
   - **业务层错误**：业务逻辑错误
   - **接口层错误**：API 调用错误
   - **系统层错误**：基础设施错误

2. **错误信息规范化**
   - 使用标准的错误码
   - 提供清晰的错误描述
   - 包含足够的调试信息
   - 避免敏感信息泄露

3. **错误恢复机制**
   - 实现自动重试策略
   - 使用熔断器保护
   - 提供降级方案
   - 确保最终一致性

4. **错误监控和分析**
   - 实时错误收集
   - 错误率统计
   - 告警机制
   - 错误趋势分析

这些自定义错误返回机制提供了完整的错误处理解决方案，帮助开发者构建更加健壮和可靠的分布式系统。

## 扩展性
基于Wrapper（中间件）
