import React, { useState, useEffect } from 'react';
import './DeviceManager.css';

const DeviceManager = () => {
    const server_url = "http://localhost:8080";
    const [devices, setDevices] = useState([]);
    const [roads, setRoads] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showAddModal, setShowAddModal] = useState(false);
    const [showEditModal, setShowEditModal] = useState(false);
    const [showDeleteModal, setShowDeleteModal] = useState(false);
    const [currentDevice, setCurrentDevice] = useState({});
    const [formData, setFormData] = useState({
        name: '',
        device_id: '',
        road_id: '',
        type: 'camera', // Default type
        status: 'Active',
        ip_address: '',
        location_details: '',
        direction_from: '', // New field
        direction_to: ''    // New field
    });

    const directions = ['North', 'South', 'East', 'West'];

    useEffect(() => {
        fetchDevices();
        fetchRoads();
    }, []);

    const fetchDevices = async () => {
        try {
            setLoading(true);
            const response = await fetch(`${server_url}/api/devices`);
            const data = await response.json();
            setDevices(data);
            setLoading(false);
        } catch (error) {
            console.error('Error fetching devices:', error);
            setLoading(false);
        }
    };

    const fetchRoads = async () => {
        try {
            const response = await fetch(`${server_url}/api/roads`);
            const data = await response.json();
            setRoads(data);
        } catch (error) {
            console.error('Error fetching roads:', error);
        }
    };

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData({
            ...formData,
            [name]: value
        });
    };

    const handleAddDevice = async (e) => {
        e.preventDefault();
        try {
            const response = await fetch(`${server_url}/api/devices`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData),
            });

            if (response.ok) {
                console.log(await response.json())
                setShowAddModal(false);
                resetForm();
                fetchDevices();
            } else {
                console.error('Failed to add device');
            }
        } catch (error) {
            console.error('Error adding device:', error);
        }
    };

    const handleEditClick = (device) => {
        setCurrentDevice(device);
        setFormData({
            name: device.name,
            device_id: device.device_id,
            road_id: device.road_id,
            type: device.type,
            status: device.status,
            ip_address: device.ip_address || '',
            location_details: device.location_details || ''
        });
        setShowEditModal(true);
    };

    const handleUpdateDevice = async (e) => {
        e.preventDefault();
        try {
            const response = await fetch(`${server_url}/api/devices/${currentDevice.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData),
            });

            if (response.ok) {
                setShowEditModal(false);
                fetchDevices();
            } else {
                console.error('Failed to update device');
            }
        } catch (error) {
            console.error('Error updating device:', error);
        }
    };

    const handleDeleteClick = (device) => {
        setCurrentDevice(device);
        setShowDeleteModal(true);
    };

    const handleDeleteDevice = async () => {
        try {
            const response = await fetch(`${server_url}/api/devices/${currentDevice.id}`, {
                method: 'DELETE',
            });

            if (response.ok) {
                setShowDeleteModal(false);
                fetchDevices();
            } else {
                console.error('Failed to delete device');
            }
        } catch (error) {
            console.error('Error deleting device:', error);
        }
    };

    const resetForm = () => {
        setFormData({
            name: '',
            device_id: '',
            road_id: '',
            type: 'camera',
            status: 'Active',
            ip_address: '',
            location_details: ''
        });
    };

    const getDeviceTypeLabel = (type) => {
        switch (type) {
            case 'camera':
                return 'Camera';
            case 'traffic_light':
                return 'Đèn giao thông';
            default:
                return type;
        }
    };

    const getRoadNameById = (roadId) => {
        const road = roads.find(r => r.id === roadId);
        return road ? road.name : 'Không xác định';
    };

    const renderDirectionFields = () => {
        if (formData.type !== 'camera') {
            return null;
        }
        return (
            <>
                <div className="form-group">
                    <label htmlFor="direction_from">Hướng từ (Direction From):</label>
                    <select
                        id="direction_from"
                        name="direction_from"
                        value={formData.direction_from}
                        onChange={handleInputChange}
                        // required // Make it required if a camera always needs this
                    >
                        <option value="">-- Chọn hướng --</option>
                        {directions.map(dir => (
                            <option key={`from-${dir}`} value={dir}>{dir}</option>
                        ))}
                    </select>
                </div>
                <div className="form-group">
                    <label htmlFor="direction_to">Hướng đến (Direction To):</label>
                    <select
                        id="direction_to"
                        name="direction_to"
                        value={formData.direction_to}
                        onChange={handleInputChange}
                        // required // Make it required if a camera always needs this
                    >
                        <option value="">-- Chọn hướng --</option>
                        {directions.map(dir => (
                            <option key={`to-${dir}`} value={dir}>{dir}</option>
                        ))}
                    </select>
                </div>
            </>
        );
    };

    return (
        <div className="device-manager">
            <header className="manager-header">
                <h1>Quản lý thiết bị</h1>
                <button 
                    className="add-button"
                    onClick={() => {
                        resetForm();
                        setShowAddModal(true);
                    }}
                >
                    + Thêm thiết bị mới
                </button>
            </header>

            <div className="devices-table-container">
                {loading ? (
                    <div className="loading">Đang tải dữ liệu...</div>
                ) : (
                    <table className="devices-table">
                        <thead>
                            <tr>
                                <th>Tên thiết bị</th>
                                <th>ID thiết bị</th>
                                <th>Đường</th>
                                <th>Loại thiết bị</th>
                                <th>Địa chỉ IP</th>
                                <th>Trạng thái</th>
                                <th>Thao tác</th>
                            </tr>
                        </thead>
                        <tbody>
                            {devices.length > 0 ? (
                                devices.map((device) => (
                                    <tr key={device.id}>
                                        <td>{device.name}</td>
                                        <td>{device.device_id}</td>
                                        <td>{getRoadNameById(device.road_id)}</td>
                                        <td>{getDeviceTypeLabel(device.type)}</td>
                                        <td>{device.ip_address || '—'}</td>
                                        <td>
                                            <span className={`status ${device.status === 'Active' ? 'active' : 'inactive'}`}>
                                                {device.status === 'Active' ? 'Hoạt động' : 'Không hoạt động'}
                                            </span>
                                        </td>
                                        <td className="action-buttons">
                                            <button 
                                                className="edit-button"
                                                onClick={() => handleEditClick(device)}
                                            >
                                                Sửa
                                            </button>
                                            <button 
                                                className="delete-button"
                                                onClick={() => handleDeleteClick(device)}
                                            >
                                                Xóa
                                            </button>
                                        </td>
                                    </tr>
                                ))
                            ) : (
                                <tr>
                                    <td colSpan="7" className="no-data">Không có dữ liệu</td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                )}
            </div>

            {/* Add Device Modal */}
            {showAddModal && (
                <div className="modal-overlay">
                    <div className="modal">
                        <div className="modal-header">
                            <h2>Thêm thiết bị mới</h2>
                            <button className="close-button" onClick={() => setShowAddModal(false)}>×</button>
                        </div>
                        <form onSubmit={handleAddDevice}>
                            <div className="form-group">
                                <label htmlFor="name">Tên thiết bị:</label>
                                <input
                                    type="text"
                                    id="name"
                                    name="name"
                                    value={formData.name}
                                    onChange={handleInputChange}
                                    required
                                />
                            </div>
                            <div className="form-group">
                                <label htmlFor="device_id">ID thiết bị:</label>
                                <input
                                    type="text"
                                    id="device_id"
                                    name="device_id"
                                    value={formData.device_id}
                                    onChange={handleInputChange}
                                    required
                                />
                            </div>
                            <div className="form-group">
                                <label htmlFor="road_id">Đường:</label>
                                <select
                                    id="road_id"
                                    name="road_id"
                                    value={formData.road_id}
                                    onChange={handleInputChange}
                                    required
                                >
                                    <option value="">-- Chọn đường --</option>
                                    {roads.map((road) => (
                                        <option key={road.id} value={road.id}>
                                            {road.location} {road.name} 
                                        </option>
                                    ))}
                                </select>
                            </div>
                            <div className="form-group">
                                <label htmlFor="type">Loại thiết bị:</label>
                                <select
                                    id="type"
                                    name="type"
                                    value={formData.type}
                                    onChange={handleInputChange}
                                    required
                                >
                                    <option value="camera">Camera</option>
                                    <option value="traffic_light">Đèn giao thông</option>
                                </select>
                            </div>
                            {/* Conditionally rendered direction fields */}
                            {renderDirectionFields()}
                            <div className="form-group">
                                <label htmlFor="ip_address">Địa chỉ IP:</label>
                                <input
                                    type="text"
                                    id="ip_address"
                                    name="ip_address"
                                    value={formData.ip_address}
                                    onChange={handleInputChange}
                                    placeholder="Ví dụ: 192.168.1.100"
                                />
                            </div>
                            <div className="form-group">
                                <label htmlFor="location_details">Chi tiết vị trí:</label>
                                <input
                                    type="text"
                                    id="location_details"
                                    name="location_details"
                                    value={formData.location_details}
                                    onChange={handleInputChange}
                                    placeholder="Ví dụ: Ngã tư phía Bắc"
                                />
                            </div>
                            <div className="form-group">
                                <label htmlFor="status">Trạng thái:</label>
                                <select
                                    id="status"
                                    name="status"
                                    value={formData.status}
                                    onChange={handleInputChange}
                                >
                                    <option value="Active">Hoạt động</option>
                                    <option value="Inactive">Không hoạt động</option>
                                </select>
                            </div>
                            <div className="modal-actions">
                                <button type="button" className="cancel-button" onClick={() => setShowAddModal(false)}>
                                    Hủy
                                </button>
                                <button type="submit" className="save-button">
                                    Lưu
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Edit Device Modal */}
            {showEditModal && (
                <div className="modal-overlay">
                    <div className="modal">
                        <div className="modal-header">
                            <h2>Sửa thông tin thiết bị</h2>
                            <button className="close-button" onClick={() => setShowEditModal(false)}>×</button>
                        </div>
                        <form onSubmit={handleUpdateDevice}>
                            <div className="form-group">
                                <label htmlFor="edit-name">Tên thiết bị:</label>
                                <input
                                    type="text"
                                    id="edit-name"
                                    name="name"
                                    value={formData.name}
                                    onChange={handleInputChange}
                                    required
                                />
                            </div>
                            <div className="form-group">
                                <label htmlFor="edit-device_id">ID thiết bị:</label>
                                <input
                                    type="text"
                                    id="edit-device_id"
                                    name="device_id"
                                    value={formData.device_id}
                                    onChange={handleInputChange}
                                    required
                                />
                            </div>
                            <div className="form-group">
                                <label htmlFor="edit-road_id">Đường:</label>
                                <select
                                    id="edit-road_id"
                                    name="road_id"
                                    value={formData.road_id}
                                    onChange={handleInputChange}
                                    required
                                >
                                    <option value="">-- Chọn đường --</option>
                                    {roads.map((road) => (
                                        <option key={road.id} value={road.id}>
                                            {road.location} {road.name}
                                        </option>
                                    ))}
                                </select>
                            </div>
                            <div className="form-group">
                                <label htmlFor="edit-type">Loại thiết bị:</label>
                                <select
                                    id="edit-type"
                                    name="type"
                                    value={formData.type}
                                    onChange={handleInputChange}
                                    required
                                >
                                    <option value="camera">Camera</option>
                                    <option value="traffic_light">Đèn giao thông</option>
                                </select>
                            </div>
                            <div className="form-group">
                                <label htmlFor="edit-ip_address">Địa chỉ IP:</label>
                                <input
                                    type="text"
                                    id="edit-ip_address"
                                    name="ip_address"
                                    value={formData.ip_address}
                                    onChange={handleInputChange}
                                    placeholder="Ví dụ: 192.168.1.100"
                                />
                            </div>
                            <div className="form-group">
                                <label htmlFor="edit-location_details">Chi tiết vị trí:</label>
                                <input
                                    type="text"
                                    id="edit-location_details"
                                    name="location_details"
                                    value={formData.location_details}
                                    onChange={handleInputChange}
                                    placeholder="Ví dụ: Ngã tư phía Bắc"
                                />
                            </div>
                            <div className="form-group">
                                <label htmlFor="edit-status">Trạng thái:</label>
                                <select
                                    id="edit-status"
                                    name="status"
                                    value={formData.status}
                                    onChange={handleInputChange}
                                >
                                    <option value="Active">Hoạt động</option>
                                    <option value="Inactive">Không hoạt động</option>
                                </select>
                            </div>
                            <div className="modal-actions">
                                <button type="button" className="cancel-button" onClick={() => setShowEditModal(false)}>
                                    Hủy
                                </button>
                                <button type="submit" className="save-button">
                                    Cập nhật
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Delete Confirmation Modal */}
            {showDeleteModal && (
                <div className="modal-overlay">
                    <div className="modal delete-modal">
                        <div className="modal-header">
                            <h2>Xác nhận xóa</h2>
                            <button className="close-button" onClick={() => setShowDeleteModal(false)}>×</button>
                        </div>
                        <div className="delete-content">
                            <p>Bạn có chắc chắn muốn xóa thiết bị <strong>{currentDevice.name}</strong>?</p>
                            <p className="warning">Thao tác này không thể hoàn tác.</p>
                        </div>
                        <div className="modal-actions">
                            <button type="button" className="cancel-button" onClick={() => setShowDeleteModal(false)}>
                                Hủy
                            </button>
                            <button type="button" className="delete-confirm-button" onClick={handleDeleteDevice}>
                                Xóa
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default DeviceManager;