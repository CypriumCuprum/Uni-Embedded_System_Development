import React, { useState, useEffect } from 'react';
import './RoadManager.css';

const RoadManager = () => {
    const server_url = "http://localhost:8080";
    const [roads, setRoads] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showAddModal, setShowAddModal] = useState(false);
    const [showEditModal, setShowEditModal] = useState(false);
    const [showDeleteModal, setShowDeleteModal] = useState(false);
    const [currentRoad, setCurrentRoad] = useState({});
    const [formData, setFormData] = useState({
        name: '',
        location: '',
        district: '',
        city: '',
        status: 'Active'
    });

    useEffect(() => {
        fetchRoads();
    }, []);

    const fetchRoads = async () => {
        try {
            setLoading(true);
            const response = await fetch(`${server_url}/api/roads`);
            const data = await response.json();
            setRoads(data);
            setLoading(false);
        } catch (error) {
            console.error('Error fetching roads:', error);
            setLoading(false);
        }
    };

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData({
            ...formData,
            [name]: value
        });
    };

    const handleAddRoad = async (e) => {
        e.preventDefault();
        try {
            const response = await fetch(`${server_url}/api/roads`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData),
            });

            if (response.ok) {
                setShowAddModal(false);
                setFormData({
                    name: '',
                    location: '',
                    district: '',
                    city: '',
                    status: 'Active'
                });
                fetchRoads();
            } else {
                console.error('Failed to add road');
            }
        } catch (error) {
            console.error('Error adding road:', error);
        }
    };

    const handleEditClick = (road) => {
        setCurrentRoad(road);
        setFormData({
            name: road.name,
            location: road.location,
            district: road.district,
            city: road.city,
            status: road.status
        });
        setShowEditModal(true);
    };

    const handleUpdateRoad = async (e) => {
        e.preventDefault();
        try {
            const response = await fetch(`${server_url}/api/roads/${currentRoad.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData),
            });

            if (response.ok) {
                setShowEditModal(false);
                fetchRoads();
            } else {
                console.error('Failed to update road');
            }
        } catch (error) {
            console.error('Error updating road:', error);
        }
    };

    const handleDeleteClick = (road) => {
        setCurrentRoad(road);
        setShowDeleteModal(true);
    };

    const handleDeleteRoad = async () => {
        try {
            const response = await fetch(`${server_url}/api/roads/${currentRoad.id}`, {
                method: 'DELETE',
            });

            if (response.ok) {
                setShowDeleteModal(false);
                fetchRoads();
            } else {
                console.error('Failed to delete road');
            }
        } catch (error) {
            console.error('Error deleting road:', error);
        }
    };

    return (
        <div className="road-manager">
            <header className="manager-header">
                <h1>Quản lý đường đi</h1>
                <button 
                    className="add-button"
                    onClick={() => {
                        setFormData({
                            name: '',
                            location: '',
                            district: '',
                            city: '',
                            status: 'Active'
                        });
                        setShowAddModal(true);
                    }}
                >
                    + Thêm đường mới
                </button>
            </header>

            <div className="roads-table-container">
                {loading ? (
                    <div className="loading">Đang tải dữ liệu...</div>
                ) : (
                    <table className="roads-table">
                        <thead>
                            <tr>
                                <th>Tên đường</th>
                                <th>Vị trí</th>
                                <th>Quận/Huyện</th>
                                <th>Thành phố</th>
                                <th>Trạng thái</th>
                                <th>Thao tác</th>
                            </tr>
                        </thead>
                        <tbody>
                            {roads.length > 0 ? (
                                roads.map((road) => (
                                    <tr key={road.id}>
                                        <td>{road.name}</td>
                                        <td>{road.location}</td>
                                        <td>{road.district}</td>
                                        <td>{road.city}</td>
                                        <td>
                                            <span className={`status ${road.status === 'Active' ? 'active' : 'inactive'}`}>
                                                {road.status=== 'Active' ? 'Hoạt động' : 'Không hoạt động'}
                                            </span>
                                        </td>
                                        <td className="action-buttons">
                                            <button 
                                                className="edit-button"
                                                onClick={() => handleEditClick(road)}
                                            >
                                                Sửa
                                            </button>
                                            <button 
                                                className="delete-button"
                                                onClick={() => handleDeleteClick(road)}
                                            >
                                                Xóa
                                            </button>
                                        </td>
                                    </tr>
                                ))
                            ) : (
                                <tr>
                                    <td colSpan="6" className="no-data">Không có dữ liệu</td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                )}
            </div>

            {/* Add Road Modal */}
            {showAddModal && (
                <div className="modal-overlay">
                    <div className="modal">
                        <div className="modal-header">
                            <h2>Thêm đường mới</h2>
                            <button className="close-button" onClick={() => setShowAddModal(false)}>×</button>
                        </div>
                        <form onSubmit={handleAddRoad}>
                            <div className="form-group">
                                <label htmlFor="name">Tên đường:</label>
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
                                <label htmlFor="location">Vị trí:</label>
                                <input
                                    type="text"
                                    id="location"
                                    name="location"
                                    value={formData.location}
                                    onChange={handleInputChange}
                                    required
                                />
                            </div>
                            <div className="form-group">
                                <label htmlFor="district">Quận/Huyện:</label>
                                <input
                                    type="text"
                                    id="district"
                                    name="district"
                                    value={formData.district}
                                    onChange={handleInputChange}
                                    required
                                />
                            </div>
                            <div className="form-group">
                                <label htmlFor="city">Thành phố:</label>
                                <input
                                    type="text"
                                    id="city"
                                    name="city"
                                    value={formData.city}
                                    onChange={handleInputChange}
                                    required
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

            {/* Edit Road Modal */}
            {showEditModal && (
                <div className="modal-overlay">
                    <div className="modal">
                        <div className="modal-header">
                            <h2>Sửa thông tin đường</h2>
                            <button className="close-button" onClick={() => setShowEditModal(false)}>×</button>
                        </div>
                        <form onSubmit={handleUpdateRoad}>
                            <div className="form-group">
                                <label htmlFor="edit-name">Tên đường:</label>
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
                                <label htmlFor="edit-location">Vị trí:</label>
                                <input
                                    type="text"
                                    id="edit-location"
                                    name="location"
                                    value={formData.location}
                                    onChange={handleInputChange}
                                    required
                                />
                            </div>
                            <div className="form-group">
                                <label htmlFor="edit-district">Quận/Huyện:</label>
                                <input
                                    type="text"
                                    id="edit-district"
                                    name="district"
                                    value={formData.district}
                                    onChange={handleInputChange}
                                    required
                                />
                            </div>
                            <div className="form-group">
                                <label htmlFor="edit-city">Thành phố:</label>
                                <input
                                    type="text"
                                    id="edit-city"
                                    name="city"
                                    value={formData.city}
                                    onChange={handleInputChange}
                                    required
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
                            <p>Bạn có chắc chắn muốn xóa đường <strong>{currentRoad.name}</strong>?</p>
                            <p className="warning">Thao tác này không thể hoàn tác.</p>
                        </div>
                        <div className="modal-actions">
                            <button type="button" className="cancel-button" onClick={() => setShowDeleteModal(false)}>
                                Hủy
                            </button>
                            <button type="button" className="delete-confirm-button" onClick={handleDeleteRoad}>
                                Xóa
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default RoadManager;