import './TrafficDashboard.css'; // Đảm bảo import file CSS vào
import IntersectionCard from './IntersectionCard';
import { useState, useEffect } from 'react';

const TrafficDashboard = () => {
    const [roads, setRoads] = useState([]);
    const [loading, setLoading] = useState(true);
    const server_url = "http://localhost:8080";

    const fetchRoads = async () => {
        try {
            setLoading(true);
            const response = await fetch(`${server_url}/api/roads/device/all`);
            const data = await response.json();
            setRoads(data);
            setLoading(false);
        } catch (error) {
            console.error('Error fetching roads:', error);
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchRoads();
    }, []);

    return (
        <div className="dashboard">

            {/* Sub Header */}
            <div className="sub-header">
                <div className="filter-buttons">
                    <button className="filter-button">Tất Cả</button>
                    <button className="filter-button active">Giao thông</button>
                    <button className="filter-button">An ninh trật tự</button>
                    <button className="filter-button">FACEID</button>
                    <button className="filter-button">Công trường</button>
                </div>

                <div className="search-area">
                    <div className="search-icon-container">
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            className="search-icon"
                            viewBox="0 0 20 20"
                            fill="currentColor"
                        >
                            <path
                                fillRule="evenodd"
                                d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z"
                                clipRule="evenodd"
                            />
                        </svg>
                    </div>
                    <input className="search-input" placeholder="Tìm kiểm" />
                    <button className="settings-button">
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            className="settings-icon"
                            viewBox="0 0 20 20"
                            fill="currentColor"
                        >
                            <path
                                fillRule="evenodd"
                                d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z"
                                clipRule="evenodd"
                            />
                        </svg>
                    </button>
                </div>
            </div>

            {/* Camera Feeds Grid */}
            <div className="feeds-grid">
                {loading ? (
                    <p>Đang tải dữ liệu...</p>
                ) : roads.length === 0 ? (
                    <p>Không có dữ liệu đường giao thông.</p>
                ) : (
                roads.map((feed) => (
                    <IntersectionCard key={feed.id} feed={feed} />
                )) )}
            </div>
        </div>
    );
};

// Traffic light component with timers

export default TrafficDashboard;
