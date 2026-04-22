import { useState } from 'react';
import { DocumentProvider } from './contexts/DocumentContext';
import { Dashboard } from './components/dashboard/Dashboard';
import { LandingPage } from './components/LandingPage';
import { useTheme } from './hooks/useTheme';

function App() {
  useTheme(); // Apply theme on mount
  const [showLanding, setShowLanding] = useState(true);

  return (
    <DocumentProvider>
      <Dashboard />
      {showLanding && <LandingPage onEnter={() => setShowLanding(false)} />}
    </DocumentProvider>
  );
}

export default App;
