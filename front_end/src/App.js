import React from 'react';
import './App.css';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import TrafficDashboard from './components/TrafficDashboard';
import StatsDisplay from './components/StatsDisplay';
import RoadManager from './components/RoadManager';
import DeviceManager from './components/DeviceManager';

function App() {
    return (
        <Router>
            <div className="App">
                <nav className="main-nav">
                    <div className="nav-logo">
                        <span>Traffic Management System</span>
                    </div>
                    <ul className="nav-items">
                        <li className="nav-item">
                            <Link to="/">Dashboard</Link>
                        </li>
                        <li className="nav-item">
                            <Link to="/roads">Quản lý đường đi</Link>
                        </li>
                        <li className="nav-item">
                            <Link to="/devices">Quản lý thiết bị</Link>
                        </li>
                        <li className="nav-item">
                            <Link to="/stats">Thống kê</Link>
                        </li>
                    </ul>
                </nav>

                <div className="content-container">
                    <Routes>
                        <Route path="/" element={<TrafficDashboard />} />
                        <Route path="/roads" element={<RoadManager />} />
                        <Route path="/devices" element={<DeviceManager />} />
                        <Route path="/stats" element={<StatsDisplay />} />
                    </Routes>
                </div>
            </div>
        </Router>
    );
}

export default App;