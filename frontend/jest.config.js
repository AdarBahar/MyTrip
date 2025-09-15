const nextJest = require('next/jest')

const createJestConfig = nextJest({
  // Provide the path to your Next.js app to load next.config.js and .env files
  dir: './',
})

// Add any custom config to be passed to Jest
const customJestConfig = {
  // Test environment
  testEnvironment: 'jsdom',
  
  // Setup files
  setupFilesAfterEnv: ['<rootDir>/tests/setup.ts'],
  
  // Test patterns
  testMatch: [
    '<rootDir>/tests/**/*.test.(ts|tsx)',
    '<rootDir>/components/**/*.test.(ts|tsx)',
    '<rootDir>/lib/**/*.test.(ts|tsx)',
    '<rootDir>/app/**/*.test.(ts|tsx)',
  ],
  
  // Module name mapping
  moduleNameMapping: {
    '^@/(.*)$': '<rootDir>/$1',
  },
  
  // Coverage configuration
  collectCoverageFrom: [
    'app/**/*.{ts,tsx}',
    'components/**/*.{ts,tsx}',
    'lib/**/*.{ts,tsx}',
    '!**/*.d.ts',
    '!**/node_modules/**',
    '!**/.next/**',
    '!**/coverage/**',
    '!**/tests/**',
  ],
  
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70,
    },
  },
  
  // Test timeout
  testTimeout: 10000,
  
  // Verbose output
  verbose: true,
  
  // Transform configuration
  transform: {
    '^.+\\.(ts|tsx)$': ['ts-jest', {
      tsconfig: 'tsconfig.json',
    }],
  },
  
  // Module file extensions
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json'],
  
  // Ignore patterns
  testPathIgnorePatterns: [
    '<rootDir>/.next/',
    '<rootDir>/node_modules/',
    '<rootDir>/coverage/',
  ],
  
  // Global setup/teardown
  globalSetup: '<rootDir>/tests/global-setup.ts',
  globalTeardown: '<rootDir>/tests/global-teardown.ts',
  
  // Reporter configuration
  reporters: [
    'default',
    ['jest-html-reporters', {
      publicPath: './coverage',
      filename: 'test-report.html',
      expand: true,
    }],
  ],
  
  // Clear mocks between tests
  clearMocks: true,
  restoreMocks: true,
  
  // Error handling
  errorOnDeprecated: true,
  
  // Watch mode configuration
  watchPathIgnorePatterns: [
    '<rootDir>/node_modules/',
    '<rootDir>/.next/',
    '<rootDir>/coverage/',
  ],
}

// Create Jest config with Next.js integration
module.exports = createJestConfig(customJestConfig)
