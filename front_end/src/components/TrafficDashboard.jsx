import './TrafficDashboard.css'; // Đảm bảo import file CSS vào
import IntersectionCard from './IntersectionCard';

const TrafficDashboard = () => {
    // Sample data for camera feeds at intersections
    const intersectionFeeds = [
        {
            id: 1,
            location: 'KHU VỰC MẶC ĐỊNH',
            street: 'Hướng đường Thành Thái',
            time: '09:06:29 14/11/2022',
            area: 'HẺM 7A THÀNH THÁI',
        },
        // { id: 2, location: "KHU VỰC MẶC ĐỊNH", street: "Hướng đường Thành Thái", time: "09:54:08 14/11/2022", area: "HẺM 7A THÀNH THÁI" },
        // { id: 3, location: "KHU VỰC MẶC ĐỊNH", street: "Hướng đường Thành Thái", time: "09:50:57 14/11/2022", area: "HẺM 7A THÀNH THÁI" },
        // { id: 4, location: "KHU VỰC MẶC ĐỊNH", street: "Hướng đường Thành Thái", time: "09:45:09 14/11/2022", area: "HẺM 7A THÀNH THÁI" },
        // { id: 5, location: "KHU VỰC MẶC ĐỊNH", street: "Hướng đường Thành Thái", time: "07:19:03 14/11/2022", area: "HẺM 7A THÀNH THÁI" },
        // { id: 6, location: "KHU VỰC MẶC ĐỊNH", street: "Hướng đường Thành Thái", time: "07:18:42 14/11/2022", area: "HẺM 7A THÀNH THÁI" },
    ];

    return (
        <div className="dashboard">
            {/* Header */}
            <header className="header">
                {/* <div className="nav-items">
                    <div className="nav-item active">Giao thông</div>
                    <div className="nav-item">Dashboard</div>
                    <div className="nav-item">Thiết bị</div>
                    <div className="nav-item">Quản lý người dùng</div>
                </div> */}
                {/* <div className="header-actions">
                    <button className="icon-button">
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            className="icon"
                            viewBox="0 0 20 20"
                            fill="currentColor"
                        >
                            <path
                                fillRule="evenodd"
                                d="M10 2a8 8 0 100 16 8 8 0 000-16zm0 14a6 6 0 100-12 6 6 0 000 12z"
                                clipRule="evenodd"
                            />
                        </svg>
                    </button>
                </div> */}
            </header>

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
                {intersectionFeeds.map((feed) => (
                    <IntersectionCard key={feed.id} feed={feed} />
                ))}
            </div>
        </div>
    );
};

// Traffic light component with timers

export default TrafficDashboard;
