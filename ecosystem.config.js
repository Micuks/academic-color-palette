module.exports = {
  apps: [{
    name: 'palette-api',
    script: 'backend_server.py',
    interpreter: 'python3',
    cwd: '/root/.openclaw/workspace/academic-color-palette',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'production'
    },
    error_file: '/tmp/palette-api-error.log',
    out_file: '/tmp/palette-api-out.log',
    log_file: '/tmp/palette-api.log',
    time: true
  }]
};