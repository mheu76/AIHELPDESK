'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { authApi, ticketApi, TicketDetail, TicketPriority, TicketStatus, User } from '@/lib/api';

export default function TicketDetailPage() {
  const router = useRouter();
  const params = useParams();
  const ticketId = typeof params?.id === 'string' ? params.id : '';

  const [ticket, setTicket] = useState<TicketDetail | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [commentText, setCommentText] = useState('');
  const [isInternal, setIsInternal] = useState(false);
  const [submittingComment, setSubmittingComment] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editStatus, setEditStatus] = useState<TicketStatus>('open');
  const [editPriority, setEditPriority] = useState<TicketPriority>('medium');
  const [submittingUpdate, setSubmittingUpdate] = useState(false);

  const isITStaff = user?.role === 'it_staff' || user?.role === 'admin';

  useEffect(() => {
    if (!ticketId) {
      setError('Invalid ticket id');
      setLoading(false);
      return;
    }
    void loadUserAndTicket();
  }, [ticketId]);

  const loadUserAndTicket = async () => {
    try {
      setLoading(true);
      setError('');

      const token = localStorage.getItem('access_token');
      if (!token) {
        router.push('/auth/login');
        return;
      }

      const [userData, ticketData] = await Promise.all([
        authApi.getMe(token),
        ticketApi.getTicket(ticketId),
      ]);

      setUser(userData);
      setTicket(ticketData);
      setEditStatus(ticketData.status);
      setEditPriority(ticketData.priority);
    } catch (err: any) {
      if (err.status === 403) {
        setError('You do not have permission to view this ticket.');
      } else if (err.status === 404) {
        setError('Ticket not found.');
      } else {
        setError(err.message || 'Failed to load ticket.');
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
        is_internal: isInternal,
      });

      const updated = await ticketApi.getTicket(ticketId);
      setTicket(updated);
      setCommentText('');
      setIsInternal(false);
    } catch (err: any) {
      if (err.status === 403) {
        setError('Only IT staff can create internal notes.');
      } else {
        setError(err.message || 'Failed to add comment.');
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
        priority: editPriority,
      });

      const updated = await ticketApi.getTicket(ticketId);
      setTicket(updated);
      setIsEditing(false);
    } catch (err: any) {
      setError(err.message || 'Failed to update ticket.');
    } finally {
      setSubmittingUpdate(false);
    }
  };

  const statusClasses: Record<TicketStatus, string> = {
    open: 'bg-blue-100 text-blue-800',
    in_progress: 'bg-yellow-100 text-yellow-800',
    resolved: 'bg-green-100 text-green-800',
    on_hold: 'bg-gray-100 text-gray-800',
    closed: 'bg-gray-100 text-gray-600',
  };

  const priorityClasses: Record<TicketPriority, string> = {
    low: 'bg-gray-100 text-gray-600',
    medium: 'bg-blue-100 text-blue-700',
    high: 'bg-orange-100 text-orange-700',
    urgent: 'bg-red-100 text-red-700',
  };

  const formatDate = (dateStr: string) =>
    new Date(dateStr).toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });

  if (loading) {
    return <div className="flex min-h-screen items-center justify-center bg-gray-50 text-gray-600">Loading ticket...</div>;
  }

  if (error && !ticket) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50 p-4">
        <div className="w-full max-w-md rounded-lg bg-white p-8 shadow-sm">
          <h2 className="mb-2 text-center text-xl font-bold">Error</h2>
          <p className="mb-6 text-center text-gray-600">{error}</p>
          <button
            onClick={() => router.push('/tickets')}
            className="w-full rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
          >
            Back to tickets
          </button>
        </div>
      </div>
    );
  }

  if (!ticket) return null;

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="mx-auto max-w-5xl space-y-6">
        <button onClick={() => router.push('/tickets')} className="text-sm text-gray-600 hover:text-gray-900">
          Back to tickets
        </button>

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-red-700">
            {error}
          </div>
        )}

        <div className="rounded-lg bg-white p-6 shadow-sm">
          <div className="mb-4 flex items-start justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                #{ticket.ticket_number} {ticket.title}
              </h1>
              <div className="mt-3 flex flex-wrap items-center gap-2">
                <span className={`rounded-full px-3 py-1 text-sm font-medium ${statusClasses[ticket.status]}`}>
                  {ticket.status}
                </span>
                <span className={`rounded-full px-3 py-1 text-sm font-medium ${priorityClasses[ticket.priority]}`}>
                  {ticket.priority}
                </span>
                <span className="rounded-full bg-gray-100 px-3 py-1 text-sm text-gray-700">{ticket.category}</span>
              </div>
            </div>

            {isITStaff && (
              <button
                onClick={() => setIsEditing(!isEditing)}
                className="rounded-md border border-blue-600 px-4 py-2 text-sm text-blue-600 hover:bg-blue-50"
              >
                {isEditing ? 'Cancel' : 'Edit'}
              </button>
            )}
          </div>

          {isEditing && isITStaff && (
            <div className="mt-4 border-t pt-4">
              <div className="mb-4 grid gap-4 md:grid-cols-2">
                <div>
                  <label className="mb-2 block text-sm font-medium text-gray-700">Status</label>
                  <select
                    value={editStatus}
                    onChange={(e) => setEditStatus(e.target.value as TicketStatus)}
                    className="w-full rounded-md border border-gray-300 px-3 py-2"
                  >
                    <option value="open">Open</option>
                    <option value="in_progress">In progress</option>
                    <option value="resolved">Resolved</option>
                    <option value="on_hold">On hold</option>
                    <option value="closed">Closed</option>
                  </select>
                </div>
                <div>
                  <label className="mb-2 block text-sm font-medium text-gray-700">Priority</label>
                  <select
                    value={editPriority}
                    onChange={(e) => setEditPriority(e.target.value as TicketPriority)}
                    className="w-full rounded-md border border-gray-300 px-3 py-2"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="urgent">Urgent</option>
                  </select>
                </div>
              </div>
              <button
                onClick={handleUpdateTicket}
                disabled={submittingUpdate}
                className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {submittingUpdate ? 'Saving...' : 'Save changes'}
              </button>
            </div>
          )}

          <div className="mt-6 grid gap-4 border-t pt-6 md:grid-cols-2">
            <div>
              <p className="text-sm text-gray-500">Requester</p>
              <p className="font-medium">{ticket.requester_name}</p>
              {ticket.requester_email && <p className="text-sm text-gray-600">{ticket.requester_email}</p>}
            </div>
            <div>
              <p className="text-sm text-gray-500">Assignee</p>
              <p className="font-medium">{ticket.assignee_name || 'Unassigned'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Created</p>
              <p className="font-medium">{formatDate(ticket.created_at)}</p>
            </div>
            {ticket.resolved_at && (
              <div>
                <p className="text-sm text-gray-500">Resolved</p>
                <p className="font-medium">{formatDate(ticket.resolved_at)}</p>
              </div>
            )}
            {ticket.session_id && (
              <div className="md:col-span-2">
                <p className="mb-1 text-sm text-gray-500">Related chat session</p>
                <button
                  onClick={() => router.push(`/chat?session=${ticket.session_id}`)}
                  className="text-sm text-blue-600 underline hover:text-blue-700"
                >
                  Open related chat
                </button>
              </div>
            )}
          </div>
        </div>

        <div className="rounded-lg bg-white p-6 shadow-sm">
          <h2 className="mb-3 text-lg font-semibold">Description</h2>
          <p className="whitespace-pre-wrap text-gray-700">{ticket.description}</p>
        </div>

        <div className="rounded-lg bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-lg font-semibold">Comments ({ticket.comments.length})</h2>

          <div className="mb-6 space-y-4">
            {ticket.comments.length === 0 ? (
              <p className="py-8 text-center text-gray-500">No comments yet.</p>
            ) : (
              ticket.comments.map((comment) => (
                <div
                  key={comment.id}
                  className={`rounded-lg border p-4 ${
                    comment.is_internal ? 'border-yellow-200 bg-yellow-50' : 'border-gray-200 bg-gray-50'
                  }`}
                >
                  <div className="mb-2 flex items-center justify-between gap-4">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-gray-900">{comment.author_name || 'Unknown'}</span>
                      {comment.is_internal && (
                        <span className="rounded bg-yellow-200 px-2 py-0.5 text-xs text-yellow-800">Internal</span>
                      )}
                    </div>
                    <span className="text-sm text-gray-500">{formatDate(comment.created_at)}</span>
                  </div>
                  <p className="whitespace-pre-wrap text-gray-700">{comment.content}</p>
                </div>
              ))
            )}
          </div>

          <form onSubmit={handleAddComment} className="border-t pt-6">
            <textarea
              value={commentText}
              onChange={(e) => setCommentText(e.target.value)}
              placeholder="Write a comment..."
              rows={4}
              className="mb-3 w-full rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <div className="flex items-center justify-between gap-4">
              <div>
                {isITStaff && (
                  <label className="flex items-center gap-2 text-sm text-gray-700">
                    <input
                      type="checkbox"
                      checked={isInternal}
                      onChange={(e) => setIsInternal(e.target.checked)}
                      className="rounded"
                    />
                    Internal note
                  </label>
                )}
              </div>
              <button
                type="submit"
                disabled={submittingComment || !commentText.trim()}
                className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {submittingComment ? 'Posting...' : 'Add comment'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
