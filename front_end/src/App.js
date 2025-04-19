import logo from './logo.svg';
import './App.css';
import TrafficDashboard from './components/TrafficDashboard';
import StatsDisplay from './components/StatsDisplay';

function App() {
    return (
        <div className="App">
            {/* <StatsDisplay/> */}
            <TrafficDashboard />
        </div>
    );
}

export default App;
