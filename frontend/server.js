#!/usr/bin/env node

/**
 * Production server for DayPlanner Frontend
 * This file is used to run the Next.js application in production mode
 */

const { createServer } = require('http')
const { parse } = require('url')
const next = require('next')

// Load environment variables
require('dotenv').config({ path: '../.env.production' })

const dev = process.env.NODE_ENV !== 'production'
const hostname = process.env.FRONTEND_HOST || '127.0.0.1'
const port = parseInt(process.env.FRONTEND_PORT || '3500', 10)

// Create Next.js app
const app = next({ dev, hostname, port })
const handle = app.getRequestHandler()

// Graceful shutdown handling
process.on('SIGTERM', () => {
  console.log('SIGTERM received, shutting down gracefully')
  process.exit(0)
})

process.on('SIGINT', () => {
  console.log('SIGINT received, shutting down gracefully')
  process.exit(0)
})

// Error handling
process.on('uncaughtException', (err) => {
  console.error('Uncaught Exception:', err)
  process.exit(1)
})

process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason)
  process.exit(1)
})

app.prepare().then(() => {
  createServer(async (req, res) => {
    try {
      // Parse the URL
      const parsedUrl = parse(req.url, true)
      
      // Handle the request
      await handle(req, res, parsedUrl)
    } catch (err) {
      console.error('Error occurred handling', req.url, err)
      res.statusCode = 500
      res.end('Internal Server Error')
    }
  })
  .once('error', (err) => {
    console.error('Server error:', err)
    process.exit(1)
  })
  .listen(port, hostname, () => {
    console.log(`> Ready on http://${hostname}:${port}`)
    console.log(`> Environment: ${process.env.NODE_ENV}`)
    console.log(`> API Base URL: ${process.env.NEXT_PUBLIC_API_BASE_URL}`)
  })
})
