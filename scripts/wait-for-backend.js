#!/usr/bin/env node

/**
 * Wait for Backend Health Check
 * 
 * This script waits for the backend to be ready before starting the frontend.
 * It polls the /api/health endpoint until it responds successfully.
 */

import http from 'http';

const BACKEND_URL = 'http://localhost:5001';
const HEALTH_ENDPOINT = '/api/health';
const MAX_RETRIES = 30; // 30 seconds max wait
const RETRY_INTERVAL = 1000; // 1 second between retries

function checkBackendHealth() {
  return new Promise((resolve, reject) => {
    const req = http.get(`${BACKEND_URL}${HEALTH_ENDPOINT}`, (res) => {
      if (res.statusCode === 200) {
        resolve(true);
      } else {
        reject(new Error(`Backend responded with status ${res.statusCode}`));
      }
    });

    req.on('error', (err) => {
      reject(err);
    });

    req.setTimeout(5000, () => {
      req.destroy();
      reject(new Error('Backend health check timeout'));
    });
  });
}

async function waitForBackend() {
  console.log('🔍 Waiting for backend to be ready...');
  
  for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
    try {
      await checkBackendHealth();
      console.log('✅ Backend is ready! Starting frontend...');
      process.exit(0);
    } catch (error) {
      if (attempt === MAX_RETRIES) {
        console.error('❌ Backend failed to start within the timeout period');
        console.error('   You can still start the frontend manually with: npm run dev:frontend');
        process.exit(1);
      }
      
      console.log(`⏳ Attempt ${attempt}/${MAX_RETRIES}: Backend not ready yet (${error.message})`);
      await new Promise(resolve => setTimeout(resolve, RETRY_INTERVAL));
    }
  }
}

// Handle process termination
process.on('SIGINT', () => {
  console.log('\n🛑 Wait script interrupted');
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.log('\n🛑 Wait script terminated');
  process.exit(0);
});

// Start waiting
waitForBackend().catch((error) => {
  console.error('💥 Unexpected error:', error);
  process.exit(1);
}); 