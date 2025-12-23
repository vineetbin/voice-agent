/**
 * Main Application Component
 * 
 * Sets up routing and global layout for the AI Voice Agent admin interface.
 */

import { Routes, Route } from 'react-router-dom';
import { Layout } from '@/components/layout';
import { DashboardPage, ConfigurationPage, CallsPage } from '@/pages';

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/config" element={<ConfigurationPage />} />
        <Route path="/calls" element={<CallsPage />} />
      </Routes>
    </Layout>
  );
}

export default App;
