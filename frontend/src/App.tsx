/**
 * Main Application Component
 * 
 * Sets up routing and global layout for the AI Voice Agent admin interface.
 */

import { Routes, Route } from 'react-router-dom';
import { Layout } from '@/components/layout';
import { DashboardPage, ConfigurationPage } from '@/pages';

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/config" element={<ConfigurationPage />} />
        <Route path="/calls" element={<CallsPlaceholder />} />
      </Routes>
    </Layout>
  );
}

// Placeholder for calls page (will be implemented in feat: call-ui)
function CallsPlaceholder() {
  return (
    <div className="text-center py-12">
      <h2 className="text-xl font-semibold text-slate-900">Calls & Testing</h2>
      <p className="text-slate-500 mt-2">Coming in next commit: feat: call-ui</p>
    </div>
  );
}

export default App;
