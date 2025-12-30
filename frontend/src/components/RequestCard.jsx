const RequestCard = ({ request }) => {
  const getStatusColor = (status) => {
    switch (status) {
      case 'approved':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'rejected':
        return 'bg-red-100 text-red-800 border-red-300';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-4 border border-gray-200">
      <div className="flex justify-between items-start mb-2">
        <div>
          <h3 className="font-semibold text-gray-800 capitalize">{request.request_type} Leave</h3>
          <p className="text-sm text-gray-600">
            {request.start_date} to {request.end_date}
          </p>
        </div>
        <span
          className={`px-3 py-1 rounded-full text-xs font-semibold border ${getStatusColor(
            request.status
          )}`}
        >
          {request.status.toUpperCase()}
        </span>
      </div>
      <div className="text-sm text-gray-600">
        <p>Duration: {request.duration_days} day(s)</p>
        {request.reason && <p className="mt-1">Reason: {request.reason}</p>}
        <p className="mt-1 text-xs text-gray-500">
          Created: {new Date(request.created_at).toLocaleDateString()}
        </p>
      </div>
    </div>
  );
};

export default RequestCard;


