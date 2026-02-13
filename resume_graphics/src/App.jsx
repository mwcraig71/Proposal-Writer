import React from 'react';
import { HashRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import GraphicBuilder from './pages/GraphicBuilder';
import BadgeBuilder from './pages/BadgeBuilder';
import KeyStaff from './pages/KeyStaff';
import SavedGraphics from './pages/SavedGraphics';

export default function App() {
  return (
    <HashRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<GraphicBuilder />} />
          <Route path="/badges" element={<BadgeBuilder />} />
          <Route path="/key-staff" element={<KeyStaff />} />
          <Route path="/saved" element={<SavedGraphics />} />
        </Routes>
      </Layout>
    </HashRouter>
  );
}
