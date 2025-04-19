import React, { useEffect, useRef, useState } from 'react';

const StatsDisplay = () => {
    const [totalDown, setTotalDown] = useState('N/A');
    const [fps, setFps] = useState('N/A');
    const [downByClass, setDownByClass] = useState([]);

    useEffect(() => {
        const wsUrl = `http://localhost:8081/ws/stats`;
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

    const handleImageError = () => {
        console.error('Failed to load video stream.');
    };

    return (
        <div>
            <h2>Live Stats</h2>
            <div>
                <strong>Total Down:</strong> {totalDown}
            </div>
            <div>
                <strong>FPS:</strong> {fps}
            </div>
            <div>
                <strong>Down by Class:</strong>
                <ul>
                    {downByClass.map(([key, value], index) =>
                        value !== null ? (
                            <li key={index}>
                                {key}: {value}
                            </li>
                        ) : (
                            <li key={index}>{key}</li>
                        ),
                    )}
                </ul>
            </div>
            <div>
                <img
                    id="video-stream"
                    src="http://localhost:8081/stream.mjpg" // endpoint phải có backend cung cấp ảnh (có thể thay đổi)
                    alt="Video Stream"
                    onError={handleImageError}
                    width={640}
                    height={480}
                />
            </div>
        </div>
    );
};

export default StatsDisplay;
