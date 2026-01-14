/**
 * CommentThread Component
 * 
 * Collaboration UI for comments and @mentions on results.
 * - Comment list with replies
 * - Add new comment
 * - @mention support (UI ready)
 * - Ready for backend integration
 */

import React, { useState } from 'react';
import { 
  MessageSquare, 
  Send, 
  Reply,
  MoreHorizontal,
  AtSign
} from 'lucide-react';
import { GlassCard } from '../GlassCard';

export interface CommentUser {
  id: string;
  name: string;
  email?: string;
  avatar?: string;
}

export interface Comment {
  id: string;
  content: string;
  author: CommentUser;
  timestamp: string;
  replies?: Comment[];
  mentions?: string[];
}

export interface CommentThreadProps {
  /** List of comments */
  comments: Comment[];
  /** Current user (for posting) */
  currentUser?: CommentUser;
  /** Loading state */
  isLoading?: boolean;
  /** Callback when new comment submitted */
  onSubmitComment?: (content: string, mentions: string[]) => Promise<void>;
  /** Callback when reply submitted */
  onSubmitReply?: (commentId: string, content: string) => Promise<void>;
  /** Users available for @mention */
  mentionableUsers?: CommentUser[];
  /** Empty state message */
  emptyMessage?: string;
  /** Additional classes */
  className?: string;
}

/**
 * Format relative time
 */
function formatRelativeTime(timestamp: string): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}

/**
 * Single Comment component
 */
const CommentItem: React.FC<{
  comment: Comment;
  onReply?: (commentId: string, content: string) => void;
  isReply?: boolean;
}> = ({ comment, onReply, isReply = false }) => {
  const [showReplyInput, setShowReplyInput] = useState(false);
  const [replyContent, setReplyContent] = useState('');

  const handleSubmitReply = () => {
    if (replyContent.trim() && onReply) {
      onReply(comment.id, replyContent.trim());
      setReplyContent('');
      setShowReplyInput(false);
    }
  };

  return (
    <div className={`${isReply ? 'ml-10 mt-3' : ''}`}>
      <div className="flex items-start gap-3">
        {/* Avatar */}
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center flex-shrink-0">
          {comment.author.avatar ? (
            <img src={comment.author.avatar} alt="" className="w-full h-full rounded-full" />
          ) : (
            <span className="text-xs font-medium text-white">
              {comment.author.name.charAt(0).toUpperCase()}
            </span>
          )}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-white">{comment.author.name}</span>
              <span className="text-xs text-white/40">{formatRelativeTime(comment.timestamp)}</span>
            </div>
            <button className="p-1 text-white/30 hover:text-white/60 transition-colors">
              <MoreHorizontal className="w-4 h-4" />
            </button>
          </div>
          
          <p className="text-sm text-white/80 mt-1">{comment.content}</p>

          {/* Actions */}
          {!isReply && (
            <div className="flex items-center gap-3 mt-2">
              <button
                onClick={() => setShowReplyInput(!showReplyInput)}
                className="flex items-center gap-1 text-xs text-white/50 hover:text-white/80 transition-colors"
              >
                <Reply className="w-3.5 h-3.5" />
                Reply
              </button>
            </div>
          )}

          {/* Reply Input */}
          {showReplyInput && (
            <div className="flex items-center gap-2 mt-3">
              <input
                type="text"
                value={replyContent}
                onChange={(e) => setReplyContent(e.target.value)}
                placeholder="Write a reply..."
                className="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                onKeyPress={(e) => e.key === 'Enter' && handleSubmitReply()}
              />
              <button
                onClick={handleSubmitReply}
                disabled={!replyContent.trim()}
                className="p-2 bg-blue-500/20 text-blue-400 rounded-lg hover:bg-blue-500/30 transition-colors disabled:opacity-50"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          )}

          {/* Replies */}
          {comment.replies && comment.replies.length > 0 && (
            <div className="mt-3 space-y-3">
              {comment.replies.map((reply) => (
                <CommentItem key={reply.id} comment={reply} isReply />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export const CommentThread: React.FC<CommentThreadProps> = ({
  comments,
  currentUser,
  isLoading = false,
  onSubmitComment,
  onSubmitReply,
  mentionableUsers = [],
  emptyMessage = 'No comments yet. Start the conversation!',
  className = ''
}) => {
  const [newComment, setNewComment] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!newComment.trim() || !onSubmitComment) return;

    setIsSubmitting(true);
    try {
      // Extract @mentions from content
      const mentions = newComment.match(/@(\w+)/g)?.map(m => m.slice(1)) || [];
      await onSubmitComment(newComment.trim(), mentions);
      setNewComment('');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReply = (commentId: string, content: string) => {
    onSubmitReply?.(commentId, content);
  };

  return (
    <GlassCard className={className}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white flex items-center gap-2">
          <MessageSquare className="w-5 h-5 text-purple-400" />
          Comments
        </h3>
        <span className="text-xs text-white/50">
          {comments.length} comment{comments.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Comment Input */}
      {currentUser && (
        <div className="flex items-start gap-3 mb-4 pb-4 border-b border-white/10">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center flex-shrink-0">
            <span className="text-xs font-medium text-white">
              {currentUser.name.charAt(0).toUpperCase()}
            </span>
          </div>
          <div className="flex-1">
            <div className="relative">
              <textarea
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                placeholder="Add a comment... Use @ to mention"
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-blue-500/50 resize-none"
                rows={2}
              />
              {mentionableUsers.length > 0 && (
                <button className="absolute bottom-2 right-2 p-1 text-white/40 hover:text-white/70 transition-colors">
                  <AtSign className="w-4 h-4" />
                </button>
              )}
            </div>
            <div className="flex justify-end mt-2">
              <button
                onClick={handleSubmit}
                disabled={!newComment.trim() || isSubmitting}
                className="flex items-center gap-2 px-4 py-2 bg-blue-500/20 text-blue-400 rounded-lg hover:bg-blue-500/30 transition-colors disabled:opacity-50 text-sm font-medium"
              >
                <Send className="w-4 h-4" />
                Post
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Comments List */}
      {isLoading ? (
        <div className="space-y-4">
          {[1, 2].map((i) => (
            <div key={i} className="flex items-start gap-3 animate-pulse">
              <div className="w-8 h-8 rounded-full bg-white/10" />
              <div className="flex-1 space-y-2">
                <div className="h-4 w-24 bg-white/10 rounded" />
                <div className="h-10 w-full bg-white/10 rounded" />
              </div>
            </div>
          ))}
        </div>
      ) : comments.length === 0 ? (
        <div className="text-center py-8">
          <div className="w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center mx-auto mb-3">
            <MessageSquare className="w-6 h-6 text-white/30" />
          </div>
          <p className="text-white/50 text-sm">{emptyMessage}</p>
        </div>
      ) : (
        <div className="space-y-4">
          {comments.map((comment) => (
            <CommentItem 
              key={comment.id} 
              comment={comment} 
              onReply={handleReply}
            />
          ))}
        </div>
      )}
    </GlassCard>
  );
};

export default CommentThread;
