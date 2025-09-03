import { NextResponse } from 'next/server';

/**
 * Kubernetes readiness probe endpoint
 * Returns 200 OK when the application is ready to serve traffic
 */
export async function GET() {
  try {
    // Check if the application is ready to serve requests
    const readinessChecks = {
      server: checkServerReady(),
      environment: checkEnvironmentReady(),
      dependencies: await checkDependenciesReady()
    };

    const allReady = Object.values(readinessChecks).every(check => check.ready);

    const response = {
      status: allReady ? 'ready' : 'not_ready',
      timestamp: new Date().toISOString(),
      checks: readinessChecks
    };

    return NextResponse.json(response, { 
      status: allReady ? 200 : 503 
    });
  } catch (error) {
    console.error('Readiness check failed:', error);
    
    return NextResponse.json(
      {
        status: 'not_ready',
        timestamp: new Date().toISOString(),
        error: error instanceof Error ? error.message : 'Readiness check failed'
      },
      { status: 503 }
    );
  }
}

/**
 * Check if the server is ready
 */
function checkServerReady(): { ready: boolean; details: any } {
  try {
    // Basic server readiness checks
    const memUsage = process.memoryUsage();
    const heapUsagePercent = (memUsage.heapUsed / memUsage.heapTotal) * 100;
    
    // Consider ready if memory usage is reasonable and uptime is sufficient
    const ready = heapUsagePercent < 95 && process.uptime() > 1;
    
    return {
      ready,
      details: {
        uptime: Math.floor(process.uptime()),
        heapUsagePercent: Math.round(heapUsagePercent * 100) / 100,
        pid: process.pid
      }
    };
  } catch (error) {
    return {
      ready: false,
      details: { error: error instanceof Error ? error.message : 'Server check failed' }
    };
  }
}

/**
 * Check if the environment is properly configured
 */
function checkEnvironmentReady(): { ready: boolean; details: any } {
  try {
    const requiredEnvVars = ['NODE_ENV'];
    const missingVars = requiredEnvVars.filter(varName => !process.env[varName]);
    
    const ready = missingVars.length === 0;
    
    return {
      ready,
      details: {
        nodeEnv: process.env.NODE_ENV || 'not_set',
        missingVars: missingVars.length > 0 ? missingVars : undefined,
        configuredVars: requiredEnvVars.filter(varName => process.env[varName])
      }
    };
  } catch (error) {
    return {
      ready: false,
      details: { error: error instanceof Error ? error.message : 'Environment check failed' }
    };
  }
}

/**
 * Check if dependencies are ready
 */
async function checkDependenciesReady(): Promise<{ ready: boolean; details: any }> {
  try {
    // For frontend, we mainly need to ensure the application can start
    // In a more complex setup, this could check database connections, etc.
    
    const details: any = {
      nextjs: 'available',
      staticAssets: 'checking'
    };
    
    // Quick check for critical files
    try {
      const { promises: fs } = await import('fs');
      const path = await import('path');
      
      // Check if package.json exists (basic dependency check)
      await fs.access(path.join(process.cwd(), 'package.json'));
      details.packageJson = 'available';
      
      // In production, check for build artifacts
      if (process.env.NODE_ENV === 'production') {
        try {
          await fs.access(path.join(process.cwd(), '.next'));
          details.buildArtifacts = 'available';
        } catch {
          details.buildArtifacts = 'missing';
          return {
            ready: false,
            details: { ...details, error: 'Build artifacts missing in production' }
          };
        }
      }
      
      details.staticAssets = 'available';
      
    } catch (error) {
      return {
        ready: false,
        details: { 
          ...details, 
          error: error instanceof Error ? error.message : 'Dependency check failed' 
        }
      };
    }
    
    return {
      ready: true,
      details
    };
  } catch (error) {
    return {
      ready: false,
      details: { error: error instanceof Error ? error.message : 'Dependencies check failed' }
    };
  }
}