/**
 * Test Page
 * Simple test to verify Next.js is working
 */

export default function TestPage() {
  return (
    <div style={{ padding: '20px' }}>
      <h1>Test Page</h1>
      <p>If you can see this page, Next.js is working correctly.</p>
      <p>Current time: {new Date().toISOString()}</p>
      
      <div style={{
        marginTop: '20px',
        padding: '20px',
        backgroundColor: '#f0f0f0',
        border: '1px solid #ccc',
        borderRadius: '8px'
      }}>
        <h2>Debug Test</h2>
        <p>This is a simple test page to verify the app is working.</p>
        <p>Visit this page at: <code>http://localhost:3000/test-page</code></p>
      </div>
    </div>
  );
}
