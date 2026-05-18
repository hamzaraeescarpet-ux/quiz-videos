import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import History from './pages/History';
import Pricing from './pages/Pricing';
import Navbar from './components/Navbar';
import { AuthProvider } from './AuthContext';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <div className="min-h-screen bg-dark-900 text-white flex flex-col font-sans">
          <Navbar />
          <main className="flex-grow container mx-auto p-4 md:p-8">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/history" element={<History />} />
              <Route path="/pricing" element={<Pricing />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
