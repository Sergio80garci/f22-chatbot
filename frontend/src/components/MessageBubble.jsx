import ReactMarkdown from 'react-markdown'

const FILE_ICON = { pdf: '📄', docx: '📝', xlsx: '📊' }

function getIcon(filename) {
  const ext = filename.split('.').pop().toLowerCase()
  return FILE_ICON[ext] || '📄'
}

export default function MessageBubble({ role, content, sources, relatedQuestions = [], onSendMessage }) {
  const isUser = role === 'user'

  return (
    <div className={`message-wrapper ${isUser ? 'user' : 'assistant'}`}>
      {/* Header label */}
      <span style={{
        fontSize: '0.72rem',
        color: 'var(--sii-gris)',
        marginBottom: '0.25rem',
        paddingLeft: isUser ? 0 : '0.25rem',
      }}>
        {isUser ? 'Tú' : 'Asistente F22'}
      </span>

      <div className={`message-bubble ${isUser ? 'user' : 'assistant'}`}>
        {isUser ? (
          <span>{content}</span>
        ) : (
          <div className="markdown-body">
            <ReactMarkdown>{content}</ReactMarkdown>
          </div>
        )}
      </div>

      {/* Sources */}
      {!isUser && sources && sources.length > 0 && (
        <div className="message-sources">
          <span style={{ fontSize: '0.74rem', color: 'var(--sii-gris)', alignSelf: 'center' }}>
            Fuentes:
          </span>
          {sources.map(src => (
            <span key={src} className="source-tag" title={src}>
              {getIcon(src)} {src}
            </span>
          ))}
        </div>
      )}

      {/* Related Questions */}
      {!isUser && relatedQuestions && relatedQuestions.length > 0 && (
        <div className="related-questions">
          <p style={{ fontSize: '0.8rem', color: 'var(--sii-gris)', marginBottom: '0.4rem' }}>
            Preguntas relacionadas:
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
            {relatedQuestions.map((q, idx) => (
              <button
                key={idx}
                onClick={() => onSendMessage(q)}
                className="related-question-btn"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
