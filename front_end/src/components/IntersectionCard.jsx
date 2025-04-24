import { useEffect, useState } from 'react';
import './TrafficDashboard.css';
import TrafficLight from './TrafficLight';
import { Box, Button, FormControlLabel, Stack, Switch, TextField, Typography } from '@mui/material';
import { Flare, Label } from '@mui/icons-material';

// Individual intersection card with dual video feeds
const IntersectionCard = ({ feed }) => {
    const [totalDown, setTotalDown] = useState('N/A');
    const [fps, setFps] = useState('N/A');
    const [downByClass, setDownByClass] = useState([]);
    const [isAutoMode, setIsAutoMode] = useState(true);
    const [cycleDuration, setCycleDuration] = useState(0); // Default cycle duration in seconds
    const [pendingCycleDuration, setPendingCycleDuration] = useState(10);
    const [cycleUpdatePending, setCycleUpdatePending] = useState(false);
    const [inputGreen, setInputGreen] = useState('');
    const [inputRed, setInputRed] = useState('');
    const [light1, setLight1] = useState({})
    const [light2, setLight2] = useState({})
    useEffect(() => {
        const wsUrl = `http://localhost:8080/ws/stats/1`;
        console.log(`Attempting to connect WebSocket to: ${wsUrl}`);

        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            console.log('WebSocket connection opened');
            setDownByClass([]);
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);

                if (data.total_down !== undefined) {
                    setTotalDown(data.total_down);
                } else {
                    setTotalDown('N/A');
                }

                if (data.fps !== undefined) {
                    setFps(data.fps.toFixed(1));
                } else {
                    setFps('N/A');
                }

                if (data.down_by_class && typeof data.down_by_class === 'object') {
                    const sorted = Object.entries(data.down_by_class).sort(([a], [b]) => a.localeCompare(b));
                    setDownByClass(sorted);
                } else {
                    setDownByClass([['Data not available', null]]);
                }
            } catch (err) {
                console.error('Error processing WebSocket message:', err);
                console.error('Raw data:', event.data);
                setDownByClass([['Error loading data', null]]);
            }
        };

        ws.onerror = (event) => {
            console.error('WebSocket error observed:', event);
            setTotalDown('Error');
            setFps('Error');
            setDownByClass([['WebSocket Error', null]]);
        };

        ws.onclose = (event) => {
            console.log(`WebSocket closed: Code=${event.code}, Reason=${event.reason}, WasClean=${event.wasClean}`);
            setTotalDown('Disconnected');
            setFps('N/A');
            setDownByClass([['Connection Closed', null]]);
        };

        return () => {
            ws.close();
        };
    }, []);
    useEffect(()=>{
        const mqttUrl1 = 'http://localhost:8080/ws/mqtt1'
        const mqttUrl2 = 'http://localhost:8080/ws/mqtt2'
        const ws1 = new WebSocket(mqttUrl1);
        const ws2 = new WebSocket(mqttUrl2);
        ws1.onopen = () => {
            console.log('WebSocket connection opened');
            setDownByClass([]);
        };
        ws1.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                const {messages} = data;
                console.log('messages', messages);
                if (messages) {
                    messages.forEach(value => {
                        if(parseInt(value?.road) === 1){
                            setLight1(value);
                        }
                    });
                }
                console.log('Received data MQTT:', data);
            } catch (err) {
                console.error('Error processing WebSocket message:', err);
            }
        };
        ws1.onerror = (event) => {
            console.error('WebSocket error observed:', event);
        };
        ws1.onclose = (event) => {
            console.log(`WebSocket closed: Code=${event.code}, Reason=${event.reason}, WasClean=${event.wasClean}`);
        };

        ws2.onopen = () => {
            console.log('WebSocket connection opened');
            setDownByClass([]);
        };
        ws2.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                const {messages} = data;
                console.log('messages', messages);
                if (messages) {
                    messages.forEach(value => {
                        if(parseInt(value?.road) === 2){
                            setLight2( value);
                        }
                    });
                }
                console.log('Received data MQTT:', data);
            } catch (err) {
                console.error('Error processing WebSocket message:', err);
            }
        };
        ws2.onerror = (event) => {
            console.error('WebSocket error observed:', event);
        };
        ws2.onclose = (event) => {
            console.log(`WebSocket closed: Code=${event.code}, Reason=${event.reason}, WasClean=${event.wasClean}`);
        };

        return () => {
            ws1.close();
            ws2.close();
        };
    },[])
    // console.log('light', light);

    const handleModeToggle = () => {
        setIsAutoMode((prev) => !prev);
    };

    const handleInputChange = (e) => {
        if (e.target.name === 'green') {
            setInputGreen(e.target.value);
        }
        if (e.target.name === 'red') {
            setInputRed(e.target.value);
        }
    };
    const handleConfirmCycle = async () => {
        const greenCycle = parseInt(inputGreen);
        const redCycle = parseInt(inputRed);
        if ( greenCycle> 0 && redCycle > 0) {
            const inputValue = greenCycle + ',' + redCycle;
            setCycleUpdatePending(true);
            const res = await fetch(`http://localhost:8080/api/cycle?message=${inputValue}`, {
                method: 'POST',
                // headers: {
                //     'Content-Type': 'application/json',
                // },
                // body: JSON.stringify({ green: greenCycle, red: redCycle }),
            });
            if (res.ok) {
                console.log('Cycle duration updated successfully');
            } else {
                console.error('Error updating cycle duration:', res.statusText);
            }
            setInputGreen('');
            setInputRed('');
            setCycleUpdatePending(false);
            // setCycleUpdatePending(true);
            // setPendingCycleDuration(inputValue);
            // console.log('Cycle duration set to:', inputValue);
        }
    };
    // console.log('pendingCycleDuration ', pendingCycleDuration);
    const handleUpdateCycle = () => {
        if (cycleUpdatePending) {
            setCycleDuration(pendingCycleDuration);
            setCycleUpdatePending(false);
            // setInputValue(pendingCycleDuration);
        }
    };
    return (
        <div className="intersection-card">
            {/* Dual Camera Feed Images */}
            <div className="camera-feeds">
                {/* First Camera Feed */}
                <div className="camera-feed">
                    <div className="camera-image-container">
                        <img
                            src="http://localhost:8080/stream1.mjpg"
                            alt="Traffic camera view 1"
                            className="camera-image"
                        />
                    </div>

                    {/* Green bounding boxes overlay */}

                    {/* Traffic Light Component for first view */}
                    <TrafficLight light = {light1} />
                </div>

                {/* Second Camera Feed */}
                <div className="camera-feed">
                    <div className="camera-image-container">
                        <img
                            src="http://localhost:8080/stream2.mjpg"
                            alt="Traffic camera view 2"
                            className="camera-image"
                        />
                    </div>

                    {/* Green bounding boxes overlay */}

                    {/* Traffic Light Component for second view */}
                    {
                        console.log("light", light2)
                    }
                    <TrafficLight light={light2} />
                </div>
            </div>

            {/* Info Section - Common for both cameras in the intersection */}
            <div className="feed-info">
                <div className="feed-location">{feed.location}</div>
                <div className="feed-detail">
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        className="detail-icon"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                    >
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
                        />
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
                        />
                    </svg>
                    {feed.street}
                </div>
                <div className="feed-detail">
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        className="detail-icon"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                    >
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                        />
                    </svg>
                    {feed.time}
                </div>
                <div className="feed-detail">
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        className="detail-icon"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                    >
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
                        />
                    </svg>
                    {feed.area}
                </div>
                <div className="feed-detail">Lưu lượng: {totalDown}</div>
                <div className="feed-detail">FPS: {fps}</div>
                <div className='feed-detail'>Thời gian: {light1?.content} </div>

                <Box className="traffic-control" sx={{ mt: 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1, justifyContent: 'space-between' }}>
                        {/* <FormControlLabel
                            label="Chế độ tự động"
                            control={<Switch checked={isAutoMode} onChange={handleModeToggle} color="primary" />}
                            labelPlacement="start"
                            sx={{ ml: 0.5 }}
                        /> */}
                        <span>Chế độ tự động</span>
                        <Switch
                            checked={isAutoMode}
                            onChange={handleModeToggle}
                            color="primary"
                            style={{ justifyContent: 'end' }}
                        />
                    </Box>

                    {!isAutoMode && (
                        <Box
                            sx={{
                                mt: 1,
                                p: 1,
                                bgcolor: 'background.paper',
                                borderRadius: 1,
                                boxShadow: 1,
                            }}
                        >
                            <Stack direction="row" spacing={1} alignItems="center" marginTop={1}>
                                <TextField
                                    label="Chu kỳ đèn xanh (giây)"
                                    name='green'
                                    type="number"
                                    size="small"
                                    value={inputGreen}
                                    onChange={handleInputChange}
                                    sx={{ width: '250px' }}
                                />
                                <TextField
                                    label="Chu kỳ đèn đỏ (giây)"
                                    name='red'
                                    type="number"
                                    size="small"
                                    value={inputRed}
                                    onChange={handleInputChange}
                                    sx={{ width: '250px' }}
                                />
                                <Button variant="contained" size="small" color="primary" style={{fontSize:12}} onClick={handleConfirmCycle}>
                                    Xác nhận
                                </Button>
                            </Stack>
                            {cycleUpdatePending && (
                                <Typography
                                    variant="caption"
                                    sx={{
                                        display: 'block',
                                        mt: 1,
                                        color: 'warning.main',
                                        fontStyle: 'italic',
                                    }}
                                >
                                    Sẽ áp dụng sau khi hoàn thành chu kỳ hiện tại
                                </Typography>
                            )}
                        </Box>
                    )}
                </Box>
            </div>

            {/* Bottom Action */}
            <div className="feed-action">
                <button className="error-btn">Báo lỗi</button>
            </div>
        </div>
    );
};

export default IntersectionCard;
