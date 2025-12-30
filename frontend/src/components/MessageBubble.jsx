const MessageBubble = ({ message }) => {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
          isUser
            ? 'bg-indigo-600 text-white'
            : 'bg-gray-100 text-gray-800'
        }`}
      >
        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        {message.data && message.intent === 'leave_request' && (
          <div className="mt-2 pt-2 border-t border-gray-300">
            <p className="text-xs opacity-90">
              ✓ Leave request created successfully
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default MessageBubble;


