import { useEffect, useState } from 'react';
import './TrafficDashboard.css';
const TrafficLight = ({ position, cycle, updateCycle }) => {
    const [lightState, setLightState] = useState(position === 'left' ? 'green' : 'red');
    const [timer, setTimer] = useState(position === 'left' ? parseInt(cycle) : parseInt(cycle) + 5); // Start with green for left and red for right

    useEffect(() => {
        const interval = setInterval(() => {
            setTimer((prevTimer) => {
                if (prevTimer <= 1) {
                    // Change light state when timer reaches 0
                    if (lightState === 'red') {
                        setLightState('green');
                        return parseInt(cycle); // Green light duration
                    } else if (lightState === 'green') {
                        setLightState('yellow');
                        return 5; // Yellow light duration
                    } else {
                        setLightState('red');
                        return parseInt(cycle) + 5; // Red light duration
                    }
                }
                return prevTimer - 1;
            });
        }, 1000);

        return () => clearInterval(interval);
    }, [lightState, cycle]);

    if (position === 'left') {
        console.log('cycle', cycle);
        console.log('tỉmer', timer);
    }

    useEffect(() => {
        if (lightState === 'yellow' && updateCycle) {
            updateCycle();
        }
    }, [lightState]);
    // console.log('position ' + position + ';lightState ' + lightState + ';timer ', timer);

    return (
        <div className="traffic-light">
            <div className="light-container">
                <div className={`light red ${lightState === 'red' ? 'active' : ''}`}></div>
                <div className={`light yellow ${lightState === 'yellow' ? 'active' : ''}`}></div>
                <div className={`light green ${lightState === 'green' ? 'active' : ''}`}></div>
            </div>
            <div className="timer">{timer}s</div>
        </div>
    );
};

export default TrafficLight;
