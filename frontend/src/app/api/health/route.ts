import { NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import path from 'path';

/**
 * Enhanced health check endpoint for container monitoring
 * Returns detailed health status with component checks
 */
export async function GET() {
  try {
    const startTime = Date.now();
    
    // Perform all health checks
    const [memoryCheck, buildCheck, staticAssetsCheck, backendConnectivityCheck] = await Promise.allSettled([
      checkMemoryUsage(),
      checkBuildHealth(),
      checkStaticAssets(),
      checkBackendConnectivity()
    ]);

    const responseTime = Date.now() - startTime;
    
    // Determine overall status
    let overallStatus = 'healthy';
    const checks: Record<string, any> = {};
    
    // Process memory check
    if (memoryCheck.status === 'fulfilled') {
      checks.memory = memoryCheck.value;
      if (memoryCheck.value.status !== 'ok') {
        overallStatus = 'degraded';
      }
    } else {
      checks.memory = { status: 'error', message: 'Memory check failed' };
      overallStatus = 'unhealthy';
    }
    
    // Process build check
    if (buildCheck.status === 'fulfilled') {
      checks.build = buildCheck.value;
      if (buildCheck.value.status === 'error') {
        overallStatus = 'unhealthy';
      }
    } else {
      checks.build = { status: 'error', message: 'Build check failed' };
      overallStatus = 'unhealthy';
    }
    
    // Process static assets check
    if (staticAssetsCheck.status === 'fulfilled') {
      checks.staticAssets = staticAssetsCheck.value;
      if (staticAssetsCheck.value.status === 'error') {
        overallStatus = 'degraded';
      }
    } else {
      checks.staticAssets = { status: 'error', message: 'Static assets check failed' };
      overallStatus = 'degraded';
    }
    
    // Process backend connectivity check
    if (backendConnectivityCheck.status === 'fulfilled') {
      checks.backendConnectivity = backendConnectivityCheck.value;
      if (backendConnectivityCheck.value.status === 'error') {
        overallStatus = 'degraded';
      }
    } else {
      checks.backendConnectivity = { status: 'error', message: 'Backend connectivity check failed' };
      overallStatus = 'degraded';
    }

    const healthStatus = {
      status: overallStatus,
      timestamp: new Date().toISOString(),
      uptime: Math.floor(process.uptime()),
      responseTime: `${responseTime}ms`,
      environment: process.env.NODE_ENV || 'development',
      version: process.env.npm_package_version || '1.0.0',
      nodeVersion: process.version,
      platform: process.platform,
      architecture: process.arch,
      checks,
      components: {
        server: {
          status: 'healthy',
          details: {
            pid: process.pid,
            uptime: `${Math.floor(process.uptime())}s`,
            nodeVersion: process.version
          }
        },
        application: {
          status: overallStatus === 'unhealthy' ? 'unhealthy' : 'healthy',
          details: {
            nextjs: 'running',
            environment: process.env.NODE_ENV || 'development',
            buildMode: process.env.NODE_ENV === 'production' ? 'production' : 'development'
          }
        }
      }
    };

    // Return appropriate HTTP status code based on health
    const httpStatus = overallStatus === 'unhealthy' ? 503 : 
                      overallStatus === 'degraded' ? 200 : 200;

    return NextResponse.json(healthStatus, { status: httpStatus });
  } catch (error) {
    console.error('Health check failed:', error);
    
    return NextResponse.json(
      {
        status: 'unhealthy',
        timestamp: new Date().toISOString(),
        uptime: Math.floor(process.uptime()),
        error: error instanceof Error ? error.message : 'Unknown error',
        components: {
          server: {
            status: 'error',
            details: { error: 'Health check exception' }
          }
        }
      },
      { status: 503 }
    );
  }
}

/**
 * Check memory usage and return detailed status
 */
async function checkMemoryUsage(): Promise<{ status: string; details: any }> {
  try {
    const memUsage = process.memoryUsage();
    const heapUsagePercent = (memUsage.heapUsed / memUsage.heapTotal) * 100;
    const rssUsageMB = Math.round(memUsage.rss / 1024 / 1024);
    const heapUsedMB = Math.round(memUsage.heapUsed / 1024 / 1024);
    const heapTotalMB = Math.round(memUsage.heapTotal / 1024 / 1024);
    
    let status = 'ok';
    if (heapUsagePercent > 90) {
      status = 'critical';
    } else if (heapUsagePercent > 75) {
      status = 'warning';
    }
    
    return {
      status,
      details: {
        heapUsagePercent: Math.round(heapUsagePercent * 100) / 100,
        heapUsedMB,
        heapTotalMB,
        rssUsageMB,
        external: Math.round(memUsage.external / 1024 / 1024),
        arrayBuffers: Math.round(memUsage.arrayBuffers / 1024 / 1024)
      }
    };
  } catch (error) {
    return {
      status: 'error',
      details: { error: error instanceof Error ? error.message : 'Memory check failed' }
    };
  }
}

/**
 * Check if the build is healthy and verify Next.js configuration
 */
async function checkBuildHealth(): Promise<{ status: string; details: any }> {
  try {
    const details: any = {
      nodeEnv: process.env.NODE_ENV || 'development',
      nextjsVersion: 'unknown',
      buildMode: process.env.NODE_ENV === 'production' ? 'production' : 'development'
    };
    
    // Try to get Next.js version from package.json
    try {
      const packageJsonPath = path.join(process.cwd(), 'package.json');
      const packageJson = JSON.parse(await fs.readFile(packageJsonPath, 'utf8'));
      details.nextjsVersion = packageJson.dependencies?.next || packageJson.devDependencies?.next || 'unknown';
      details.appVersion = packageJson.version || '1.0.0';
    } catch {
      // Package.json not accessible, continue with unknown version
    }
    
    // Check if we're in production and verify build artifacts
    if (process.env.NODE_ENV === 'production') {
      try {
        // Check for Next.js build directory
        const buildPath = path.join(process.cwd(), '.next');
        const buildStat = await fs.stat(buildPath);
        details.buildExists = buildStat.isDirectory();
        details.buildTime = buildStat.mtime.toISOString();
        
        // Check for static files
        const staticPath = path.join(buildPath, 'static');
        const staticStat = await fs.stat(staticPath);
        details.staticExists = staticStat.isDirectory();
        
        return {
          status: 'ok',
          details
        };
      } catch (error) {
        return {
          status: 'error',
          details: {
            ...details,
            error: 'Production build artifacts not found',
            buildExists: false
          }
        };
      }
    } else {
      // Development mode
      details.developmentMode = true;
      return {
        status: 'ok',
        details
      };
    }
  } catch (error) {
    return {
      status: 'error',
      details: { error: error instanceof Error ? error.message : 'Build check failed' }
    };
  }
}

/**
 * Check static assets availability
 */
async function checkStaticAssets(): Promise<{ status: string; details: any }> {
  try {
    const details: any = {};
    
    // Check public directory
    try {
      const publicPath = path.join(process.cwd(), 'public');
      const publicStat = await fs.stat(publicPath);
      details.publicDirExists = publicStat.isDirectory();
      
      // Check for common static files
      const commonFiles = ['favicon.ico', 'next.svg', 'vercel.svg'];
      const fileChecks: Record<string, boolean> = {};
      
      for (const file of commonFiles) {
        try {
          await fs.access(path.join(publicPath, file));
          fileChecks[file] = true;
        } catch {
          fileChecks[file] = false;
        }
      }
      
      details.staticFiles = fileChecks;
      details.staticFilesAvailable = Object.values(fileChecks).some(exists => exists);
      
    } catch (error) {
      details.publicDirExists = false;
      details.error = 'Public directory not accessible';
    }
    
    // In production, check for Next.js static assets
    if (process.env.NODE_ENV === 'production') {
      try {
        const nextStaticPath = path.join(process.cwd(), '.next', 'static');
        const nextStaticStat = await fs.stat(nextStaticPath);
        details.nextStaticExists = nextStaticStat.isDirectory();
      } catch {
        details.nextStaticExists = false;
      }
    }
    
    const status = details.publicDirExists ? 'ok' : 'warning';
    
    return { status, details };
  } catch (error) {
    return {
      status: 'error',
      details: { error: error instanceof Error ? error.message : 'Static assets check failed' }
    };
  }
}

/**
 * Check backend connectivity
 */
async function checkBackendConnectivity(): Promise<{ status: string; details: any }> {
  try {
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || process.env.API_URL || 'http://localhost:8000';
    const timeoutMs = 3000; // 3 second timeout
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
    
    try {
      const startTime = Date.now();
      const response = await fetch(`${backendUrl}/health`, {
        method: 'GET',
        signal: controller.signal,
        headers: {
          'User-Agent': 'Frontend-Health-Check/1.0'
        }
      });
      
      clearTimeout(timeoutId);
      const responseTime = Date.now() - startTime;
      
      const isHealthy = response.ok;
      let backendHealth = null;
      
      try {
        backendHealth = await response.json();
      } catch {
        // Backend didn't return JSON, that's okay for basic connectivity
      }
      
      return {
        status: isHealthy ? 'ok' : 'warning',
        details: {
          backendUrl,
          responseTime: `${responseTime}ms`,
          httpStatus: response.status,
          connected: true,
          backendStatus: backendHealth?.status || 'unknown'
        }
      };
    } catch (error) {
      clearTimeout(timeoutId);
      
      if (error instanceof Error && error.name === 'AbortError') {
        return {
          status: 'error',
          details: {
            backendUrl,
            connected: false,
            error: 'Connection timeout'
          }
        };
      }
      
      return {
        status: 'error',
        details: {
          backendUrl,
          connected: false,
          error: error instanceof Error ? error.message : 'Connection failed'
        }
      };
    }
  } catch (error) {
    return {
      status: 'error',
      details: { error: error instanceof Error ? error.message : 'Backend connectivity check failed' }
    };
  }
}