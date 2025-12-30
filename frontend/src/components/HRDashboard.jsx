import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import { logout } from '../services/auth';
import ChatInterface from './ChatInterface';

const HRDashboard = () => {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const { user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    fetchRequests();
  }, []);

  const fetchRequests = async () => {
    try {
      console.log('Fetching leave requests...');
      const response = await api.get('/api/requests/all');
      console.log('Requests fetched:', response.data);
      setRequests(response.data);
    } catch (error) {
      console.error('Error fetching requests:', error);
      console.error('Error details:', error.response?.data);
      alert(`Failed to load requests: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (requestId) => {
    try {
      await api.patch(`/api/requests/${requestId}/approve`);
      fetchRequests();
    } catch (error) {
      console.error('Error approving request:', error);
      alert('Failed to approve request');
    }
  };

  const handleReject = async (requestId) => {
    try {
      await api.patch(`/api/requests/${requestId}/reject`);
      fetchRequests();
    } catch (error) {
      console.error('Error rejecting request:', error);
      alert('Failed to reject request');
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const filteredRequests = requests.filter((req) => {
    if (filter === 'all') return true;
    return req.status === filter;
  });

  const getStatusColor = (status) => {
    switch (status) {
      case 'approved':
        return 'bg-green-100 text-green-800';
      case 'rejected':
        return 'bg-red-100 text-red-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="h-screen flex flex-col bg-gradient-to-br from-blue-50 to-indigo-100">
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-800">HR Dashboard</h1>
          <div className="flex items-center space-x-4">
            <span className="text-gray-600">Welcome, {user?.full_name}</span>
            <button
              onClick={handleLogout}
              className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        {/* Requests Section */}
        <div className="flex-1 bg-white m-4 rounded-lg shadow-lg flex flex-col">
          <div className="bg-indigo-600 text-white px-6 py-4 rounded-t-lg flex justify-between items-center">
            <h2 className="text-xl font-semibold">Leave Requests</h2>
            <div className="flex space-x-2">
              <button
                onClick={() => setFilter('all')}
                className={`px-3 py-1 rounded text-sm ${
                  filter === 'all' ? 'bg-white text-indigo-600' : 'bg-indigo-500 text-white'
                }`}
              >
                All
              </button>
              <button
                onClick={() => setFilter('pending')}
                className={`px-3 py-1 rounded text-sm ${
                  filter === 'pending' ? 'bg-white text-indigo-600' : 'bg-indigo-500 text-white'
                }`}
              >
                Pending
              </button>
              <button
                onClick={() => setFilter('approved')}
                className={`px-3 py-1 rounded text-sm ${
                  filter === 'approved' ? 'bg-white text-indigo-600' : 'bg-indigo-500 text-white'
                }`}
              >
                Approved
              </button>
              <button
                onClick={() => setFilter('rejected')}
                className={`px-3 py-1 rounded text-sm ${
                  filter === 'rejected' ? 'bg-white text-indigo-600' : 'bg-indigo-500 text-white'
                }`}
              >
                Rejected
              </button>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto p-4">
            {loading ? (
              <div className="text-center text-gray-500">Loading...</div>
            ) : filteredRequests.length === 0 ? (
              <div className="text-center text-gray-500 mt-8">
                <p>No requests found.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {filteredRequests.map((request) => (
                  <div
                    key={request.id}
                    className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm"
                  >
                    <div className="flex justify-between items-start mb-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-semibold text-gray-800 capitalize">
                            {request.request_type} Leave
                          </h3>
                          {request.user_name && (
                            <span className="text-xs text-gray-500">by {request.user_name}</span>
                          )}
                        </div>
                        <p className="text-sm text-gray-600">
                          {request.start_date} to {request.end_date} ({request.duration_days} days)
                        </p>
                        {request.user_email && (
                          <p className="text-xs text-gray-500 mt-1">{request.user_email}</p>
                        )}
                      </div>
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-semibold ${getStatusColor(
                          request.status
                        )}`}
                      >
                        {request.status.toUpperCase()}
                      </span>
                    </div>
                    {request.reason && (
                      <p className="text-sm text-gray-600 mb-2">Reason: {request.reason}</p>
                    )}
                    {request.reviewed_by_name && (
                      <p className="text-xs text-gray-500 mb-2">
                        Reviewed by: {request.reviewed_by_name} on {request.reviewed_at ? new Date(request.reviewed_at).toLocaleDateString() : ''}
                      </p>
                    )}
                    <div className="flex justify-end space-x-2">
                      {request.status === 'pending' && (
                        <>
                          <button
                            onClick={() => handleApprove(request.id)}
                            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                          >
                            Approve
                          </button>
                          <button
                            onClick={() => handleReject(request.id)}
                            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                          >
                            Reject
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Chat Section */}
        <div className="w-96 bg-white m-4 rounded-lg shadow-lg flex flex-col">
          <div className="bg-indigo-600 text-white px-6 py-4 rounded-t-lg">
            <h2 className="text-xl font-semibold">HR Assistant</h2>
          </div>
          <div className="flex-1 overflow-hidden">
            <ChatInterface />
          </div>
        </div>
      </div>
    </div>
  );
};

export default HRDashboard;

