import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Navbar from './components/Navbar/Navbar';
import Home from './pages/Home/Home';
import Marketplace from './pages/Marketplace/Marketplace';
import Portfolio from './pages/Portfolio/Portfolio';
import Login from './pages/Login/Login';
import ForgotPassword from './pages/Login/ForgotPassword';
import Signup from './pages/Signup/Signup';
import Profile from './pages/Profile/Profile';
import KYC from './pages/KYC/KYC';
import LoanRequest from './pages/LoanRequest/LoanRequest';
import Payment from './pages/Payment/Payment';
import DevKycCheck from './pages/DevKycCheck/DevKycCheck';

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="app">
          <Navbar />
          <div className="content">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/marketplace" element={<Marketplace />} />
              <Route path="/portfolio" element={<Portfolio />} />
              <Route path="/login" element={<Login />} />
              <Route path="/forgot-password" element={<ForgotPassword />} />
              <Route path="/signup" element={<Signup />} />
              <Route path="/profile" element={<Profile />} />
              <Route path="/kyc" element={<KYC />} />
              <Route path="/request-loan" element={<LoanRequest />} />
              <Route path="/payment" element={<Payment />} />
              <Route path="/dev-kyc-check" element={<DevKycCheck />} />
            </Routes>
          </div>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
