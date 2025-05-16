// pages/backend-test.tsx
import { useEffect, useState } from 'react';

export default function BackendTestPage() {
  const [response, setResponse] = useState('');

  const backendUrl = 'https://python-backend-459331316403.us-central1.run.app';

  useEffect(() => {
    fetch(`${backendUrl}/api/projects`)  // adjust endpoint if your backend serves API here
      .then((res) => res.text()) // or .json() if backend sends JSON
      .then((data) => setResponse(data))
      .catch((err) => setResponse(`Error: ${err.message}`));
  }, []);

  return (
    <div style={{ padding: '2rem', fontFamily: 'sans-serif' }}>
      <h1>Backend Test</h1>
      <p><strong>Response from backend:</strong></p>
      <pre>{response}</pre>
    </div>
  );
}
