import { NextResponse } from 'next/server';

/**
 * Kubernetes liveness probe endpoint
 * Returns 200 OK when the application is alive and functioning
 * This should be a lightweight check that doesn't depend on external services
 */
export async function GET() {
  try {
    // Perform basic liveness checks
    const livenessChecks = {
      process: checkProcessAlive(),
      memory: checkMemoryLiveness(),
      server: checkServerLiveness()
    };

    const isAlive = Object.values(livenessChecks).every(check => check.alive);

    const response = {
      status: isAlive ? 'alive' : 'dead',
      timestamp: new Date().toISOString(),
      uptime: Math.floor(process.uptime()),
      checks: livenessChecks
    };

    return NextResponse.json(response, { 
      status: isAlive ? 200 : 503 
    });
  } catch (error) {
    console.error('Liveness check failed:', error);
    
    // If we can't even perform the liveness check, the process is likely in trouble
    return NextResponse.json(
      {
        status: 'dead',
        timestamp: new Date().toISOString(),
        error: error instanceof Error ? error.message : 'Liveness check failed'
      },
      { status: 503 }
    );
  }
}

/**
 * Check if the process is alive and responsive
 */
function checkProcessAlive(): { alive: boolean; details: any } {
  try {
    // Basic process health indicators
    const details = {
      pid: process.pid,
      uptime: Math.floor(process.uptime()),
      nodeVersion: process.version,
      platform: process.platform,
      arch: process.arch
    };
    
    // Process is alive if we can get these basic metrics
    // and uptime is reasonable (not negative or extremely high without restart)
    const uptime = process.uptime();
    const alive = uptime >= 0 && uptime < (30 * 24 * 60 * 60); // Less than 30 days
    
    return { alive, details };
  } catch (error) {
    return {
      alive: false,
      details: { error: error instanceof Error ? error.message : 'Process check failed' }
    };
  }
}

/**
 * Check memory usage for liveness (not readiness)
 * Only fail if memory usage is critically high
 */
function checkMemoryLiveness(): { alive: boolean; details: any } {
  try {
    const memUsage = process.memoryUsage();
    const heapUsagePercent = (memUsage.heapUsed / memUsage.heapTotal) * 100;
    const rssUsageMB = Math.round(memUsage.rss / 1024 / 1024);
    
    // Only consider dead if memory usage is critically high (>98%)
    // This is different from readiness which might be more conservative
    const alive = heapUsagePercent < 98;
    
    const details = {
      heapUsagePercent: Math.round(heapUsagePercent * 100) / 100,
      heapUsedMB: Math.round(memUsage.heapUsed / 1024 / 1024),
      heapTotalMB: Math.round(memUsage.heapTotal / 1024 / 1024),
      rssUsageMB,
      status: heapUsagePercent > 95 ? 'critical' : 
              heapUsagePercent > 80 ? 'high' : 'normal'
    };
    
    return { alive, details };
  } catch (error) {
    return {
      alive: false,
      details: { error: error instanceof Error ? error.message : 'Memory check failed' }
    };
  }
}

/**
 * Check if the server is responsive
 */
function checkServerLiveness(): { alive: boolean; details: any } {
  try {
    // Check if we can perform basic operations
    const startTime = Date.now();
    
    // Simple computation to verify the event loop is responsive
    let sum = 0;
    for (let i = 0; i < 1000; i++) {
      sum += i;
    }
    // Use sum to avoid unused variable warning
    const computationResult = sum > 0;
    
    const computationTime = Date.now() - startTime;
    
    // If basic computation takes too long, the server might be unresponsive
    const alive = computationTime < 100; // 100ms threshold
    
    const details = {
      computationTime: `${computationTime}ms`,
      eventLoopResponsive: alive,
      computationResult,
      timestamp: new Date().toISOString()
    };
    
    return { alive, details };
  } catch (error) {
    return {
      alive: false,
      details: { error: error instanceof Error ? error.message : 'Server responsiveness check failed' }
    };
  }
}