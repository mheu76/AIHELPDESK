'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { ticketApi, authApi, TicketDetail, TicketComment, TicketStatus, TicketPriority, User } from '@/lib/api';

export default function TicketDetailPage() {
  const router = useRouter();
  const params = useParams();
  const ticketId = params.id as string;

  const [ticket, setTicket] = useState<TicketDetail | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Comment form
  const [commentText, setCommentText] = useState('');
  const [isInternal, setIsInternal] = useState(false);
  const [submittingComment, setSubmittingComment] = useState(false);

  // Update form (IT staff only)
  const [isEditing, setIsEditing] = useState(false);
  const [editStatus, setEditStatus] = useState<TicketStatus>('open');
  const [editPriority, setEditPriority] = useState<TicketPriority>('medium');
  const [submittingUpdate, setSubmittingUpdate] = useState(false);

  const isITStaff = user?.role === 'it_staff' || user?.role === 'admin';

  useEffect(() => {
    loadUserAndTicket();
  }, [ticketId]);

  const loadUserAndTicket = async () => {
    try {
      setLoading(true);
      setError('');

      const token = localStorage.getItem('access_token');
      if (!token) {
        router.push('/login');
        return;
      }

      const [userData, ticketData] = await Promise.all([
        authApi.getMe(token),
        ticketApi.getTicket(ticketId)
      ]);

      setUser(userData);
      setTicket(ticketData);
      setEditStatus(ticketData.status);
      setEditPriority(ticketData.priority);
    } catch (err: any) {
      if (err.status === 403) {
        setError('이 티켓에 접근할 권한이 없습니다');
      } else if (err.status === 404) {
        setError('티켓을 찾을 수 없습니다');
      } else {
        setError(err.message || '티켓을 불러오는데 실패했습니다');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleAddComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!commentText.trim()) return;

    try {
      setSubmittingComment(true);
      setError('');

      await ticketApi.addComment(ticketId, {
        content: commentText,
        is_internal: isInternal
      });

      // Reload ticket to get new comment
      const updated = await ticketApi.getTicket(ticketId);
      setTicket(updated);
      setCommentText('');
      setIsInternal(false);
    } catch (err: any) {
      if (err.status === 403) {
        setError('내부 메모는 IT 담당자만 작성할 수 있습니다');
      } else {
        setError(err.message || '코멘트 추가에 실패했습니다');
      }
    } finally {
      setSubmittingComment(false);
    }
  };

  const handleUpdateTicket = async () => {
    if (!ticket) return;

    try {
      setSubmittingUpdate(true);
      setError('');

      await ticketApi.updateTicket(ticketId, {
        status: editStatus,
        priority: editPriority
      });

      // Reload ticket
      const updated = await ticketApi.getTicket(ticketId);
      setTicket(updated);
      setIsEditing(false);
    } catch (err: any) {
      setError(err.message || '티켓 업데이트에 실패했습니다');
    } finally {
      setSubmittingUpdate(false);
    }
  };

  const getStatusBadge = (status: TicketStatus) => {
    const colors: Record<TicketStatus, string> = {
      open: 'bg-blue-100 text-blue-800',
      in_progress: 'bg-yellow-100 text-yellow-800',
      resolved: 'bg-green-100 text-green-800',
      on_hold: 'bg-gray-100 text-gray-800',
      closed: 'bg-gray-100 text-gray-600'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getPriorityBadge = (priority: TicketPriority) => {
    const colors: Record<TicketPriority, string> = {
      low: 'bg-gray-100 text-gray-600',
      medium: 'bg-blue-100 text-blue-700',
      high: 'bg-orange-100 text-orange-700',
      urgent: 'bg-red-100 text-red-700'
    };
    return colors[priority] || 'bg-gray-100 text-gray-800';
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">티켓을 불러오는 중...</p>
        </div>
      </div>
    );
  }

  if (error && !ticket) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-sm p-8 max-w-md w-full">
          <div className="text-red-600 text-center mb-4">⚠️</div>
          <h2 className="text-xl font-bold text-center mb-2">오류</h2>
          <p className="text-gray-600 text-center mb-6">{error}</p>
          <button
            onClick={() => router.push('/tickets')}
            className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            티켓 목록으로 돌아가기
          </button>
        </div>
      </div>
    );
  }

  if (!ticket) return null;

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-5xl mx-auto">
        {/* Back button */}
        <button
          onClick={() => router.push('/tickets')}
          className="mb-6 text-gray-600 hover:text-gray-900 flex items-center gap-2"
        >
          ← 티켓 목록으로
        </button>

        {/* Error banner */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {/* Ticket Header */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="flex items-start justify-between mb-4">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <h1 className="text-2xl font-bold text-gray-900">
                  #{ticket.ticket_number} {ticket.title}
                </h1>
              </div>
              <div className="flex items-center gap-2 flex-wrap">
                <span className={`px-3 py-1 text-sm font-medium rounded-full ${getStatusBadge(ticket.status)}`}>
                  {ticket.status}
                </span>
                <span className={`px-3 py-1 text-sm font-medium rounded-full ${getPriorityBadge(ticket.priority)}`}>
                  {ticket.priority}
                </span>
                <span className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded-full">
                  {ticket.category}
                </span>
              </div>
            </div>

            {isITStaff && (
              <button
                onClick={() => setIsEditing(!isEditing)}
                className="px-4 py-2 text-sm text-blue-600 hover:text-blue-700 border border-blue-600 rounded-md hover:bg-blue-50"
              >
                {isEditing ? '취소' : '수정'}
              </button>
            )}
          </div>

          {/* Edit form (IT staff only) */}
          {isEditing && isITStaff && (
            <div className="border-t pt-4 mt-4">
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    상태
                  </label>
                  <select
                    value={editStatus}
                    onChange={(e) => setEditStatus(e.target.value as TicketStatus)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="open">접수</option>
                    <option value="in_progress">진행중</option>
                    <option value="resolved">해결됨</option>
                    <option value="on_hold">보류</option>
                    <option value="closed">종료</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    우선순위
                  </label>
                  <select
                    value={editPriority}
                    onChange={(e) => setEditPriority(e.target.value as TicketPriority)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="low">낮음</option>
                    <option value="medium">보통</option>
                    <option value="high">높음</option>
                    <option value="urgent">긴급</option>
                  </select>
                </div>
              </div>
              <button
                onClick={handleUpdateTicket}
                disabled={submittingUpdate}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {submittingUpdate ? '업데이트 중...' : '저장'}
              </button>
            </div>
          )}

          {/* Ticket metadata */}
          <div className="grid grid-cols-2 gap-4 mt-6 pt-6 border-t">
            <div>
              <p className="text-sm text-gray-500">요청자</p>
              <p className="font-medium">{ticket.requester_name}</p>
              {ticket.requester_email && (
                <p className="text-sm text-gray-600">{ticket.requester_email}</p>
              )}
            </div>
            <div>
              <p className="text-sm text-gray-500">담당자</p>
              <p className="font-medium">{ticket.assignee_name || '미배정'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">생성일</p>
              <p className="font-medium">{formatDate(ticket.created_at)}</p>
            </div>
            {ticket.resolved_at && (
              <div>
                <p className="text-sm text-gray-500">해결일</p>
                <p className="font-medium">{formatDate(ticket.resolved_at)}</p>
              </div>
            )}
            {ticket.session_id && (
              <div className="col-span-2">
                <p className="text-sm text-gray-500 mb-1">연결된 채팅</p>
                <button
                  onClick={() => router.push(`/chat?session=${ticket.session_id}`)}
                  className="text-blue-600 hover:text-blue-700 text-sm underline"
                >
                  채팅 세션 보기 →
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Description */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <h2 className="text-lg font-semibold mb-3">상세 내용</h2>
          <p className="text-gray-700 whitespace-pre-wrap">{ticket.description}</p>
        </div>

        {/* Comments */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">코멘트 ({ticket.comments.length})</h2>

          {/* Comment list */}
          <div className="space-y-4 mb-6">
            {ticket.comments.length === 0 ? (
              <p className="text-gray-500 text-center py-8">아직 코멘트가 없습니다</p>
            ) : (
              ticket.comments.map((comment) => (
                <div
                  key={comment.id}
                  className={`border rounded-lg p-4 ${
                    comment.is_internal ? 'bg-yellow-50 border-yellow-200' : 'bg-gray-50 border-gray-200'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-gray-900">
                        {comment.author_name || '익명'}
                      </span>
                      {comment.is_internal && (
                        <span className="px-2 py-0.5 text-xs bg-yellow-200 text-yellow-800 rounded">
                          내부 메모
                        </span>
                      )}
                    </div>
                    <span className="text-sm text-gray-500">
                      {formatDate(comment.created_at)}
                    </span>
                  </div>
                  <p className="text-gray-700 whitespace-pre-wrap">{comment.content}</p>
                </div>
              ))
            )}
          </div>

          {/* Add comment form */}
          <form onSubmit={handleAddComment} className="border-t pt-6">
            <textarea
              value={commentText}
              onChange={(e) => setCommentText(e.target.value)}
              placeholder="코멘트를 입력하세요..."
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 mb-3"
            />
            <div className="flex items-center justify-between">
              <div>
                {isITStaff && (
                  <label className="flex items-center gap-2 text-sm text-gray-700">
                    <input
                      type="checkbox"
                      checked={isInternal}
                      onChange={(e) => setIsInternal(e.target.checked)}
                      className="rounded"
                    />
                    내부 메모 (임직원에게 보이지 않음)
                  </label>
                )}
              </div>
              <button
                type="submit"
                disabled={submittingComment || !commentText.trim()}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {submittingComment ? '등록 중...' : '코멘트 추가'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
